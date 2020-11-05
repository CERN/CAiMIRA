import json
from pathlib import Path

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
            model = form.build_model(
                # TODO: This argument to be removed.
                tmp_raw_form_data=requested_model_config,
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as err:
            if DEBUG:
                import traceback
                traceback.print_last()
            response_json = {'code': 400, 'error': f'Your request was invalid {err}'}
            self.set_status(400)
            self.finish(json.dumps(response_json))
            return

        report = build_report(model, form)
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


def make_app(debug=False, prefix='/calculator'):
    static_dir = Path(__file__).absolute().parent / 'static'
    urls = [
        (
            prefix + r'()', StaticFileHandler, {'path': static_dir / 'form.html'}
        ),
        (
            prefix + r'/report', ConcentrationModel
        ),
        (
            prefix + r'/baseline-model/result', StaticModel
        ),
        (
            prefix + r'/static/(.*)',
            StaticFileHandler,
            {'path': static_dir}
        ),
    ]
    return Application(
        urls,
        debug=debug,
    )
