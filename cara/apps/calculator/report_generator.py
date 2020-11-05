from datetime import datetime
from pathlib import Path

import jinja2

from cara import models
from .model_generator import FormData


def build_report(model: models.Model, form: FormData):
    now = datetime.now()
    time = now.strftime('%d/%m/%Y %H:%M:%S')
    request = {'the': 'form', 'request': 'data'}
    context = {'model': model, 'request': request, 'creation_date': time, 'model_version': 'Beta v1.0.0', 
            'simulation_name': 'SAMPLE', 'room_number': '40/1-02A', 'room_volume': 30, 'ventilation_type': 'natural_ventilation', 
            'air_supply': 1, 'air_changes': 2, 'windows_number': 5, 'window_height': 2, 'window_width': 1, 
            'opening_distance': 0.05, 'windows_open': '20 minutes every 2 hours', 'hepa_option': 'No', 'total_people': 8,
            'infected_people': 7, 'activity_type': 'Office work – typical scenario with all persons seated, talking',
            'activity_start': '00:00', 'activity_finish': '01:15', 'exposure_start': '00:00', 'exposure_finish': '01:15',
            'event_type' : 'single_event', 'single_event_date': '5th November', 'recurrent_event_month': 'November',
            'lunch_option': 'No', 'lunch_start': '00:00', 'lunch_finish': '01:15', 'coffee_breaks': 4,'coffee_duration': 15, 
            'coffee_times': [['00:00','00:00'], ['00:00','00:00'], ['00:00','00:00'], ['00:00','00:00']], 'mask_wearing': 'No', 
            'infection_probability': round(model.infection_probability(), 2), 'reproduction_rate': 2}

    p = Path(__file__).parent / 'templates'
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(p)))
    template = env.get_template('report.html.j2')
    return template.render(**context)