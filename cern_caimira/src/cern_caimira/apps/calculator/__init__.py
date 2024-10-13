# This module is part of CAiMIRA. Please see the repository at
# https://gitlab.cern.ch/caimira/caimira for details of the license and terms of use.

import ast
import logging
import asyncio
import concurrent.futures
import datetime
import base64
import functools
import html
import json
import importlib.metadata
from pprint import pformat
import os
from pathlib import Path
import traceback
import typing
import uuid
import zlib

import jinja2
import loky
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.log
from caimira import __version__ as calculator_version
from caimira.calculator.models.profiler import CaimiraProfiler, Profilers
from caimira.calculator.store.data_registry import DataRegistry
from caimira.calculator.store.data_service import DataService

from caimira.api.controller import virus_report_controller, co2_report_controller
from caimira.calculator.report.virus_report_data import calculate_report_data
from caimira.calculator.validators.virus import virus_validator

from . import markdown_tools
from .report.virus_report import VirusReportGenerator
from ..calculator.report.co2_report import CO2ReportGenerator
from .user import AuthenticatedUser, AnonymousUser

LOG = logging.getLogger("Calculator")


class ProfilerPage(RequestHandler):
    """Render the profiler page.

    This class does not inherit from BaseRequestHandler to avoid profiling the
    profiler page itself.
    """
    def get(self) -> None:
        profiler = CaimiraProfiler()

        template_environment = self.settings["template_environment"]
        template = template_environment.get_template("profiler.html.j2")
        report = template.render(
            user=AnonymousUser(),
            active_page="Profiler",
            xsrf_form_html=self.xsrf_form_html(),
            is_active=profiler.is_active,
            sessions=profiler.sessions,
        )
        self.finish(report)

    def post(self) -> None:
        profiler = CaimiraProfiler()

        if self.get_argument("start", None) is not None:
            name = self.get_argument("name", None)
            profiler_type = Profilers.from_str(self.get_argument("profiler_type", ""))
            profiler.start_session(name, profiler_type)
        elif self.get_argument("stop", None) is not None:
            profiler.stop_session()
        elif self.get_argument("clear", None) is not None:
            profiler.clear_sessions()

        self.redirect(CaimiraProfiler.ROOT_URL)


class ProfilerReport(RequestHandler):
    """Render the profiler HTML report."""
    def get(self, report_id) -> None:
        profiler = CaimiraProfiler()
        _, report_html = profiler.get_report(report_id)
        if report_html:
            self.finish(report_html)
        else:
            self.send_error(404)


class BaseRequestHandler(RequestHandler):

    async def prepare(self):
        """Called at the beginning of a request before  `get`/`post`/etc."""

        # Read the secure cookie which exists if we are in an authenticated
        # context (though not if the caimira webservice is running standalone).
        session = json.loads(self.get_secure_cookie('session') or 'null')

        if session:
            self.current_user = AuthenticatedUser(
                username=session['username'],
                email=session['email'],
                fullname=session['fullname'],
            )
        else:
            self.current_user = AnonymousUser()

        profiler = CaimiraProfiler()
        if profiler.is_active and not self.request.path.startswith(CaimiraProfiler.ROOT_URL):
            self._request_profiler = profiler.start_profiler()

    def on_finish(self) -> None:
        """Called at the end of the request."""
        profiler = CaimiraProfiler()
        if profiler.is_active and self._request_profiler:
            profiler.stop_profiler(
                profiler=self._request_profiler,
                uri=self.request.uri or "",
                path=self.request.path,
                query=self.request.query,
                method=self.request.method,
            )

    def write_error(self, status_code: int, **kwargs) -> None:
        template = self.settings["template_environment"].get_template(
            "error.html.j2")

        error_id = uuid.uuid4()
        # Print the error to the log (and not to the browser!)
        if "exc_info" in kwargs:
            print(f"ERROR UUID {error_id}")
            print(traceback.format_exc())
        self.finish(template.render(
            user=self.current_user,
            get_url = template.globals['get_url'],
            get_calculator_url = template.globals["get_calculator_url"],
            active_page='Error',
            documentation_url = template.globals["documentation_url"],
            error_id=error_id,
            status_code=status_code,
            datetime=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        ))


