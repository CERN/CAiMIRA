import numpy as np
import dataclasses
import pytest
import numpy.testing as npt

from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry

import caimira.ventilation.deterministic_emitters as de
import caimira.ventilation.get_models as get_models
import caimira.ventilation.find_requirements as find_requirements

data_registry = DataRegistry()

@pytest.fixture
def CO2_emitters():
    return [
        de.DeterministicPopulation(
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            activity=de.deterministic_activity_distributions(data_registry)["Seated"],
        ),
        de.DeterministicPopulation(
            number=10,
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            activity=de.deterministic_activity_distributions(data_registry)["Seated"],
        ),
        de.DeterministicPopulation(
            number=2,
            presence=models.SpecificInterval(present_times=((8., 12.5), )),
            activity=de.deterministic_activity_distributions(data_registry)["Seated"],
        ),
        ]

@pytest.fixture
def deterministic_CO2_models(CO2_emitters):
    return [
        de.DeterministicCO2ConcentrationModel(
            data_registry=data_registry,
            room=models.Room(volume=50, humidity=0.6, inside_temp=models.PiecewiseConstant(
            (0, 24), (20+273.15, ))),
            ventilation=get_models.custom_ventilation(air_exch_values=[0.25]),
            CO2_emitters=CO2_emitter,
        ) 
        for CO2_emitter in CO2_emitters]

@pytest.mark.parametrize(
    "target_CO2_lim, time, expected_air_exch, expected_CO2_lim",
    [
        [1440.44, 9, 0.2*4.2*0.5057557584400184, 1440.44],
        [441.44, 9, 200*4.2*0.5057557584400184, 441.44],
        [840.44, 17, 0.5*4.2*0.5057557584400184, 840.44],
        [10000, 13, 0, 440.44],
        [100, 13, 0, 440.44],
    ]
)
def test_get_new_air_exch_from_target_CO2_single_model(target_CO2_lim, time, expected_air_exch, deterministic_CO2_models, expected_CO2_lim):
    deterministic_CO2_model = deterministic_CO2_models[0]
    air_exch_result = find_requirements.get_new_air_exch_from_target_CO2([deterministic_CO2_model], target_CO2_lim, time)

    new_air_exch = np.max([air_exch_result, 0.25])
    
    adjusted_deterministic_CO2_model = dataclasses.replace(
            deterministic_CO2_model, **{
                'ventilation': get_models.custom_ventilation(air_exch_values=[0.25, new_air_exch], transition_times=[0,0.001,time])
            }
        )
            
    conc_limit_result = adjusted_deterministic_CO2_model._normed_concentration_limit(time)*adjusted_deterministic_CO2_model.normalization_factor()

    npt.assert_almost_equal(air_exch_result, expected_air_exch)
    npt.assert_almost_equal(conc_limit_result, expected_CO2_lim)

@pytest.mark.parametrize(
    "target_CO2_lim, time, expected_air_exch, expected_CO2_lim",
    [
        [1440.44, 9, 13*0.2*4.2*0.5057557584400184, 1440.44],
        [441.44, 9, 13*200*4.2*0.5057557584400184, 441.44],
        [840.44, 17, 11*0.5*4.2*0.5057557584400184, 840.44],
        [10000, 13, 0, 440.44],
        [100, 13, 0, 440.44],
    ]
)
def test_get_new_air_exch_from_target_CO2_multiple_models(target_CO2_lim, time, expected_air_exch, deterministic_CO2_models, expected_CO2_lim):
    air_exch_result = find_requirements.get_new_air_exch_from_target_CO2(deterministic_CO2_models, target_CO2_lim, time)

    new_air_exch = np.max([air_exch_result, 0.25])
    
    adjusted_deterministic_CO2_models = [dataclasses.replace(
            deterministic_CO2_model, **{
                'ventilation': get_models.custom_ventilation(air_exch_values=[0.25, new_air_exch], transition_times=[0,0.001,time])
            }
        ) for deterministic_CO2_model in deterministic_CO2_models]
            
    conc_limit_result = np.sum([
        adjusted_deterministic_CO2_model._normed_concentration_limit(time)*adjusted_deterministic_CO2_model.normalization_factor() 
        for adjusted_deterministic_CO2_model in adjusted_deterministic_CO2_models]) \
            - 2*adjusted_deterministic_CO2_models[0].min_background_concentration()
    
    npt.assert_almost_equal(air_exch_result, expected_air_exch)
    npt.assert_almost_equal(conc_limit_result, expected_CO2_lim)