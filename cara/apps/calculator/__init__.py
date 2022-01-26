# This module is part of CARA. Please see the repository at
# https://gitlab.cern.ch/cara/cara for details of the license and terms of use.

import asyncio
import concurrent.futures
import datetime
import base64
import functools
import html
import json
import os
from pathlib import Path
import traceback
import typing
import uuid
import zlib

import jinja2
import loky
from tornado.web import Application, RequestHandler, StaticFileHandler
import tornado.log

from . import markdown_tools
from . import model_generator
from .report_generator import ReportGenerator
from .user import AuthenticatedUser, AnonymousUser


# The calculator version is based on a combination of the model version and the
# semantic version of the calculator itself. The version uses the terms
# "{MAJOR}.{MINOR}.{PATCH}" to describe the 3 distinct numbers constituting a version.
# Effectively, if the model increases its MAJOR version then so too should this
# calculator version. If the calculator needs to make breaking changes (e.g. change
# form attributes) then it can also increase its MAJOR version without needing to
# increase the overall CARA version (found at ``cara.__version__``).
__version__ = "3.3.0"


class BaseRequestHandler(RequestHandler):
    async def prepare(self):
        """Called at the beginning of a request before  `get`/`post`/etc."""

        # Read the secure cookie which exists if we are in an authenticated
        # context (though not if the cara webservice is running standalone).
        session = json.loads(self.get_secure_cookie('session') or 'null')

        if session:
            self.current_user = AuthenticatedUser(
                username=session['username'],
                email=session['email'],
                fullname=session['fullname'],
            )
        else:
            self.current_user = AnonymousUser()

    def write_error(self, status_code: int, **kwargs) -> None:
        template = self.settings["template_environment"].get_template(
            "page.html.j2")

        error_id = uuid.uuid4()
        contents = (
            f'Unfortunately an error occurred when processing your request. '
            f'Please let us know about this issue with as much detail as possible at '
            f'<a href="mailto:CARA-dev@cern.ch">CARA-dev@cern.ch</a>, reporting status '
            f'code {status_code}, the error id of "{error_id}" and the time of the '
            f'request ({datetime.datetime.utcnow()}).<br><br><br><br>'
        )
        # Print the error to the log (and not to the browser!)
        if "exc_info" in kwargs:
            print(f"ERROR UUID {error_id}")
            print(traceback.format_exc())
        self.finish(template.render(
            user=self.current_user,
            calculator_prefix=self.settings["calculator_prefix"],
            active_page='Error',
            contents=contents
        ))


class Missing404Handler(BaseRequestHandler):
    async def prepare(self):
        await super().prepare()
        self.set_status(404)
        template = self.settings["template_environment"].get_template(
            "page.html.j2")
        self.finish(template.render(
            user=self.current_user,
            calculator_prefix=self.settings["calculator_prefix"],
            active_page='Error',
            contents='Unfortunately the page you were looking for does not exist.<br><br><br><br>'
        ))


class ConcentrationModel(BaseRequestHandler):
    async def post(self):
        requested_model_config = {
            name: self.get_argument(name) for name in self.request.arguments
        }
        if self.settings.get("debug", False):
            from pprint import pprint
            pprint(requested_model_config)
            start = datetime.datetime.now()

        try:
            form = model_generator.FormData.from_dict(requested_model_config)
        except Exception as err:
            if self.settings.get("debug", False):
                import traceback
                print(traceback.format_exc())
            response_json = {'code': 400, 'error': f'Your request was invalid {html.escape(str(err))}'}
            self.set_status(400)
            self.finish(json.dumps(response_json))
            return

        base_url = self.request.protocol + "://" + self.request.host
        report_generator: ReportGenerator = self.settings['report_generator']
        executor = loky.get_reusable_executor(
            max_workers=self.settings['handler_worker_pool_size'],
            timeout=300,
        )
        report_task = executor.submit(
            report_generator.build_report, base_url, form,
            executor_factory=functools.partial(
                concurrent.futures.ThreadPoolExecutor,
                self.settings['report_generation_parallelism'],
            ),
        )
        report: str = await asyncio.wrap_future(report_task)
        self.finish(report)