class Missing404Handler(BaseRequestHandler):
    async def prepare(self):
        await super().prepare()
        self.set_status(404)
        template = self.settings["template_environment"].get_template(
            "error.html.j2")
        self.finish(template.render(
            user=self.current_user,
            get_url = template.globals['get_url'],
            get_calculator_url = template.globals["get_calculator_url"],
            active_page='Error',
            status_code=404,
        ))


class ConcentrationModel(BaseRequestHandler):
    async def post(self) -> None:
        debug = self.settings.get("debug", False)

        data_registry: DataRegistry = self.settings["data_registry"]
        data_service: typing.Optional[DataService] = self.settings.get("data_service", None)
        if data_service:
            data_service.update_registry(data_registry)

        requested_model_config = {
            name: self.get_argument(name) for name in self.request.arguments
        }
        LOG.debug(pformat(requested_model_config))

        try:
            form = virus_report_controller.generate_form_obj(requested_model_config, data_registry)
        except Exception as err:
            LOG.exception(err)
            response_json = {'code': 400, 'error': f'Your request was invalid {html.escape(str(err))}'}
            self.set_status(400)
            self.finish(json.dumps(response_json))
            return

        base_url = self.request.protocol + "://" + self.request.host
        report_generator: VirusReportGenerator = self.settings['report_generator']
        executor = loky.get_reusable_executor(
            max_workers=self.settings['handler_worker_pool_size'],
            timeout=300,
        )
        # Re-generate the report with the conditional probability of infection plot
        if self.get_cookie('conditional_plot'):
            form.conditional_probability_viral_loads = True if self.get_cookie('conditional_plot') == '1' else False
            self.clear_cookie('conditional_plot') # Clears cookie after changing the form value.

        report_task = executor.submit(
            report_generator.build_report, base_url, form,
            executor_factory=functools.partial(
                concurrent.futures.ThreadPoolExecutor,
                self.settings['report_generation_parallelism'],
            ),
        )
        report: str = await asyncio.wrap_future(report_task)
        self.finish(report)


class ConcentrationModelJsonResponse(BaseRequestHandler):
    def check_xsrf_cookie(self):
        """
        This request handler implements a stateless API that returns report data in JSON format.
        Thus, XSRF cookies are disabled by overriding base class implementation of this method with a pass statement.
        """
        pass

    async def post(self) -> None:
        """
        Expects algorithm input in HTTP POST request body in JSON format.
        Returns report data (algorithm output) in HTTP POST response body in JSON format.
        """
        debug = self.settings.get("debug", False)

        data_registry: DataRegistry = self.settings["data_registry"]
        data_service: typing.Optional[DataService] = self.settings.get("data_service", None)
        if data_service:
            data_service.update_registry(data_registry)

        requested_model_config = json.loads(self.request.body)
        LOG.debug(pformat(requested_model_config))

        try:
            form = virus_report_controller.generate_form_obj(requested_model_config, data_registry)
        except Exception as err:
            LOG.exception(err)
            response_json = {'code': 400, 'error': f'Your request was invalid {html.escape(str(err))}'}
            self.set_status(400)
            await self.finish(json.dumps(response_json))
            return

        executor = loky.get_reusable_executor(
            max_workers=self.settings['handler_worker_pool_size'],
            timeout=300,
        )
        report_data_task = executor.submit(calculate_report_data, form,
                                           executor_factory=functools.partial(
                                               concurrent.futures.ThreadPoolExecutor,
                                               self.settings['report_generation_parallelism'],
                                           ),)
        report_data: dict = await asyncio.wrap_future(report_data_task)
        await self.finish(report_data)


