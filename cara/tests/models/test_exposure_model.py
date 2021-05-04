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
    cm = KnownConcentrations(lambda t: 1.2 if np.floor(t) % 2 else np.array([1.2, 1.2]))
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
