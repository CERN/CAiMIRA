import re

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass

from caimira import models
from caimira.store.data_registry import DataRegistry

@dataclass(frozen=True)
class KnownConcentrationModelBase(models._ConcentrationModelBase):
    """
    A _ConcentrationModelBase class where all the class methods are
    redefined with a value taken from new parameters. Useful for testing.

    """
    known_population: models.Population

    known_removal_rate: float

    known_min_background_concentration: float

    known_normalization_factor: float

    @property
    def population(self) -> models.Population:
        return self.known_population

    def removal_rate(self, time: float) -> float:
        return self.known_removal_rate

    def min_background_concentration(self) -> float:
        return self.known_min_background_concentration

    def normalization_factor(self, time = None) -> float:
        return self.known_normalization_factor


@pytest.mark.parametrize(
    "override_params", [
        {'volume': np.array([100, 120])},
        {'humidity': np.array([0.5, 0.4])},
        {'air_change': np.array([100, 120])},
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
    ]
)
def test_concentration_model_vectorisation(override_params, data_registry):
    defaults = {
        'volume': 75,
        'humidity': 0.5,
        'air_change': 100,
        'viral_load_in_sputum': 1e9
    }
    defaults.update(override_params)

    always = models.PeriodicInterval(240, 240)  # TODO: This should be a thing on an interval.
    c_model = models.ConcentrationModel(
        data_registry,
        models.Room(defaults['volume'], models.PiecewiseConstant((0., 24.), (293,)), defaults['humidity']),
        models.AirChange(always, defaults['air_change']),
        models.InfectedPopulation(
            data_registry=data_registry,
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
def simple_conc_model(data_registry):
    interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    return models.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = models.InfectedPopulation(
            data_registry=data_registry,
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


@pytest.fixture
def dummy_population(simple_conc_model) -> models.Population:
    return models.Population(
        number=1,
        presence=simple_conc_model.infected.presence,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
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


# The expected numbers were obtained via the quad integration of the
# normed_integrated_concentration method with 0 (start) and 2 (stop) as limits.
@pytest.mark.parametrize([
    "known_min_background_concentration",
    "expected_normed_integrated_concentration"],
    [
        [0.0, 0.00018533333708996207],
        [240.0, 48.000185340695275],
        [440.0, 88.00018534069527],
        [600., 120.00018534069527],
        [1000., 200.0001853407918],
    ]
)
def test_normed_integrated_concentration_with_background_concentration(
    data_registry: DataRegistry,
    simple_conc_model: models.ConcentrationModel,
    dummy_population: models.Population,
    known_min_background_concentration: float,
    expected_normed_integrated_concentration: float):

    known_conc_model = KnownConcentrationModelBase(
        data_registry,
        room = simple_conc_model.room,
        ventilation = simple_conc_model.ventilation,
        known_population = dummy_population,
        known_removal_rate = 100.,
        known_min_background_concentration = known_min_background_concentration,
        known_normalization_factor = 10.)
    npt.assert_almost_equal(known_conc_model.normed_integrated_concentration(0, 2), expected_normed_integrated_concentration)


# The expected numbers were obtained via the quad integration of the
# normed_integrated_concentration method with 0 (start) and 2 (stop) as limits.
@pytest.mark.parametrize([
    "known_removal_rate",
    "known_min_background_concentration",
    "known_normalization_factor",
    "expected_normed_integrated_concentration"],
    [
        [np.array([0.25, 10]), 0.0, 10., np.array([0.012161005755130391, 0.0017333437605308818])],
        [100, np.array([0, 240.0]), 10., np.array([0.00018533333708996207, 48.000185340695275])],
        [100, 440.0, np.array([10., 20.]), np.array([88.00018534069527, 44.000185340695275])],
        [np.array([10, 100]), np.array([600., 800.]), 10., np.array([120.00173334473946, 160.0001853406953])],
        [np.array([50, 100,]), np.array([1000.,1100.]), np.array([10., 20.]), np.array([200.00036800764332, 110.00018534069527])],
    ]
)
def test_normed_integrated_concentration_vectorisation(
    data_registry: DataRegistry,
    simple_conc_model: models.ConcentrationModel,
    dummy_population: models.Population,
    known_removal_rate: float,
    known_min_background_concentration: float,
    known_normalization_factor: float,
    expected_normed_integrated_concentration: float):

    known_conc_model = KnownConcentrationModelBase(
        data_registry = data_registry,
        room = simple_conc_model.room,
        ventilation = simple_conc_model.ventilation,
        known_population = dummy_population,
        known_removal_rate = known_removal_rate,
        known_min_background_concentration = known_min_background_concentration,
        known_normalization_factor = known_normalization_factor)

    integrated_concentration = known_conc_model.normed_integrated_concentration(0, 2)

    assert isinstance(integrated_concentration, np.ndarray)
    assert integrated_concentration.shape == (2, )
    npt.assert_almost_equal(integrated_concentration, expected_normed_integrated_concentration)


@pytest.mark.parametrize([
    "known_removal_rate",
    "known_min_background_concentration",
    "expected_concentration"],
    [
        [0., 240., 240. + 0.5/75],
        [0.0001, 240.0, 240. + 0.5/75],
        [1e-6, 240.0, 240 + 0.5/75],
        [0., np.array([240., 240.]), np.array([240. + 0.5/75, 240. + 0.5/75])],
        [np.array([0.0001, 1e-6]), np.array([240., 240.]), np.array([240. + 0.5/75, 240. + 0.5/75])],
    ]
)
def test_zero_ventilation_rate(
    data_registry: DataRegistry,
    simple_conc_model: models.ConcentrationModel,
    dummy_population: models.Population,
    known_removal_rate: float,
    known_min_background_concentration: float,
    expected_concentration: float):

    known_conc_model = KnownConcentrationModelBase(
        data_registry = data_registry,
        room = simple_conc_model.room,
        ventilation = simple_conc_model.ventilation,
        known_population = dummy_population,
        known_removal_rate = known_removal_rate,
        known_normalization_factor=1.,
        known_min_background_concentration = known_min_background_concentration)

    normed_concentration = known_conc_model.concentration(1)
    assert normed_concentration == pytest.approx(expected_concentration, abs=1e-6)
