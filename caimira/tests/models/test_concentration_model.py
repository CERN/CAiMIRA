import re
import typing

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass
from caimira.calculator.models.dataclass_utils import replace, nested_replace
from caimira.calculator.models.monte_carlo.data import expiration_distributions

from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry

SAMPLE_SIZE=250_000

@dataclass(frozen=True)
class KnownConcentrationModelBase(models._ConcentrationModelBase):
    """
    A _ConcentrationModelBase class where all the class methods are
    redefined with a value taken from new parameters. Useful for testing.

    """
    known_populations: typing.Tuple[models.Population, ...]

    known_removal_rate: models._VectorizedFloat

    known_min_background_concentration: models._VectorizedFloat

    known_normalization_factor: models._VectorizedFloat

    @property
    def populations(self) -> typing.Tuple[models.Population, ...]:
        return self.known_populations

    def min_background_concentration(self) -> models._VectorizedFloat:
        return self.known_min_background_concentration
    
    def _to_population_matrix(self, value, other) -> models._PopulationMatrix:
        """
        Convert 'value' to a models._PopulationMatrix with dimensions matching 'other'.
        """
        if isinstance(value, float):
            if isinstance(other, float):
                return np.asarray([[value]])
            return np.full((1, len(other)), value)
        return value.reshape(1, -1)

    def removal_rate(self, time: float) -> models._PopulationMatrix:
        return self._to_population_matrix(self.known_removal_rate, self.known_normalization_factor)

    def normalization_factor(self) -> models._PopulationMatrix:
        return self._to_population_matrix(self.known_normalization_factor, self.known_removal_rate)


@pytest.mark.parametrize(
    "override_params", [
        {'volume': np.array([100, 120])},
        {'humidity': np.array([0.5, 0.4])},
        {'air_change': np.array([100, 120])},
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
    ]
)
def test_concentration_model_vectorization(override_params, data_registry):
    defaults = {
        'volume': 75,
        'humidity': 0.5,
        'air_change': 100,
        'viral_load_in_sputum': np.array([1e9])
    }
    defaults.update(override_params)

    always = models.PeriodicInterval(240, 240)  # TODO: This should be a thing on an interval.
    c_model = models.ConcentrationModel(
        data_registry = data_registry,
        room = models.Room(defaults['volume'], models.PiecewiseConstant((0., 24.), (293,)), defaults['humidity']),
        ventilation = models.AirChange(always, defaults['air_change']),
        infected_populations = (
            models.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=always,
                mask=models.Mask(
                    factor_exhale=0.95,
                    η_inhale=0.3,
                ),
                activity=models.Activity(
                    0.51,
                    0.75,
                ),
                virus=models.SARSCoV2(
                    viral_load_in_sputum=defaults['viral_load_in_sputum'],
                    infectious_dose=50.,
                    viable_to_RNA_ratio = 0.5,
                    transmissibility_factor=1.0,
                ),
                expiration=models._ExpirationBase.types['Breathing'],
                host_immunity=0.,
            ),
        ),
        evaporation_factor=0.3,
        short_range=((),),
    )
    assert isinstance(c_model.concentration(10), float)


@pytest.fixture
def simple_conc_model(data_registry):
    interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    return models.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected_populations = (
            models.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=interesting_times,
                mask=models.Mask.types['Type I'],
                activity=models.Activity.types['Seated'],
                virus=models.Virus.types['SARS_CoV_2'],
                expiration=models.Expiration.types['Breathing'],
                host_immunity=0.,
            ),
        ),
        evaporation_factor=0.3,
        short_range=((),),
    )

@pytest.fixture
def simple_conc_model_extended_presence(data_registry):
    ventilation_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    return models.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(ventilation_times, 100),
        infected_populations = (
            models.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.], [20., 20.001]), ),
                mask=models.Mask.types['Type I'],
                activity=models.Activity.types['Seated'],
                virus=models.Virus.types['SARS_CoV_2'],
                expiration=models.Expiration.types['Breathing'],
                host_immunity=0.,
            ),
        ),
        evaporation_factor=0.3,
        short_range=((),),
    )


@pytest.fixture
def dummy_population(simple_conc_model) -> models.Population:
    return models.Population(
        number=1,
        presence=simple_conc_model.infected_populations[0].presence,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )

@pytest.fixture
def diameter_dependent_model(data_registry) -> models.ConcentrationModel:
    always = models.SpecificInterval(((0., 24.), ))
    return models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(25, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.AirChange(always, 5),
        infected_populations = (
            models.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=models.PeriodicInterval(120, 60),
                virus=models.Virus.types['SARS_CoV_2_DELTA'],
                mask=models.Mask.types['No mask'],
                activity=models.Activity.types['Seated'],
                expiration=expiration_distributions(data_registry)['Breathing'].build_model(250_000),
                host_immunity=0.,
            ),
        ),
        evaporation_factor=0.3,
        short_range=((),),
    )

