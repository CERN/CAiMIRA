import typing

from caimira.calculator.models import models, dataclass_utils
from caimira.calculator.store.data_registry import DataRegistry
import caimira.calculator.models.monte_carlo.models as mc

import caimira.ventilation.deterministic_emitters as de
from caimira.ventilation.scenarios import ScenarioVar

data_registry = DataRegistry()

def custom_ventilation(
        air_exch_values: typing.Union[list, float], 
        transition_times: list = [0,0.001]
        ) -> models.MultipleVentilation:
    if isinstance(air_exch_values, float) or isinstance(air_exch_values, int):
        air_exch_values = (air_exch_values,)
    else:
        if len(air_exch_values) == 1:
            air_exch_values = (air_exch_values[0],)
        else:
            air_exch_values = tuple(air_exch_values)
    transition_times = tuple(transition_times)
    return models.CustomVentilation(
                        ventilation_value=models.PiecewiseConstant(
                            transition_times=transition_times,
                            values=air_exch_values,
                            )
                    )

def get_exposure_model(
        air_exch_values: typing.Union[list, float], 
        vent_transition_times: list,
        scenario: ScenarioVar,
        ) -> models.ExposureModel:
    if len(scenario) < 3:
        print("ERROR: scenario must be (room, infected, exposed).")
    room, infected, exposed = scenario
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=mc.ConcentrationModel(
            data_registry=data_registry,
            room=room,
            ventilation=custom_ventilation(air_exch_values=air_exch_values, transition_times=vent_transition_times),
            infected=infected,
            evaporation_factor=0.3,
        ),
        short_range=(),
        exposed=exposed,
        geographical_data=(),
    )

def simple_to_deterministic_population(simple_population: models.SimplePopulation) -> de.DeterministicPopulation:
    activity_type = simple_population.activity.name
    return de.DeterministicPopulation(
        number=simple_population.number,
        presence=simple_population.presence,
        activity=de.deterministic_activity_distributions(data_registry)[activity_type],
    )


def get_deterministic_CO2_models(
        exposure_model: models.ExposureModel
    ) -> typing.Tuple[de.DeterministicCO2ConcentrationModel]:
    CO2_model_infected = de.DeterministicCO2ConcentrationModel(
        data_registry=data_registry,
        room=exposure_model.concentration_model.room,
        ventilation=exposure_model.concentration_model.ventilation,
        CO2_emitters=simple_to_deterministic_population(exposure_model.concentration_model.infected),
    )

    CO2_model_exposed = de.DeterministicCO2ConcentrationModel(
        data_registry=data_registry,
        room=exposure_model.concentration_model.room,
        ventilation=exposure_model.concentration_model.ventilation,
        CO2_emitters=simple_to_deterministic_population(exposure_model.exposed),
    )

    return CO2_model_infected, CO2_model_exposed

def get_CO2_models(
        exposure_model: models.ExposureModel
    ) -> typing.Tuple[models.CO2ConcentrationModel]:
    # For the CO2 concentration profile we assume that the breaks for the infected and the exposed occur at the same time(s).
    CO2_model_infected: models.CO2ConcentrationModel = models.CO2ConcentrationModel(
        data_registry=data_registry,
        room=exposure_model.concentration_model.room,
        ventilation=exposure_model.concentration_model.ventilation,
        CO2_emitters=exposure_model.concentration_model.infected,
    )

    dynamic_exposed: models.Population = exposure_model.exposed
    CO2_model_exposed: models.CO2ConcentrationModel = dataclass_utils.nested_replace(CO2_model_infected, {
        'CO2_emitters.number': dynamic_exposed.number,
        'CO2_emitters.presence': dynamic_exposed.presence,
        'CO2_emitters.activity': dynamic_exposed.activity,
    })

    return CO2_model_infected, CO2_model_exposed