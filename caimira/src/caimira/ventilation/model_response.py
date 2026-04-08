import typing
import numpy as np

from caimira.calculator.models import models
from caimira.calculator.report.virus_report_data import interesting_times

import caimira.ventilation.get_models as get_models
from caimira.ventilation.scenarios import ScenarioVar

SAMPLE_SIZE: int = 250_000

def first_vent_transition_times(scenario: ScenarioVar) -> list[float]:
    _, infected, exposed = scenario
    model_start = min(infected.build_model(1).presence_interval().boundaries()[0][0], exposed.build_model(1).presence_interval().boundaries()[0][0])
    return [model_start, model_start+0.00001] # Short interval to initialize the ventilation, the ventilation rate of the last interval continues after the last time

def calculate_infection_probability(
        scenario: ScenarioVar,
        air_exch_values: list[float], 
        vent_transition_times: typing.Optional[list] = None,
        ) -> float:
    if not vent_transition_times:
        vent_transition_times = first_vent_transition_times(scenario)
    exposure_model = get_models.get_exposure_model(air_exch_values, vent_transition_times, scenario)
    exposure_model = exposure_model.build_model(SAMPLE_SIZE)
    pis = np.array(exposure_model.infection_probability()/100)
    pi = np.mean(pis)
    return pi

def calculate_deposited_exposure(
        scenario: ScenarioVar,
        air_exch_values: list[float], 
        vent_transition_times: typing.Optional[list] = None,
        ) -> float:
    if not vent_transition_times:
        vent_transition_times = first_vent_transition_times(scenario)
    exposure_model = get_models.get_exposure_model(air_exch_values, vent_transition_times, scenario).build_model(SAMPLE_SIZE)
    dose = np.mean(exposure_model.deposited_exposure())
    return dose

def model_concentration_results(
        scenario,
        air_exch_list: list[float], 
        vent_transition_times: typing.Optional[list] = None, 
        viral_values: bool = True, 
        CO2_values: bool = True,
        deterministic_CO2: bool = True
    ):
    if not vent_transition_times:
        vent_transition_times = first_vent_transition_times(scenario)
    exposure_model = get_models.get_exposure_model(air_exch_list, vent_transition_times, scenario).build_model(size=SAMPLE_SIZE)
    times = interesting_times(
        exposure_model, approx_n_pts=1000)
    
    all_concentrations = []
    if viral_values:
        ############# Peak viral concentration ############
        concentrations_viral = [
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

        ############# Inhaled dose ############
        deposited_exposure = exposure_model.deposited_exposure()
        mean = round(np.mean(deposited_exposure), 4)
        percentil_05 = round(np.quantile(deposited_exposure, 0.05), 0)
        percentil_95 = round(np.quantile(deposited_exposure, 0.95), 0)
        print('Inhaled dose: ', f'{mean} [{percentil_05} - {percentil_95}]')

        ############# Probability of Infection ############
        pis = exposure_model.infection_probability()/100
        mean_pi = round(np.mean(pis), 4)
        percentil_05 = round(np.quantile(pis, 0.05), 0)
        percentil_95 = round(np.quantile(pis, 0.95), 0)
        print('Probability of infection: ', f'{mean_pi} [{percentil_05} - {percentil_95}]')

        all_concentrations.append(concentrations_viral)

    ############# Peak CO2 concentration #############
    if CO2_values:
        if deterministic_CO2:
            CO2_model_infected, CO2_model_exposed = get_models.get_deterministic_CO2_models(exposure_model)
        else:
            CO2_model_infected, CO2_model_exposed = get_models.get_CO2_models(exposure_model)

        model_start = exposure_model.concentration_model.infected.presence_interval().boundaries()[0][0]
        model_end = exposure_model.concentration_model.infected.presence_interval().boundaries()[-1][1]

        if deterministic_CO2:
            concentrations_CO2_infected = [
                np.array(CO2_model_infected.concentration(float(time)))
                if model_start <= time <= model_end
                else CO2_model_exposed.min_background_concentration()
                for time in times
            ]
        else:
            concentrations_CO2_infected = [
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

        concentrations_CO2 = (
            np.add(
                concentrations_CO2_infected,
                concentration_CO2_exposed,
            )
            - CO2_model_exposed.min_background_concentration()
        )

        all_concentrations.append(concentrations_CO2)

    else: 
        all_concentrations.append(None)
    return exposure_model, times, all_concentrations