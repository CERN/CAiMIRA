from dataclasses import dataclass

import numpy as np
import numpy.testing as npt
import pytest

from cara import models


@pytest.mark.parametrize(
    "override_params", [
        {'volume': np.array([100, 120])},
        {'air_change': np.array([100, 120])},
        {'virus_halflife': np.array([1.1, 1.5])},
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
        {'coefficient_of_infectivity': np.array([0.02, 0.05])},
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
        'coefficient_of_infectivity': 0.02,
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
                coefficient_of_infectivity=defaults['coefficient_of_infectivity'],
            ),
            expiration=models.Expiration(
                ejection_factor=(0.084, 0.009, 0.003, 0.002),
            ),
        )
    )
    concentrations = c_model.concentration(10)
    assert isinstance(concentrations, np.ndarray)
    assert concentrations.shape == (2, )


@pytest.mark.parametrize(
    "time, expected_next_state_change", [
        [0, 0],
        [1, 4],
        [4, 4],
        [24, 24],
    ]
)
def test_concentration_model_next_state_change(time,expected_next_state_change):
    always = models.PeriodicInterval(240, 240)
    c_model = models.ConcentrationModel(
        models.Room(75),
        models.AirChange(always, 100),
        models.InfectedPopulation(
            number=1,
            presence=always,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
        )
    )
    assert c_model._next_state_change(time) == expected_next_state_change
    with pytest.raises(ValueError, match="Time larger than highest state change"):
        c_model._next_state_change(24.1)


@dataclass(frozen=True)
class DummyVentilation(models.Ventilation):
    # Dummy ventilation where air_exchange depends on time explicitly

    #: The interval in which the ventilation is operating.
    active: models.Interval

    def air_exchange(self, room: models.Room, time: float) -> models._VectorisedFloat:
        if not self.active.triggered(time):
            return 0.
        return time*0.5


@dataclass(frozen=True)
class DummyPopulation(models.Population):
    # Dummy infected population where emission rate depends on time 
    # explicitly
    virus: models.Virus
    expiration: models.Expiration

    def emission_rate_when_present(self) -> models._VectorisedFloat:
        return 50.

    def individual_emission_rate(self, time) -> models._VectorisedFloat:
        """
        The emission rate of a single individual in the population.
        """

        if not self.person_present(time):
            return 0.

        return self.emission_rate_when_present()*time

    def emission_rate(self, time) -> models._VectorisedFloat:
        """
        The emission rate of the entire population.
        """
        return self.individual_emission_rate(time) * self.number


def test_concentration_model_constant_parameters():
    always = models.SpecificInterval(present_times=[(0,24)])
    c_model = models.ConcentrationModel(
        models.Room(75),
        DummyVentilation(always),
        DummyPopulation(
            number=1,
            presence=always,
            mask=models.Mask(
                η_exhale=0.95,
                η_leaks=0.15,
                η_inhale=0.3,
            ),
            activity=models.Activity(
                0.51,
                0.75,
            ),
            virus=models.Virus(
                halflife=1.1,
                viral_load_in_sputum=1e9,
                coefficient_of_infectivity=0.02,
            ),
            expiration=models.Expiration(
                ejection_factor=(0.084, 0.009, 0.003, 0.002),
            ),
        )
    )
    times = [0.1, 10, 20, 24]
    concentration_limits = np.array([c_model._concentration_limit(t)
                                     for t in times])
    IVRRs = np.array([c_model.infectious_virus_removal_rate(t)
                      for t in times])
    assert np.all(concentration_limits==concentration_limits[-1])
    assert np.all(IVRRs==IVRRs[-1])
