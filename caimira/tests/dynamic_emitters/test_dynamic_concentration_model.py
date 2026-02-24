import re

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass

from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry

known_min_background_concentration = 440.44

@dataclass(frozen=True)
class KnownConcentrationModelBase(models._ConcentrationModelBase):
    """
    A _ConcentrationModelBase class where all the class methods are
    redefined with a value taken from new parameters. Useful for testing.

    """
    known_multiple_populations: models.MultiplePopulations

    known_removal_rate: float

    known_min_background_concentration: float

    known_normalization_factor: float

    @property
    def population(self) -> models.MultiplePopulations:
        return self.known_multiple_populations

    def removal_rate(self, time: float) -> float:
        return self.known_removal_rate

    def min_background_concentration(self) -> float:
        return self.known_min_background_concentration

    def normalization_factor(self) -> float:
        return self.known_normalization_factor

    
@pytest.fixture
def dummy_multiple_populations() -> models.MultiplePopulations:
    interesting_times1 = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    population1 = models.Population(
        number=1,
        presence=interesting_times1,
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )

    interesting_times2 = models.SpecificInterval(([0.4, 1.], [1.1, 2]), )
    population2 = models.Population(
        number=10,
        presence=interesting_times2,
        mask=models.Mask.types['Cloth'],
        activity=models.Activity.types['Heavy exercise'],
        host_immunity=0.,
    )

    interesting_times3 = models.SpecificInterval(([5., 6.],), )
    population3 = models.Population(
        number=5,
        presence=interesting_times3,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Light activity'],
        host_immunity=0.5,
    )
    return models.MultiplePopulations([population1, population2, population3])

@pytest.fixture
def simple_dynamic_conc_model(data_registry, dummy_multiple_populations):
    interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    return KnownConcentrationModelBase(
        data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        known_multiple_populations = dummy_multiple_populations,
        known_removal_rate = 10.,
        known_min_background_concentration = known_min_background_concentration,
        known_normalization_factor = 10.)

def test_multiple_populations(simple_dynamic_conc_model):
    assert isinstance(simple_dynamic_conc_model.population, models.MultiplePopulations)
    assert np.all([isinstance(population, models.SimplePopulation) for population in simple_dynamic_conc_model.population.populations])

def test_state_change_times(simple_dynamic_conc_model):
    expected_transition_times = sorted(set((0.0, 0.4, 0.5, 1., 1.1, 2, 3., 5, 6)))
    result = simple_dynamic_conc_model.state_change_times()
    npt.assert_array_equal(result, expected_transition_times)

def test_first_presence_time(simple_dynamic_conc_model):
    npt.assert_array_equal(simple_dynamic_conc_model._first_presence_time(), 0.4)

def test_concentration(simple_dynamic_conc_model):
    assert isinstance(simple_dynamic_conc_model.concentration(0), float)
    npt.assert_almost_equal(simple_dynamic_conc_model.concentration(0),known_min_background_concentration)
    assert simple_dynamic_conc_model.concentration(0.5) > known_min_background_concentration

