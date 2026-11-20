import pytest

import numpy as np
from caimira.calculator.models.dataclass_utils import replace, nested_replace
from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions, expiration_distributions, mask_distributions

import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.models import models

SAMPLE_SIZE = 10

@pytest.fixture
def deterministic_properties():
    return {
        "virus": models.Virus.types['SARS_CoV_2'],
        "mask": models.Mask.types['Type I'],
        "activity": models.Activity.types['Seated'],
        "expiration": models.Expiration.types['Breathing'],
    }

@pytest.fixture
def random_properties(data_registry):
    return {
        "virus": virus_distributions(data_registry)['SARS_CoV_2'].build_model(SAMPLE_SIZE), # prebuilt so all infected populations have the exact same virus
        "mask": mask_distributions(data_registry)['Type I'],
        "activity": activity_distributions(data_registry)['Seated'],
        "expiration": expiration_distributions(data_registry)['Breathing'],
    }

@pytest.fixture
def random_infected_population(data_registry, random_properties):
    return mc.InfectedPopulation(
        data_registry=data_registry,
        number=1,
        presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
        virus=random_properties["virus"],
        mask=random_properties["mask"],
        activity=random_properties["activity"],
        expiration=random_properties["expiration"],
        host_immunity=0.,
    )

@pytest.fixture
def random_non_dynamic_concentration_model(data_registry, baseline_sr_model, random_infected_population):
    # all random variables (virus, activity, expiration, mask) MC sampled
    return mc.ConcentrationModel(
        data_registry=data_registry,
        room=mc.Room(volume=75, inside_temp=mc.PiecewiseConstant((0., 24.), (293,))),
        ventilation=mc.AirChange(
            active=mc.SpecificInterval(((0., 24.), )),
            air_exch=30.,
        ),
        infected_populations=(random_infected_population,),
        evaporation_factor=0.3,
        short_range=(baseline_sr_model,),
    )

@pytest.fixture
def dynamic_mc_conc_model(random_non_dynamic_concentration_model, baseline_sr_model, random_infected_population):
    # all random variables (virus, activity, expiration, mask) MC sampled
    n_pop = 2
    return replace(random_non_dynamic_concentration_model, 
        infected_populations=(random_infected_population,)*n_pop,
        short_range=(baseline_sr_model,)*n_pop,
    )

@pytest.fixture
def diameter_dependent_conc_models(random_non_dynamic_concentration_model, deterministic_properties):
    base_random_conc_model = random_non_dynamic_concentration_model.build_model(SAMPLE_SIZE)
    infected = base_random_conc_model.infected_populations[0]
    return [
        replace(base_random_conc_model, infected_populations = (replace(infected, virus=deterministic_properties["virus"]),)),
        replace(base_random_conc_model, infected_populations = (replace(infected, mask=deterministic_properties["mask"]),)),
        replace(base_random_conc_model, infected_populations = (replace(infected, activity=deterministic_properties["activity"]),)),
        replace(base_random_conc_model, infected_populations = (
                                            replace(
                                                infected, 
                                                virus=deterministic_properties["virus"],
                                                mask=deterministic_properties["mask"],
                                            ),
                                        ),
        ),
        replace(base_random_conc_model, infected_populations = (
                                            replace(
                                                infected, 
                                                mask=deterministic_properties["mask"],
                                                activity=deterministic_properties["activity"],
                                            ),
                                        ),
        ),
        replace(base_random_conc_model, infected_populations = (
                                            replace(
                                                infected, 
                                                virus=deterministic_properties["virus"],
                                                activity=deterministic_properties["activity"],
                                            ),
                                        ),
        ),
        replace(base_random_conc_model, infected_populations = (
                                                replace(
                                                    infected, 
                                                    virus=deterministic_properties["virus"],
                                                    mask=deterministic_properties["mask"],
                                                    activity=deterministic_properties["activity"],
                                                ),
                                            ),
            ),
    ]

