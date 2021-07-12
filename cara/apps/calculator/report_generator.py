import base64
import dataclasses
from datetime import datetime, timedelta
import io
import typing
import zlib

import qrcode
import urllib
import jinja2
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np

from cara import models
from .model_generator import FormData
from ... import dataclass_utils


@dataclasses.dataclass(frozen=True)
class RepeatEvents:
    repeats: int
    probability_of_infection: float
    expected_new_cases: float


def model_start_end(model: models.ExposureModel):
    t_start = min(model.exposed.presence.boundaries()[0][0],
                  model.concentration_model.infected.presence.boundaries()[0][0])
    t_end = max(model.exposed.presence.boundaries()[-1][1],
                model.concentration_model.infected.presence.boundaries()[-1][1])
    return t_start, t_end


def calculate_report_data(model: models.ExposureModel):
    resolution = 600

    t_start, t_end = model_start_end(model)
    times = list(np.linspace(t_start, t_end, resolution))
    concentrations = [np.mean(model.concentration_model.concentration(time))
                      for time in times]
    highest_const = max(concentrations)
    prob = np.mean(model.infection_probability())
    er = np.mean(model.concentration_model.infected.emission_rate_when_present())
    exposed_occupants = model.exposed.number
    expected_new_cases = np.mean(model.expected_new_cases())

    repeated_events = []
    for n in [1, 2, 3, 4, 5]:

        repeat_model = dataclass_utils.replace(model, repeats=n)
        repeated_events.append(
            RepeatEvents(
                repeats=n,
                probability_of_infection=np.mean(repeat_model.infection_probability()),
                expected_new_cases=np.mean(repeat_model.expected_new_cases()),
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
        "scenario_plot_src": img2base64(_figure2bytes(plot(times, concentrations, model))),
        "repeated_events": repeated_events,
    }


def generate_qr_code(base_url, calculator_prefix, form: FormData):
    form_dict = FormData.to_dict(form, strip_defaults=True)

    # Generate the calculator URL arguments that would be needed to re-create this
    # form.
    args = urllib.parse.urlencode(form_dict)

    # Then zlib compress + base64 encode the string. To be inverted by the
    # /_c/ endpoint.
    compressed_args = base64.b64encode(zlib.compress(args.encode())).decode()
    qr_url = f"{base_url}/_c/{compressed_args}"
    url = f"{base_url}{calculator_prefix}?{args}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    return {
        'image': img2base64(_img2bytes(img)),
        'link': url,
        'qr_url': qr_url,
    }


def _img2bytes(figure):
    # Draw the image
    img_data = io.BytesIO()
    figure.save(img_data, format='png', bbox_inches="tight")
    return img_data


def _figure2bytes(figure):
    # Draw the image
    img_data = io.BytesIO()
    figure.savefig(img_data, format='png', bbox_inches="tight")
    return img_data


def img2base64(img_data) -> str:
    plt.close()
    img_data.seek(0)
    pic_hash = base64.b64encode(img_data.read()).decode('ascii')
    # A src suitable for a tag such as f'<img id="scenario_concentration_plot" src="{result}">.
    return f'data:image/png;base64,{pic_hash}'


def plot(times, concentrations, model: models.ExposureModel):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    datetimes = [datetime(1970, 1, 1) + timedelta(hours=time) for time in times]
    ax.plot(datetimes, concentrations, lw=2, color='#1f77b4', label='Mean concentration')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    ax.set_xlabel('Time of day')
    ax.set_ylabel('Mean concentration ($q/m^3$)')
    ax.set_title('Mean concentration of infectious quanta')
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))

    # Plot presence of exposed person
    for i, (presence_start, presence_finish) in enumerate(model.exposed.presence.boundaries()):
        plt.fill_between(
            datetimes, concentrations, 0,
            where=(np.array(times) > presence_start) & (np.array(times) < presence_finish),
            color="#1f77b4", alpha=0.1,
            label="Presence of exposed person(s)" if i == 0 else ""
        )

    # Place a legend outside of the axes itself.
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0)

    return fig


