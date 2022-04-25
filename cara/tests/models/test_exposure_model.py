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
    normed_concentration_function: typing.Callable = lambda x: 0

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
        models.Activity.types['Standing'], host_immunity=0.,
    ),
    # A population with some array component for η_inhale.
    models.Population(
        10, halftime, models.Mask(np.array([0.3, 0.35])),
        models.Activity.types['Standing'], host_immunity=0.
    ),
    # A population with some array component for inhalation_rate.
    models.Population(
        10, halftime, models.Mask.types['Type I'],
        models.Activity(np.array([0.51, 0.57]), 0.57), host_immunity=0.
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
        virus=models.Virus.types['SARS_CoV_2_ALPHA'],
        expiration=models.Expiration.types['Speaking'],
        host_immunity=0.,
    )
    normed_func = lambda x: func(x) / dummy_infected_population.emission_rate_when_present()
    return KnownNormedconcentration(dummy_room, dummy_ventilation,
                                dummy_infected_population, 0.3, normed_func)


@pytest.mark.parametrize(
    "population, cm, expected_exposure, expected_probability", [
        [populations[1], known_concentrations(lambda t: 36.),
         np.array([64.02320633, 59.45012016]), np.array([67.9503762594, 65.2366759251])],

        [populations[2], known_concentrations(lambda t: 36.),
         np.array([40.91708675, 45.73086166]), np.array([51.6749232285, 55.6374622042])],

        [populations[0], known_concentrations(lambda t: np.array([36., 72.])),
         np.array([45.73086166, 91.46172332]), np.array([55.6374622042, 80.3196524031])],

        [populations[1], known_concentrations(lambda t: np.array([36., 72.])),
         np.array([64.02320633, 118.90024032]), np.array([67.9503762594, 87.9151129926])],

        [populations[2], known_concentrations(lambda t: np.array([36., 72.])),
         np.array([40.91708675, 91.46172332]), np.array([51.6749232285, 80.3196524031])],
    ])
def test_exposure_model_ndarray(population, cm,
                                expected_exposure, expected_probability, sr_model):
    model = ExposureModel(cm, sr_model, population)
    np.testing.assert_almost_equal(
        model.deposited_exposure(), expected_exposure
    )
    np.testing.assert_almost_equal(
        model.infection_probability(), expected_probability, decimal=10
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)
    assert model.infection_probability().shape == (2,)
    assert model.expected_new_cases().shape == (2,)


@pytest.mark.parametrize("population, expected_deposited_exposure", [
        [populations[0], np.array([1.52436206, 1.52436206])],
        [populations[1], np.array([2.13410688, 1.98167067])],
        [populations[2], np.array([1.36390289, 1.52436206])],
    ])
def test_exposure_model_ndarray_and_float_mix(population, expected_deposited_exposure, sr_model):
    cm = known_concentrations(
        lambda t: 0. if np.floor(t) % 2 else np.array([1.2, 1.2]))
    model = ExposureModel(cm, sr_model, population)

    np.testing.assert_almost_equal(
        model.deposited_exposure(), expected_deposited_exposure
    )

    assert isinstance(model.infection_probability(), np.ndarray)
    assert isinstance(model.expected_new_cases(), np.ndarray)


@pytest.mark.parametrize("population, expected_deposited_exposure", [
        [populations[0], np.array([1.52436206, 1.52436206])],
        [populations[1], np.array([2.13410688, 1.98167067])],
        [populations[2], np.array([1.36390289, 1.52436206])],
    ])
def test_exposure_model_vector(population, expected_deposited_exposure, sr_model):
    cm_array = known_concentrations(lambda t: np.array([1.2, 1.2]))
    model_array = ExposureModel(cm_array, sr_model, population)
    np.testing.assert_almost_equal(
        model_array.deposited_exposure(), np.array(expected_deposited_exposure)
    )


def test_exposure_model_scalar(sr_model):
    cm_scalar = known_concentrations(lambda t: 1.2)
    model_scalar = ExposureModel(cm_scalar, sr_model, populations[0])
    expected_deposited_exposure = 1.52436206
    np.testing.assert_almost_equal(
        model_scalar.deposited_exposure(), expected_deposited_exposure
    )


@pytest.fixture
def conc_model():
    interesting_times = models.SpecificInterval(
        ([0., 1.], [1.01, 1.02], [12., 24.]),
    )
    always = models.SpecificInterval(((0., 24.), ))
    return models.ConcentrationModel(
        models.Room(25, models.PiecewiseConstant((0., 24.), (293,))),
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
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )


@pytest.fixture
def sr_model():
    return ()
    

# Expected deposited exposure were computed with a trapezoidal integration, using
# a mesh of 10'000 pts per exposed presence interval.
@pytest.mark.parametrize(
    ["exposed_time_interval", "expected_deposited_exposure"],
    [
        [(0., 1.), 45.6008710],
        [(1., 1.01), 0.5280401],
        [(1.01, 1.02), 0.51314096385],
        [(12., 12.01), 0.016255813185],
        [(12., 24.), 645.63619275],
        [(0., 24.), 700.7322474],
    ]
)
def test_exposure_model_integral_accuracy(exposed_time_interval,
                                          expected_deposited_exposure, conc_model, sr_model):
    presence_interval = models.SpecificInterval((exposed_time_interval,))
    population = models.Population(
        10, presence_interval, models.Mask.types['Type I'],
        models.Activity.types['Standing'], 0.,
    )
    model = ExposureModel(conc_model, sr_model, population)
    np.testing.assert_allclose(model.deposited_exposure(), expected_deposited_exposure)


def test_infectious_dose_vectorisation(sr_model):
    infected_population = models.InfectedPopulation(
        number=1,
        presence=halftime,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Standing'],
        virus=models.SARSCoV2(
            viral_load_in_sputum=1e9,
            infectious_dose=np.array([50, 20, 30]),
            viable_to_RNA_ratio = 0.5,
            transmissibility_factor=1.0,
        ),
        expiration=models.Expiration.types['Speaking'],
        host_immunity=0.,
    )
    cm = known_concentrations(lambda t: 1.2)
    cm = replace(cm, infected=infected_population)

    presence_interval = models.SpecificInterval(((0., 1.),))
    population = models.Population(
        10, presence_interval, models.Mask.types['Type I'],
        models.Activity.types['Standing'], 0.,
    )
    model = ExposureModel(cm, sr_model, population)
    inf_probability = model.infection_probability()
    assert isinstance(inf_probability, np.ndarray)
    assert inf_probability.shape == (3, )
