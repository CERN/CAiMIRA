import json
from pathlib import Path

import jinja2
import mistune
from tornado.web import Application, RequestHandler, StaticFileHandler

from . import model_generator
from .report_generator import build_report


DEBUG = True


class ConcentrationModel(RequestHandler):
    def post(self):
        requested_model_config = {
            name: self.get_argument(name) for name in self.request.arguments
        }
        if DEBUG:
            from pprint import pprint
            pprint(requested_model_config)

        try:
            form = model_generator.FormData.from_dict(requested_model_config)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as err:
            if DEBUG:
                import traceback
                print(traceback.format_exc())
            response_json = {'code': 400, 'error': f'Your request was invalid {err}'}
            self.set_status(400)
            self.finish(json.dumps(response_json))
            return

        report = build_report(form.build_model(), form)
        self.finish(report)


class StaticModel(RequestHandler):
    def get(self):
        requested_model_config = model_generator.baseline_raw_form_data()
        form = model_generator.FormData.from_dict(model_generator.baseline_raw_form_data())
        model = form.build_model(
            # TODO: This argument to be removed.
            tmp_raw_form_data=requested_model_config,
        )
        report = build_report(model, form)
        self.finish(report)


class LandingPage(RequestHandler):
    def get(self):
        import jinja2
        p = Path(__file__).parent.parent / "templates"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(Path(p)))
        template = env.get_template("index.html.j2")
        report = template.render(**{})
        self.finish(report)


class CalculatorForm(RequestHandler):
    def get(self):

        cara_templates = Path(__file__).parent.parent / "templates"
        calculator_templates = Path(__file__).parent / "templates"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader([cara_templates, calculator_templates]),
        )

        template = self.settings['template_environment'].get_template("calculator.form.html.j2")
        report = template.render()
        self.finish(report)


class ReadmeHandler(RequestHandler):
    def get(self):
        template = self.settings['template_environment'].get_template("page.html.j2")
        markdown = (Path(__file__).parent / 'README.md').read_text()
        self.write(template.render(
            active_page="calculator/user-guide",
            contents=mistune.markdown(markdown)),
        )


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
    )
