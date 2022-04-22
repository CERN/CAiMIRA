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
    assert isinstance(model._normed_jet_exposure_between_bounds(concentration_model, 10.75, 10.85), np.ndarray)
    assert isinstance(model._normed_interpolated_longrange_exposure_between_bounds(concentration_model, 10.75, 10.85), np.ndarray)
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


def test_extract_between_bounds_raise_on_wrong_order(short_range_model):
    model = short_range_model.build_model(1)
    with pytest.raises(ValueError, match='time1 must be less or equal to time2'):
        model.extract_between_bounds(11.,10.)


@pytest.mark.parametrize(
    "time1, time2, expected_start, expected_stop", [
        [10., 12., 10.5, 11.],
        [10., 10.7, 10.5, 10.7],
        [10., 10.45, 0., 0.],
        [11.01, 11.5, 0., 0.],
        [10.8, 10.9, 10.8, 10.9],
        [10.8, 11.5, 10.8, 11.],
        [10.5, 11., 10.5, 11.],
    ]
)
def test_extract_between_bounds(short_range_model, time1, time2,
                                expected_start, expected_stop):
    model = short_range_model.build_model(1)
    np.testing.assert_equal(
        model.extract_between_bounds(time1, time2),
        (expected_start, expected_stop),
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
        expected_short_range_concentration, rtol=0.02
    )

