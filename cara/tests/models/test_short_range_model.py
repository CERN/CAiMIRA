import typing
from unicodedata import decimal

import numpy as np
import pytest

from cara import models
from cara.models import ShortRangeModel
from cara.apps.calculator.model_generator import build_expiration
from cara.monte_carlo.data import dilution_factor, short_range_expiration_distributions


@pytest.fixture
def concentration_model():
    return models.ConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.AirChange(
            active=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            air_exch=30.,
        ),
        infected=models.InfectedPopulation(
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            expiration=build_expiration({'Speaking': 0.33, 'Breathing': 0.67}).build_model(250000),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )


activities = ['Breathing', 'Speaking', 'Shouting']


@pytest.fixture
def presences():
    return [models.SpecificInterval((10.5, 11.0)),
        models.SpecificInterval((14.5, 15.0)),
        models.SpecificInterval((16.5, 17.5)),]


@pytest.fixture
def expirations():
    return [short_range_expiration_distributions[activity] for activity in activities]


@pytest.fixture
def dilutions():
    return dilution_factor(activities=activities,
                        distance=np.random.uniform(0.5, 1.5, 250000))


def test_short_range_model_ndarray(concentration_model, presences, expirations, dilutions):
    model = ShortRangeModel(presences, expirations, dilutions)
    assert isinstance(model._normed_concentration(concentration_model, 10.75), np.ndarray)
    assert isinstance(model.short_range_concentration(concentration_model, 14.75), np.ndarray)
    assert isinstance(model.normed_exposure_between_bounds(concentration_model, 16.6, 17.7), np.ndarray) 


@pytest.mark.parametrize(
    "time, expected_sr_normed_concentration, expected_concentration", [
        [10.75, 1.1670056689678455e-08, 11.67005668967846],
        # [14.75, 3.6414877020308386e-06, 3641.4877020308395],
        # [16.75, 1.973757599365769e-05, 19737.57599365769],
    ]
)
def test_short_range_model(time, expected_sr_normed_concentration, expected_concentration, 
                        concentration_model, presences, expirations, dilutions):
    
    model = ShortRangeModel(presences, expirations, dilutions)
    np.testing.assert_almost_equal(
        model._normed_concentration(concentration_model, time).mean(), expected_sr_normed_concentration, decimal=0
    )
    np.testing.assert_almost_equal(
        model.short_range_concentration(concentration_model, time).mean(), expected_concentration, decimal=0
    )