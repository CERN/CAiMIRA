import typing

import numpy as np
import numpy.testing
import pytest
from dataclasses import dataclass

from caimira.calculator.models import models
from caimira.calculator.models.models import ExposureModel
from caimira.calculator.models.dataclass_utils import replace
from caimira.calculator.models.monte_carlo.data import expiration_distributions
from caimira.calculator.store.data_registry import DataRegistry

@dataclass(frozen=True)
class KnownNormedconcentration(models.ConcentrationModel):
    """
    A ConcentrationModel which is based on pre-known exposure concentrations and
    which therefore doesn't need other components. Useful for testing.

    """
    normed_concentration_function: typing.Callable = lambda x: 0

    def removal_rate(self, time: float) -> models._VectorisedFloat:
        # Very large decay constant -> same as constant concentration
        return 1.e50

    def _normed_concentration_limit(self, time: float) -> models._VectorisedFloat:
        return self.normed_concentration_function(time) * self.infected.number

    def state_change_times(self):
        return [0., 24.]

    def _next_state_change(self, time: float):
        return 24.

    def _normed_concentration(self, time: float) -> models._VectorisedFloat:  # noqa
        return self.normed_concentration_function(time) * self.infected.number


halftime = models.PeriodicInterval(120, 60)
populations = [
    # A simple scalar population.
    models.Population(
        10, halftime, activity=models.Activity.types['Standing'],
        mask=models.Mask.types['Type I'], host_immunity=0.,
    ),
    # A population with some array component for η_inhale.
    models.Population(
        10, halftime, activity=models.Activity.types['Standing'],
        mask=models.Mask(np.array([0.3, 0.35])), host_immunity=0.
    ),
    # A population with some array component for inhalation_rate.
    models.Population(
        10, halftime, activity=models.Activity(np.array([0.51, 0.57]), 0.57),
        mask=models.Mask.types['Type I'], host_immunity=0.
    ),
]

def known_concentrations(func, data_registry=DataRegistry()):
    dummy_room = models.Room(50, 0.5)
    dummy_ventilation = models._VentilationBase()
    dummy_infected_population = models.InfectedPopulation(
        data_registry=data_registry,
        number=1,
        presence=halftime,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Standing'],
        virus=models.Virus.types['SARS_CoV_2_ALPHA'],
        expiration=models.Expiration.types['Speaking'],
        host_immunity=0.,
    )
    normed_func = lambda x: (func(x) /
        dummy_infected_population.emission_rate_per_person_when_present())
    return KnownNormedconcentration(data_registry, dummy_room, dummy_ventilation,
                                dummy_infected_population, 0.3, normed_func)


@pytest.mark.parametrize(
    "population, cm, expected_exposure, expected_probability", [
        [populations[1], known_concentrations(lambda t: 18.),
         np.array([61.47704218, 57.08582488]), np.array([66.46671825, 63.74477329])],

        [populations[2], known_concentrations(lambda t: 18.),
         np.array([39.28983899, 43.91217299]), np.array([39.28983899, 54.18007995])],

        [populations[0], known_concentrations(lambda t: np.array([18., 36.])),
         np.array([43.91217299, 87.82434597]), np.array([54.18007995, 79.00534926])],

        [populations[1], known_concentrations(lambda t: np.array([18., 36.])),
         np.array([61.47704218, 122.9540844]), np.array([66.46671825, 88.75519015])],

        [populations[2], known_concentrations(lambda t: np.array([18., 36.])),
         np.array([39.28983899, 87.82434597]), np.array([50.25690322, 79.00534926])],
    ])
def test_exposure_model_ndarray(data_registry, population, cm,
                                expected_exposure, expected_probability, sr_model, cases_model):
    model = ExposureModel(data_registry, cm, sr_model, population, cases_model)
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
def test_exposure_model_ndarray_and_float_mix(data_registry, population, expected_deposited_exposure, sr_model, cases_model):
    cm = known_concentrations(
        lambda t: 0. if np.floor(t) % 2 else np.array([0.6, 0.6]))
    model = ExposureModel(data_registry, cm, sr_model, population, cases_model)

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
def test_exposure_model_vector(data_registry, population, expected_deposited_exposure, sr_model, cases_model):
    cm_array = known_concentrations(lambda t: np.array([0.6, 0.6]))
    model_array = ExposureModel(data_registry, cm_array, sr_model, population, cases_model)
    np.testing.assert_almost_equal(
        model_array.deposited_exposure(), np.array(expected_deposited_exposure)
    )


