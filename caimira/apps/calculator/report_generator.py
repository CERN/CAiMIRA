import concurrent.futures
import base64
import dataclasses
from datetime import datetime
import io
import json
import typing
import urllib
import zlib

import jinja2
import numpy as np
import matplotlib.pyplot as plt

from caimira import models
from caimira.apps.calculator import markdown_tools
from ... import monte_carlo as mc
from .model_generator import FormData, DEFAULT_MC_SAMPLE_SIZE
from ... import dataclass_utils
from caimira.store.configuration import config


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
    if not approx_n_pts: approx_n_pts = sim_duration * 15

    # Expand the times list to ensure that we have a maximum gap size between
    # the key times.
    nice_times = fill_big_gaps(times, gap_size=(sim_duration) / approx_n_pts)
    return nice_times


def concentrations_with_sr_breathing(form: FormData, model: models.ExposureModel, times: typing.List[float], short_range_intervals: typing.List) -> typing.List[float]:
    lower_concentrations = []
    for time in times:
        for index, (start, stop) in enumerate(short_range_intervals):
            # For visualization issues, add short-range breathing activity to the initial long-range concentrations
            if start <= time <= stop and form.short_range_interactions[index]['expiration'] == 'Breathing':
                lower_concentrations.append(np.array(model.concentration(float(time))).mean())
                break
        lower_concentrations.append(np.array(model.concentration_model.concentration(float(time))).mean())
    return lower_concentrations


def calculate_report_data(form: FormData, model: models.ExposureModel) -> typing.Dict[str, typing.Any]:
    times = interesting_times(model)
    short_range_intervals = [interaction.presence.boundaries()[0] for interaction in model.short_range]
    short_range_expirations = [interaction['expiration'] for interaction in form.short_range_interactions] if form.short_range_option == "short_range_yes" else []
    
    concentrations = [
        np.array(model.concentration(float(time))).mean()
        for time in times
    ]  
    lower_concentrations = concentrations_with_sr_breathing(form, model, times, short_range_intervals)
    
    cumulative_doses = np.cumsum([
        np.array(model.deposited_exposure_between_bounds(float(time1), float(time2))).mean()
        for time1, time2 in zip(times[:-1], times[1:])
    ])
    long_range_cumulative_doses = np.cumsum([
        np.array(model.long_range_deposited_exposure_between_bounds(float(time1), float(time2))).mean()
        for time1, time2 in zip(times[:-1], times[1:])
    ])

    CO2_model: models.CO2ConcentrationModel = form.build_CO2_model()
    CO2_concentrations = {'CO₂': {'concentrations': [
        np.array(CO2_model.concentration(float(time))).mean()
        for time in times
    ]}}

    prob = np.array(model.infection_probability())
    prob_dist_count, prob_dist_bins = np.histogram(prob/100, bins=100, density=True)
    prob_probabilistic_exposure = np.array(model.total_probability_rule()).mean()
    expected_new_cases = np.array(model.expected_new_cases()).mean()
    uncertainties_plot_src = img2base64(_figure2bytes(uncertainties_plot(model, prob))) if form.conditional_probability_plot else None
    exposed_presence_intervals = [list(interval) for interval in model.exposed.presence_interval().boundaries()]
    conditional_probability_data = {key: value for key, value in 
                                    zip(('viral_loads', 'pi_means', 'lower_percentiles', 'upper_percentiles'), 
                                        manufacture_conditional_probability_data(model, prob))}

    CO2_times = list(form.CO2_data['times']) if form.CO2_data_option else []
    CO2_values = list(form.CO2_data['CO2']) if form.CO2_data_option else []
    ex, airs = model.CO2_profile.CO2_fit_params()
    co2_plot = img2base64(_figure2bytes(CO2_plot(CO2_times, CO2_values))) if form.CO2_data_option else None

    return {
        "model_repr": repr(model),
        "times": list(times),
        "exposed_presence_intervals": exposed_presence_intervals,
        "short_range_intervals": short_range_intervals,
        "short_range_expirations": short_range_expirations,
        "concentrations": concentrations,
        "concentrations_zoomed": lower_concentrations,
        "cumulative_doses": list(cumulative_doses),
        "long_range_cumulative_doses": list(long_range_cumulative_doses),
        "prob_inf": prob.mean(),
        "prob_inf_sd": prob.std(),
        "prob_dist": list(prob),
        "prob_hist_count": list(prob_dist_count),
        "prob_hist_bins": list(prob_dist_bins),
        "prob_probabilistic_exposure": prob_probabilistic_exposure,
        "expected_new_cases": expected_new_cases,
        "uncertainties_plot_src": uncertainties_plot_src,
        "CO2_concentrations": CO2_concentrations,
        "vl_dist": list(np.log10(model.concentration_model.virus.viral_load_in_sputum)),
        "conditional_probability_data": conditional_probability_data,
    }


