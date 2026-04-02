import typing
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq
import bisect

from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry

from caimira.calculator.report.virus_report_data import interesting_times

import caimira.ventilation.scenarios as scenarios
from caimira.ventilation.get_models import *


SAMPLE_SIZE: int = 250_000
data_registry = DataRegistry()


def calculate_infection_probability(
        air_exch_values: typing.Union[MutableTuple, float] = (0.25,), 
        vent_transition_times: MutableTuple = (0,0.001),
        scenario: ScenarioVar = scenarios.shared_office()
        ) -> float:
    exposure_model = get_exposure_model(air_exch_values, vent_transition_times, scenario)
    exposure_model = exposure_model.build_model(SAMPLE_SIZE)
    pis: models._VectorisedFloat = np.array(exposure_model.infection_probability()/100)
    pi = np.mean(pis)
    return pi

def calculate_deposited_exposure(
        air_exch_values: typing.Union[MutableTuple, float] = (0.25,), 
        vent_transition_times: MutableTuple = (0,0.001),
        scenario: ScenarioVar = scenarios.shared_office()
        ) -> float:
    exposure_model = get_exposure_model(air_exch_values, vent_transition_times, scenario)
    exposure_model = exposure_model.build_model(SAMPLE_SIZE)
    dose = np.mean(exposure_model.deposited_exposure())
    return dose

def carry_forward_air_change_times(air_change_per_hour_list, vent_transition_times, clean_air_delivery_transition_times):
    """
    Re-specify the air exchange value at intervals between the time points in vent_transition_times
    for the finer intervals between the time points in clean_air_delivery_transition_times.
    Note that vent_transition_times is a subset of clean_air_delivery_transition_times and both lists are sorted.
    """
    extended_air_change_per_hour_list = []
    for time in clean_air_delivery_transition_times[:-1]:
        i = bisect.bisect_right(vent_transition_times, time) - 1
        if i >= 0 and i < len(air_change_per_hour_list):
            extended_air_change_per_hour_list.append(air_change_per_hour_list[i])
        elif i == len(air_change_per_hour_list):
            extended_air_change_per_hour_list.append(air_change_per_hour_list[-1])
    return extended_air_change_per_hour_list


def clean_air_per_sec_per_pers(
        air_change_per_hour_list: typing.Union[MutableTuple, float], 
        vent_transition_times: MutableTuple, 
        exposure_model: models.ExposureModel
    ) -> tuple[list[float], list[float]]:
    """
    Convert from air exchange per hour to liter per second per person.
    """
    room=exposure_model.concentration_model.room

    clean_air_delivery_transition_times = sorted(
        set(exposure_model.population_state_change_times()) |
        set(vent_transition_times[:-1]) # Remove the last transition time
    )

    longer_air_change_per_hour_list = np.array(carry_forward_air_change_times(air_change_per_hour_list, vent_transition_times, clean_air_delivery_transition_times))

    clean_air_delivery = []
    for air_exch, time in zip(longer_air_change_per_hour_list, clean_air_delivery_transition_times[1:]):
        n_occupants = (
            exposure_model.exposed.people_present(time) 
            + exposure_model.concentration_model.infected.people_present(time)
        )

        if n_occupants == 0:
            clean_air_delivery.append("inf")

        else:
            Q_ach = 1000 / 3600 * air_exch * room.volume # Volumetric flow rate in L s^{−1}
            clean_air_delivery.append(Q_ach / n_occupants)

    return clean_air_delivery, clean_air_delivery_transition_times

def find_constant_air_exch(
    lim_probability_infection: float,
    scenario: ScenarioVar = scenarios.shared_office(),
    lo=0,
    hi=60,
    tol=1e-2,
) -> tuple[float, float]:
    
    f = lambda air_exch: calculate_infection_probability(air_exch_values=air_exch, scenario=scenario)
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

