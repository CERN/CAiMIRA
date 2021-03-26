import datetime
import html
import json
import os
from pathlib import Path
import traceback
import uuid

import jinja2
import mistune
from tornado.web import Application, RequestHandler, StaticFileHandler

from . import model_generator
from .report_generator import build_report
from .user import AuthenticatedUser, AnonymousUser


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
            contents='Unfortunately the page you were looking for does not exist.<br><br><br><br>'
        ))


class ConcentrationModel(BaseRequestHandler):
    def post(self):
        requested_model_config = {
            name: self.get_argument(name) for name in self.request.arguments
        }
        if self.settings.get("debug", False):
            from pprint import pprint
            pprint(requested_model_config)

        try:
            form = model_generator.FormData.from_dict(requested_model_config)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as err:
            if self.settings.get("debug", False):
                import traceback
                print(traceback.format_exc())
            response_json = {'code': 400, 'error': f'Your request was invalid {html.escape(str(err))}'}
            self.set_status(400)
            self.finish(json.dumps(response_json))
            return

        base_url = self.request.protocol + "://" + self.request.host
        report = build_report(base_url, form.build_model(), form)
        self.finish(report)


class StaticModel(BaseRequestHandler):
    def get(self):
        form = model_generator.FormData.from_dict(model_generator.baseline_raw_form_data())
        model = form.build_model()
        base_url = self.request.protocol + "://" + self.request.host
        report = build_report(base_url, model, form)
        self.finish(report)


class LandingPage(BaseRequestHandler):
    def get(self):
        template = self.settings["template_environment"].get_template(
            "index.html.j2")
        report = template.render(user=self.current_user)
        self.finish(report)


class CalculatorForm(BaseRequestHandler):
    def get(self):
        template = self.settings["template_environment"].get_template(
            "calculator.form.html.j2")
        report = template.render(
            user=self.current_user,
            xsrf_form_html=self.xsrf_form_html(),
        )
        self.finish(report)


class ReadmeHandler(BaseRequestHandler):
    def get(self):
        template = self.settings['template_environment'].get_template("userguide.html.j2")
        readme = template.render(
            active_page="calculator/user-guide",
            user=self.current_user
        )
        self.finish(readme)


def make_app(debug=False, prefix='/calculator'):
    static_dir = Path(__file__).absolute().parent.parent / 'static'
    calculator_static_dir = Path(__file__).absolute().parent / 'static'
    urls = [
        (r'/?', LandingPage),
        (r'/static/(.*)', StaticFileHandler, {'path': static_dir}),
        (prefix + r'/?', CalculatorForm),
        (prefix + r'/report', ConcentrationModel),
        (prefix + r'/baseline-model/result', StaticModel),
        (prefix + r'/user-guide', ReadmeHandler),
        (prefix + r'/static/(.*)', StaticFileHandler, {'path': calculator_static_dir}),
    ]

    cara_templates = Path(__file__).parent.parent / "templates"
    calculator_templates = Path(__file__).parent / "templates"
    template_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader([cara_templates, calculator_templates]),
    )

    return Application(
        urls,
        debug=debug,
        template_environment=template_environment,
        default_handler_class=Missing404Handler,
        xsrf_cookies=True,
        # COOKIE_SECRET being undefined will result in no login information being
        # presented to the user.
        cookie_secret=os.environ.get('COOKIE_SECRET', '<undefined>'),
    )
