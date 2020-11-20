import base64
import dataclasses
from datetime import datetime
import io
from pathlib import Path
import typing

import jinja2
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np

from cara import models
from .model_generator import FormData


@dataclasses.dataclass(frozen=True)
class RepeatEvents:
    repeats: int
    probability_of_infection: float
    expected_new_cases: float


def calculate_report_data(model: models.ExposureModel):
    resolution = 600

    t_start = min(model.exposed.presence.boundaries()[0][0],
                  model.concentration_model.infected.presence.boundaries()[0][0])
    t_end = max(model.exposed.presence.boundaries()[-1][1],
                model.concentration_model.infected.presence.boundaries()[-1][1])

    times = list(np.linspace(t_start, t_end, resolution))
    concentrations = [model.concentration_model.concentration(time) for time in times]
    highest_const = max(concentrations)
    prob = model.infection_probability()
    er = model.concentration_model.infected.emission_rate_when_present()
    exposed_occupants = model.exposed.number
    expected_new_cases = model.expected_new_cases()

    repeated_events = []
    for n in [1, 2, 3, 4, 5]:
        repeat_model = dataclasses.replace(model, repeats=n)
        repeated_events.append(
            RepeatEvents(
                repeats=n,
                probability_of_infection=repeat_model.infection_probability(),
                expected_new_cases=repeat_model.expected_new_cases(),
            )
        )

    return {
        "times": times,
        "concentrations": concentrations,
        "highest_const": highest_const,
        "prob_inf": prob,
        "emission_rate": er,
        "exposed_occupants": exposed_occupants,
        "expected_new_cases": expected_new_cases,
        "scenario_plot_src": embed_figure(plot(times, concentrations)),
        "repeated_events": repeated_events,
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

    ax.set_xlabel('Time (hour of day)')
    ax.set_ylabel('Concentration ($q/m^3$)')
    ax.set_title('Concentration of infectious quanta')

    # top = max([0.75, max(concentrations)])
    # print(max(concentrations))
    # ax.set_ylim(bottom=1e-4, top=top)
    return fig


def minutes_to_time(minutes: int) -> str:
    minute_string = str(minutes % 60)
    minute_string = "0" * (2 - len(minute_string)) + minute_string
    hour_string = str(minutes // 60)
    hour_string = "0" * (2 - len(hour_string)) + hour_string

    return f"{hour_string}:{minute_string}"


def manufacture_alternative_scenarios(form: FormData) -> typing.Dict[str, models.ExposureModel]:
    scenarios = {}

    with_mask = dataclasses.replace(form, mask_wearing='continuous')
    without_mask = dataclasses.replace(form, mask_wearing='removed')

    scenarios['With mask'] = with_mask.build_model()
    scenarios['Without mask'] = without_mask.build_model()

    return scenarios


def comparison_plot(scenarios: typing.Dict[str, models.ExposureModel]):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    resolution = 350
    times = None
    for name, model in scenarios.items():
        if times is None:
            t_start = min(model.exposed.presence.boundaries()[0][0],
                          model.concentration_model.infected.presence.boundaries()[0][0])
            t_end = max(model.exposed.presence.boundaries()[-1][1],
                        model.concentration_model.infected.presence.boundaries()[-1][1])
            times = np.linspace(t_start, t_end, resolution)
        concentrations = [model.concentration_model.concentration(time) for time in times]

        ax.plot(times, concentrations, label=name)

    ax.legend()
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    ax.set_xlabel('Time (hour of day)')
    ax.set_ylabel('Concentration ($q/m^3$)')
    ax.set_title('Concentration of infectious quanta')

    return fig


def comparison_report(scenarios: typing.Dict[str, models.ExposureModel]):
    statistics = {}
    for name, model in scenarios.items():
        statistics[name] = {
            'probability_of_infection': model.infection_probability(),
            'expected_new_cases': model.expected_new_cases(),
        }
    return {
        'plot': embed_figure(comparison_plot(scenarios)),
        'stats': statistics,
    }


def build_report(model: models.ExposureModel, form: FormData):
    now = datetime.now()
    time = now.strftime("%d/%m/%Y %H:%M:%S")
    request = {"the": "form", "request": "data"}

    context = {
        'model': model,
        'request': request,
        'form': form,
        'creation_date': time,
    }

    context.update(calculate_report_data(model))
    alternative_scenarios = manufacture_alternative_scenarios(form)
    context['alternative_scenarios'] = comparison_report(alternative_scenarios)

    cara_templates = Path(__file__).parent.parent / "templates"
    calculator_templates = Path(__file__).parent / "templates"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([cara_templates, calculator_templates]),
        undefined=jinja2.StrictUndefined,
    )
    env.filters['minutes_to_time'] = minutes_to_time
    env.filters['float_format'] = "{0:.2f}".format
    env.filters['int_format'] = "{:0.0f}".format
    template = env.get_template("report.html.j2")
    return template.render(**context)