def plot_probabilities(
    lim_probability_infection_list: list[float], 
    scenario: ScenarioVar = scenarios.shared_office(), 
    air_exch_list: list[float] = list(range(0, 60, 2))
    ):

    infection_probability = [calculate_infection_probability(air_exch_values=air_exch, scenario=scenario) for air_exch in air_exch_list]
    dose = [calculate_deposited_exposure(air_exch_values=air_exch, scenario=scenario) for air_exch in air_exch_list]

    print(f"0 ACH   =>   P(I) = {calculate_infection_probability(air_exch_values=0, scenario=scenario)*100:.2f}%, Dose = {calculate_deposited_exposure(air_exch_values=0, scenario=scenario):.2f}")

    fig, ax1 = plt.subplots(1, 1, figsize = (6,4))
    #fig, (ax1, ax2) = plt.subplots(1, 2, figsize = (12,5))

    ax1.plot(
        air_exch_list,
        infection_probability,
        linewidth=2,
        color="tab:blue",
        label="Infection probability P(I)"
    )
    ax1.set_ylabel('Infection probability P(I)', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # ax2.plot(
    #     air_exch_list,
    #     dose,
    #     linewidth=2,
    #     color="tab:red",
    #     label="Dose"
    # )
    # ax2.set_ylabel('Viral dose', color='tab:red')
    # ax2.tick_params(axis='y', labelcolor='tab:red')

    ax3 = ax1.twinx()

    ax3.plot(
        air_exch_list,
        dose,
        linewidth=2,
        color="tab:red",
        label="Dose",
        linestyle="--"
    )
    ax3.set_ylabel('Viral dose', color='tab:red')
    ax3.tick_params(axis='y', labelcolor='tab:red')

    for lim_probability_infection in lim_probability_infection_list:
        if lim_probability_infection > 0:
            lim_air_exch, probability = find_constant_air_exch(lim_probability_infection, scenario, hi=air_exch_list[-1])
            dose = calculate_deposited_exposure(air_exch_values=lim_air_exch, scenario=scenario)

            ax1.plot(
                lim_air_exch,
                probability,
                "o",
                color="k",
                markersize=8,
            )

            ax1.annotate(
                #f"P(I) limit: {lim*100}% \n({lim_air_exch:.1f}, {probability:.2%})",
                f"({lim_air_exch:.1f}, {probability:.1%})",
                xy=(lim_air_exch, probability),
                xytext=(5, 5),           
                textcoords="offset points",
                fontsize=10,
                color="k"
            )

            # ax2.plot(
            #     lim_air_exch,
            #     dose,
            #     "o",
            #     color="k",
            #     markersize=8,
            # )

            # ax2.annotate(
            #     f"({lim_air_exch:.1f}, {dose:.1f})",
            #     xy=(lim_air_exch, dose),
            #     xytext=(5, 5),           
            #     textcoords="offset points",
            #     fontsize=10,
            #     color="k"
            # )

    ax1.set_xlabel("Air Changes per Hour", fontsize=12)
    #ax2.set_xlabel("Air Changes per Hour", fontsize=12)
    ax1.grid(True, linestyle="--", alpha=0.6)
    #ax2.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()


def model_concentration_results(
        air_exch_list: typing.Union[MutableTuple, float], 
        vent_transition_times: MutableTuple = (0,0.001), 
        scenario: ScenarioVar = scenarios.shared_office(), 
        viral_values: bool = True, 
        CO2_values: bool = True,
        deterministic_CO2: bool = True
    ):
    
    exposure_model = get_exposure_model(air_exch_list, vent_transition_times, scenario).build_model(size=SAMPLE_SIZE)
    times: models._VectorisedFloat = interesting_times(
        exposure_model, approx_n_pts=1000)
    
    all_concentrations = []
    if viral_values:
        ############# Peak viral concentration ############
        concentrations_viral: models._VectorisedFloat = [
            np.array(exposure_model.concentration(float(time)))
            for time in times
        ]

        peak_concentration_index: int = np.argmax(
            [c.mean() for c in concentrations_viral])

        mean = round(np.mean(concentrations_viral[peak_concentration_index]), 0)
        percentil_05 = round(np.quantile(
            concentrations_viral[peak_concentration_index], 0.05), 0)
        percentil_95 = round(np.quantile(
            concentrations_viral[peak_concentration_index], 0.95), 0)
        # print('Peak concentration: ', f'{mean} [{percentil_05} - {percentil_95}]')

        ############ Plot the results #############
        # plt.plot(times, [np.mean(c) for c in concentrations_viral])
        # plt.xlabel('Time of day')
        # plt.ylabel('concentration (IRP / m3)')
        # plt.show()

        ############# Inhaled dose ############
        deposited_exposure: models._VectorisedFloat = exposure_model.deposited_exposure()
        mean = round(np.mean(deposited_exposure), 4)
        percentil_05 = round(np.quantile(deposited_exposure, 0.05), 0)
        percentil_95 = round(np.quantile(deposited_exposure, 0.95), 0)
        print('Inhaled dose: ', f'{mean} [{percentil_05} - {percentil_95}]')

        ############# Probability of Infection ############
        pis: models._VectorisedFloat = exposure_model.infection_probability()/100
        mean_pi = round(np.mean(pis), 4)
        percentil_05 = round(np.quantile(pis, 0.05), 0)
        percentil_95 = round(np.quantile(pis, 0.95), 0)
        print('Probability of infection: ', f'{mean_pi} [{percentil_05} - {percentil_95}]')

        all_concentrations.append(concentrations_viral)

    ############# Peak CO2 concentration #############
    if CO2_values:
        if deterministic_CO2:
            CO2_model_infected, CO2_model_exposed = get_deterministic_CO2_models(exposure_model)
        else:
            CO2_model_infected, CO2_model_exposed = get_CO2_models(exposure_model)

        model_start = exposure_model.concentration_model.infected.presence_interval().boundaries()[0][0]
        model_end = exposure_model.concentration_model.infected.presence_interval().boundaries()[-1][1]

        if deterministic_CO2:
            concentrations_CO2_infected: models._VectorisedFloat = [
                np.array(CO2_model_infected.concentration(float(time)))
                if model_start <= time <= model_end
                else CO2_model_exposed.min_background_concentration()
                for time in times
            ]
        else:
            concentrations_CO2_infected: models._VectorisedFloat = [
                np.array(CO2_model_infected.concentration(float(time)))
                if model_start <= time <= model_end
                else np.ones(SAMPLE_SIZE)*CO2_model_exposed.min_background_concentration()
                for time in times
            ]
        # Sum contributions from both populations, and the background.
        model_start = exposure_model.exposed.presence_interval().boundaries()[0][0]
        model_end = exposure_model.exposed.presence_interval().boundaries()[-1][1]

        if deterministic_CO2:
            concentration_CO2_exposed = [ #### TODO: fix so that the profile after model_end is correct
                        np.array(CO2_model_exposed.concentration(float(time)))
                        if model_start <= time <= model_end
                        else CO2_model_exposed.min_background_concentration()
                        for time in times
                    ]
        else:
            concentration_CO2_exposed = [ #### TODO: fix so that the profile after model_end is correct
                        np.array(CO2_model_exposed.concentration(float(time)))
                        if model_start <= time <= model_end
                        else np.ones(SAMPLE_SIZE)*CO2_model_exposed.min_background_concentration()
                        for time in times
                    ]

        concentrations_CO2: models._VectorisedFloat = (
            np.add(
                concentrations_CO2_infected,
                concentration_CO2_exposed,
            )
            - CO2_model_exposed.min_background_concentration()
        )

        all_concentrations.append(concentrations_CO2)

    else: 
        all_concentrations.append([])
    #return times, air_exch, probability, concentrations_viral
    return exposure_model, times, all_concentrations

def plot_model_concentration_results(
        air_exch_list: typing.Union[MutableTuple, float], 
        vent_transition_times: MutableTuple = (0,0.001), 
        scenario: ScenarioVar = scenarios.shared_office(), 
        viral_values: bool = True, 
        CO2_values: bool = True,
        deterministic_CO2: bool = True
    ):
    ax1_ymax = 0
    ax2_ymax = 0
    exposure_model, times, concentrations = model_concentration_results(air_exch_list, vent_transition_times, scenario, viral_values, CO2_values, deterministic_CO2)
    concentrations_viral, concentrations_CO2 = concentrations
    ############ Combined plot: Viral concentration + CO2 ############
    fig, ax1 = plt.subplots(figsize = (6,4))

    # ===== Viral concentration (LEFT AXIS) =====
    mean_viral = [np.mean(c) for c in concentrations_viral]
    ax1.plot(
        times,
        mean_viral,
        color='tab:blue',
        label='Viral concentration'
    )
    ax1.set_xlabel('Time of day')
    ax1.set_ylabel('Viral concentration (IRP / m³)', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    if max(mean_viral)*1.1 > ax1_ymax:
        ax1_ymax = max(mean_viral)*1.1
    ax1.set_ylim([0,ax1_ymax])

    # Optional uncertainty band
    # ax1.fill_between(
    #     times,
    #     [np.quantile(c, 0.05) for c in concentrations_viral],
    #     [np.quantile(c, 0.95) for c in concentrations_viral],
    #     color='tab:blue',
    #     alpha=0.2
    # )
    if isinstance(air_exch_list, list):
        clean_air_delivery, _ = clean_air_per_sec_per_pers(air_exch_list, vent_transition_times, exposure_model)
        print(f"Air changes per hour: Mean: {np.mean(air_exch_list)}, All values: {[round(air_exch, 2) for air_exch in air_exch_list]}")
    else:
        clean_air_delivery, _ = clean_air_per_sec_per_pers([air_exch_list], vent_transition_times, exposure_model)
        print(f"Air changes per hour: {air_exch_list:.2f}")
    print(f"Clean-Air Delivery (L/s/person): Mean: {np.mean([[cld for cld in clean_air_delivery if isinstance(cld, float)]])}, All values: {[round(cld, 2) if type(cld)==float else cld for cld in clean_air_delivery]}")

    # ===== CO2 concentration (RIGHT AXIS) =====
    if CO2_values:
        ax2 = ax1.twinx()
        if isinstance(concentrations_CO2[0], float):
            mean_CO2 = concentrations_CO2
        else:
            mean_CO2 = [np.mean(c) for c in concentrations_CO2]
        print(f"Max CO2: {np.max(mean_CO2):.2f}")
        ax2.plot(
            times,
            mean_CO2,
            color='tab:red',
            label='CO₂ concentration'
        )
        ax2.set_ylabel('CO₂ concentration (ppm)', color='tab:red')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        if deterministic_CO2:
            new_ax2_ymax = max(concentrations_CO2)*1.1
            if new_ax2_ymax > ax2_ymax:
                ax2_ymax = new_ax2_ymax*1.1
            ax2.set_ylim([440,ax2_ymax])
        else:
            new_ax2_ymax = max([np.quantile(c, 0.95) for c in concentrations_CO2])*1.1
            if new_ax2_ymax > ax2_ymax:
                ax2_ymax = new_ax2_ymax*1.1
            ax2.set_ylim([440,ax2_ymax])

            ax2.fill_between(
                times,
                [np.quantile(c, 0.05) for c in concentrations_CO2],
                [np.quantile(c, 0.95) for c in concentrations_CO2],
                color='tab:red',
                alpha=0.2
            )

        # ===== Combined legend =====
        lines = ax1.get_lines() + ax2.get_lines()
        labels = [line.get_label() for line in lines]
        ax1.legend(lines, labels, loc='best')

    plt.tight_layout()
    plt.show()

def find_next_air_exch_by_co2(
    air_exch_list: typing.Union[MutableTuple, float], 
    vent_transition_times: MutableTuple, 
    max_CO2: float,
    min_CO2_fraction: float = 0.95,
    target_CO2_fraction: float = 0.95,
    scenario: ScenarioVar = scenarios.shared_office(),
    max_ventilation_changes: typing.Optional[int] = None,
    change_ventilation_at: typing.Optional[list[float]] = None,
    ):
    #TODO? differentiate between when/how often ventilation may be increased and decreased?
    if max_ventilation_changes and change_ventilation_at:
        print(f"May satisfy both max_ventilation_changes and change_ventilation_at, using change_ventilation_at")
    
    if min_CO2_fraction < 0 or min_CO2_fraction > 1:
        raise ValueError(f"target_fraction must be in range [0, 1], got {min_CO2_fraction}")
    exposure_model, times, concentrations = model_concentration_results(air_exch_list, vent_transition_times, scenario, viral_values=False)
    CO2_models: typing.Tuple[models.CO2ConcentrationModel] = get_CO2_models(exposure_model)

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
        if max_ventilation_changes:
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
    else:
        return find_next_air_exch_by_co2(air_exch_list, vent_transition_times, max_CO2, min_CO2_fraction, target_CO2_fraction, scenario, max_ventilation_changes, change_ventilation_at)
    

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