class StaticModel(BaseRequestHandler):
    async def get(self) -> None:
        debug = self.settings.get("debug", False)

        data_registry: DataRegistry = self.settings["data_registry"]
        data_service: typing.Optional[DataService] = self.settings.get("data_service", None)
        if data_service:
            data_service.update_registry(data_registry)

        form = virus_report_controller.generate_form_obj(virus_validator.baseline_raw_form_data(), data_registry)

        base_url = self.request.protocol + "://" + self.request.host
        report_generator: VirusReportGenerator = self.settings['report_generator']
        executor = loky.get_reusable_executor(max_workers=self.settings['handler_worker_pool_size'])

        report_task = executor.submit(
            report_generator.build_report, base_url, form,
            executor_factory=functools.partial(
                concurrent.futures.ThreadPoolExecutor,
                self.settings['report_generation_parallelism'],
            ),
        )
        report: str = await asyncio.wrap_future(report_task)
        self.finish(report)


class LandingPage(BaseRequestHandler):
    def get(self):
        template_environment = self.settings["template_environment"]
        template = template_environment.get_template(
            "index.html.j2")
        report = template.render(
            documentation_url = template.globals["documentation_url"],
            user=self.current_user,
            get_url = template_environment.globals['get_url'],
            get_calculator_url = template_environment.globals['get_calculator_url'],
            text_blocks=template_environment.globals["common_text"],
        )
        self.finish(report)


class CalculatorForm(BaseRequestHandler):
    def get(self):
        data_registry: DataRegistry = self.settings["data_registry"]
        data_service: typing.Optional[DataService] = self.settings.get("data_service", None)
        if data_service:
            data_service.update_registry(data_registry)

        template_environment = self.settings["template_environment"]
        template = template_environment.get_template(
            "calculator.form.html.j2")
        report = template.render(
            user=self.current_user,
            xsrf_form_html=self.xsrf_form_html(),
            get_url = template.globals['get_url'],
            get_calculator_url = template.globals["get_calculator_url"],
            calculator_version=calculator_version,
            text_blocks=template_environment.globals["common_text"],
            data_registry=data_registry.to_dict(),
        )
        self.finish(report)


class CompressedCalculatorFormInputs(BaseRequestHandler):
    def get(self, compressed_args: str):
        # Convert a base64 zlib encoded shortened URL into a non compressed
        # URL, and redirect.
        try:
            args = zlib.decompress(base64.b64decode(compressed_args)).decode()
        except Exception as err:  # noqa
            self.set_status(400)
            return self.finish("Invalid calculator data: it seems incomplete. Was there an error copying & pasting the URL?")
        template_environment = self.settings["template_environment"]
        self.redirect(f'{template_environment.globals["get_calculator_url"]()}?{args}')


class ArveData(BaseRequestHandler):
    async def get(self, hotel_id, floor_id):
        client_id = self.settings["arve_client_id"]
        client_secret = self.settings['arve_client_secret']
        arve_api_key = self.settings['arve_api_key']

        if (client_id == None or client_secret == None or arve_api_key == None):
            # If the credentials are not defined, we skip the ARVE API connection
            return self.send_error(401)

        http_client = AsyncHTTPClient()

        URL = 'https://arveapi.auth.eu-central-1.amazoncognito.com/oauth2/token'
        headers = { "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": b"Basic " + base64.b64encode(f'{client_id}:{client_secret}'.encode())
        }

        try:
            response = await http_client.fetch(HTTPRequest(
                url=URL,
                method='POST',
                headers=headers,
                body="grant_type=client_credentials"
            ),
            raise_error=True)
        except Exception as e:
            print("Something went wrong: %s" % e)

        access_token = json.loads(response.body)['access_token']

        URL = f'https://api.arve.swiss/v1/{hotel_id}/{floor_id}'
        headers = {
              "x-api-key": arve_api_key,
              "Authorization": f'Bearer {access_token}'
        }
        try:
            response = await http_client.fetch(HTTPRequest(
                url=URL,
                method='GET',
                headers=headers,
            ),
            raise_error=True)
        except Exception as e:
            print("Something went wrong: %s" % e)

        self.set_header("Content-Type", 'application/json')
        return self.finish(response.body)