@pytest.mark.parametrize(
    "volume, outside_temp, window_height, opening_length", [
        [np.array([50, 100]), models.PiecewiseConstant((0., 24.), (293.,)), 1., 1.,], # Verify (room) volume vectorization.
        [50, models.PiecewiseConstant((0., 12, 24.),
            (np.array([293., 300.]), np.array([305., 310.]),)), 1., 1.,], # Verify (ventilation) outside_temp vectorization.
        [50, models.PiecewiseConstant((0., 24.), (293.,)),
            np.array([1., 0.5]), 1.], # Verify (ventilation) window_height vectorization.
        [50, models.PiecewiseConstant((0., 24.), (293.,)),
            1., np.array([1., 0.5])], # Verify (ventilation) opening_length vectorization.
    ]
)
def test_diameter_vectorization_window_opening(data_registry, diameter_dependent_model, volume, outside_temp,
                                                window_height, opening_length):
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                            "or virus decay constant can be arrays at the same time."):
        replace(diameter_dependent_model,
            room = models.Room(volume=volume, inside_temp=models.PiecewiseConstant((0., 24.), (293.,)), humidity=0.3),
            ventilation=models.SlidingWindow(
                data_registry=data_registry,
                active=models.PeriodicInterval(period=120, duration=120),
                outside_temp=outside_temp,
                window_height=window_height,
                opening_length=opening_length
            ),
        )


def test_diameter_vectorization_hinged_window(diameter_dependent_model):
    # Verify (ventilation) window_width vectorization.
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                            "or virus decay constant can be arrays at the same time."):
        replace(diameter_dependent_model,
            ventilation = models.HingedWindow(active=models.PeriodicInterval(period=120, duration=120),
                                        outside_temp=models.PiecewiseConstant((0., 24.), (293.,)),
                                        window_height=1.,
                                        opening_length=1.,
                                        window_width=np.array([1., 0.5]))
        )


def test_diameter_vectorization_HEPA_filter(diameter_dependent_model):
    # Verify (ventilation) q_air_mech vectorization.
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                            "or virus decay constant can be arrays at the same time."):
        replace(diameter_dependent_model,
            ventilation = models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                            q_air_mech=np.array([0.5, 1.]))
        )


def test_diameter_vectorization_air_change(diameter_dependent_model):
    # Verify (ventilation) air_exch vectorization.
    with pytest.raises(ValueError, match="If the diameter is an array, none of the ventilation parameters "
                                            "or virus decay constant can be arrays at the same time."):
        replace(diameter_dependent_model,
            ventilation = models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                            air_exch=np.array([0.5, 1.]))
        )


@pytest.mark.parametrize(
    "volume, inside_temp, humidity, error_message", [
        [np.array([50, 100]), models.PiecewiseConstant((0., 24.), (293.,)), 0.3,
        "If the diameter is an array, none of the ventilation parameters or virus decay constant "
        "can be arrays at the same time."], # Verify room volume vectorization
        [50, models.PiecewiseConstant((0., 12, 24.), (np.array([293., 300.]), np.array([305., 310.]))), 0.3,
        "If the diameter is an array, none of the ventilation parameters or virus decay constant "
        "can be arrays at the same time."], # Verify room inside_temp vectorization
        [50, models.PiecewiseConstant((0., 24.), (293.,)), np.array([0.3, 0.5]),
        "If the diameter is an array, none of the ventilation parameters or virus decay constant "
        "can be arrays at the same time."], # Verify room humidity vectorization
    ]
)
def test_diameter_vectorization_room(diameter_dependent_model, volume, inside_temp, humidity, error_message):
    with pytest.raises(ValueError, match=error_message):
        replace(diameter_dependent_model,
            room = models.Room(volume=volume, inside_temp=inside_temp, humidity=humidity),
            ventilation = models.HVACMechanical(active=models.SpecificInterval(((0., 24.), )), q_air_mech=100.)
        )

def test_invalid_short_range(simple_conc_model):
    with pytest.raises(ValueError, match="'short_range' must contain exactly one tuple of short-range interactions "
            "for each infected population. Got 1 infected populations and " \
            "2 tuples of short-range interactions."):
        nested_replace(simple_conc_model, {'short_range': ((),())})
    with pytest.raises(ValueError, match="'short_range' must contain exactly one tuple of short-range interactions "
            "for each infected population. Got 1 infected populations and " \
            "0 tuples of short-range interactions."):
        nested_replace(simple_conc_model, {'short_range': ()})

