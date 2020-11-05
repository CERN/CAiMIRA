import json
from pathlib import Path

import jinja2
from tornado.web import Application, RequestHandler, StaticFileHandler

import cara.models

from datetime import datetime

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


class StaticModel(RequestHandler):
    def get(self):

        import cara.apps.expert
        model = cara.apps.expert.baseline_model

        now = datetime.now()
        time = now.strftime("%d/%m/%Y %H:%M:%S")
        request = {'the': 'form', 'request': 'data'}
        context = {'model': model, 'request': request, 'creation_date': time, 'model_version': 'Beta v1.0.0', 
                'simulation_name': 'SAMPLE', 'room_number': '40/1-02A', 'room_volume': 30, 'mechanical_ventilation': 'Yes', 
                'air_supply': 1, 'air_changes': 2, 'windows_number': 5, 'window_height': 2, 'window_width': 1, 
                'opening_distance': 0.05, 'windows_open': '20 minutes every 2 hours', 'hepa_filtration': 'No', 'total_people': 8,
                'infected_people': 7, 'activity_type': 'Office work – typical scenario with all persons seated, talking',
                'activity_start': '00:00', 'activity_finish': '01:15', 'exposure_start': '00:00', 'exposure_finish': '01:15',
                'single_event_date': '5th November', 'lunch_option': 'Yes', 'lunch_start': '00:00', 'lunch_finish': '01:15', 
                'coffee_option': 'Yes', 'coffee_number': 4,'coffee_duration': 15, 'coffee_start1': '00:00', 'coffee_finish1': '00:00',
                'coffee_start2': '00:00','coffee_finish2': '00:00', 'coffee_start3': '00:00', 'coffee_finish3': '00:00', 
                'coffee_start4': '00:00', 'coffee_finish4': '00:00', 'mask_wearing': 'Yes', 
                'infection_probability': round(model.infection_probability(), 2), 'reproduction_rate': 2}

        p = Path(__file__).parent / 'templates'
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(Path(p)))
        template = env.get_template('report.html.j2')
        self.write(template.render(**context))


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
