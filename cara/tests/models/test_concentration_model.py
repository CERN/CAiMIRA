import re

import numpy as np
import pytest

from cara import models


@pytest.mark.parametrize(
    "override_params", [
        {'volume': np.array([100, 120])},
        {'air_change': np.array([100, 120])},
        {'virus_halflife': np.array([1.1, 1.5])},
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
        {'quantum_infectious_dose': np.array([50, 20])},
        {'η_exhale': np.array([0.92, 0.95])},
        {'η_leaks': np.array([0.15, 0.20])},
    ]
)
def test_concentration_model_vectorisation(override_params):
    defaults = {
        'volume': 75,
        'air_change': 100,
        'virus_halflife': 1.1,
        'viral_load_in_sputum': 1e9,
        'quantum_infectious_dose': 50,
        'η_exhale': 0.95,
        'η_leaks': 0.15,
    }
    defaults.update(override_params)

    always = models.PeriodicInterval(240, 240)  # TODO: This should be a thing on an interval.
    c_model = models.ConcentrationModel(
        models.Room(defaults['volume']),
        models.AirChange(always, defaults['air_change']),
        models.InfectedPopulation(
            number=1,
            presence=always,
            mask=models.Mask(
                η_exhale=defaults['η_exhale'],
                η_leaks=defaults['η_leaks'],
                η_inhale=0.3,
            ),
            activity=models.Activity(
                0.51,
                0.75,
            ),
            virus=models.Virus(
                halflife=defaults['virus_halflife'],
                viral_load_in_sputum=defaults['viral_load_in_sputum'],
                quantum_infectious_dose=defaults['quantum_infectious_dose'],
            ),
            expiration=models.Expiration(
                ejection_factor=(0.084, 0.009, 0.003, 0.002),
            ),
        )
    )
    concentrations = c_model.concentration(10)
    assert isinstance(concentrations, np.ndarray)
    assert concentrations.shape == (2, )


@pytest.fixture
def simple_conc_model():
    interesting_times = models.SpecificInterval(([0, 1], [1.1, 1.999], [2, 3]), )
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
    assert simple_conc_model._next_state_change(time) == expected_next_state_change


def test_next_state_change_time_out_of_range(simple_conc_model: models.ConcentrationModel):
    with pytest.raises(
            ValueError,
            match=re.escape("The requested time (3.1) is greater than last available state change time (3)")
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
    assert c1 == c2 + c3