@pytest.mark.parametrize(
    "time, expected_last_state_change", [
        [-15., 0.],  # Out of range goes to the first state.
        [0., 0.],
        [0.5, 0.0],
        [0.51, 0.5],
        [1., 0.5],
        [1.05, 1.],
        [1.1, 1.],
        [1.11, 1.1],
        [2., 1.1],
        [2.1, 2],
        [3., 2],
        [15., 3.],  # Out of range goes to the last state.
    ]
)
def test_last_state_change_time(
        simple_conc_model: models.ConcentrationModel,
        time,
        expected_last_state_change,
):
    assert simple_conc_model.last_state_change(float(time)) == expected_last_state_change


def test_integrated_concentration(simple_conc_model):
    c1 = simple_conc_model.integrated_concentration(0, 2)
    c2 = simple_conc_model.integrated_concentration(0, 1)
    c3 = simple_conc_model.integrated_concentration(1, 2)
    assert c1 != 0
    npt.assert_almost_equal(c1, c2 + c3, decimal=15)


# The expected numbers were obtained via the quad integration of the
# normed_time_integrated_concentration_addition_by_population method with 0 (start) and 2 (stop) as limits.
@pytest.mark.parametrize([
    "known_min_background_concentration",
    "expected_normed_time_integrated_concentration_addition_by_population"],
    [
        [0.0, 0.00018533333708996207],
        [240.0, 48.000185340695275],
        [440.0, 88.00018534069527],
        [600., 120.00018534069527],
        [1000., 200.0001853407918],
    ]
)
def test_normed_time_integrated_concentration_addition_by_population_with_background_concentration(
    data_registry: DataRegistry,
    simple_conc_model: models.ConcentrationModel,
    dummy_population: models.Population,
    known_min_background_concentration: float,
    expected_normed_time_integrated_concentration_addition_by_population: float):

    known_normalization_factor = 10.

    known_conc_model = KnownConcentrationModelBase(
        data_registry,
        room = simple_conc_model.room,
        ventilation = simple_conc_model.ventilation,
        known_populations = (dummy_population,),
        known_removal_rate = 100.,
        known_min_background_concentration = known_min_background_concentration,
        known_normalization_factor = known_normalization_factor,
    )
    normed_int_conc_with_normed_background = known_conc_model.normed_time_integrated_concentration_addition_by_population(0, 2)+(2-0)*known_min_background_concentration/known_normalization_factor
    npt.assert_almost_equal(normed_int_conc_with_normed_background, expected_normed_time_integrated_concentration_addition_by_population)

    # Dynamic infected
    known_conc_model_two_pop = nested_replace(known_conc_model, {"known_populations": (dummy_population,)*2})
    normed_int_conc_no_normed_background = known_conc_model_two_pop.normed_time_integrated_concentration_addition_by_population(0, 2)
    expected_normed_int_conc_addition_one_pop = expected_normed_time_integrated_concentration_addition_by_population-(2-0)*known_min_background_concentration/known_normalization_factor
    npt.assert_almost_equal(np.sum(normed_int_conc_no_normed_background), 2*expected_normed_int_conc_addition_one_pop)


# The expected numbers were obtained via the quad integration of the
# normed_time_integrated_concentration_addition_by_population method with 0 (start) and 2 (stop) as limits.
@pytest.mark.parametrize([
    "known_removal_rate",
    "known_min_background_concentration",
    "known_normalization_factor",
    "expected_normed_time_integrated_concentration"],
    [
        [np.array([[0.25, 10]]), np.array([[0.0, 0.0]]), np.array([[10., 10.]]), np.array([[0.012161005755130391, 0.0017333437605308818]])],
        [np.array([[100, 100]]), np.array([[0, 240.0]]), np.array([[10., 10.]]), np.array([[0.00018533333708996207, 48.000185340695275]])],
        [np.array([[100, 100]]), np.array([[440.0, 440.0]]), np.array([[10., 20.]]), np.array([[88.00018534069527, 44.000185340695275]])],
        [np.array([[10., 100]]), np.array([[600., 800.]]), 10., np.array([[120.00173334473946, 160.0001853406953]])],
        [np.array([[50., 100]]), np.array([[1000.,1100.]]), np.array([[10., 20.]]), np.array([[200.00036800764332, 110.00018534069527]])],
    ]
)
def test_normed_time_integrated_concentration_addition_by_population_vectorization(
    data_registry: DataRegistry,
    simple_conc_model: models.ConcentrationModel,
    dummy_population: models.Population,
    known_removal_rate: float,
    known_min_background_concentration: float,
    known_normalization_factor: float,
    expected_normed_time_integrated_concentration: float):

    known_conc_model = KnownConcentrationModelBase(
        data_registry = data_registry,
        room = simple_conc_model.room,
        ventilation = simple_conc_model.ventilation,
        known_populations = (dummy_population,),
        known_removal_rate = known_removal_rate,
        known_min_background_concentration = known_min_background_concentration,
        known_normalization_factor = known_normalization_factor)

    normed_integrated_concentration = known_conc_model.normed_time_integrated_concentration_addition_by_population(0, 2)
    integrated_concentration = known_conc_model.integrated_concentration(0, 2)

    assert isinstance(normed_integrated_concentration, np.ndarray)
    assert normed_integrated_concentration.shape == (1, 2)
    npt.assert_almost_equal(normed_integrated_concentration+(2-0)*known_min_background_concentration/known_normalization_factor, expected_normed_time_integrated_concentration)
    npt.assert_almost_equal(integrated_concentration, np.mean(expected_normed_time_integrated_concentration*known_normalization_factor)) # type: ignore

    # Dynamic infected
    known_conc_model_four_pop = nested_replace(known_conc_model, {"known_populations": (dummy_population,)*4})
    integrated_concentration_four_pop = known_conc_model_four_pop.integrated_concentration(0, 2)
    expected_integrated_concentration_four_pop = np.mean( # type: ignore
        4*(expected_normed_time_integrated_concentration*known_normalization_factor)           # min background concentration (integrated over [0,2]) added four times here
        - 3*(2-0)*known_min_background_concentration                                           # and hence subtracted three times here
    )
    npt.assert_allclose(integrated_concentration_four_pop, expected_integrated_concentration_four_pop, rtol=1e-5)