def test_exposure_model_scalar(data_registry, sr_model, cases_model):
    cm_scalar = known_concentrations(lambda t: 0.6)
    model_scalar = ExposureModel(data_registry, cm_scalar, sr_model, populations[0], cases_model)
    expected_deposited_exposure = 1.52436206
    np.testing.assert_almost_equal(
        model_scalar.deposited_exposure(), expected_deposited_exposure
    )


@pytest.fixture
def conc_model(data_registry):
    interesting_times = models.SpecificInterval(
        ([0., 1.], [1.01, 1.02], [12., 24.]),
    )
    always = models.SpecificInterval(((0., 24.), ))
    return models.ConcentrationModel(
        data_registry,
        models.Room(25, models.PiecewiseConstant((0., 24.), (293,))),
        models.AirChange(always, 5),
        models.EmittingPopulation(
            data_registry=data_registry,
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
def diameter_dependent_model(conc_model, data_registry) -> models.InfectedPopulation:
    # Generate a diameter dependent model
    return replace(conc_model,
        infected = models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=halftime,
            virus=models.Virus.types['SARS_CoV_2_DELTA'],
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            expiration=expiration_distributions(data_registry)['Breathing'],
            host_immunity=0.,
        ))


@pytest.fixture
def sr_model():
    return ()


@pytest.fixture
def cases_model():
    return ()


# Expected deposited exposure were computed with a trapezoidal integration, using
# a mesh of 10'000 pts per exposed presence interval.
@pytest.mark.parametrize(
    ["exposed_time_interval", "expected_deposited_exposure"],
    [
        [(0., 1.), 42.63222033436878],
        [(1., 1.01), 0.485377549596179],
        [(1.01, 1.02), 0.47058239520823814],
        [(12., 12.01), 0.01622776617499709],
        [(12., 24.), 595.1115223695439],
        [(0., 24.), 645.8401125684933],
    ]
)
def test_exposure_model_integral_accuracy(data_registry, exposed_time_interval,
                                          expected_deposited_exposure, conc_model, sr_model, cases_model):
    presence_interval = models.SpecificInterval((exposed_time_interval,))
    population = models.Population(
        10, presence_interval, models.Activity.types['Standing'],
        models.Mask.types['Type I'], 0.,
    )
    model = ExposureModel(data_registry, conc_model, sr_model, population, cases_model)
    np.testing.assert_allclose(model.deposited_exposure(), expected_deposited_exposure)


def test_infectious_dose_vectorisation(sr_model, cases_model, data_registry):
    infected_population = models.InfectedPopulation(
        data_registry=data_registry,
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
    cm = known_concentrations(lambda t: 0.6)
    cm = replace(cm, infected=infected_population)

    presence_interval = models.SpecificInterval(((0., 1.),))
    population = models.Population(
        10, presence_interval, models.Activity.types['Standing'],
        models.Mask.types['Type I'], 0.,
    )
    model = ExposureModel(data_registry, cm, sr_model, population, cases_model)
    inf_probability = model.infection_probability()
    assert isinstance(inf_probability, np.ndarray)
    assert inf_probability.shape == (3, )


@pytest.mark.parametrize(
    "pop, cases, infectiousness_days, AB, prob_random_individual", [
        [100_000, 68, 7, 5, 0.023800],
        [200_000, 121, np.array([7, 14]), 5, np.array([0.021175, 0.042350])],
        [np.array([100_000, 200_000]), 68, 14, 10, np.array([0.0952, 0.0476])],
        [150_000, np.array([68, 121]), 14, 2, np.array([0.012693, 0.022587])],
        [np.array([100_000, 200_000]), np.array([68, 121]), 7, 5, np.array([0.023450, 0.021175])]
    ]
)
def test_probability_random_individual(pop, cases, infectiousness_days, AB, prob_random_individual):
    cases = models.Cases(geographic_population=pop, geographic_cases=cases,
                        ascertainment_bias=AB)
    virus=models.SARSCoV2(
        viral_load_in_sputum=1e9,
        infectious_dose=50.,
        viable_to_RNA_ratio = 0.5,
        transmissibility_factor=1,
        infectiousness_days=infectiousness_days,
    )
    np.testing.assert_allclose(
        cases.probability_random_individual(virus), prob_random_individual, rtol=0.05
    )


@pytest.mark.parametrize(
    "pop, cases, AB, exposed, infected, prob_meet_infected_person", [
        [100000, 68, 5, 10, 1, 0.321509274],
        [100000, 121, 5, 20, 1, 0.302950694],
        [100000, np.array([68, 121]), 5, np.array([10, 20]), 1, np.array([0.321509274, 0.302950694])],
    ]
)
def test_prob_meet_infected_person(pop, cases, AB, exposed, infected, prob_meet_infected_person):
    cases = models.Cases(geographic_population=pop, geographic_cases=cases,
                        ascertainment_bias=AB)
    virus = models.Virus.types['SARS_CoV_2']
    np.testing.assert_allclose(cases.probability_meet_infected_person(virus, infected, exposed+infected),
                            prob_meet_infected_person, rtol=0.05)


@pytest.mark.parametrize(
    "exposed_population, cm, pop, cases, AB, probabilistic_exposure_probability",[
        [10, known_concentrations(lambda t: 18.),
        100000, 68, 5, 41.50971131],
        [10, known_concentrations(lambda t: 0.1),
        100000, 68, 5, 2.185785075],
        [20, known_concentrations(lambda t: 36.),
        100000, 68, 5, 64.09068488],
        [30, known_concentrations(lambda t: 0.6),
        100000, 68, 5, 55.93154502],
    ])
def test_probabilistic_exposure_probability(data_registry, sr_model, exposed_population, cm,
        pop, AB, cases, probabilistic_exposure_probability):

    population = models.Population(
        exposed_population, models.PeriodicInterval(120, 60), models.Activity.types['Standing'],
        models.Mask.types['Type I'], host_immunity=0.,)
    model = ExposureModel(data_registry, cm, sr_model, population, models.Cases(geographic_population=pop,
        geographic_cases=cases, ascertainment_bias=AB),)
    np.testing.assert_allclose(
        model.total_probability_rule(), probabilistic_exposure_probability, rtol=0.05
    )


@pytest.mark.parametrize(
    "volume, outside_temp, window_height, opening_length", [
        [np.array([50, 100]), models.PiecewiseConstant((0., 24.), (293.,)), 1., 1.,], # Verify (room) volume vectorisation.
        [50, models.PiecewiseConstant((0., 12, 24.),
            (np.array([293., 300.]), np.array([305., 310.]),)), 1., 1.,], # Verify (ventilation) outside_temp vectorisation.
        [50, models.PiecewiseConstant((0., 24.), (293.,)),
            np.array([1., 0.5]), 1.], # Verify (ventilation) window_height vectorisation.
        [50, models.PiecewiseConstant((0., 24.), (293.,)),
            1., np.array([1., 0.5])], # Verify (ventilation) opening_length vectorisation.
    ]
)
def test_diameter_vectorisation_window_opening(data_registry, diameter_dependent_model, sr_model, volume, outside_temp,
                                                window_height, opening_length, cases_model):
    concentration = replace(diameter_dependent_model,
        room = models.Room(volume=volume, inside_temp=models.PiecewiseConstant((0., 24.), (293.,)), humidity=0.3),
        ventilation=models.SlidingWindow(
            data_registry=data_registry,
            active=models.PeriodicInterval(period=120, duration=120),
            outside_temp=outside_temp,
            window_height=window_height,
            opening_length=opening_length
        ),
    )
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                        "or virus decay constant can be arrays at the same time."):
        models.ExposureModel(data_registry, concentration, sr_model, populations[0], cases_model)


def test_diameter_vectorisation_hinged_window(data_registry, diameter_dependent_model, sr_model, cases_model):
    # Verify (ventilation) window_width vectorisation.
    concentration = replace(diameter_dependent_model,
        ventilation = models.HingedWindow(active=models.PeriodicInterval(period=120, duration=120),
                                    outside_temp=models.PiecewiseConstant((0., 24.), (293.,)),
                                    window_height=1.,
                                    opening_length=1.,
                                    window_width=np.array([1., 0.5]))
    )
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                        "or virus decay constant can be arrays at the same time."):
        models.ExposureModel(data_registry, concentration, sr_model, populations[0], cases_model)


