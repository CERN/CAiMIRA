import concurrent.futures
import base64
import dataclasses
import io
import typing
import numpy as np
import matplotlib.pyplot as plt

from caimira.calculator.models import models
# from caimira.apps.calculator import markdown_tools
# from caimira.profiler import profile
from caimira.calculator.store.data_registry import DataRegistry
from caimira.calculator.models import monte_carlo as mc
from caimira.calculator.validators.virus.virus_validator import VirusFormData
from caimira.calculator.models import dataclass_utils

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



def concentrations_with_sr_breathing(form: VirusFormData, model: models.ExposureModel, times: typing.List[float], short_range_intervals: typing.List) -> typing.List[float]:
    lower_concentrations = []
    for time in times:
        for index, (start, stop) in enumerate(short_range_intervals):
            # For visualization issues, add short-range breathing activity to the initial long-range concentrations
            if start <= time <= stop and form.short_range_interactions[index]['expiration'] == 'Breathing':
                lower_concentrations.append(np.array(model.concentration(float(time))).mean())
                break
        lower_concentrations.append(np.array(model.concentration_model.concentration(float(time))).mean())
    return lower_concentrations


def _calculate_deposited_exposure(model, time1, time2, fn_name=None):
    return np.array(model.deposited_exposure_between_bounds(float(time1), float(time2))).mean(),fn_name


def _calculate_long_range_deposited_exposure(model, time1, time2, fn_name=None):
    return np.array(model.long_range_deposited_exposure_between_bounds(float(time1), float(time2))).mean(), fn_name


def _calculate_co2_concentration(CO2_model, time, fn_name=None):
    return np.array(CO2_model.concentration(float(time))).mean(), fn_name


# @profile
def calculate_report_data(form: VirusFormData, model: models.ExposureModel, executor_factory: typing.Callable[[], concurrent.futures.Executor]) -> typing.Dict[str, typing.Any]:
    times = interesting_times(model)
    short_range_intervals = [interaction.presence.boundaries()[0] for interaction in model.short_range]
    short_range_expirations = [interaction['expiration'] for interaction in form.short_range_interactions] if form.short_range_option == "short_range_yes" else []

    concentrations = [
        np.array(model.concentration(float(time))).mean()
        for time in times
    ]
    lower_concentrations = concentrations_with_sr_breathing(form, model, times, short_range_intervals)

    CO2_model: models.CO2ConcentrationModel = form.build_CO2_model()

    # compute deposited exposures and CO2 concentrations in parallel to increase performance
    deposited_exposures = []
    long_range_deposited_exposures = []
    CO2_concentrations = []

    tasks = []
    with executor_factory() as executor:
        for time1, time2 in zip(times[:-1], times[1:]):
            tasks.append(executor.submit(_calculate_deposited_exposure, model, time1, time2, fn_name="de"))
            tasks.append(executor.submit(_calculate_long_range_deposited_exposure, model, time1, time2, fn_name="lr"))
            # co2 concentration: takes each time as param, not the interval
            tasks.append(executor.submit(_calculate_co2_concentration, CO2_model, time1, fn_name="co2"))
        # co2 concentration: calculate the last time too
        tasks.append(executor.submit(_calculate_co2_concentration, CO2_model, times[-1], fn_name="co2"))

    for task in tasks:
        result, fn_name = task.result()
        if fn_name == "de":
            deposited_exposures.append(result)
        elif fn_name == "lr":
            long_range_deposited_exposures.append(result)
        elif fn_name == "co2":
            CO2_concentrations.append(result)

    cumulative_doses = np.cumsum(deposited_exposures)
    long_range_cumulative_doses = np.cumsum(long_range_deposited_exposures)

    prob = np.array(model.infection_probability())
    prob_dist_count, prob_dist_bins = np.histogram(prob/100, bins=100, density=True)
    prob_probabilistic_exposure = np.array(model.total_probability_rule()).mean()
    expected_new_cases = np.array(model.expected_new_cases()).mean()
    uncertainties_plot_src = img2base64(_figure2bytes(uncertainties_plot(model, prob))) if form.conditional_probability_plot else None
    exposed_presence_intervals = [list(interval) for interval in model.exposed.presence_interval().boundaries()]
    conditional_probability_data = {key: value for key, value in
                                    zip(('viral_loads', 'pi_means', 'lower_percentiles', 'upper_percentiles'),
                                        manufacture_conditional_probability_data(model, prob))}


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


def conditional_prob_inf_given_vl_dist(
        data_registry: DataRegistry,
        infection_probability: models._VectorisedFloat,
        viral_loads: np.ndarray,
        specific_vl: float,
        step: models._VectorisedFloat
    ):

    pi_means = []
    lower_percentiles = []
    upper_percentiles = []

    for vl_log in viral_loads:
        specific_prob = infection_probability[np.where((vl_log-step/2-specific_vl)*(vl_log+step/2-specific_vl)<0)[0]] #type: ignore
        pi_means.append(specific_prob.mean())
        lower_percentiles.append(np.quantile(specific_prob, data_registry.conditional_prob_inf_given_viral_load['lower_percentile']))
        upper_percentiles.append(np.quantile(specific_prob, data_registry.conditional_prob_inf_given_viral_load['upper_percentile']))

    return pi_means, lower_percentiles, upper_percentiles


def manufacture_conditional_probability_data(
    exposure_model: models.ExposureModel,
    infection_probability: models._VectorisedFloat
):
    data_registry: DataRegistry = exposure_model.data_registry

    min_vl = data_registry.conditional_prob_inf_given_viral_load['min_vl']
    max_vl = data_registry.conditional_prob_inf_given_viral_load['max_vl']
    step = (max_vl - min_vl)/100
    viral_loads = np.arange(min_vl, max_vl, step)
    specific_vl = np.log10(exposure_model.concentration_model.virus.viral_load_in_sputum)
    pi_means, lower_percentiles, upper_percentiles = conditional_prob_inf_given_vl_dist(data_registry, infection_probability, viral_loads,
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