def generate_permalink(base_url, get_root_url,  get_root_calculator_url, form: FormData):
    form_dict = FormData.to_dict(form, strip_defaults=True)

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


def conditional_prob_inf_given_vl_dist(infection_probability: models._VectorisedFloat, 
                                       viral_loads: np.ndarray, specific_vl: float, step: models._VectorisedFloat):
    pi_means = []
    lower_percentiles = []
    upper_percentiles = []
    
    for vl_log in viral_loads:
        specific_prob = infection_probability[np.where((vl_log-step/2-specific_vl)*(vl_log+step/2-specific_vl)<0)[0]] #type: ignore
        pi_means.append(specific_prob.mean())
        lower_percentiles.append(np.quantile(specific_prob, config.conditional_prob_inf_given_viral_load['lower_percentile']))
        upper_percentiles.append(np.quantile(specific_prob, config.conditional_prob_inf_given_viral_load['upper_percentile']))
    
    return pi_means, lower_percentiles, upper_percentiles


def manufacture_conditional_probability_data(exposure_model: models.ExposureModel, 
                                             infection_probability: models._VectorisedFloat):
    
    min_vl = config.conditional_prob_inf_given_viral_load['min_vl']
    max_vl = config.conditional_prob_inf_given_viral_load['max_vl']
    step = (max_vl - min_vl)/100
    viral_loads = np.arange(min_vl, max_vl, step)   
    specific_vl = np.log10(exposure_model.concentration_model.virus.viral_load_in_sputum)
    pi_means, lower_percentiles, upper_percentiles = conditional_prob_inf_given_vl_dist(infection_probability, viral_loads, 
                                                                                        specific_vl, step)
    
    return list(viral_loads), list(pi_means), list(lower_percentiles), list(upper_percentiles)


def uncertainties_plot(exposure_model: models.ExposureModel, prob: models._VectorisedFloat):
    fig = plt.figure(figsize=(4, 7), dpi=110)
    
    infection_probability = prob / 100
    viral_loads, pi_means, lower_percentiles, upper_percentiles = manufacture_conditional_probability_data(exposure_model, infection_probability)

    fig, axs = plt.subplots(2, 3, 
        gridspec_kw={'width_ratios': [5, 0.5] + [1],
            'height_ratios': [3, 1], 'wspace': 0},
        sharey='row', 
        sharex='col')

    for y, x in [(0, 1)] + [(1, i + 1) for i in range(2)]:
        axs[y, x].axis('off')

    axs[0, 1].set_visible(False)

    axs[0, 0].plot(viral_loads, pi_means, label='Predictive total probability')
    axs[0, 0].fill_between(viral_loads, lower_percentiles, upper_percentiles, alpha=0.1, label='5ᵗʰ and 95ᵗʰ percentile')

    axs[0, 2].hist(infection_probability, bins=30, orientation='horizontal')
    axs[0, 2].set_xticks([])
    axs[0, 2].set_xticklabels([])
    axs[0, 2].set_facecolor("lightgrey")

    highest_bar = axs[0, 2].get_xlim()[1]
    axs[0, 2].set_xlim(0, highest_bar)

    axs[0, 2].text(highest_bar * 0.5, 0.5,
                        rf"$\bf{np.round(np.mean(infection_probability) * 100, 1)}$%", ha='center', va='center')
    axs[1, 0].hist(np.log10(exposure_model.concentration_model.infected.virus.viral_load_in_sputum),
                    bins=150, range=(2, 10), color='grey')
    axs[1, 0].set_facecolor("lightgrey")
    axs[1, 0].set_yticks([])
    axs[1, 0].set_yticklabels([])
    axs[1, 0].set_xticks([i for i in range(2, 13, 2)])
    axs[1, 0].set_xticklabels(['$10^{' + str(i) + '}$' for i in range(2, 13, 2)])
    axs[1, 0].set_xlim(2, 10)
    axs[1, 0].set_xlabel('Viral load\n(RNA copies)', fontsize=12)
    axs[0, 0].set_ylabel('Conditional Probability\nof Infection', fontsize=12)
 
    axs[0, 0].text(9.5, -0.01, '$(i)$')
    axs[1, 0].text(9.5, axs[1, 0].get_ylim()[1] * 0.8, '$(ii)$')
    axs[0, 2].set_title('$(iii)$', fontsize=10)

    axs[0, 0].legend()
    return fig
    

