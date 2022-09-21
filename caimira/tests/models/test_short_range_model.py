import typing

import numpy as np
import pytest

from caimira import models
import caimira.monte_carlo as mc_models
from caimira.apps.calculator.model_generator import build_expiration
from caimira.monte_carlo.data import short_range_expiration_distributions,\
        expiration_distributions, short_range_distances, activity_distributions

SAMPLE_SIZE = 250_000


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
    concentration_model = concentration_model.build_model(SAMPLE_SIZE)
    model = short_range_model.build_model(SAMPLE_SIZE)
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
    model = mc_models.ShortRangeModel(expiration=short_range_expiration_distributions['Breathing'],
                                    activity=models.Activity.types[activity],
                                    presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                                    distance=0.854).build_model(SAMPLE_SIZE)
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
        [10.5, 5.401601371244907],
        [10.6, 5.401601371244907],
        [11.0, 5.401601371244907],
        [12.0, 0.],
    ]
)
def test_short_range_concentration(time, expected_short_range_concentration,
                                   concentration_model, short_range_model):
    concentration_model = concentration_model.build_model(SAMPLE_SIZE)
    model = short_range_model.build_model(SAMPLE_SIZE)
    np.testing.assert_allclose(
        np.array(model.short_range_concentration(concentration_model, time)).mean(),
        expected_short_range_concentration, rtol=0.02
    )


def test_short_range_exposure_with_ndarray_mask():
    c_model = mc_models.ConcentrationModel(
        room=models.Room(volume=50, humidity=0.3),
        ventilation=models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                     air_exch=10_000_000,),
        infected=mc_models.InfectedPopulation(
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            virus=models.Virus.types['SARS_CoV_2_DELTA'],
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            expiration=expiration_distributions['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    sr_model = mc_models.ShortRangeModel(expiration=short_range_expiration_distributions['Shouting'],
                                         activity=models.Activity.types['Heavy exercise'],
                                         presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                                         distance=0.854)
    e_model = mc_models.ExposureModel(
        concentration_model = c_model,
        short_range = (sr_model,),
        exposed = mc_models.Population(
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            mask=models.Mask(η_inhale=np.array([0., 0.3, 0.5])),
            activity=models.Activity.types['Light activity'],
            host_immunity=0.,
        ),
        geographical_data = mc_models.Cases(),
    ).build_model(SAMPLE_SIZE)
    assert isinstance(e_model.deposited_exposure(), np.ndarray)
    assert len(e_model.deposited_exposure()) == 3
    np.testing.assert_allclose(e_model.deposited_exposure(),
            e_model.deposited_exposure()[0]*np.array([1., 0.7, 0.5]),
            rtol=1e-8)