class GenericExtraPage(BaseRequestHandler):

    def initialize(self, active_page: str, filename: str):
        self.active_page = active_page
        # The endpoint that will be used as template name
        self.filename = filename

    def get(self):
        template_environment = self.settings["template_environment"]
        template = template_environment.get_template(self.filename)
        self.finish(template.render(
            user=self.current_user,
            get_url = template.globals['get_url'],
            get_calculator_url = template.globals["get_calculator_url"],
            active_page=self.active_page,
            text_blocks=template_environment.globals["common_text"]
        ))


class CO2ModelResponse(BaseRequestHandler):
    async def post(self, endpoint: str) -> None:
        data_registry: DataRegistry = self.settings["data_registry"]
        data_service: typing.Optional[DataService] = self.settings.get("data_service", None)
        if data_service:
            data_service.update_registry(data_registry)

        requested_model_config = tornado.escape.json_decode(self.request.body)
        try:
            form = co2_report_controller.generate_form_obj(requested_model_config, data_registry)
        except Exception as err:
            if self.settings.get("debug", False):
                import traceback
                print(traceback.format_exc())
            response_json = {'code': 400, 'error': f'Your request was invalid {html.escape(str(err))}'}
            self.set_status(400)
            self.finish(json.dumps(response_json))
            return

        CO2_report_generator: CO2ReportGenerator = CO2ReportGenerator()
        if endpoint.rstrip('/') == 'plot':
            report = CO2_report_generator.build_initial_plot(form)
            self.finish(report)
        else:
            executor = loky.get_reusable_executor(
                max_workers=self.settings['handler_worker_pool_size'],
                timeout=300,
            )
            report_task = executor.submit(
                CO2_report_generator.build_fitting_results, form,
            )

            report = await asyncio.wrap_future(report_task)
            self.finish(report)


def get_url(app_root: str, relative_path: str = '/'):
        return app_root.rstrip('/') + relative_path.rstrip('/')

def get_calculator_url(app_root: str, calculator_prefix: str, relative_path: str = '/'):
        return app_root.rstrip('/') + calculator_prefix.rstrip('/') + relative_path.rstrip('/')

