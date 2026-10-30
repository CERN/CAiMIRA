import pytest

import numpy as np

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions, expiration_distributions, mask_distributions

SAMPLE_SIZE = 10

@pytest.fixture
def dynamic_mc_conc_model(data_registry, baseline_sr_model):
    # all random variables (virus, activity, expiration, mask) MC sampled
    virus = virus_distributions(data_registry)['SARS_CoV_2'].build_model(SAMPLE_SIZE)
    return mc.ConcentrationModel(
        data_registry=data_registry,
        room=mc.Room(volume=75, inside_temp=mc.PiecewiseConstant((0., 24.), (293,))),
        ventilation=mc.AirChange(
            active=mc.SpecificInterval(((0., 24.), )),
            air_exch=30.,
        ),
        infected_populations=(
            mc.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
                virus=virus,
                mask=mask_distributions(data_registry)['Type I'],
                activity=activity_distributions(data_registry)['Seated'],
                expiration=expiration_distributions(data_registry)['Breathing'],
                host_immunity=0.,
            ),
            mc.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
                virus=virus,
                mask=mask_distributions(data_registry)['Type I'],
                activity=activity_distributions(data_registry)['Seated'],
                expiration=expiration_distributions(data_registry)['Breathing'],
                host_immunity=0.,
            ),
        ),
        evaporation_factor=0.3,
        short_range=(
            baseline_sr_model,
            baseline_sr_model,
        ),
    )

def mixed_infected_populations(data_registry, virus):
    # vary which random variables are fixed and which are set deterministically
    return (
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus, 
            mask=mask_distributions(data_registry)['Type I'], # random
            activity=activity_distributions(data_registry)['Seated'], # random
            expiration=expiration_distributions(data_registry)['Breathing'], # random
            host_immunity=0.,
        ),
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus, 
            mask=models.Mask.types['Type I'], # deterministic
            activity=activity_distributions(data_registry)['Seated'],  # random
            expiration=expiration_distributions(data_registry)['Breathing'],  # random
            host_immunity=0.,
        ),
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus, 
            mask=mask_distributions(data_registry)['Type I'], # random
            activity=models.Activity.types['Seated'],  # deterministic
            expiration=expiration_distributions(data_registry)['Breathing'],  # random
            host_immunity=0.,
        ),
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus, 
            mask=mask_distributions(data_registry)['Type I'], # random
            activity=activity_distributions(data_registry)['Seated'],  # random
            expiration=models.Expiration.types['Breathing'],  # deterministic
            host_immunity=0.,
        ),
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus, 
            mask=mask_distributions(data_registry)['Type I'], # random
            activity=models.Activity.types['Seated'], # deterministic
            expiration=models.Expiration.types['Breathing'], # deterministic
            host_immunity=0.,
        ),
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus, 
            mask=models.Mask.types['Type I'], # deterministic
            activity=activity_distributions(data_registry)['Seated'],  # random
            expiration=models.Expiration.types['Breathing'],  # deterministic
            host_immunity=0.,
        ),
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus, 
            mask=models.Mask.types['Type I'], # deterministic
            activity=models.Activity.types['Seated'], # deterministic
            expiration=expiration_distributions(data_registry)['Breathing'], # random
            host_immunity=0.,
        ),
    )

@pytest.fixture
def non_dynamic_mixed_conc_models(data_registry, baseline_sr_model):
    viruses = [
        virus_distributions(data_registry)['SARS_CoV_2'].build_model(SAMPLE_SIZE), # random
        models.Virus.types['SARS_CoV_2'], # deterministic
    ]
    return tuple(
        mc.ConcentrationModel(
            data_registry=data_registry,
            room=mc.Room(
                volume=75,
                inside_temp=mc.PiecewiseConstant(
                    (0.0, 24.0),
                    (293,),
                ),
            ),
            ventilation=mc.AirChange(
                active=mc.SpecificInterval(((0.0, 24.0),)),
                air_exch=30.0,
            ),
            infected_populations=(infected_population,),
            evaporation_factor=0.3,
            short_range=(baseline_sr_model,),
        )
        for virus in viruses
        for infected_population in mixed_infected_populations(
            data_registry=data_registry,
            virus=virus,
        )
    )


