import re
import typing

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass

from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry

@dataclass(frozen=True)
class KnownConcentrationModelBase(models._ConcentrationModelBase):
    """
    A _ConcentrationModelBase class where all the class methods are
    redefined with a value taken from new parameters. Useful for testing.

    """
    known_population: models.Population

    known_removal_rate: float

    known_normalization_factor: float

    @property
    def population(self) -> models.Population:
        return self.known_population

    def removal_rate(self, time: float) -> float:
        return self.known_removal_rate

    def normalization_factor(self) -> float:
        return self.known_normalization_factor

@dataclass(frozen=True)
class KnownTotalViralConcentrationModelBase(models._TotalConcentrationModelBase):
    """
    A _TotalViralConcentrationModelBase class with several infected populations, 
    where all the class methods are redefined with a value taken from new parameters. 
    Useful for testing.
    """
    known_populations: typing.Tuple[models.Population, ...]

    known_removal_rate: float

    known_min_background_concentration: float

    known_normalization_factor: float

    @property
    def populations(self) -> typing.Tuple[models.Population, ...]:
        return self.known_populations
    
    @property
    def concentration_models(self) -> typing.Tuple[models.KnownConcentrationModelBase, ...]:
        return tuple(KnownConcentrationModelBase(
        data_registry=self.data_registry,
        room = self.room,
        ventilation = self.ventilation,
        known_population = population,
        known_removal_rate = self.known_removal_rate,
        known_normalization_factor = self.known_normalization_factor)
        for population in self.known_populations)

    def min_background_concentration(self) -> float:
        return self.known_min_background_concentration


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
    c_model = models.TotalViralConcentrationModel(
        data_registry,
        models.Room(defaults['volume'], models.PiecewiseConstant((0., 24.), (293,)), defaults['humidity']),
        models.AirChange(always, defaults['air_change']),
        (models.InfectedPopulation(
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
            short_range=(),
        ),),
        evaporation_factor=0.3,
    )
    assert isinstance(c_model.concentration(10), float)
    assert isinstance(c_model.concentration_models[0].concentration_increase(10), np.ndarray)
    assert c_model.concentration_models[0].concentration_increase(10).shape == (2, )


@pytest.fixture
def simple_total_conc_model(data_registry):
    interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    return models.TotalViralConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected_populations = (models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
            short_range=(),
        ),),
        evaporation_factor=0.3,
    )

@pytest.fixture
def simple_total_conc_model_extended_presence(data_registry):
    ventilation_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    return models.TotalViralConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(ventilation_times, 100),
        infected_populations = (models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.], [20., 20.001]), ),
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
            short_range=(),
        ),),
        evaporation_factor=0.3,
    )


@pytest.fixture
def dummy_population(simple_total_conc_model) -> models.Population:
    return models.Population(
        number=1,
        presence=simple_total_conc_model.infected_populations[0].presence,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )

def test_total_concentration_model(simple_total_conc_model):
    assert isinstance(simple_total_conc_model, models.TotalViralConcentrationModel)
    assert isinstance(simple_total_conc_model.populations, tuple)
    assert len(simple_total_conc_model.populations) == 1
    assert isinstance(simple_total_conc_model.populations[0], models.InfectedPopulation)
    assert isinstance(simple_total_conc_model.concentration_models, tuple)
    assert len(simple_total_conc_model.concentration_models) == 1
    assert isinstance(simple_total_conc_model.concentration_models[0], models.ConcentrationModel)


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
        simple_total_conc_model: models.TotalViralConcentrationModel,
        time,
        expected_last_state_change,
):
    assert simple_total_conc_model.concentration_models[0].last_state_change(float(time)) == expected_last_state_change


def test_first_presence_time(simple_total_conc_model):
    assert simple_total_conc_model.concentration_models[0]._first_presence_time() == 0.5


def test_integrated_concentration(simple_total_conc_model):
    c1 = simple_total_conc_model.integrated_concentration(0, 2)
    c2 = simple_total_conc_model.integrated_concentration(0, 1)
    c3 = simple_total_conc_model.integrated_concentration(1, 2)
    assert c1 != 0
    npt.assert_almost_equal(c1, c2 + c3, decimal=15)



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
    simple_total_conc_model: models.TotalViralConcentrationModel,
    dummy_population: models.Population,
    known_removal_rate: float,
    known_min_background_concentration: float,
    expected_concentration: float):

    known_conc_model = KnownTotalViralConcentrationModelBase(
        data_registry = data_registry,
        room = simple_total_conc_model.room,
        ventilation = simple_total_conc_model.ventilation,
        known_populations = (dummy_population,),
        known_removal_rate = known_removal_rate,
        known_normalization_factor=1.,
        known_min_background_concentration = known_min_background_concentration)

    normed_concentration = known_conc_model.concentration(1)
    assert normed_concentration == pytest.approx(expected_concentration, abs=1e-6)

@pytest.mark.parametrize("time", [3.1,10])
def test_concentration_limit_last_state_change(simple_total_conc_model, time):
    npt.assert_almost_equal(simple_total_conc_model.concentration_models[0]._normed_concentration_limit(time), simple_total_conc_model.min_background_concentration()/simple_total_conc_model.concentration_models[0].normalization_factor())

@pytest.mark.parametrize([
    "start",
    "stop"],
    [
        [10, 19],
        [3, 19],
        [0., 19],
        [0., 20],
    ]
)
def test_concentration_after_last_state_change(simple_total_conc_model, simple_total_conc_model_extended_presence, start, stop):
    """
    Test that the concentration results for a model with no more presence of emitters  
    equals the concentration results of a model where the emitter will reenter at a later point.
    """
    time = (start+stop)/2
    npt.assert_almost_equal(simple_total_conc_model.concentration_models[0].removal_rate(time), simple_total_conc_model_extended_presence.concentration_models[0].removal_rate(time))
    npt.assert_almost_equal(simple_total_conc_model.concentration_models[0]._normed_concentration(time), simple_total_conc_model_extended_presence.concentration_models[0]._normed_concentration(time))
    npt.assert_almost_equal(simple_total_conc_model.concentration_models[0].normed_integrated_concentration(start, stop), simple_total_conc_model_extended_presence.concentration_models[0].normed_integrated_concentration(start, stop))

    npt.assert_almost_equal(simple_total_conc_model.concentration(time), simple_total_conc_model.concentration_models[0].concentration_increase(time) + np.array(simple_total_conc_model.min_background_concentration()).mean())
    npt.assert_almost_equal(simple_total_conc_model_extended_presence.concentration(time), simple_total_conc_model_extended_presence.concentration_models[0].concentration_increase(time) + np.array(simple_total_conc_model.min_background_concentration()).mean())
    npt.assert_almost_equal(simple_total_conc_model.concentration(time), simple_total_conc_model_extended_presence.concentration(time))

    npt.assert_almost_equal(simple_total_conc_model.integrated_concentration(start, stop), simple_total_conc_model.concentration_models[0].integrated_concentration_increase(start, stop) + (stop - start) * np.array(simple_total_conc_model.min_background_concentration()).mean())
    npt.assert_almost_equal(simple_total_conc_model_extended_presence.integrated_concentration(start, stop), simple_total_conc_model_extended_presence.concentration_models[0].integrated_concentration_increase(start, stop) + (stop - start) * np.array(simple_total_conc_model.min_background_concentration()).mean())
    npt.assert_almost_equal(simple_total_conc_model_extended_presence.integrated_concentration(start, stop), simple_total_conc_model.integrated_concentration(start, stop))