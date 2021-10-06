import typing

import numpy as np
import numpy.testing
import pytest
from dataclasses import dataclass

from cara import models
from cara.models import ExposureModel
from cara.dataclass_utils import replace


@dataclass(frozen=True)
class KnownNormedconcentration(models.ConcentrationModel):
    """
    A ConcentrationModel which is based on pre-known exposure concentrations and
    which therefore doesn't need other components. Useful for testing.

    """
    normed_concentration_function: typing.Callable

    def infectious_virus_removal_rate(self, time: float) -> models._VectorisedFloat:
        # very large decay constant -> same as constant concentration
        return 1.e50

    def _normed_concentration_limit(self, time: float) -> models._VectorisedFloat:
        return self.normed_concentration_function(time)

    def state_change_times(self):
        return [0., 24.]

    def _next_state_change(self, time: float):
        return 24.

    def _normed_concentration(self, time: float) -> models._VectorisedFloat:  # noqa
        return self.normed_concentration_function(time)


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
        models.Activity(np.array([0.51, 0.57]), 0.57),
    ),
]


def known_concentrations(func):
    dummy_room = models.Room(50, 0.5)
    dummy_ventilation = models._VentilationBase()
    dummy_infected_population = models.InfectedPopulation(
        number=1,
        presence=halftime,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Standing'],
        virus=models.Virus.types['SARS_CoV_2_B117'],
        expiration=models.Expiration.types['Speaking'],
        host_immunity=0.,
    )
    normed_func = lambda x: func(x) / dummy_infected_population.emission_rate_when_present()
    return KnownNormedconcentration(dummy_room, dummy_ventilation,
                                dummy_infected_population, normed_func)


@pytest.mark.parametrize(
    "population, cm, f_dep, expected_exposure, expected_probability", [
        [populations[1], known_concentrations(lambda t: 36.), 1.,
         np.array([432, 432]), np.array([99.6803184113, 99.5181053773])],

        [populations[2], known_concentrations(lambda t: 36.), 1.,
         np.array([432, 432]), np.array([97.4574432074, 98.3493482895])],

        [populations[0], known_concentrations(lambda t: np.array([36., 72.])), 1.,
         np.array([432, 864]), np.array([98.3493482895, 99.9727534893])],

        [populations[1], known_concentrations(lambda t: np.array([36., 72.])), 1.,
         np.array([432, 864]), np.array([99.6803184113, 99.9976777757])],

        [populations[0], known_concentrations(lambda t: 72.), np.array([0.5, 1.]),
         864, np.array([98.3493482895, 99.9727534893])],
    ])
def test_exposure_model_ndarray(population, cm, f_dep,
                                expected_exposure, expected_probability):
    model = ExposureModel(cm, population, fraction_deposited=f_dep)
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
    cm = known_concentrations(
        lambda t: 0. if np.floor(t) % 2 else np.array([1.2, 1.2]))
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
    interesting_times = models.SpecificInterval(
        ([0., 1.], [1.01, 1.02], [12., 24.]),
    )
    always = models.SpecificInterval(((0., 24.), ))
    return models.ConcentrationModel(
        models.Room(25),
        models.AirChange(always, 5),
        models.EmittingPopulation(
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            known_individual_emission_rate=970 * 50,
            # superspreading event, where ejection factor is fixed based
            # on Miller et al. (2020) - 50 represents the infectious dose.
        )
    )


# Expected exposure were computed with a trapezoidal integration, using
# a mesh of 10'000 pts per exposed presence interval.
@pytest.mark.parametrize(
    ["exposed_time_interval", "expected_exposure"],
    [
        [(0., 1.), 266.67176],
        [(1., 1.01), 3.0879539],
        [(1.01, 1.02), 3.00082435],
        [(12., 12.01), 0.095063235],
        [(12., 24.), 3775.65025],
        [(0., 24.), 4097.8494],
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


def test_infectious_dose_vectorisation():
    infected_population = models.InfectedPopulation(
        number=1,
        presence=halftime,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Standing'],
        virus=models.SARSCoV2(
            viral_load_in_sputum=1e9,
            infectious_dose=np.array([50, 20, 30]),
            viable_to_RNA_ratio = 0.5,
        ),
        expiration=models.Expiration.types['Speaking'],
        host_immunity=0.,
    )
    cm = known_concentrations(lambda t: 1.2)
    cm = replace(cm, infected=infected_population)

    presence_interval = models.SpecificInterval(((0., 1.),))
    population = models.Population(
        10, presence_interval, models.Mask.types['Type I'],
        models.Activity.types['Standing'],
    )
    model = ExposureModel(cm, population, fraction_deposited=1.0)
    inf_probability = model.infection_probability()
    assert isinstance(inf_probability, np.ndarray)
    assert inf_probability.shape == (3, )
