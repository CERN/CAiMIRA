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
                viable_to_RNA_ratio = 0.5,
                transmissibility_factor=1.0,
            ),
            expiration=models._ExpirationBase.types['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    concentrations = c_model.concentration(10)
    assert isinstance(concentrations, np.ndarray)
    assert concentrations.shape == (2, )


@pytest.fixture
def simple_conc_model():
    interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
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
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )


@pytest.mark.parametrize(
    "time, expected_last_state_change", [
        [-15., 0.],  # Out of range goes to the first state.
        [0., 0.],
        [0.5, 0.0],
        [0.51, 0.5],
        [1., 0.5],
        [1.05, 1.],
        [1.1, 1.],
        [1.11, 1.1],
        [2., 1.1],
        [2.1, 2],
        [3., 2],
        [15., 3.],  # Out of range goes to the last state.
    ]
)
def test_last_state_change_time(
        simple_conc_model: models.ConcentrationModel,
        time,
        expected_last_state_change,
):
    assert simple_conc_model.last_state_change(float(time)) == expected_last_state_change


@pytest.mark.parametrize(
    "time, expected_next_state_change", [
        [0.0, 0.0],
        [0.5, 0.5],
        [1, 1],
        [1.05, 1.1],
        [1.1, 1.1],
        [1.11, 2],
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


def test_first_presence_time(simple_conc_model):
    assert simple_conc_model._first_presence_time() == 0.5


def test_integrated_concentration(simple_conc_model):
    c1 = simple_conc_model.integrated_concentration(0, 2)
    c2 = simple_conc_model.integrated_concentration(0, 1)
    c3 = simple_conc_model.integrated_concentration(1, 2)
    assert c1 != 0
    npt.assert_almost_equal(c1, c2 + c3, decimal=15)
