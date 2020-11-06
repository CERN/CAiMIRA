import base64
from datetime import datetime
import io
from pathlib import Path

import jinja2
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np

from cara import models
from .model_generator import FormData


def calculate_report_data(model: models.Model):
    resolution = 600

    # TODO: Have this for exposed not infected.
    t_start = model.infected.presence.boundaries()[0][0]
    t_end = model.infected.presence.boundaries()[-1][1]

    times = list(np.linspace(t_start, t_end, resolution))
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
        "scenario_plot_src": embed_figure(plot(times, concentrations)),
    }


def embed_figure(figure) -> str:
    # Draw the scenario graph.
    img_data = io.BytesIO()

    figure.savefig(img_data, format='png', bbox_inches="tight")
    plt.close()
    img_data.seek(0)
    pic_hash = base64.b64encode(img_data.read()).decode('ascii')
    # A src suitable for a tag such as f'<img id="scenario_concentration_plot" src="{result}">.
    return f'data:image/png;base64,{pic_hash}'


def plot(times, concentrations):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(times, concentrations)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    ax.set_xlabel('Hours from start of event')
    ax.set_ylabel('Concentration ($q/m^3$)')
    ax.set_title('Concentration of infectious quanta aerosols')

    # top = max([0.75, max(concentrations)])
    # print(max(concentrations))
    # ax.set_ylim(bottom=1e-4, top=top)
    return fig


def minutes_to_string(minutes: int) -> str:
    minute_string = str(minutes % 60)
    minute_string = "0" * (2 - len(minute_string)) + minute_string
    hour_string = str(minutes // 60)
    hour_string = "0" * (2 - len(hour_string)) + hour_string

    return f"{hour_string}:{minute_string}"


def build_report(model: models.Model, form: FormData):
    now = datetime.now()
    time = now.strftime("%d/%m/%Y %H:%M:%S")
    request = {"the": "form", "request": "data"}

    context = {
        'model': model,
        'request': request,
        'form': form,
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
        'infected_start': 826,
        'infected_finish': 827,
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
    }

    context.update(calculate_report_data(model))

    p = Path(__file__).parent / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(Path(p)))
    template = env.get_template("report.html.j2")
    return template.render(**context)