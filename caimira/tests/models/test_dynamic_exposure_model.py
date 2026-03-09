import re

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass

from caimira.calculator.models import models

known_min_background_concentration = 440.44

@dataclass(frozen=True)
class KnownConcentrationModel(models._ConcentrationModelBase):
    """
    A _ConcentrationModelBase class where all the class methods are
    redefined with a value taken from new parameters. Useful for testing.

    """
    infected: models.MultipleInfectedPopulations

    known_removal_rate: float

    known_min_background_concentration: float

    known_normalization_factors: list[float]

    evaporation_factor = 0.3

    @property
    def population(self) -> models.MultipleInfectedPopulations:
        return self.infected

    def removal_rate(self, time: float) -> float:
        return self.known_removal_rate

    def min_background_concentration(self) -> float:
        return self.known_min_background_concentration

    def normalization_factor_list(self) -> float:
        return self.known_normalization_factors

    
@pytest.fixture
def dummy_multiple_infected_populations(data_registry) -> models.MultipleInfectedPopulations:
    interesting_times1 = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    group1 = models.InfectedPopulation(
        data_registry=data_registry,
        virus=models.Virus.types['SARS_CoV_2_ALPHA'],
        expiration=models.Expiration.types['Speaking'],
        number=1,
        presence=interesting_times1,
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )

    interesting_times2 = models.SpecificInterval(([0.4, 1.], [1.1, 2]), )
    group2 = models.InfectedPopulation(
        data_registry=data_registry,
        virus=models.Virus.types['SARS_CoV_2_ALPHA'],
        expiration=models.Expiration.types['Speaking'],
        number=10,
        presence=interesting_times2,
        mask=models.Mask.types['Cloth'],
        activity=models.Activity.types['Heavy exercise'],
        host_immunity=0.,
    )

    interesting_times3 = models.SpecificInterval(([5., 6.],), )
    group3 = models.InfectedPopulation(
        data_registry=data_registry,
        virus=models.Virus.types['SARS_CoV_2_ALPHA'],
        expiration=models.Expiration.types['Speaking'],
        number=5,
        presence=interesting_times3,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Light activity'],
        host_immunity=0.5,
    )
    return models.MultipleInfectedPopulations([group1, group2, group3])

@pytest.fixture
def dynamic_conc_model(data_registry, dummy_multiple_infected_populations):
    interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    return KnownConcentrationModel(
        data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = dummy_multiple_infected_populations,
        known_removal_rate = 10.,
        known_min_background_concentration = known_min_background_concentration,
        known_normalization_factors = [(10.,4), (2,1), (0,4)])

@pytest.fixture
def dynamic_exposure_model(data_registry, dynamic_conc_model):
    return models.ExposureModel(
        data_registry=data_registry,
        concentration_model=dynamic_conc_model,
        short_range=(),
        exposed=models.Population(
            number=10,
            presence=models.SpecificInterval(((8, 12), (13, 17), )),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.
        ),
        geographical_data=(),
    )

def test_normalization_factor_change(dynamic_conc_model): 
    state_change_times = dynamic_conc_model.population.transition_times()
    assert state_change_times == [0.0, 0.4, 0.5, 1.0, 1.1, 2, 3.0, 5.0, 6.0]
    for i in range(1, len(state_change_times)):
        time = (state_change_times[i] + state_change_times[i-1])/2
        assert dynamic_conc_model.normalization_factor(state_change_times[i]) == dynamic_conc_model.normalization_factor(time)

@pytest.mark.parametrize(
    "time, expected_normalization_factor", [
        [0.0,  0],
        [0.4,  0],
        [0.45, 2],
        [0.5,  2],
        [0.6,  60/11],
        [1.0,  60/11],
        [1.1,  0],
        [1.5,  60/11],
        [2,    60/11],
        [3.0,  40],
        [5.0,  0],
        [6.0,  0],
    ]
)
def test_normalization_factor(time, expected_normalization_factor, dynamic_conc_model):
    assert np.allclose(dynamic_conc_model.normalization_factor(time), expected_normalization_factor)

def test_normed_integrated_concentration(dynamic_conc_model):
    normed_integrated_concentration = dynamic_conc_model.normed_integrated_concentration(0.6,1)
    assert np.all(normed_integrated_concentration >= 0)

def test_common_particle(dynamic_exposure_model):
    particles = [group.particle
                for group in dynamic_exposure_model.concentration_model.infected.groups]
    fdeps = dynamic_exposure_model.long_range_fraction_deposited()
    assert len(set(particles)) == 1
    assert len(set(fdeps)) == 1 

@pytest.mark.parametrize(
    "start, stop, normalization_factor", [
        [0.4,  0.5, 2],
        [0.41, 0.5, 2],
        [1.1,  2,   60/11],
        [5,    6,   0],
    ]
)
def test_long_range_deposited_exposure_within_interval(start, stop, normalization_factor, dynamic_exposure_model):
    fdep = dynamic_exposure_model.long_range_fraction_deposited()[0] # Common particle
    inhalation_rate = dynamic_exposure_model.exposed.activity.inhalation_rate
    normed_integrated_concentration = dynamic_exposure_model.concentration_model.normed_integrated_concentration(start, stop)
    expected_deposited_exposure = np.mean(normed_integrated_concentration*fdep)*normalization_factor*inhalation_rate
    result_deposited_exposure = dynamic_exposure_model._long_range_deposited_exposure_within_interval(start, stop)
    
    assert np.allclose(expected_deposited_exposure, result_deposited_exposure)
    with pytest.raises(ValueError):
        dynamic_exposure_model._long_range_deposited_exposure_within_interval(0,1)
