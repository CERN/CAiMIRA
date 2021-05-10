import typing

import numpy as np
import numpy.testing
import pytest

from cara import models
from cara.models import ExposureModel


class KnownConcentrations(models.ConcentrationModel):
    """
    A ConcentrationModel which is based on pre-known quanta concentrations and
    which therefore doesn't need other components. Useful for testing.

    """
    def __init__(self, concentration_function: typing.Callable) -> None:
        self._func = concentration_function

    def infectious_virus_removal_rate(self, time: float) -> models._VectorisedFloat:
        # very large decay constant -> same as constant concentration
        return 1.e50

    def _concentration_limit(self, time: float) -> models._VectorisedFloat:
        return self._func(time)

    def state_change_times(self):
        return [0, 24]

    def _next_state_change(self, time: float):
        return 24

    def concentration(self, time: float) -> models._VectorisedFloat:  # noqa
        return self._func(time)


halftime = models.PeriodicInterval(120, 60)
populations = [
    # A simple scalar population.
    models.Population(
        10, halftime, models.Mask.types['Type I'],
        models.Activity.types['Standing'],
    ),
    # A population with some array component for η_inhale.
    models.Population(
        10, halftime, models.Mask(0.95, 0.15, np.array([0.3, 0.35])),
        models.Activity.types['Standing'],
    ),
]


@pytest.mark.parametrize(
    "population, cm, expected_exposure",[
    [populations[1], KnownConcentrations(lambda t: 1.2), np.array([14.4, 14.4])],
    [populations[0], KnownConcentrations(lambda t: np.array([1.2, 2.4])), np.array([14.4, 28.8])],
    [populations[1], KnownConcentrations(lambda t: np.array([1.2, 2.4])), np.array([14.4, 28.8])],
    ])
def test_exposure_model_ndarray(population, cm, expected_exposure):
    model = ExposureModel(cm, population)
    np.testing.assert_almost_equal(
        model.quanta_exposure(), expected_exposure
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)
    assert model.infection_probability().shape == (2,)
    assert model.expected_new_cases().shape == (2,)


@pytest.mark.parametrize("population", populations)
def test_exposure_model_ndarray_and_float_mix(population):
    cm = KnownConcentrations(lambda t: 0 if np.floor(t) % 2 else np.array([1.2, 1.2]))
    model = ExposureModel(cm, population)

    expected_exposure = np.array([14.4, 14.4])
    np.testing.assert_almost_equal(
        model.quanta_exposure(), expected_exposure
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)


@pytest.mark.parametrize("population", populations)
def test_exposure_model_compare_scalar_vector(population):
    cm_scalar = KnownConcentrations(lambda t: 1.2)
    cm_array = KnownConcentrations(lambda t: np.array([1.2, 1.2]))
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
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
        )
    )

# expected quanta were computed with a trapezoidal integration, using
# a mesh of 10'000 pts per exposed presence interval.
@pytest.mark.parametrize("exposed_time_interval, expected_quanta", [
        [(0, 1), 0.0055680845],
        [(1, 1.01), 6.4960491e-05],
        [(1.01, 1.02), 6.3187723e-05],
        [(12, 12.01), 1.9307359e-06],
        [(12, 24), 0.079347465],
        [(0, 24), 0.086122050],
    ]
)
def test_exposure_model_integral_accuracy(exposed_time_interval,
                                          expected_quanta, conc_model):
    presence_interval = models.SpecificInterval((exposed_time_interval,))
    population = models.Population(
        10, presence_interval, models.Mask.types['Type I'],
        models.Activity.types['Standing'],
    )
    model = ExposureModel(conc_model, population)
    np.testing.assert_allclose(model.quanta_exposure(), expected_quanta)
