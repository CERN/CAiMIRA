import json
from pathlib import Path

from tornado.web import Application, RequestHandler, StaticFileHandler

import cara.models


def build_model(request: dict) -> cara.models.Model:
    return None


def build_response(model: cara.models.Model):
    return {'items': 'foobar'}


class ConcentrationModel(RequestHandler):
    def post(self):
        requested_model_config = {
            name: self.get_argument(name) for name in self.request.arguments
        }
        try:
            model = build_model(requested_model_config)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as err:
            response_json = {'code': 400, 'error': f'Your request was invalid {err}'}
            self.set_status(400)
            self.finish(json.dumps(response_json))
            return

        response_json = build_response(model)
        response_json['room_name'] = requested_model_config.get('room_name', 'unknown')
        self.write(response_json)


def make_app(debug=False, prefix='/calculator'):
    static_dir = Path(__file__).absolute().parent / 'static'
    urls = [
        (
            prefix + r'()', StaticFileHandler, {'path': static_dir / 'form.html'}
        ),
        (
            prefix + r'/api/calculator', ConcentrationModel
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
