from datetime import datetime
from pathlib import Path

import jinja2
import numpy as np

from cara import models
from .model_generator import FormData


def calculate_report_data(model: models.Model):
    resolution = 600
    times = list(np.linspace(0, 10, resolution))
    concentrations = [model.concentration(time) for time in times]
    highest_const = max(concentrations)
    prob = model.infection_probability()
    er = model.infected.emission_rate(0.1)
    exposed_occupants = model.exposed_occupants
    r0 = prob * exposed_occupants / 100
    return {
        "times": times,
        "concentrations": concentrations,
        "highest_const": highest_const,
        "prob_inf": prob,
        "emission_rate": er,
        "exposed_occupants": exposed_occupants,
        "R0": r0,
    }


def build_report(model: models.Model, form: FormData):
    now = datetime.now()
    time = now.strftime("%d/%m/%Y %H:%M:%S")
    request = {"the": "form", "request": "data"}
    context = {
        'model': model, 
        'request': request, 
        'creation_date': time, 
        'model_version': 'Beta v1.0.0', 
        'simulation_name': form.simulation_name, 
        'room_number': form.room_number, 
        'room_volume': form.room_volume, 
        'ventilation_type': form.ventilation_type, 
        'air_supply': form.air_supply, 
        'air_changes': form.air_changes, 
        'windows_number': form.windows_number, 
        'window_height': form.window_height, 
        'window_width': form.window_width, 
        'opening_distance': form.opening_distance, 
        'windows_open': form.windows_open, 
        'hepa_option': 'No', 
        'total_people': form.total_people,
        'infected_people': form.infected_people,
        'activity_type': form.activity_type,
        'activity_start': form.activity_start, 
        'activity_finish': form.activity_finish, 
        'exposure_start': '00:00', 
        'exposure_finish': '01:15',
        'event_type': form.event_type, 
        'single_event_date': form.single_event_date, 
        'recurrent_event_month': form.recurrent_event_month,
        'lunch_option': form.lunch_option, 
        'lunch_start': form.lunch_start, 
        'lunch_finish': form.lunch_finish, 
        'coffee_breaks': form.coffee_breaks,
        'coffee_duration': form.coffee_duration, 
        'coffee_times': [['00:00','00:00'], ['00:00','00:00'], ['00:00','00:00'], ['00:00','00:00']], 
        'mask_wearing': form.mask_wearing, 
        'infection_probability': round(model.infection_probability(), 2), 
        'reproduction_rate': 2
    }

    context.update(calculate_report_data(model))

    p = Path(__file__).parent / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(Path(p)))
    template = env.get_template("report.html.j2")
    return template.render(**context)