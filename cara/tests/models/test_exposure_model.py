import decimal
import typing

import numpy as np
import numpy.testing
import pytest
from dataclasses import dataclass

from cara import models
from cara.models import ExposureModel


@dataclass(frozen=True)
class KnownConcentrations(models.ConcentrationModel):
    """
    A ConcentrationModel which is based on pre-known quanta concentrations and
    which therefore doesn't need other components. Useful for testing.

    """
    #def __init__(self, concentration_function: typing.Callable) -> None:
    #    self._func = concentration_function

    
    concentration_function: typing.Callable

    def infectious_virus_removal_rate(self, time: float) -> models._VectorisedFloat:
        # very large decay constant -> same as constant concentration
        return 1.e50

    def _concentration_limit(self, time: float) -> models._VectorisedFloat:
        return self.concentration_function(time)

    def state_change_times(self):
        return [0, 24]

    def _next_state_change(self, time: float):
        return 24

    def concentration(self, time: float) -> models._VectorisedFloat:  # noqa
        return self.concentration_function(time)


halftime = models.PeriodicInterval(120, 60)
populations = [
    # A simple scalar population.
    models.Population(
        10, halftime, models.Mask.types['Type I'],
        models.Activity.types['Standing'],
    ),
    # A population with some array component for η_inhale.
    models.Population(
        10, halftime, models.Mask(np.array([0.3, 0.35])),
        models.Activity.types['Standing'],
    ),
    # A population with some array component for inhalation_rate.
    models.Population(
        10, halftime, models.Mask.types['Type I'],
        models.Activity(np.array([0.51,0.57]), 0.57),
    ),
]


@pytest.mark.parametrize(
    "population, cm, f_dep, expected_exposure, expected_cumulated_exposure, expected_probability",[
    [populations[1], KnownConcentrations(None, None, None, lambda t: 1.2), 1.,
     np.array([14.4, 14.4]), np.array([3.44736/0.6, 3.20112/0.6]), np.array([99.6803184113, 99.5181053773])],

    [populations[2], KnownConcentrations(None, None, None, lambda t: 1.2), 1.,
     np.array([14.4, 14.4]), np.array([2.2032/0.6, 2.4624/0.6]), np.array([97.4574432074, 98.3493482895])],

    [populations[0], KnownConcentrations(None, None, None,lambda t: np.array([1.2, 2.4])), 1.,
     np.array([14.4, 28.8]), np.array([2.4624/0.6, 4.9248/0.6]), np.array([98.3493482895, 99.9727534893])],

    [populations[1], KnownConcentrations(None, None, None,lambda t: np.array([1.2, 2.4])), 1.,
     np.array([14.4, 28.8]), np.array([3.44736/0.6, 6.40224/0.6]), np.array([99.6803184113, 99.9976777757])],

    [populations[0], KnownConcentrations(None, None, None,lambda t: 2.4), np.array([0.5, 1.]),
     28.8, np.array([4.104, 8.208]), np.array([98.3493482895, 99.9727534893])],
    ])
def test_exposure_model_ndarray(population, cm, f_dep, 
                                expected_exposure, expected_cumulated_exposure, expected_probability):
    model = ExposureModel(cm, population, fraction_deposited = f_dep)
    np.testing.assert_almost_equal(
        model.quanta_exposure(), expected_exposure
    )
    np.testing.assert_almost_equal(
        model.infection_probability(), expected_probability, decimal=10
    )
    np.testing.assert_almost_equal(
        model.cumulated_exposure(), expected_cumulated_exposure, decimal=10
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)
    assert isinstance(model.cumulated_exposure(), np.ndarray)
    assert model.infection_probability().shape == (2,)
    assert model.expected_new_cases().shape == (2,)
    assert model.cumulated_exposure().shape == (2,)


@pytest.mark.parametrize("population", populations)
def test_exposure_model_ndarray_and_float_mix(population):
    cm = KnownConcentrations(None, None, None, lambda t: 0 if np.floor(t) % 2 else np.array([1.2, 1.2]))
    model = ExposureModel(cm, population)

    expected_exposure = np.array([14.4, 14.4])
    np.testing.assert_almost_equal(
        model.quanta_exposure(), expected_exposure
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)


@pytest.mark.parametrize("population", populations)
def test_exposure_model_compare_scalar_vector(population):
    cm_scalar = KnownConcentrations(None, None, None,lambda t: 1.2)
    cm_array = KnownConcentrations(None, None, None, lambda t: np.array([1.2, 1.2]))
    model_scalar = ExposureModel(cm_scalar, population)
    model_array = ExposureModel(cm_array, population)
    expected_exposure = 14.4
    np.testing.assert_almost_equal(
        model_scalar.quanta_exposure(), expected_exposure
    )
    np.testing.assert_almost_equal(
        model_array.quanta_exposure(), np.array([expected_exposure]*2)
    )


@pytest.fixture
def conc_model():
    interesting_times = models.SpecificInterval(([0, 1], [1.01, 1.02], [12, 24]))
    always = models.SpecificInterval(((0, 24),))
    return models.ConcentrationModel(
        models.Room(25),
        models.AirChange(always, 5),
        models.InfectedPopulation(
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Superspreading event'],
        )
    )

# expected quanta were computed with a trapezoidal integration, using
# a mesh of 10'000 pts per exposed presence interval.
@pytest.mark.parametrize("exposed_time_interval, expected_quanta", [
        [(0, 1), 5.3334352],
        [(1, 1.01), 0.061759078],
        [(1.01, 1.02), 0.060016487],
        [(12, 12.01), 0.0019012647],
        [(12, 24), 75.513005],
        [(0, 24), 81.956988],
    ]
)
def test_exposure_model_integral_accuracy(exposed_time_interval,
                                          expected_quanta, conc_model):
    presence_interval = models.SpecificInterval((exposed_time_interval,))
    population = models.Population(
        10, presence_interval, models.Mask.types['Type I'],
        models.Activity.types['Standing'],
    )
    model = ExposureModel(conc_model, population, fraction_deposited=1.)
    np.testing.assert_allclose(model.quanta_exposure(), expected_quanta)
