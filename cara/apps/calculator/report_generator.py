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
        "model": model,
        "form": form,
        "creation_date": time,
        "model_version": "Beta v1.0.0",
        "simulation_name": "SAMPLE",
        "room_number": "40/1-02A",
        "room_volume": 30,
        "mechanical_ventilation": "Yes",
        "air_supply": 1,
        "air_changes": 2,
        "windows_number": 5,
        "window_height": 2,
        "window_width": 1,
        "opening_distance": 0.05,
        "windows_open": "20 minutes every 2 hours",
        "hepa_filtration": "No",
        "total_people": 8,
        "infected_people": 7,
        "activity_type": "Office work – typical scenario with all persons seated, talking",
        "activity_start": "00:00",
        "activity_finish": "01:15",
        "exposure_start": "00:00",
        "exposure_finish": "01:15",
        "single_event_date": "5th November",
        "lunch_option": "Yes",
        "lunch_start": "00:00",
        "lunch_finish": "01:15",
        "coffee_option": "Yes",
        "coffee_number": 4,
        "coffee_duration": 15,
        "coffee_start1": "00:00",
        "coffee_finish1": "00:00",
        "coffee_start2": "00:00",
        "coffee_finish2": "00:00",
        "coffee_start3": "00:00",
        "coffee_finish3": "00:00",
        "coffee_start4": "00:00",
        "coffee_finish4": "00:00",
        "mask_wearing": "Yes",
        "infection_probability": round(model.infection_probability(), 2),
        "reproduction_rate": 2,
    }

    context.update(calculate_report_data(model))

    p = Path(__file__).parent / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(Path(p)))
    template = env.get_template("report.html.j2")
    return template.render(**context)
