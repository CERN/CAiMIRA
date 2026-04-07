import typing
import numpy as np
from scipy.optimize import brentq
import bisect

from caimira.calculator.models import models

import caimira.ventilation.get_models as get_models
import caimira.ventilation.model_response as model_response
from caimira.ventilation.scenarios import ScenarioVar

def carry_forward_air_change_times(
        air_change_per_hour_list: typing.Union[list, float], 
        vent_transition_times: list, 
        extended_vent_transition_times: list,
    ):
    """
    Re-specify the air exchange value at intervals between the time points in vent_transition_times
    for the finer intervals between the time points in extended_vent_transition_times.
    Note that vent_transition_times is a subset of extended_vent_transition_times and both lists are sorted.
    """
    extended_air_change_per_hour_list = []
    for time in extended_vent_transition_times[:-1]:
        i = bisect.bisect_right(vent_transition_times, time) - 1
        if i >= 0 and i < len(air_change_per_hour_list):
            extended_air_change_per_hour_list.append(air_change_per_hour_list[i])
        elif i == len(air_change_per_hour_list):
            extended_air_change_per_hour_list.append(air_change_per_hour_list[-1])
    return extended_air_change_per_hour_list

def max_occupancy(exposure_model: models.ExposureModel) -> int:
    times = exposure_model.population_state_change_times()
    max_n = 1
    for time in times:
        n_occupants = (
            exposure_model.exposed.people_present(time) 
            + exposure_model.concentration_model.infected.people_present(time)
        )
        if n_occupants > max_n:
            max_n = n_occupants
    return max_n

def clean_air_per_sec_per_pers(
        air_change_per_hour_list: typing.Union[list, float], 
        exposure_model: models.ExposureModel
    ) -> tuple[list[float], list[float]]:
    """
    Convert from air exchange per hour to liter per second per person.
    """
    room=exposure_model.concentration_model.room
    n_occupants = max_occupancy(exposure_model)
    return [1000 / 3600 * air_exch * room.volume / n_occupants for air_exch in air_change_per_hour_list]

def find_constant_air_exch(
    scenario: ScenarioVar,
    lim_probability_infection: float,
    lo=0,
    hi=60,
    tol=1e-2,
) -> tuple[float, float]:
    
    f = lambda air_exch: model_response.calculate_infection_probability(air_exch_values=air_exch, scenario=scenario)
    f0 = lambda air_exch: f(air_exch) - lim_probability_infection

    f_lo = f0(lo)
    f_hi = f0(hi)

    if f_lo <= 0:
        p = f(lo)
        return lo, p

    if f_hi > 0:
        p = f(hi)
        return hi, p

    root_air_exch = brentq(f0, lo, hi, xtol=tol)

    # Guarantee probability of infection <= lim_probability_infection 
    # OBS: Only guaranteed for this model build 
    p = f(root_air_exch)

    if p > lim_probability_infection:
        # Slightly increase air exchange 
        root_air_exch = np.nextafter(root_air_exch, hi)
        p = f(root_air_exch)

    return root_air_exch, p


def find_next_air_exch_by_co2(
    scenario: ScenarioVar,
    air_exch_list: typing.Union[list, float], 
    vent_transition_times: typing.Optional[list], 
    max_CO2: float,
    min_CO2_fraction: float = 0.95,
    target_CO2_fraction: float = 0.95,
    max_ventilation_changes: typing.Optional[int] = None,
    change_ventilation_at: typing.Optional[list[float]] = None,
    run_count: int = 1
    ):
    if not vent_transition_times:
        vent_transition_times = model_response.first_vent_transition_times(scenario)
    #TODO? differentiate between when/how often ventilation may be increased and decreased?
    if max_ventilation_changes and change_ventilation_at:
        print(f"May satisfy both max_ventilation_changes and change_ventilation_at, using change_ventilation_at")
    
    if min_CO2_fraction < 0 or min_CO2_fraction > 1:
        raise ValueError(f"target_fraction must be in range [0, 1], got {min_CO2_fraction}")
    exposure_model, times, concentrations = model_response.model_concentration_results(scenario, air_exch_list, vent_transition_times, viral_values=False)
    CO2_models: typing.Tuple[models.CO2ConcentrationModel] = get_models.get_CO2_models(exposure_model)

    if max_CO2 < CO2_models[0].min_background_concentration():
        raise ValueError(f"max_CO2 must be higher than the background concentration {CO2_models[0].min_background_concentration()}")
    
    if change_ventilation_at:
        raise NotImplementedError("TODO: let user define which times to change/increase ventilation (not just how many)") ###TODO: IMPLELMENT 
    
    concentrations_CO2 = concentrations[-1]
    min_CO2 = np.max([max_CO2*min_CO2_fraction, CO2_models[0].min_background_concentration()])
    target = np.max([max_CO2*target_CO2_fraction, CO2_models[0].min_background_concentration()])

    within_limit = True
    if change_ventilation_at:
        #TODO: match times in change_ventilation_at to closests the times in "times" (and the corresponding concentrations) and loop through these
        #concentrations_to_loop = 
        #times_to_loop = 
        pass
    else:
        if max_ventilation_changes and run_count > 1: # Let first change of the ventilation rate occur whenever
            k = np.max([len(concentrations_CO2) // max_ventilation_changes, 1])
        else:
            k = 1
        concentrations_to_loop = concentrations_CO2[::k]
        times_to_loop = times[::k]

    for c, time in zip(concentrations_to_loop, times_to_loop):
        if time > np.max(vent_transition_times): # allow some time for co2 level to decrease below max limit
            if c > max_CO2:
                within_limit = False
                vent_transition_times[-1]=time
                vent_transition_times.append(time+0.000000001) # Need one more element in this list

                new_air_exch = np.max([get_new_air_exch_from_target_CO2(CO2_models, target, time), 0.25])
                air_exch_list.append(new_air_exch)

                break
            elif c < min_CO2 and air_exch_list[-1] != 0.25:
                within_limit = False
                vent_transition_times[-1]=time
                vent_transition_times.append(time+0.000000001) # Need one more element in this list

                new_air_exch = np.max([air_exch_list[-1]/2, 0.25])
                air_exch_list.append(new_air_exch)

                break
            else:
                continue
        else:
            continue

    if within_limit:
        return air_exch_list, vent_transition_times
    elif run_count > len(times):
        raise RuntimeError("Failed to converge")
    else:
        run_count += 1
        return find_next_air_exch_by_co2(scenario, air_exch_list, vent_transition_times, max_CO2, min_CO2_fraction, target_CO2_fraction, max_ventilation_changes, change_ventilation_at, run_count)
    

def get_new_air_exch_from_target_CO2(
        CO2_models: list[models.CO2ConcentrationModel], 
        target: float,
        time: float,
    ) -> float:
    """
    Let the target be the wanted CO2 concentration limit.
    Find the corresponding air exchange per hour.
    """
    room_volumes = list(set([CO2_model.room.volume for CO2_model in CO2_models]))
    background_concentrations = list(set([CO2_model.min_background_concentration() for CO2_model in CO2_models]))
    if len(room_volumes) != 1:
        raise ValueError("CO2 models must have the same room")
    if len(background_concentrations) != 1:
        raise ValueError("CO2 models must have the same background concentration")
    background_concentration = background_concentrations[0]
    room_volume = room_volumes[0]

    abs_CO2_emission = 0
    for CO2_model in CO2_models:
        abs_CO2_emission += CO2_model.population.people_present(time)*CO2_model.normalization_factor()

    return np.mean(abs_CO2_emission / (room_volume * (target - background_concentration)))