@pytest.fixture
def dynamic_mc_exposure_model(data_registry, dynamic_mc_conc_model):
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=dynamic_mc_conc_model,
        exposed=mc.Population(
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            mask=mask_distributions(data_registry)['Type I'], # random
            activity=activity_distributions(data_registry)['Seated'], # random
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
        exposed_to_short_range=1,
    )


@pytest.fixture
def mc_co2_conc_model(data_registry) -> mc.CO2ConcentrationModel:
    return mc.CO2ConcentrationModel(
        data_registry=data_registry,
        room=mc.Room(200, mc.PiecewiseConstant((0., 24.), (293,))),
        ventilation=mc.AirChange(mc.PeriodicInterval(period=120, duration=120), 0.25),
        CO2_emitting_populations=(
            mc.SimplePopulation(
                number=5,
                presence=mc.SpecificInterval((((0., 4.), (20., 20.1)))),
                activity=activity_distributions(data_registry)['Seated'],
            ),
            mc.SimplePopulation(
                number=5,
                presence=mc.SpecificInterval((((0., 4.), (20., 20.1)))),
                activity=activity_distributions(data_registry)['Seated'],
            ),
        ),
    )

def get_exposure_model(data_registry, conc_model):
    return mc.ExposureModel(
            data_registry=data_registry,
            concentration_model=conc_model,
            exposed=mc.Population(
                number=1,
                presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
                mask=mask_distributions(data_registry)['Type I'], # random
                activity=activity_distributions(data_registry)['Seated'], # random
                host_immunity=0.,
            ),
            geographical_data=models.Cases(),
            exposed_to_short_range=1,
    )

def _test_conc_model_types(model: models._ConcentrationModelBase, time, start, stop):
    assert isinstance(model.min_background_concentration(), float)
    assert isinstance(model.removal_rate(time), np.ndarray)
    assert isinstance(model._normed_concentration_addition_limit_by_population(time), np.ndarray)
    assert isinstance(model._normed_concentration_addition_by_population(time), np.ndarray)
    assert isinstance(model.normalization_factor(), np.ndarray)
    assert isinstance(model.concentration_addition_by_population(time), np.ndarray)
    assert isinstance(model.concentration(time), float)
    assert isinstance(model.normed_time_integrated_concentration_addition_by_population(start,stop), np.ndarray)
    assert isinstance(model.time_integrated_concentration_addition_by_population(start,stop), np.ndarray)
    assert isinstance(model.time_integrated_concentration(start,stop), float)
    assert model.volume().shape == (1, 1)  # type: ignore


def _test_conc_dimensions(model: models.ConcentrationModel, n_samples: int, time, start, stop):
    _test_conc_model_types(model, time, start, stop)
    assert len(model.populations) == len(model.short_range)
    assert isinstance(model.short_range_normalization_factors(), np.ndarray)
    assert model.volume().shape == (1, 1) # type: ignore

    deterministic_activity_and_virus: bool = not (
        isinstance(model.infected_populations[0].activity.exhalation_rate, np.ndarray) or 
        isinstance(model.infected_populations[0].virus.viral_load_in_sputum, np.ndarray)
    )

    if deterministic_activity_and_virus:
        assert model.short_range_normalization_factors().shape == (len(model.populations), 1)
    else:
        assert model.short_range_normalization_factors().shape == (len(model.populations), n_samples)

    if model.monte_carlo_diameter():
        n_diameters = n_samples
    else:
        n_diameters = 1
    assert model.removal_rate(time).shape == (len(model.populations), n_diameters)
    assert model._normed_concentration_addition_limit_by_population(time).shape == (len(model.populations), n_diameters)
    assert model._normed_concentration_addition_by_population(time).shape == (len(model.populations), n_diameters)
    assert model.normed_time_integrated_concentration_addition_by_population(start,stop).shape == (len(model.populations), n_diameters)

    if deterministic_activity_and_virus and not model.monte_carlo_diameter():
        dim2 = 1
    else:
        dim2 = n_samples
    assert model.normalization_factor().shape == (len(model.populations), dim2)
    assert model.concentration_addition_by_population(time).shape == (len(model.populations), dim2)
    assert model.time_integrated_concentration_addition_by_population(start,stop).shape == (len(model.populations), dim2)