def _img2bytes(figure):
    # Draw the image
    img_data = io.BytesIO()
    figure.save(img_data, format='png', bbox_inches="tight")
    return img_data


def _figure2bytes(figure):
    # Draw the image
    img_data = io.BytesIO()
    figure.savefig(img_data, format='png', bbox_inches="tight", transparent=True, dpi=110)
    return img_data


def img2base64(img_data) -> str:
    img_data.seek(0)
    pic_hash = base64.b64encode(img_data.read()).decode('ascii')
    # A src suitable for a tag such as f'<img id="scenario_concentration_plot" src="{result}">.
    return f'data:image/png;base64,{pic_hash}'


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


def percentage(absolute: float) -> float:
    return absolute * 100


def non_zero_percentage(percentage: int) -> str:
    if percentage < 0.01:
        return "<0.01%"
    elif percentage < 1:
        return "{:0.2f}%".format(percentage)
    elif np.isnan(percentage):
        return "99.9%"
    else:
        return "{:0.1f}%".format(percentage)


def manufacture_viral_load_scenarios_percentiles(model: mc.ExposureModel) -> typing.Dict[str, mc.ExposureModel]:
    viral_load = model.concentration_model.infected.virus.viral_load_in_sputum
    scenarios = {}
    for percentil in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99):
        vl = np.quantile(viral_load, percentil)
        specific_vl_scenario = dataclass_utils.nested_replace(model, 
            {'concentration_model.infected.virus.viral_load_in_sputum': vl}
        )
        scenarios[str(vl)] = np.mean(specific_vl_scenario.infection_probability())
    return scenarios