def make_app(
        debug: bool = False,
        APPLICATION_ROOT: str = '/',
        calculator_prefix: str = '/calculator',
        theme_dir: typing.Optional[Path] = None,
) -> Application:
    static_dir = Path(__file__).absolute().parent.parent / 'static'
    calculator_static_dir = Path(__file__).absolute().parent / 'static'

    get_root_url = functools.partial(get_url, APPLICATION_ROOT)
    get_root_calculator_url = functools.partial(get_calculator_url, APPLICATION_ROOT, calculator_prefix)

    base_urls: typing.List = [
        (get_root_url(r'/?'), LandingPage),
        (get_root_calculator_url(r'/?'), CalculatorForm),
        (get_root_calculator_url(r'/co2-fit/(.*)'), CO2ModelResponse),
        (get_root_calculator_url(r'/report'), ConcentrationModel),
        (get_root_url(r'/static/(.*)'), StaticFileHandler, {'path': static_dir}),
        (get_root_calculator_url(r'/static/(.*)'), StaticFileHandler, {'path': calculator_static_dir}),
    ]

    urls: typing.List = base_urls + [
        (get_root_url(r'/_c/(.*)'), CompressedCalculatorFormInputs),
        (get_root_calculator_url(r'/report-json'), ConcentrationModelJsonResponse),
        (get_root_calculator_url(r'/baseline-model/result'), StaticModel),
        (get_root_calculator_url(r'/api/arve/v1/(.*)/(.*)'), ArveData),
        # Generic Pages
        (get_root_url(r'/expert-app'), GenericExtraPage, {
            'active_page': 'expert-app',
            'filename': 'expert-app.html.j2'}),
    ]

    profiler_enabled = int(os.environ.get('CAIMIRA_PROFILER_ENABLED', 0))
    if profiler_enabled:
        urls += [
            (get_root_url(CaimiraProfiler.ROOT_URL), ProfilerPage),
            (get_root_url(r'{root_url}/(.*)'.format(root_url=CaimiraProfiler.ROOT_URL)), ProfilerReport),
        ]

    interface: str = os.environ.get('CAIMIRA_THEME', '<undefined>')
    if interface != '<undefined>' and (interface != '<undefined>' and 'cern' not in interface): urls = list(filter(lambda i: i in base_urls, urls))

    # Any extra generic page must be declared in the env. variable "EXTRA_PAGES"
    extra_pages: typing.Union[str, typing.List] = os.environ.get('EXTRA_PAGES', [])
    pages: typing.List = []
    try:
        pages = ast.literal_eval(extra_pages) # type: ignore
    except (SyntaxError, ValueError):
        LOG.warning('Warning: There was a problem with the extra pages. Is the "EXTRA_PAGES" environment variable defined?')
        pass

    for extra in pages:
        urls.append((get_root_url(r'%s' % extra['url_path']),
                        GenericExtraPage, {
                            'active_page': extra['url_path'].strip('/'),
                            'filename': extra['filename'], }))

    caimira_templates = Path(__file__).parent.parent / "templates"
    calculator_templates = Path(__file__).parent / "templates"
    templates_directories = [caimira_templates, calculator_templates]
    if theme_dir:
        templates_directories.insert(0, theme_dir)
    loader = jinja2.FileSystemLoader([str(path) for path in templates_directories])
    template_environment = jinja2.Environment(
        loader=loader,
        undefined=jinja2.StrictUndefined,  # fail when rendering any undefined template context variable
    )

    template_environment.globals["common_text"] = markdown_tools.extract_rendered_markdown_blocks(
        template_environment.get_template('common_text.md.j2')
    )
    template_environment.globals['get_url']=get_root_url
    template_environment.globals['get_calculator_url']=get_root_calculator_url
    template_environment.globals['documentation_url']='https://caimira.docs.cern.ch'

    if debug:
        tornado.log.enable_pretty_logging()

    data_registry = DataRegistry()
    data_service = None
    try:
        data_service_enabled = int(os.environ.get('DATA_SERVICE_ENABLED', 0))
    except ValueError:
        data_service_enabled = None

    if data_service_enabled: data_service = DataService.create()

    return Application(
        urls,
        debug=debug,
        data_registry=data_registry,
        data_service=data_service,
        template_environment=template_environment,
        default_handler_class=Missing404Handler,
        report_generator=VirusReportGenerator(loader, get_root_url, get_root_calculator_url),
        xsrf_cookies=True,
        # COOKIE_SECRET being undefined will result in no login information being
        # presented to the user.
        cookie_secret=os.environ.get('COOKIE_SECRET', '<undefined>'),
        arve_client_id=os.environ.get('ARVE_CLIENT_ID', None),
        arve_client_secret=os.environ.get('ARVE_CLIENT_SECRET', None),
        arve_api_key=os.environ.get('ARVE_API_KEY', None),

        # Process parallelism controls. There is a balance between serving a single report
        # requests quickly or serving multiple requests concurrently.
        # The defaults are: handle one report at a time, and allow parallelism
        # of that report generation. A value of ``None`` will result in the number of
        # processes being determined based on the number of CPUs. For some deployments,
        # such as on OpenShift this number does *not* reflect the real number of CPUs that
        # can be used, and it is recommended to specify these values explicitly (through
        # the environment variables).
        handler_worker_pool_size=(
            int(os.environ.get("HANDLER_WORKER_POOL_SIZE", 1)) or None
        ),
        report_generation_parallelism=(
            int(os.environ.get('REPORT_PARALLELISM', 0)) or None
        ),
    )
