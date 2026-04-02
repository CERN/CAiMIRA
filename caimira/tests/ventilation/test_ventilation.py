import numpy as np
import pytest
import numpy.testing as npt

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo.models as mc
from caimira.calculator.store.data_registry import DataRegistry

import caimira.ventilation.ventilation as vent
from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions
from caimira.calculator.validators.virus.virus_validator import build_expiration


data_registry=DataRegistry()


def shared_office_exposure_model(air_exch_values, vent_transition_times) -> models.ExposureModel:
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=mc.ConcentrationModel(
            data_registry=data_registry,
            room=mc.Room(volume=50, humidity=0.6, inside_temp=mc.PiecewiseConstant(
                (0, 24), (20+273.15, ))),
            ventilation=vent.custom_ventilation(air_exch_values=air_exch_values, transition_times=vent_transition_times),
            infected=mc.InfectedPopulation(
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
                        ),
            evaporation_factor=0.3,
        ),
        short_range=(),
        exposed=mc.Population(
                number=3,
                presence=mc.SpecificInterval(
                    present_times=((8.5, 12.5), (13.5, 17.5))),
                activity=activity_distributions(data_registry)['Seated'],
                mask=models.Mask.types['No mask'],
                host_immunity=0.,
            ),
        geographical_data=(),
    ).build_model(size=1)

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
    assert vent.carry_forward_air_change_times(air_exch_list, vent_transition_times, new_vent_transition_times) == expected_new_air_exch_list

cf = (1/4)*(1000/3600)*50
@pytest.mark.parametrize(
    "air_exch_list, vent_transition_times, expected_clean_air_delivery, expected_clean_air_delivery_transition_times",
    [
        [[0.25], [0, 0.001], ["inf", 0.25*cf, "inf", 0.25*cf], [0, 8.5, 12.5, 13.5, 17.5]],
         [[1], [0, 0.001], ["inf", 1*cf, "inf", 1*cf], [0, 8.5, 12.5, 13.5, 17.5]],
         [[0.25, 1], [0, 9, 9.1], ["inf", 0.25*cf, 1*cf, "inf", 1*cf], [0, 8.5, 9, 12.5, 13.5, 17.5]],
        [[0.25, 1, 9, 2, 0.5, 1], [0, 4, 9, 12.5, 13, 17, 17.000001], ["inf", "inf", 1*cf, 9*cf, "inf", "inf", 0.5*cf, 1*cf], [0, 4, 8.5, 9, 12.5, 13, 13.5, 17, 17.5]],
        [[0.25, 1], [0, 18, 18.0001], ["inf", 0.25*cf, "inf", 0.25*cf, "inf"], [0, 8.5, 12.5, 13.5, 17.5, 18]],
    ]
)
def test_clean_air_per_sec_per_pers_conversion(air_exch_list, vent_transition_times, expected_clean_air_delivery, expected_clean_air_delivery_transition_times):
    exposure_model = shared_office_exposure_model(air_exch_list, vent_transition_times)
    clean_air_delivery, clean_air_delivery_transition_times = vent.clean_air_per_sec_per_pers(air_exch_list, vent_transition_times, exposure_model)
    assert clean_air_delivery_transition_times == expected_clean_air_delivery_transition_times
    assert len(clean_air_delivery) == len(clean_air_delivery_transition_times) -1
    assert [
            pytest.approx(e) if isinstance(e, float) else e
            for e in clean_air_delivery
        ] == expected_clean_air_delivery