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
    A ConcentrationModel which is based on pre-known exposure concentrations and
    which therefore doesn't need other components. Useful for testing.

    """
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
dummyRoom = models.Room(50, 0.5)
dummyVentilation = models._VentilationBase()
dummyInfPopulation = models.InfectedPopulation(
    number=1,
    presence=halftime,
    mask=models.Mask.types['Type I'],
    activity=models.Activity.types['Standing'],
    virus=models.Virus.types['SARS_CoV_2_B117'],
    expiration=models.Expiration.types['Talking']
)

def known_concentrations(func):
    return KnownConcentrations(dummyRoom, dummyVentilation, dummyInfPopulation, func)


@pytest.mark.parametrize(
    "population, cm, f_dep, expected_exposure, expected_probability",[
    [populations[1], known_concentrations(lambda t: 1.2), 1.,
     np.array([14.4, 14.4]), np.array([17.4296889121, 16.292365501])], #(1 - e**(-(0.57*(1-0.35)*14.4)/30))*100

    [populations[2], known_concentrations(lambda t: 1.2), 1.,
     np.array([14.4, 14.4]), np.array([11.5205620042, 12.7855362382])],

    [populations[0], known_concentrations(lambda t: np.array([1.2, 2.4])), 1.,
     np.array([14.4, 28.8]), np.array([12.7855362382, 23.9363731074])],

    [populations[1], known_concentrations(lambda t: np.array([1.2, 2.4])), 1.,
     np.array([14.4, 28.8]), np.array([17.4296889121, 29.9303192658])],

    [populations[0], known_concentrations(lambda t: 2.4), np.array([0.5, 1.]),
     28.8, np.array([12.7855362382, 23.9363731074])],
    ])
def test_exposure_model_ndarray(population, cm, f_dep,
                                expected_exposure, expected_probability):
    model = ExposureModel(cm, population, fraction_deposited = f_dep)
    np.testing.assert_almost_equal(
        model.exposure(), expected_exposure
    )
    np.testing.assert_almost_equal(
        model.infection_probability(), expected_probability, decimal=10
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)
    assert model.infection_probability().shape == (2,)
    assert model.expected_new_cases().shape == (2,)


@pytest.mark.parametrize("population", populations)
def test_exposure_model_ndarray_and_float_mix(population):
    cm = known_concentrations(lambda t: 0 if np.floor(t) % 2 else np.array([1.2, 1.2]))
    model = ExposureModel(cm, population)

    expected_exposure = np.array([14.4, 14.4])
    np.testing.assert_almost_equal(
        model.exposure(), expected_exposure
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)


@pytest.mark.parametrize("population", populations)
def test_exposure_model_compare_scalar_vector(population):
    cm_scalar = known_concentrations(lambda t: 1.2)
    cm_array = known_concentrations(lambda t: np.array([1.2, 1.2]))
    model_scalar = ExposureModel(cm_scalar, population)
    model_array = ExposureModel(cm_array, population)
    expected_exposure = 14.4
    np.testing.assert_almost_equal(
        model_scalar.exposure(), expected_exposure
    )
    np.testing.assert_almost_equal(
        model_array.exposure(), np.array([expected_exposure]*2)
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

# expected exposure were computed with a trapezoidal integration, using
# a mesh of 10'000 pts per exposed presence interval.
@pytest.mark.parametrize("exposed_time_interval, expected_exposure", [
        [(0, 1), 266.67176],
        [(1, 1.01), 3.0879539],
        [(1.01, 1.02), 3.00082435],
        [(12, 12.01), 0.095063235],
        [(12, 24), 3775.65025],
        [(0, 24), 4097.8494],
    ]
)
def test_exposure_model_integral_accuracy(exposed_time_interval,
                                          expected_exposure, conc_model):
    presence_interval = models.SpecificInterval((exposed_time_interval,))
    population = models.Population(
        10, presence_interval, models.Mask.types['Type I'],
        models.Activity.types['Standing'],
    )
    model = ExposureModel(conc_model, population, fraction_deposited=1.)
    np.testing.assert_allclose(model.exposure(), expected_exposure)

@pytest.mark.parametrize(
    "override_params", [
        {'infectious_dose': np.array([50, 20, 30])},
    ]
)
def test_infectious_dose_vectorisation(override_params):
    defaults = {
        'infectious_dose': 50
    }
    defaults.update(override_params)

    infPopulation = models.InfectedPopulation(
        number=1,
        presence=halftime,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Standing'],
        virus = models.SARSCoV2(
        viral_load_in_sputum=1e9,
            infectious_dose=defaults['infectious_dose'],
        ),
        expiration=models.Expiration.types['Talking']
    )
    cm = KnownConcentrations(dummyRoom, dummyVentilation, infPopulation, lambda t: 1.2)

    presence_interval = models.SpecificInterval(((0, 1),))
    population = models.Population(
        10, presence_interval, models.Mask.types['Type I'],
        models.Activity.types['Standing'],
    )
    model = ExposureModel(cm, population, fraction_deposited=1.0)
    inf_probability = model.infection_probability()
    assert isinstance(inf_probability, np.ndarray)
    assert inf_probability.shape == (3, )
