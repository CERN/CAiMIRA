import re

import numpy as np
import numpy.testing as npt
import pytest

from cara import models


@pytest.mark.parametrize(
    "override_params", [
        {'volume': np.array([100, 120])},
        {'humidity': np.array([0.5, 0.4])},
        {'air_change': np.array([100, 120])},
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
    ]
)
def test_concentration_model_vectorisation(override_params):
    defaults = {
        'volume': 75,
        'humidity': 0.5,
        'air_change': 100,
        'viral_load_in_sputum': 1e9
    }
    defaults.update(override_params)

    always = models.PeriodicInterval(240, 240)  # TODO: This should be a thing on an interval.
    c_model = models.ConcentrationModel(
        models.Room(defaults['volume'], defaults['humidity']),
        models.AirChange(always, defaults['air_change']),
        models.InfectedPopulation(
            number=1,
            presence=always,
            mask=models.Mask(
                factor_exhale=0.95,
                η_inhale=0.3,
            ),
            activity=models.Activity(
                0.51,
                0.75,
            ),
            virus=models.SARSCoV2(
                viral_load_in_sputum=defaults['viral_load_in_sputum'],
                infectious_dose=50.,
            ),
            expiration=models.Expiration((1., 0., 0.)),
        )
    )
    concentrations = c_model.concentration(10)
    assert isinstance(concentrations, np.ndarray)
    assert concentrations.shape == (2, )


@pytest.fixture
def simple_conc_model():
    interesting_times = models.SpecificInterval(([0., 1.], [1.1, 1.999], [2., 3.]), )
    return models.ConcentrationModel(
        models.Room(75),
        models.AirChange(interesting_times, 100),
        models.InfectedPopulation(
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
        )
    )


@pytest.mark.parametrize(
    "time, expected_next_state_change", [
        [0, 0],
        [1, 1],
        [1.05, 1.1],
        [1.1, 1.1],
        [1.11, 1.999],
        [1.9991, 2],
        [2, 2],
        [2.1, 3],
        [3, 3],
    ]
)
def test_next_state_change_time(
        simple_conc_model: models.ConcentrationModel,
        time,
        expected_next_state_change,
):
    assert simple_conc_model._next_state_change(float(time)) == expected_next_state_change


def test_next_state_change_time_out_of_range(simple_conc_model: models.ConcentrationModel):
    with pytest.raises(
            ValueError,
            match=re.escape("The requested time (3.1) is greater than last available state change time (3.0)")
    ):
        simple_conc_model._next_state_change(3.1)


@pytest.mark.parametrize(
    "start, stop, is_valid", [
        [0, 1.05, False],
        [0.99, 1.1, False],
        [0.5, 1.01, False],
        [0, 1, True],
        [1.01, 1.1, True],
        [0.01, 1, True],
        [1.11, 1.99, True],
    ]
)
def test_valid_interval(
        start, stop, is_valid,
        simple_conc_model: models.ConcentrationModel
):
    assert simple_conc_model._is_interval_between_state_changes(start, stop) == is_valid


def test_integrated_concentration(simple_conc_model):
    c1 = simple_conc_model.integrated_concentration(0, 2)
    c2 = simple_conc_model.integrated_concentration(0, 1)
    c3 = simple_conc_model.integrated_concentration(1, 2)
    assert c1 != 0
    npt.assert_almost_equal(c1, c2 + c3, decimal=15)