def manufacture_alternative_scenarios(form: FormData) -> typing.Dict[str, mc.ExposureModel]:
    scenarios = {}
    if (form.short_range_option == "short_range_no"):
        # Two special option cases - HEPA and/or FFP2 masks.
        FFP2_being_worn = bool(form.mask_wearing_option == 'mask_on' and form.mask_type == 'FFP2')
        if FFP2_being_worn and form.hepa_option:
            FFP2andHEPAalternative = dataclass_utils.replace(form, mask_type='Type I')
            if not (form.hepa_option and form.mask_wearing_option == 'mask_on' and form.mask_type == 'Type I'):
                scenarios['Base scenario with HEPA filter and Type I masks'] = FFP2andHEPAalternative.build_mc_model()
        if not FFP2_being_worn and form.hepa_option:
            noHEPAalternative = dataclass_utils.replace(form, mask_type = 'FFP2')
            noHEPAalternative = dataclass_utils.replace(noHEPAalternative, mask_wearing_option = 'mask_on')
            noHEPAalternative = dataclass_utils.replace(noHEPAalternative, hepa_option=False)
            if not (not form.hepa_option and FFP2_being_worn):
                scenarios['Base scenario without HEPA filter, with FFP2 masks'] = noHEPAalternative.build_mc_model()

        # The remaining scenarios are based on Type I masks (possibly not worn)
        # and no HEPA filtration.
        form = dataclass_utils.replace(form, mask_type='Type I')
        if form.hepa_option:
            form = dataclass_utils.replace(form, hepa_option=False)

        with_mask = dataclass_utils.replace(form, mask_wearing_option='mask_on')
        without_mask = dataclass_utils.replace(form, mask_wearing_option='mask_off')

        if form.ventilation_type == 'mechanical_ventilation':
            #scenarios['Mechanical ventilation with Type I masks'] = with_mask.build_mc_model()
            if not (form.mask_wearing_option == 'mask_off'):
                scenarios['Mechanical ventilation without masks'] = without_mask.build_mc_model()

        elif form.ventilation_type == 'natural_ventilation':
            #scenarios['Windows open with Type I masks'] = with_mask.build_mc_model()
            if not (form.mask_wearing_option == 'mask_off'):
                scenarios['Windows open without masks'] = without_mask.build_mc_model()

        # No matter the ventilation scheme, we include scenarios which don't have any ventilation.
        with_mask_no_vent = dataclass_utils.replace(with_mask, ventilation_type='no_ventilation')
        without_mask_or_vent = dataclass_utils.replace(without_mask, ventilation_type='no_ventilation')

        if not (form.mask_wearing_option == 'mask_on' and form.mask_type == 'Type I' and form.ventilation_type == 'no_ventilation'):
            scenarios['No ventilation with Type I masks'] = with_mask_no_vent.build_mc_model()
        if not (form.mask_wearing_option == 'mask_off' and form.ventilation_type == 'no_ventilation'):
            scenarios['Neither ventilation nor masks'] = without_mask_or_vent.build_mc_model()
    
    else:
        no_short_range_alternative = dataclass_utils.replace(form, short_range_interactions=[])
        scenarios['Base scenario without short-range interactions'] = no_short_range_alternative.build_mc_model()

    return scenarios


def scenario_statistics(mc_model: mc.ExposureModel, sample_times: typing.List[float], compute_prob_exposure: bool):
    model = mc_model.build_model(size=DEFAULT_MC_SAMPLE_SIZE)
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
        form: FormData,
        report_data: typing.Dict[str, typing.Any],
        scenarios: typing.Dict[str, mc.ExposureModel],
        sample_times: typing.List[float],
        executor_factory: typing.Callable[[], concurrent.futures.Executor],
):
    if (form.short_range_option == "short_range_no"):
        statistics = {
            'Current scenario' : {
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


@dataclasses.dataclass
class ReportGenerator:
    jinja_loader: jinja2.BaseLoader
    get_root_url: typing.Any
    get_root_calculator_url: typing.Any

    def build_report(
            self,
            base_url: str,
            form: FormData,
            executor_factory: typing.Callable[[], concurrent.futures.Executor],
    ) -> str:
        model = form.build_model()
        context = self.prepare_context(base_url, model, form, executor_factory=executor_factory)
        return self.render(context)

    def prepare_context(
            self,
            base_url: str,
            model: models.ExposureModel,
            form: FormData,
            executor_factory: typing.Callable[[], concurrent.futures.Executor],
    ) -> dict:
        now = datetime.utcnow().astimezone()
        time = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        context = {
            'model': model,
            'form': form,
            'creation_date': time,
        }

        scenario_sample_times = interesting_times(model)
        report_data = calculate_report_data(form, model)
        context.update(report_data)

        alternative_scenarios = manufacture_alternative_scenarios(form)
        context['alternative_viral_load'] = manufacture_viral_load_scenarios_percentiles(model) if form.conditional_probability_viral_loads else None
        context['alternative_scenarios'] = comparison_report(
            form, report_data, alternative_scenarios, scenario_sample_times, executor_factory=executor_factory,
        )
        context['permalink'] = generate_permalink(base_url, self.get_root_url, self.get_root_calculator_url, form)
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
        env.filters['float_format'] = "{0:.2f}".format
        env.filters['int_format'] = "{:0.0f}".format
        env.filters['percentage'] = percentage
        env.filters['JSONify'] = json.dumps
        return env

    def render(self, context: dict) -> str:
        template = self._template_environment().get_template("calculator.report.html.j2")
        return template.render(**context, text_blocks=template.globals["common_text"])
