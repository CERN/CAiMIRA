import typing

import numpy as np
import pytest

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo as mc_models
from caimira.calculator.validators.virus.virus_validator import build_expiration
from caimira.calculator.models.monte_carlo.data import short_range_expiration_distributions,\
        expiration_distributions, short_range_distances, activity_distributions

SAMPLE_SIZE = 250_000

@pytest.fixture
def short_range_model(data_registry):
    return mc_models.ShortRangeModel(
        data_registry=data_registry,
        exposed_identifier="exposed_1",
        activity=activity_distributions(data_registry)['Seated'], # NOTE: not within infected.activity. In the future, this initialization might trigger an error.
        expiration=short_range_expiration_distributions(data_registry)['Breathing'],
        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
        distance=short_range_distances(data_registry),
        )

@pytest.fixture
def concentration_model(data_registry, short_range_model) -> mc_models.ConcentrationModel:
    return mc_models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=75),
        ventilation=models.AirChange(
            active=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            air_exch=10_000_000.,
        ),
        infected=mc_models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            expiration=build_expiration(data_registry, {'Speaking': 0.33, 'Breathing': 0.67}),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
        short_range=(short_range_model,),
    )


@pytest.fixture
def exposure_model(data_registry, concentration_model):
    return mc_models.ExposureModel(
        data_registry=data_registry,
        concentration_model=(concentration_model,),
        exposed = mc_models.Population(
            identifier="exposed_1",
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            host_immunity=0.,
        ),
        geographical_data = models.Cases(),
        exposed_to_short_range = 1,
    )

@pytest.mark.parametrize(
    "make_args",
    [
        pytest.param(
            lambda data_registry: (activity_distributions(data_registry)["Seated"], 0.8),
            id="random-activity_fixed-distance",
        ),
        pytest.param(
            lambda data_registry: (models.Activity.types["Seated"], short_range_distances(data_registry)),
            id="fixed-activity_random-distance",
        ),
    ],
)
def test_short_range_distance_dimentions(data_registry, make_args):
    """
    Tests that the dilution factor can be computed for `ShortRangeModel` instances with:

    - an activity whose exhalation rate is sampled via Monte Carlo and a fixed distance; and
    - an activity with a fixed exhalation rate and a distance sampled via Monte Carlo.

    This test is motivated by the transition point (`xstar`) for the dilution factor being computed from
    `activity.exhalation_rate`. Dimensionality errors may occur when comparing the distance and `xstar`
    (as in `ShortRangeModel.dilution_factor`) if one is a Monte Carlo random variable and the other is
    a fixed value. This test checks that such errors are avoided.
    """
    activity, distance = make_args(data_registry)
    sr_model = mc_models.ShortRangeModel(
        data_registry=data_registry,
        exposed_identifier="",
        activity=activity,
        expiration=short_range_expiration_distributions(data_registry)["Speaking"],
        presence=models.SpecificInterval(present_times=((10.75, 11.0),)),
        distance=distance,
    ).build_model(2)
    assert len(sr_model.dilution_factor()) == 2


def test_short_range_model_ndarray(concentration_model, short_range_model):
    concentration_model = concentration_model.build_model(SAMPLE_SIZE)
    model = short_range_model.build_model(SAMPLE_SIZE)
    assert isinstance(model.dilution_factor(), np.ndarray)
    assert isinstance(model._normed_jet_origin_concentration(), np.ndarray)
    assert isinstance(model._normed_diluted_jet_concentration(), np.ndarray)


@pytest.mark.parametrize(
    "activity, expected_dilution", [
        ["Seated", 85.73002264],
        ["Standing", 76.19303543],
        ["Light activity", 32.45103906],
        ["Moderate activity", 21.79749405],
        ["Heavy exercise", 16.372],
    ]
)
def test_dilution_factor(data_registry, activity, expected_dilution):
    model = mc_models.ShortRangeModel(
        data_registry=data_registry,
        exposed_identifier="",
        activity=models.Activity.types[activity],
        expiration=short_range_expiration_distributions(data_registry)['Breathing'],
        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
        distance=0.854
    ).build_model(SAMPLE_SIZE)
    assert isinstance(model.dilution_factor(), np.ndarray)
    np.testing.assert_almost_equal(
        model.dilution_factor(), expected_dilution
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
    "time, expected_short_range_concentration_component", [
        [8.5, 0.],
        [10.5, 5.6333025],
        [10.6, 5.6333025],
        [11.0, 5.6333025],
        [12.0, 0.],
    ]
)
def test_short_range_concentration(time, expected_short_range_concentration_component, exposure_model):
    exposure_model = exposure_model.build_model(SAMPLE_SIZE)
    np.testing.assert_allclose(
        np.mean(exposure_model.concentration(time))-np.mean(exposure_model.long_range_concentration(time)),
        expected_short_range_concentration_component, rtol=0.02
    )


def test_short_range_exposure_with_ndarray_mask(data_registry):
    sr_model = mc_models.ShortRangeModel(
        data_registry=data_registry,
        exposed_identifier="exposed_2",
        activity=models.Activity.types['Heavy exercise'],                           # NOTE: not within infected.activity. In the future, this initialization might trigger an error.
        expiration=short_range_expiration_distributions(data_registry)['Shouting'], # NOTE: not within infected.expiration. In the future, this initialization might trigger an error.
        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
        distance=0.854,
    )
    c_model = mc_models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=50, humidity=0.3),
        ventilation=models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                        air_exch=10_000_000,),
        infected=mc_models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12.5), (13.5, 17.5))),
            virus=models.Virus.types['SARS_CoV_2_DELTA'],
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            expiration=expiration_distributions(data_registry)['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
        short_range=(sr_model,),
    )
    e_model = mc_models.ExposureModel(
        data_registry = data_registry,
        concentration_model = (c_model,),
        exposed = mc_models.Population(
            identifier="exposed_2",
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