@pytest.mark.parametrize([
    "known_removal_rate",
    "known_min_background_concentration",
    "expected_concentration"],
    [
        [0., 240., 240. + 0.5/75],
        [0.0001, 240.0, 240. + 0.5/75],
        [1e-6, 240.0, 240 + 0.5/75],
        [0., np.array([240., 240.]), np.array([240. + 0.5/75, 240. + 0.5/75])],
        [np.array([0., 1e-6]), np.array([240., 240.]), np.array([240. + 0.5/75, 240. + 0.5/75])],
        [np.array([0, 0.0001, 1e-6]), np.array([240., 240., 240.]), np.array([240. + 0.5/75, 240. + 0.5/75, 240. + 0.5/75])],
    ]
)
def test_zero_ventilation_rate(
    data_registry: DataRegistry,
    simple_conc_model: models.ConcentrationModel,
    dummy_population: models.Population,
    known_removal_rate: float,
    known_min_background_concentration: float,
    expected_concentration: float):

    known_conc_model = KnownConcentrationModelBase(
        data_registry = data_registry,
        room = simple_conc_model.room,
        ventilation = simple_conc_model.ventilation,
        known_populations = (dummy_population,),
        known_removal_rate = known_removal_rate,
        known_normalization_factor=1.,
        known_min_background_concentration = known_min_background_concentration)

    concentration = known_conc_model.concentration(1)
    assert concentration == pytest.approx(expected_concentration, abs=1e-6)

    # Dynamic infected
    known_conc_model_with_two_dummy_populations = nested_replace(known_conc_model, {"known_populations": (dummy_population, dummy_population)})
    concentration_two_pop = known_conc_model_with_two_dummy_populations.concentration(1)
    expected_concentration_two_pop = 2*expected_concentration - known_min_background_concentration
    npt.assert_allclose(concentration_two_pop, expected_concentration_two_pop, rtol=1e-5)

@pytest.mark.parametrize("time", [3.1,10])
def test_concentration_limit_last_state_change(simple_conc_model, time):
    npt.assert_almost_equal(simple_conc_model._normed_concentration_addition_limit_by_population(time), simple_conc_model.min_background_concentration()/simple_conc_model.normalization_factor())

@pytest.mark.parametrize([
    "start",
    "stop"],
    [
        [10, 19],
        [3, 19],
        [0., 19],
        [0., 20],
    ]
)
def test_concentration_after_last_state_change(simple_conc_model, simple_conc_model_extended_presence, start, stop):
    """
    Test that the concentration results for a model with no more presence of emitters  
    equals the concentration results of a model where the emitter will reenter at a later point.
    """
    time = (start+stop)/2
    npt.assert_almost_equal(simple_conc_model.removal_rate(time), simple_conc_model_extended_presence.removal_rate(time))
    npt.assert_almost_equal(simple_conc_model.concentration(time), simple_conc_model_extended_presence.concentration(time))
    npt.assert_almost_equal(simple_conc_model._normed_concentration_addition_by_population(time), simple_conc_model_extended_presence._normed_concentration_addition_by_population(time))
    npt.assert_almost_equal(simple_conc_model.normed_time_integrated_concentration_addition_by_population(start, stop), simple_conc_model_extended_presence.normed_time_integrated_concentration_addition_by_population(start, stop))
    npt.assert_almost_equal(simple_conc_model.integrated_concentration(start, stop), simple_conc_model_extended_presence.integrated_concentration(start, stop))