def _test_exposure_dimensions(model: models.ExposureModel, n_samples: int, time, start, stop):
    assert len(model.infected_populations) == len(model.concentration_model.infected_populations)
    assert len(model.infected_populations) == len(model.concentration_model.short_range)
    assert isinstance(model.concentration(time), float)
    assert isinstance(model._long_range_normed_exposure_between_bounds_by_infected_population(start,stop), np.ndarray)
    assert isinstance(model.long_range_deposited_exposure_between_bounds_by_infected_population(start,stop), np.ndarray)
    assert isinstance(model.long_range_deposited_exposure_between_bounds(start,stop), np.ndarray)
    assert isinstance(model.deposited_exposure_between_bounds(start,stop), np.ndarray)

    if model.monte_carlo_diameter():
        assert model._long_range_normed_exposure_between_bounds_by_infected_population(start,stop).shape == (len(model.infected_populations), n_samples) # type: ignore
    else:
        assert model._long_range_normed_exposure_between_bounds_by_infected_population(start,stop).shape == (len(model.infected_populations), 1) # type: ignore
    assert model.long_range_deposited_exposure_between_bounds_by_infected_population(start,stop).shape == (len(model.infected_populations), n_samples) # type: ignore
    assert model.long_range_deposited_exposure_between_bounds(start,stop).shape == (n_samples,) # type: ignore

    assert model.long_range_deposited_exposure_between_bounds(start,stop).shape == model.deposited_exposure_between_bounds(start,stop).shape # type: ignore
    assert model.deposited_exposure_between_bounds(start,stop).shape == model.deposited_exposure().shape # type: ignore
    assert model.deposited_exposure(short_range=True).shape == model.deposited_exposure(short_range=False).shape # type: ignore
    assert model.deposited_exposure().shape == model.individual_infection_probability().shape # type: ignore
    assert model.individual_infection_probability(short_range=True).shape == model.individual_infection_probability(short_range=False).shape # type: ignore
    assert model.expected_new_cases().shape == model.individual_infection_probability().shape # type: ignore
    #assert model.expected_new_cases().shape == model.reproduction_number().shape # type: ignore

@pytest.mark.parametrize(
    ("time", "start", "stop"),
    [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (4.0, 1.0, 4.0),
        (8.0, 4.0, 9.0),
        (12.0, 8.0, 12.0),
    ],
)
def test_deterministic_non_dynamic_model(
    baseline_concentration_model,
    time: float,
    start: float,
    stop: float,
) -> None:
    assert len(baseline_concentration_model.populations) == 1
    _test_conc_dimensions(
        baseline_concentration_model,
        n_samples=1,
        time=time,
        start=start,
        stop=stop,
    )

@pytest.mark.parametrize(
    ("time", "start", "stop"),
    [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (4.0, 1.0, 4.0),
        (8.0, 4.0, 9.0),
        (12.0, 8.0, 12.0),
    ],
)
def test_probabilistic_dynamic_conc_model(
    dynamic_mc_conc_model,
    time: float,
    start: float,
    stop: float,
) -> None:
    model = dynamic_mc_conc_model.build_model(SAMPLE_SIZE)
    assert len(model.populations) == 2
    _test_conc_dimensions(
        model, 
        n_samples=SAMPLE_SIZE,
        time=time,
        start=start,
        stop=stop,
    )

@pytest.mark.parametrize(
    ("time", "start", "stop"),
    [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (4.0, 1.0, 4.0),
        (8.0, 4.0, 9.0),
        (12.0, 8.0, 12.0),
    ],
)
def test_probabilistic_dynamic_exposure_model(
    dynamic_mc_exposure_model,
    time: float,
    start: float,
    stop: float,
) -> None:
    model = dynamic_mc_exposure_model.build_model(SAMPLE_SIZE)
    assert len(model.infected_populations) == 2
    _test_exposure_dimensions(model, 
        n_samples=SAMPLE_SIZE,
        time=time,
        start=start,
        stop=stop,
    )