@pytest.fixture
def dynamic_mixed_model(data_registry, baseline_sr_model):
    virus = virus_distributions(data_registry)['SARS_CoV_2'].build_model(SAMPLE_SIZE) # random
    virus = models.Virus.types['SARS_CoV_2'] # deterministic
    infected_populations = mixed_infected_populations(data_registry=data_registry, virus=virus)
    return mc.ConcentrationModel(
        data_registry=data_registry,
        room=mc.Room(volume=75, inside_temp=mc.PiecewiseConstant((0., 24.), (293,))),
        ventilation=mc.AirChange(
            active=mc.SpecificInterval(((0., 24.), )),
            air_exch=30.,
        ),
        infected_populations=infected_populations,
        evaporation_factor=0.3,
        short_range=(baseline_sr_model,)*len(infected_populations),
    )

@pytest.fixture
def mc_co2_conc_model(data_registry):
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

def _test_types(model, time, start, stop):
    assert isinstance(model.min_background_concentration(), np.ndarray)
    assert isinstance(model.removal_rate(time), np.ndarray)
    assert isinstance(model._normed_concentration_addition_limit(time), np.ndarray)
    assert isinstance(model._normed_concentration_addition(time), np.ndarray)
    assert isinstance(model.normalization_factor(), np.ndarray)
    assert isinstance(model.concentration_by_population(time), np.ndarray)
    assert isinstance(model.concentration(time), np.ndarray)
    assert isinstance(model.normed_time_integrated_concentration_addition(start,stop), np.ndarray)
    assert isinstance(model.integrated_concentration_by_population(start,stop), np.ndarray)
    assert isinstance(model.integrated_concentration(start,stop), np.ndarray)
    assert model.volume().shape == (1, 1)  # type: ignore


