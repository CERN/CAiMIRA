from datetime import datetime
import dataclasses

import concurrent.futures
import json
import typing
import jinja2
import numpy as np
import urllib
import base64
import zlib

from . import markdown_tools

from caimira.calculator.validators.virus.virus_validator import VirusFormData
from caimira.calculator.models import dataclass_utils, models, monte_carlo as mc


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


def model_start_end(model: models.ExposureModel):
    t_start = min(model.exposed.presence_interval().boundaries()[0][0],
                  model.concentration_model.infected.presence_interval().boundaries()[0][0])
    t_end = max(model.exposed.presence_interval().boundaries()[-1][1],
                model.concentration_model.infected.presence_interval().boundaries()[-1][1])
    return t_start, t_end


def fill_big_gaps(array, gap_size):
    """
    Insert values into the given sorted list if there is a gap of more than ``gap_size``.
    All values in the given array are preserved, even if they are within the ``gap_size`` of one another.

    >>> fill_big_gaps([1, 2, 4], gap_size=0.75)
    [1, 1.75, 2, 2.75, 3.5, 4]

    """
    result = []
    if len(array) == 0:
        raise ValueError("Input array must be len > 0")

    last_value = array[0]
    for value in array:
        while value - last_value > gap_size + 1e-15:
            last_value = last_value + gap_size
            result.append(last_value)
        result.append(value)
        last_value = value
    return result


def non_temp_transition_times(model: models.ExposureModel):
    """
    Return the non-temperature (and PiecewiseConstant) based transition times.

    """
    def walk_model(model, name=""):
        # Extend walk_dataclass to handle lists of dataclasses
        # (e.g. in MultipleVentilation).
        for name, obj in dataclass_utils.walk_dataclass(model, name=name):
            if name.endswith('.ventilations') and isinstance(obj, (list, tuple)):
                for i, item in enumerate(obj):
                    fq_name_i = f'{name}[{i}]'
                    yield fq_name_i, item
                    if dataclasses.is_dataclass(item):
                        yield from dataclass_utils.walk_dataclass(item, name=fq_name_i)
            else:
                yield name, obj

    t_start, t_end = model_start_end(model)

    change_times = {t_start, t_end}
    for name, obj in walk_model(model, name="exposure"):
        if isinstance(obj, models.Interval):
            change_times |= obj.transition_times()

    # Only choose times that are in the range of the model (removes things
    # such as PeriodicIntervals, which extend beyond the model itself).
    return sorted(time for time in change_times if (t_start <= time <= t_end))


def interesting_times(model: models.ExposureModel, approx_n_pts: typing.Optional[int] = None) -> typing.List[float]:
    """
    Pick approximately ``approx_n_pts`` time points which are interesting for the
    given model. If not provided by argument, ``approx_n_pts`` is set to be 15 times
    the number of hours of the simulation.

    Initially the times are seeded by important state change times (excluding
    outside temperature), and the times are then subsequently expanded to ensure
    that the step size is at most ``(t_end - t_start) / approx_n_pts``.

    """
    times = non_temp_transition_times(model)
    sim_duration = max(times) - min(times)
    if not approx_n_pts:
        approx_n_pts = sim_duration * 15

    # Expand the times list to ensure that we have a maximum gap size between
    # the key times.
    nice_times = fill_big_gaps(times, gap_size=(sim_duration) / approx_n_pts)
    return nice_times


def manufacture_viral_load_scenarios_percentiles(model: mc.ExposureModel) -> typing.Dict[str, mc.ExposureModel]:
    viral_load = model.concentration_model.infected.virus.viral_load_in_sputum
    scenarios = {}
    for percentil in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99):
        vl = np.quantile(viral_load, percentil)
        specific_vl_scenario = dataclass_utils.nested_replace(model,
                                                              {'concentration_model.infected.virus.viral_load_in_sputum': vl}
                                                              )
        scenarios[str(vl)] = np.mean(
            specific_vl_scenario.infection_probability())
    return scenarios


