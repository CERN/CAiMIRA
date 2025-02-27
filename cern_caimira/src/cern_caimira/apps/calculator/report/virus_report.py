from datetime import datetime
import dataclasses

import concurrent.futures
import json
import typing
import jinja2
import urllib
import zlib
import base64
import numpy as np

from .. import markdown_tools

from caimira.calculator.models import models
from caimira.calculator.validators.virus.virus_validator import VirusFormData
from caimira.calculator.report.virus_report_data import alternative_scenarios_data, calculate_report_data, calculate_vl_scenarios_percentiles


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


def hour_format(hour: float) -> str:
    # Convert float hour to HH:MM format
    hours = int(hour)
    minutes = int(hour % 1 * 60)
    return f"{hours}:{minutes if minutes != 0 else '00'}"


def percentage(absolute: float) -> float:
    return absolute * 100


def non_zero_percentage(percentage: int) -> str:
    if percentage < 0.01:
        return "<0.01%"
    elif percentage < 1:
        return "{:0.2f}%".format(percentage)
    elif percentage > 99.9 or np.isnan(percentage):
        return ">99.9%"
    else:
        return "{:0.1f}%".format(percentage)


def generate_permalink(base_url, get_root_url,  get_root_calculator_url, form: VirusFormData):
    form_dict = VirusFormData.to_dict(form, strip_defaults=True)

    # Generate the calculator URL arguments that would be needed to re-create this
    # form.
    args = urllib.parse.urlencode(form_dict)

    # Then zlib compress + base64 encode the string. To be inverted by the
    # /_c/ endpoint.
    compressed_args = base64.b64encode(zlib.compress(args.encode())).decode()
    qr_url = f"{base_url}{get_root_url()}/_c/{compressed_args}"
    url = f"{base_url}{get_root_calculator_url()}?{args}"

    return {
        'link': url,
        'shortened': qr_url,
    }


@dataclasses.dataclass
class VirusReportGenerator:
    jinja_loader: jinja2.BaseLoader
    get_root_url: typing.Any
    get_root_calculator_url: typing.Any

    def build_report(
            self,
            base_url: str,
            form: VirusFormData,
            executor_factory: typing.Callable[[], concurrent.futures.Executor],
    ) -> str:
        context = self.prepare_context(
            base_url, form, executor_factory=executor_factory)
        return self.render(context)

    def prepare_context(
            self,
            base_url: str,
            form: VirusFormData,
            executor_factory: typing.Callable[[], concurrent.futures.Executor],
    ) -> dict:
        now = datetime.utcnow().astimezone()
        time = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        context = {
            'form': form,
            'creation_date': time,
        }

        # Main report data
        report_data = calculate_report_data(form, executor_factory)
        context.update(report_data)

        # Model and Data Registry
        model: models.ExposureModel = report_data['model']
        data_registry_version: typing.Optional[str] = f"v{model.data_registry.version}" if model.data_registry.version else None

        # Alternative scenarios data
        if form.occupancy_format == 'static':
            context.update(alternative_scenarios_data(form, report_data, executor_factory)) 

        # Alternative viral load data
        if form.conditional_probability_viral_loads:
            alternative_viral_load: typing.Dict[str,typing.Any] = calculate_vl_scenarios_percentiles(model)
            context.update(alternative_viral_load)

        # Permalink
        permalink: typing.Dict[str, str] = generate_permalink(
            base_url, self.get_root_url, self.get_root_calculator_url, form)

        # URLs (root, calculator and permalink)
        context.update({
            'model_repr': repr(model),
            'data_registry_version': data_registry_version,
            'permalink': permalink,
            'get_url': self.get_root_url,
            'get_calculator_url': self.get_root_calculator_url,
        })

        return context

    def _template_environment(self) -> jinja2.Environment:
        env = jinja2.Environment(
            loader=self.jinja_loader,
            undefined=jinja2.StrictUndefined,
        )
        env.globals["common_text"] = markdown_tools.extract_rendered_markdown_blocks(
            env.get_template('common_text.md.j2')
        )
        env.filters['non_zero_percentage'] = non_zero_percentage
        env.filters['readable_minutes'] = readable_minutes
        env.filters['minutes_to_time'] = minutes_to_time
        env.filters['hour_format'] = hour_format
        env.filters['float_format'] = "{0:.2f}".format
        env.filters['int_format'] = "{:0.0f}".format
        env.filters['percentage'] = percentage
        env.filters['JSONify'] = json.dumps
        return env

    def render(self, context: dict) -> str:
        template = self._template_environment().get_template("calculator.report.html.j2")
        return template.render(**context, text_blocks=template.globals["common_text"])
