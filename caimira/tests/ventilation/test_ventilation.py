import numpy as np
import pytest
import numpy.testing as npt

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo.models as mc
from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions
from caimira.calculator.validators.virus.virus_validator import build_expiration
from caimira.calculator.store.data_registry import DataRegistry

import caimira.ventilation.get_models as get_models
import caimira.ventilation.find_requirements as find_requirements


data_registry=DataRegistry()


def shared_office_scenario() -> models.ExposureModel:
    room=mc.Room(volume=50, humidity=0.6, inside_temp=mc.PiecewiseConstant( # type: ignore
                (0, 24), (20+273.15, )))
    infected=mc.InfectedPopulation( # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((8.5, 12.5), (13.5, 17.5))),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types['No mask'],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Speaking': 1/3, 'Breathing': 2/3}),
                            host_immunity=0.,
                        )
    exposed=mc.Population( # type: ignore
                number=3,
                presence=models.SpecificInterval(
                    present_times=((8.5, 12.5), (13.5, 17.5))),
                activity=activity_distributions(data_registry)['Seated'],
                mask=models.Mask.types['No mask'],
                host_immunity=0.,
            )
    return room, infected, exposed

@pytest.mark.parametrize(
    "vent_transition_times, air_exch_list, new_vent_transition_times, expected_new_air_exch_list",
    [
        [[0,    2], [0.25],
         [0, 1, 2], [0.25, 0.25]],
        [[0,    2, 4, 8, 10,     12, 15],         [1,    2, 3, 7, 9,    1], 
         [0, 1, 2, 4, 8, 10, 11, 12, 15, 20, 22], [1, 1, 2, 3, 7, 9, 9, 1, 1, 1]],
    ]
)
def test_carry_forward_air_change_times(vent_transition_times, air_exch_list, new_vent_transition_times, expected_new_air_exch_list):
    assert find_requirements.carry_forward_air_change_times(air_exch_list, vent_transition_times, new_vent_transition_times) == expected_new_air_exch_list

@pytest.mark.parametrize(
    "air_exch_list",
    [
        [0.25],
         [1],
         [0.25, 1],
        [0.25, 1, 9, 2, 0.5, 1],
        [0.25, 1],
    ]
)
def test_conversion(air_exch_list):
    expected_clean_air_delivery = [(1/4)*(1000/3600)*50*air_exch for air_exch in air_exch_list]
    clean_air_delivery = find_requirements.ACH_to_CADR(air_exch_list, shared_office_scenario())
    air_exch_list_result = find_requirements.CADR_to_ACH(clean_air_delivery, shared_office_scenario())
    npt.assert_allclose(clean_air_delivery, expected_clean_air_delivery)
    npt.assert_allclose(air_exch_list_result, air_exch_list)