def test_diameter_vectorisation_HEPA_filter(data_registry, diameter_dependent_model, sr_model, cases_model):
    # Verify (ventilation) q_air_mech vectorisation.
    concentration = replace(diameter_dependent_model,
        ventilation = models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                        q_air_mech=np.array([0.5, 1.]))
    )
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                        "or virus decay constant can be arrays at the same time."):
        models.ExposureModel(data_registry, concentration, sr_model, populations[1], cases_model)


def test_diameter_vectorisation_air_change(data_registry, diameter_dependent_model, sr_model, cases_model):
    # Verify (ventilation) air_exch vectorisation.
    concentration = replace(diameter_dependent_model,
        ventilation = models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                        air_exch=np.array([0.5, 1.]))
    )
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                        "or virus decay constant can be arrays at the same time."):
        models.ExposureModel(data_registry, concentration, sr_model, populations[2], cases_model)


@pytest.mark.parametrize(
    "volume, inside_temp, humidity, error_message", [
        [np.array([50, 100]), models.PiecewiseConstant((0., 24.), (293.,)), 0.3,
        "If the diameter is an array, none of the ventilation parameters or virus decay constant "
        "can be arrays at the same time."], # Verify room volume vectorisation
        [50, models.PiecewiseConstant((0., 12, 24.), (np.array([293., 300.]), np.array([305., 310.]))), 0.3,
        "If the diameter is an array, none of the ventilation parameters or virus decay constant "
        "can be arrays at the same time."], # Verify room inside_temp vectorisation
        [50, models.PiecewiseConstant((0., 24.), (293.,)), np.array([0.3, 0.5]),
        "If the diameter is an array, none of the ventilation parameters or virus decay constant "
        "can be arrays at the same time."], # Verify room humidity vectorisation
    ]
)
def test_diameter_vectorisation_room(data_registry, diameter_dependent_model, sr_model, cases_model, volume, inside_temp, humidity, error_message):
    concentration = replace(diameter_dependent_model,
        room = models.Room(volume=volume, inside_temp=inside_temp, humidity=humidity),
        ventilation = models.HVACMechanical(active=models.SpecificInterval(((0., 24.), )), q_air_mech=100.))
    with pytest.raises(ValueError, match=error_message):
        models.ExposureModel(data_registry, concentration, sr_model, populations[0], cases_model)


@pytest.mark.parametrize(
    ["cm", "host_immunity", "expected_probability"],
    [
        [known_concentrations(lambda t: 18.), np.array([0.25, 0.5]), np.array([55.93365366, 39.78768672])],
        [known_concentrations(lambda t: 18.), np.array([0., 1.]), np.array([66.46671825, 0.])],
    ]
)
def test_host_immunity_vectorisation(data_registry, sr_model, cases_model, cm, host_immunity, expected_probability):
    population = models.Population(
        10, halftime, models.Activity.types['Standing'],
        models.Mask(np.array([0.3, 0.35])), host_immunity=host_immunity
    )
    model = ExposureModel(data_registry, cm, sr_model, population, cases_model)
    inf_probability = model.infection_probability()

    np.testing.assert_almost_equal(
        inf_probability, expected_probability, decimal=1
    )
    assert isinstance(inf_probability, np.ndarray)
    assert inf_probability.shape == (2, )
