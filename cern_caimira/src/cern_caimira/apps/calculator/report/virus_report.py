from datetime import datetime
import dataclasses

import concurrent.futures
import json
import typing
import jinja2
import numpy as np

from .. import markdown_tools

from caimira.calculator.models import models
from caimira.calculator.validators.virus.virus_validator import VirusFormData
from caimira.calculator.report.virus_report_data import calculate_report_data, interesting_times, manufacture_alternative_scenarios, manufacture_viral_load_scenarios_percentiles, comparison_report, generate_permalink


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
        model = form.build_model()
        context = self.prepare_context(
            base_url, model, form, executor_factory=executor_factory)
        return self.render(context)

    def prepare_context(
            self,
            base_url: str,
            model: models.ExposureModel,
            form: VirusFormData,
            executor_factory: typing.Callable[[], concurrent.futures.Executor],
    ) -> dict:
        now = datetime.utcnow().astimezone()
        time = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        data_registry_version = f"v{model.data_registry.version}" if model.data_registry.version else None
        context = {
            'model': model,
            'form': form,
            'creation_date': time,
            'data_registry_version': data_registry_version,
        }

        scenario_sample_times = interesting_times(model)
        report_data = calculate_report_data(
            form, model, executor_factory=executor_factory)
        context.update(report_data)

        alternative_scenarios = manufacture_alternative_scenarios(form)
        context['alternative_viral_load'] = manufacture_viral_load_scenarios_percentiles(
            model) if form.conditional_probability_viral_loads else None
        context['alternative_scenarios'] = comparison_report(
            form, report_data, alternative_scenarios, scenario_sample_times, executor_factory=executor_factory,
        )
        context['permalink'] = generate_permalink(
            base_url, self.get_root_url, self.get_root_calculator_url, form)
        context['get_url'] = self.get_root_url
        context['get_calculator_url'] = self.get_root_calculator_url

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