def manufacture_alternative_scenarios(form: VirusFormData) -> typing.Dict[str, mc.ExposureModel]:
    scenarios = {}
    if (form.short_range_option == "short_range_no"):
        # Two special option cases - HEPA and/or FFP2 masks.
        FFP2_being_worn = bool(form.mask_wearing_option ==
                               'mask_on' and form.mask_type == 'FFP2')
        if FFP2_being_worn and form.hepa_option:
            FFP2andHEPAalternative = dataclass_utils.replace(
                form, mask_type='Type I')
            if not (form.hepa_option and form.mask_wearing_option == 'mask_on' and form.mask_type == 'Type I'):
                scenarios['Base scenario with HEPA filter and Type I masks'] = FFP2andHEPAalternative.build_mc_model()
        if not FFP2_being_worn and form.hepa_option:
            noHEPAalternative = dataclass_utils.replace(form, mask_type='FFP2')
            noHEPAalternative = dataclass_utils.replace(
                noHEPAalternative, mask_wearing_option='mask_on')
            noHEPAalternative = dataclass_utils.replace(
                noHEPAalternative, hepa_option=False)
            if not (not form.hepa_option and FFP2_being_worn):
                scenarios['Base scenario without HEPA filter, with FFP2 masks'] = noHEPAalternative.build_mc_model()

        # The remaining scenarios are based on Type I masks (possibly not worn)
        # and no HEPA filtration.
        form = dataclass_utils.replace(form, mask_type='Type I')
        if form.hepa_option:
            form = dataclass_utils.replace(form, hepa_option=False)

        with_mask = dataclass_utils.replace(
            form, mask_wearing_option='mask_on')
        without_mask = dataclass_utils.replace(
            form, mask_wearing_option='mask_off')

        if form.ventilation_type == 'mechanical_ventilation':
            # scenarios['Mechanical ventilation with Type I masks'] = with_mask.build_mc_model()
            if not (form.mask_wearing_option == 'mask_off'):
                scenarios['Mechanical ventilation without masks'] = without_mask.build_mc_model(
                )

        elif form.ventilation_type == 'natural_ventilation':
            # scenarios['Windows open with Type I masks'] = with_mask.build_mc_model()
            if not (form.mask_wearing_option == 'mask_off'):
                scenarios['Windows open without masks'] = without_mask.build_mc_model()

        # No matter the ventilation scheme, we include scenarios which don't have any ventilation.
        with_mask_no_vent = dataclass_utils.replace(
            with_mask, ventilation_type='no_ventilation')
        without_mask_or_vent = dataclass_utils.replace(
            without_mask, ventilation_type='no_ventilation')

        if not (form.mask_wearing_option == 'mask_on' and form.mask_type == 'Type I' and form.ventilation_type == 'no_ventilation'):
            scenarios['No ventilation with Type I masks'] = with_mask_no_vent.build_mc_model()
        if not (form.mask_wearing_option == 'mask_off' and form.ventilation_type == 'no_ventilation'):
            scenarios['Neither ventilation nor masks'] = without_mask_or_vent.build_mc_model()

    else:
        no_short_range_alternative = dataclass_utils.replace(
            form, short_range_interactions=[])
        scenarios['Base scenario without short-range interactions'] = no_short_range_alternative.build_mc_model()

    return scenarios


def scenario_statistics(
    mc_model: mc.ExposureModel,
    sample_times: typing.List[float],
    compute_prob_exposure: bool
):
    model = mc_model.build_model(
        size=mc_model.data_registry.monte_carlo_sample_size)
    if (compute_prob_exposure):
        # It means we have data to calculate the total_probability_rule
        prob_probabilistic_exposure = model.total_probability_rule()
    else:
        prob_probabilistic_exposure = 0.

    return {
        'probability_of_infection': np.mean(model.infection_probability()),
        'expected_new_cases': np.mean(model.expected_new_cases()),
        'concentrations': [
            np.mean(model.concentration(time))
            for time in sample_times
        ],
        'prob_probabilistic_exposure': prob_probabilistic_exposure,
    }


def comparison_report(
        form: VirusFormData,
        report_data: typing.Dict[str, typing.Any],
        scenarios: typing.Dict[str, mc.ExposureModel],
        sample_times: typing.List[float],
        executor_factory: typing.Callable[[], concurrent.futures.Executor],
):
    if (form.short_range_option == "short_range_no"):
        statistics = {
            'Current scenario': {
                'probability_of_infection': report_data['prob_inf'],
                'expected_new_cases': report_data['expected_new_cases'],
                'concentrations': report_data['concentrations'],
            }
        }
    else:
        statistics = {}

    if (form.short_range_option == "short_range_yes" and form.exposure_option == "p_probabilistic_exposure"):
        compute_prob_exposure = True
    else:
        compute_prob_exposure = False

    with executor_factory() as executor:
        results = executor.map(
            scenario_statistics,
            scenarios.values(),
            [sample_times] * len(scenarios),
            [compute_prob_exposure] * len(scenarios),
            timeout=60,
        )

    for (name, model), model_stats in zip(scenarios.items(), results):
        statistics[name] = model_stats

    return {
        'stats': statistics,
    }


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
class ReportGenerator:
    jinja_loader: jinja2.BaseLoader
    get_root_url: typing.Any
    get_root_calculator_url: typing.Any

    def build_report(
            self,
            base_url: str,
            form: VirusFormData,
            model: models.ExposureModel,
            report_data: dict,
            executor_factory: typing.Callable[[], concurrent.futures.Executor],
    ) -> str:
        context = self.prepare_context(
            base_url, form, model, report_data, executor_factory=executor_factory)
        return self.render(context)

    def prepare_context(
            self,
            base_url: str,
            form: VirusFormData,
            model: models.ExposureModel,
            report_data: dict,
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