def _test_conc_dimensions(model: models.ConcentrationModel, acceptable_n_samples: list[int], time, start, stop):
    _test_types(model, time, start, stop)
    assert len(model.populations) == len(model.short_range)
    assert isinstance(model.short_range_normalization_factors(), np.ndarray)
    assert model.volume().shape == (1, 1) # type: ignore
    assert model.removal_rate(time).shape in { # type: ignore
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model._normed_concentration_addition_limit(time).shape in { # type: ignore
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model._normed_concentration_addition(time).shape in { # type: ignore
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.normalization_factor().shape in { # type: ignore
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.concentration_by_population(time).shape in { # type: ignore
                (len(model.populations)+1, n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.concentration(time).shape in { # type: ignore
                (n_samples,)
                for n_samples in acceptable_n_samples
            }
    assert model.normed_time_integrated_concentration_addition(start,stop).shape in { # type: ignore
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.integrated_concentration_by_population(start,stop).shape in { # type: ignore
                (len(model.populations)+1, n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.integrated_concentration(start,stop).shape in { # type: ignore
                (n_samples,)
                for n_samples in acceptable_n_samples
            }
    assert model.short_range_normalization_factors().shape in { # type: ignore
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }

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
        acceptable_n_samples=[1],
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
    _test_conc_dimensions(model, 
        acceptable_n_samples=[SAMPLE_SIZE],
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
def test_mixed_non_dynamic_conc_model(
    non_dynamic_mixed_conc_models,
    time: float,
    start: float,
    stop: float,
) -> None:
    for mc_model in non_dynamic_mixed_conc_models:
        model = mc_model.build_model(SAMPLE_SIZE)
        assert len(model.populations) == 1
        _test_conc_dimensions(
            model,
            acceptable_n_samples=[1, SAMPLE_SIZE],
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
def test_probabilistic_dynamic_co2_model(
    mc_co2_conc_model,
    time: float,
    start: float,
    stop: float,
) -> None:
    model = mc_co2_conc_model.build_model(SAMPLE_SIZE)
    _test_types(model, time, start, stop)
    assert len(model.populations) == 2
    assert model.volume().shape == (1, 1) # type: ignore
    assert model.removal_rate(time).shape == (len(model.populations), 1) # type: ignore
    assert model._normed_concentration_addition_limit(time).shape == (len(model.populations), 1) # type: ignore
    assert model._normed_concentration_addition(time).shape == (len(model.populations), 1) # type: ignore
    assert model.normalization_factor().shape == (len(model.populations), SAMPLE_SIZE) # type: ignore
    assert model.concentration_by_population(time).shape == (len(model.populations)+1, SAMPLE_SIZE) # type: ignore
    assert model.concentration(time).shape == (SAMPLE_SIZE,) # type: ignore
    assert model.normed_time_integrated_concentration_addition(start,stop).shape == (len(model.populations), 1) # type: ignore
    assert model.integrated_concentration_by_population(start,stop).shape == (len(model.populations)+1, SAMPLE_SIZE) # type: ignore
    assert model.integrated_concentration(start,stop).shape == (SAMPLE_SIZE,) # type: ignore


@pytest.fixture
def non_dynamic_mixed_exposure_models(data_registry, non_dynamic_mixed_conc_models):
    return (
        mc.ExposureModel(
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
        ) for conc_model in non_dynamic_mixed_conc_models
    )

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


def _test_exposure_dimensions(model: models.ExposureModel, acceptable_n_samples: list[int], time, start, stop):
    assert len(model.infected_populations) == len(model.concentration_model.infected_populations)
    assert len(model.infected_populations) == len(model.concentration_model.short_range)
    assert isinstance(model.long_range_concentration(time), np.ndarray)
    assert isinstance(model.concentration(time), np.ndarray)
    assert isinstance(model._long_range_normed_exposure_between_bounds(start,stop), np.ndarray)
    assert isinstance(model.long_range_deposited_exposure_between_bounds_by_population(start,stop), np.ndarray)
    assert isinstance(model.long_range_deposited_exposure_between_bounds(start,stop), np.ndarray)
    assert isinstance(model.deposited_exposure_between_bounds(start,stop), np.ndarray)
    assert model.long_range_concentration(time).shape in { # type: ignore
                (n_samples,)
                for n_samples in acceptable_n_samples
            }
    assert model.concentration(time).shape == model.long_range_concentration(time).shape # type: ignore
    assert model._long_range_normed_exposure_between_bounds(start,stop).shape in { # type: ignore
                (len(model.infected_populations), n_samples) 
                for n_samples in acceptable_n_samples
            }
    assert model.long_range_deposited_exposure_between_bounds_by_population(start,stop).shape in { # type: ignore
                (len(model.infected_populations)+1, n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.long_range_deposited_exposure_between_bounds(start,stop).shape in { # type: ignore
                (n_samples,)
                for n_samples in acceptable_n_samples
            }
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
def test_probabilistic_dynamic_exposure_model(
    dynamic_mc_exposure_model,
    time: float,
    start: float,
    stop: float,
) -> None:
    model = dynamic_mc_exposure_model.build_model(SAMPLE_SIZE)
    assert len(model.infected_populations) == 2
    _test_exposure_dimensions(model, 
        acceptable_n_samples=[SAMPLE_SIZE],
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
def test_mixed_non_dynamic_exposure_model(
    non_dynamic_mixed_exposure_models,
    time: float,
    start: float,
    stop: float,
) -> None:
    for mc_model in non_dynamic_mixed_exposure_models:
        model = mc_model.build_model(SAMPLE_SIZE)
        assert len(model.infected_populations) == 1
        _test_exposure_dimensions(
            model,
            acceptable_n_samples=[1, SAMPLE_SIZE],
            time=time,
            start=start,
            stop=stop,
        )
        # TODO: move test into _test_exposure_dimensions once the reproduction number is implemented for dynamic occupancy
        assert model.expected_new_cases().shape == model.reproduction_number().shape  # type: ignore