class StaticModel(BaseRequestHandler):
    async def get(self):
        form = model_generator.FormData.from_dict(model_generator.baseline_raw_form_data())
        base_url = self.request.protocol + "://" + self.request.host
        report_generator: ReportGenerator = self.settings['report_generator']
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
        template = self.settings["template_environment"].get_template(
            "index.html.j2")
        report = template.render(
            user=self.current_user,
            calculator_prefix=self.settings["calculator_prefix"],
            text_blocks=template_environment.globals['common_text']
        )
        self.finish(report)


class AboutPage(BaseRequestHandler):
    def get(self):
        template_environment = self.settings["template_environment"]
        template = template_environment.get_template("about.html.j2")
        report = template.render(
            user=self.current_user,
            calculator_prefix=self.settings["calculator_prefix"],
            active_page="about",
            text_blocks=template_environment.globals['common_text']
        )
        self.finish(report)


class CalculatorForm(BaseRequestHandler):
    def get(self):
        template = self.settings["template_environment"].get_template(
            "calculator.form.html.j2")
        report = template.render(
            user=self.current_user,
            xsrf_form_html=self.xsrf_form_html(),
            calculator_prefix=self.settings["calculator_prefix"],
            calculator_version=__version__,
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
        self.redirect(f'{self.settings["calculator_prefix"]}?{args}')


class ReadmeHandler(BaseRequestHandler):
    def get(self):
        template = self.settings['template_environment'].get_template("userguide.html.j2")
        readme = template.render(
            active_page="calculator/user-guide",
            user=self.current_user,
            calculator_prefix=self.settings["calculator_prefix"],
        )
        self.finish(readme)


def make_app(
        debug: bool = False,
        calculator_prefix: str = '/calculator',
        theme_dir: typing.Optional[Path] = None,
) -> Application:
    static_dir = Path(__file__).absolute().parent.parent / 'static'
    calculator_static_dir = Path(__file__).absolute().parent / 'static'
    urls: typing.Any = [
        (r'/?', LandingPage),
        (r'/_c/(.*)', CompressedCalculatorFormInputs),
        (r'/about', AboutPage),
        (r'/static/(.*)', StaticFileHandler, {'path': static_dir}),
        (calculator_prefix + r'/?', CalculatorForm),
        (calculator_prefix + r'/report', ConcentrationModel),
        (calculator_prefix + r'/baseline-model/result', StaticModel),
        (calculator_prefix + r'/user-guide', ReadmeHandler),
        (calculator_prefix + r'/static/(.*)', StaticFileHandler, {'path': calculator_static_dir}),
    ]

    cara_templates = Path(__file__).parent.parent / "templates"
    calculator_templates = Path(__file__).parent / "templates"
    templates_directories = [cara_templates, calculator_templates]
    if theme_dir:
        templates_directories.insert(0, theme_dir)
    loader = jinja2.FileSystemLoader([str(path) for path in templates_directories])
    template_environment = jinja2.Environment(
        loader=loader,
        undefined=jinja2.StrictUndefined,  # fail when rendering any undefined template context variable
    )

    template_environment.globals['common_text'] = markdown_tools.extract_rendered_markdown_blocks(
        template_environment.get_template('common_text.md.j2')
    )

    if debug:
        tornado.log.enable_pretty_logging()

    return Application(
        urls,
        debug=debug,
        calculator_prefix=calculator_prefix,
        template_environment=template_environment,
        default_handler_class=Missing404Handler,
        report_generator=ReportGenerator(loader, calculator_prefix),
        xsrf_cookies=True,
        # COOKIE_SECRET being undefined will result in no login information being
        # presented to the user.
        cookie_secret=os.environ.get('COOKIE_SECRET', '<undefined>'),

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