@pytest.mark.parametrize(
    ("time", "start", "stop"),
    [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (4.0, 1.0, 4.0),
        (8.0, 4.0, 9.0),
        (12.0, 8.0, 12.0),
    ],
)
def test_all_non_dynamic_models(
    data_registry,
    diameter_dependent_conc_models,
    deterministic_properties,
    time: float,
    start: float,
    stop: float,
) -> None:
    """
    Test the dimensions of ConcentrationModel and ExposureModel methods with 
    different combinations of random (monte carlo sampled) and deterministic 
    input values for the infected's virus, mask, activity and expiration.
    """
    for diameter_dependent_model in diameter_dependent_conc_models:
        infected = diameter_dependent_model.infected_populations[0]
        diameter_independent_model = replace(diameter_dependent_model, infected_populations = (replace(infected, expiration=deterministic_properties["expiration"]),))

        for model in [diameter_dependent_model, diameter_independent_model]:
            assert len(model.infected_populations) == 1
            _test_conc_dimensions(model, SAMPLE_SIZE, time, start, stop)

            exposure_model = get_exposure_model(data_registry=data_registry, conc_model=model).build_model(SAMPLE_SIZE)
            assert len(exposure_model.infected_populations) == 1
            _test_exposure_dimensions(
                exposure_model,
                n_samples=SAMPLE_SIZE,
                time=time,
                start=start,
                stop=stop,
            )
            # TODO: move test into _test_exposure_dimensions once the reproduction number is implemented for dynamic occupancy
            assert exposure_model.expected_new_cases().shape == exposure_model.reproduction_number().shape  # type: ignore


@pytest.mark.parametrize(
    ("time", "start", "stop"),
    [
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 1.0),
        (4.0, 1.0, 4.0),
        (8.0, 4.0, 9.0),
        (12.0, 8.0, 12.0),
    ],
)
def test_probabilistic_dynamic_co2_model(
    mc_co2_conc_model,
    time: float,
    start: float,
    stop: float,
) -> None:
    model = mc_co2_conc_model.build_model(SAMPLE_SIZE)
    _test_conc_model_types(model, time, start, stop)
    assert len(model.populations) == 2
    assert model.volume().shape == (1, 1) # type: ignore
    assert model.removal_rate(time).shape == (len(model.populations), 1) # type: ignore
    assert model._normed_concentration_addition_limit_by_population(time).shape == (len(model.populations), 1) # type: ignore
    assert model._normed_concentration_addition_by_population(time).shape == (len(model.populations), 1) # type: ignore
    assert model.normalization_factor().shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model.concentration_addition_by_population(time).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model.normed_time_integrated_concentration_addition_by_population(start,stop).shape == (len(model.populations), 1) # type: ignore
    assert model.time_integrated_concentration_addition_by_population(start,stop).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore


    mc_co2_conc_model_vectorized_removal = replace(
        mc_co2_conc_model, 
        ventilation = models.HingedWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            outside_temp=models.PiecewiseConstant((0., 24.), (293.,)),
            window_height=1.,
            opening_length=1.,
            window_width=np.array([1., 0.5,]*int(SAMPLE_SIZE/2)) # length must equal SAMPLE_SIZE
        ),
    )
    model = mc_co2_conc_model_vectorized_removal.build_model(SAMPLE_SIZE)
    _test_conc_model_types(model, time, start, stop)
    assert len(model.populations) == 2
    assert model.volume().shape == (1, 1) # type: ignore
    assert model.removal_rate(time).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model._normed_concentration_addition_limit_by_population(time).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model._normed_concentration_addition_by_population(time).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model.normalization_factor().shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model.concentration_addition_by_population(time).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model.normed_time_integrated_concentration_addition_by_population(start,stop).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model.time_integrated_concentration_addition_by_population(start,stop).shape == (len(model.populations), SAMPLE_SIZE) # type: ignore

