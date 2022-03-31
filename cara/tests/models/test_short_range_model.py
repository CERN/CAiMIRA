import typing

import numpy as np
import pytest

from cara import models
import cara.monte_carlo as mc_models
from cara.apps.calculator.model_generator import build_expiration
from cara.monte_carlo.data import short_range_expiration_distributions, short_range_distances, activity_distributions

# TODO: seed better the random number generators
np.random.seed(2000)

@pytest.fixture
def concentration_model() -> mc_models.ConcentrationModel:
    return mc_models.ConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.AirChange(
            active=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            air_exch=10_000_000.,
        ),
        infected=mc_models.InfectedPopulation(
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            expiration=build_expiration({'Speaking': 0.33, 'Breathing': 0.67}),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )


@pytest.fixture
def short_range_model():
    return mc_models.ShortRangeModel(expiration=short_range_expiration_distributions['Breathing'],
                                     activity=activity_distributions['Seated'],
                                     presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                                     distance=short_range_distances)


def test_short_range_model_ndarray(concentration_model, short_range_model):
    concentration_model = concentration_model.build_model(250_000)
    model = short_range_model.build_model(250_000)
    assert isinstance(model._normed_concentration(concentration_model, 10.75), np.ndarray)
    assert isinstance(model.short_range_concentration(concentration_model, 10.75), np.ndarray)
    assert isinstance(model.normed_exposure_between_bounds(concentration_model, 10.75, 10.85), np.ndarray) 
    assert isinstance(model.short_range_concentration(concentration_model, 14.0), float)


@pytest.mark.parametrize(
    "activity, expected_dilution", [
        ["Seated", 176.04075727780327],
        ["Standing", 157.12965288170005],
        ["Light activity", 69.06672998536413],
        ["Moderate activity", 47.165817446310115],
        ["Heavy exercise", 23.759992220217875],
    ]
)
def test_dilution_factor(activity, expected_dilution):
    model = models.ShortRangeModel(expiration="Breathing",
                                    activity=models.Activity.types[activity],
                                    presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                                    distance=0.854)
    assert isinstance(model.dilution_factor(), np.ndarray)
    np.testing.assert_almost_equal(
        model.dilution_factor(), expected_dilution, decimal=10
    )


@pytest.mark.parametrize(
    "time, expected_short_range_concentration", [
        [8.5, 0.],
        [10.5, 15.24806213],
        [10.6, 15.24806213],
        [11.0, 15.24806213],
        [12.0, 0.],
    ]
)
def test_short_range_concentration(time, expected_short_range_concentration, concentration_model, short_range_model):
    concentration_model = concentration_model.build_model(250_000)
    model = short_range_model.build_model(250_000)
    np.testing.assert_allclose(
        np.array(model.short_range_concentration(concentration_model, time)).mean(),
        expected_short_range_concentration, rtol=0.01
    )

@pytest.mark.parametrize(
    "start, stop, expected_exposure", [
        [8.5, 12.5, 7.875963317294013e-09],
        [10.5, 11.0, 7.875963317294013e-09],
        [10.4, 11.1, 7.875963317294013e-09],
        [10.5, 11.1, 7.875963317294013e-09],
        [10.6, 11.1, 7.66539809488759e-09],
        [10.4, 10.9, 7.66539809488759e-09],
        
    ]
)
def test_normed_exposure_between_bounds(start, stop, expected_exposure, concentration_model, short_range_model):
    concentration_model = concentration_model.build_model(250_000)
    model = short_range_model.build_model(250_000)
    np.testing.assert_almost_equal(
        model.normed_exposure_between_bounds(concentration_model, start, stop).mean(), expected_exposure
    )