def minutes_to_time(minutes: int) -> str:
    minute_string = str(minutes % 60)
    minute_string = "0" * (2 - len(minute_string)) + minute_string
    hour_string = str(minutes // 60)
    hour_string = "0" * (2 - len(hour_string)) + hour_string

    return f"{hour_string}:{minute_string}"


def readable_minutes(minutes: int) -> str:
    time = float(minutes)
    unit = " minute"
    if time % 60 == 0:
        time = minutes/60
        unit = " hour"
    if time != 1:
        unit += "s"

    if time.is_integer():
        time_str = "{:0.0f}".format(time)
    else:
        time_str = "{0:.2f}".format(time)

    return time_str + unit


def non_zero_percentage(percentage: int) -> str:
    if percentage < 0.01:
        return "<0.01%"
    elif percentage < 1:
        return "{:0.2f}%".format(percentage)
    else:
        return "{:0.0f}%".format(percentage)


def manufacture_alternative_scenarios(form: FormData) -> typing.Dict[str, models.ExposureModel]:
    scenarios = {}

    # Two special option cases - HEPA and/or FFP2 masks.
    FFP2_being_worn = bool(form.mask_wearing_option == 'mask_on' and form.mask_type == 'FFP2')
    if FFP2_being_worn and form.hepa_option:
        scenarios['Base scenario with HEPA and FFP2 masks'] = form.build_model()
    elif FFP2_being_worn:
        scenarios['Base scenario with FFP2 masks'] = form.build_model()
    elif form.hepa_option:
        scenarios['Base scenario with HEPA filter'] = form.build_model()

    # The remaining scenarios are based on Type I masks (possibly not worn)
    # and no HEPA filtration.
    form = dataclass_utils.replace(form, mask_type='Type I')
    if form.hepa_option:
        form = dataclass_utils.replace(form, hepa_option=False)

    with_mask = dataclass_utils.replace(form, mask_wearing_option='mask_on')
    without_mask = dataclass_utils.replace(form, mask_wearing_option='mask_off')

    if form.ventilation_type == 'mechanical_ventilation':
        scenarios['Mechanical ventilation with Type I masks'] = with_mask.build_model()
        scenarios['Mechanical ventilation without masks'] = without_mask.build_model()

    elif form.ventilation_type == 'natural_ventilation':
        scenarios['Windows open with Type I masks'] = with_mask.build_model()
        scenarios['Windows open without masks'] = without_mask.build_model()

    # No matter the ventilation scheme, we include scenarios which don't have any ventilation.
    with_mask_no_vent = dataclass_utils.replace(with_mask, ventilation_type='no_ventilation')
    without_mask_or_vent = dataclass_utils.replace(without_mask, ventilation_type='no_ventilation')
    scenarios['No ventilation with Type I masks'] = with_mask_no_vent.build_model()
    scenarios['Neither ventilation nor masks'] = without_mask_or_vent.build_model()

    return scenarios


def comparison_plot(scenarios: typing.Dict[str, models.ExposureModel]):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    resolution = 350
    times = None

    dash_styled_scenarios = [
        'Base scenario with FFP2 masks',
        'Base scenario with HEPA filter',
        'Base scenario with HEPA and FFP2 masks',
    ]

    for name, model in scenarios.items():
        if times is None:
            t_start, t_end = model_start_end(model)
            times = np.linspace(t_start, t_end, resolution)
        datetimes = [datetime(1970, 1, 1) + timedelta(hours=time) for time in times]
        concentrations = [np.mean(model.concentration_model.concentration(time))
                          for time in times]

        if name in dash_styled_scenarios:
            ax.plot(datetimes, concentrations, label=name, linestyle='--')
        else:
            ax.plot(datetimes, concentrations, label=name, linestyle='-', alpha=0.5)

    # Place a legend outside of the axes itself.
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))

    ax.set_xlabel('Time of day')
    ax.set_ylabel('Mean concentration ($q/m^3$)')
    ax.set_title('Mean concentration of infectious quanta')

    return fig


def comparison_report(scenarios: typing.Dict[str, models.ExposureModel]):
    statistics = {}
    for name, model in scenarios.items():
        statistics[name] = {
            'probability_of_infection': np.mean(model.infection_probability()),
            'expected_new_cases': np.mean(model.expected_new_cases()),
        }
    return {
        'plot': img2base64(_figure2bytes(comparison_plot(scenarios))),
        'stats': statistics,
    }


@dataclasses.dataclass
class ReportGenerator:
    jinja_loader: jinja2.BaseLoader
    calculator_prefix: str

    def build_report(self, base_url: str, form: FormData) -> str:
        model = form.build_model()
        context = self.prepare_context(base_url, model, form)
        return self.render(context)

    def prepare_context(self, base_url: str, model: models.ExposureModel, form: FormData) -> dict:
        now = datetime.utcnow().astimezone()
        time = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        context = {
            'model': model,
            'form': form,
            'creation_date': time,
        }

        context.update(calculate_report_data(model))
        alternative_scenarios = manufacture_alternative_scenarios(form)
        context['alternative_scenarios'] = comparison_report(alternative_scenarios)
        context['qr_code'] = generate_qr_code(base_url, self.calculator_prefix, form)
        context['calculator_prefix'] = self.calculator_prefix
        context['scale_warning'] = {
            'level': 'Orange - 3', 
            'incidence_rate': 'in between 25 and 100 new cases per 100 000 inhabitants',
            'onsite_access': 'of about 5000', 
            'threshold' : ''
        } 
        return context

    def _template_environment(self) -> jinja2.Environment:
        env = jinja2.Environment(
            loader=self.jinja_loader,
            undefined=jinja2.StrictUndefined,
        )
        env.filters['non_zero_percentage'] = non_zero_percentage
        env.filters['readable_minutes'] = readable_minutes
        env.filters['minutes_to_time'] = minutes_to_time
        env.filters['float_format'] = "{0:.2f}".format
        env.filters['int_format'] = "{:0.0f}".format
        return env

    def render(self, context: dict) -> str:
        template = self._template_environment().get_template("calculator.report.html.j2")
        return template.render(**context)
