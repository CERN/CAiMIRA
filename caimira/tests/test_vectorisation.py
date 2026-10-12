import pytest

import numpy as np

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions, expiration_distributions, mask_distributions

SAMPLE_SIZE = 10

@pytest.fixture
def dynamic_mc_model(data_registry, baseline_sr_model):
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
def non_dynamic_mixed_models(data_registry, baseline_sr_model):
    virus = models.Virus.types['SARS_CoV_2'] # deterministic
    return (
        mc.ConcentrationModel(
            data_registry=data_registry,
            room=mc.Room(volume=75, inside_temp=mc.PiecewiseConstant((0., 24.), (293,))),
            ventilation=mc.AirChange(
                active=mc.SpecificInterval(((0., 24.), )),
                air_exch=30.,
            ),
            infected_populations=(infected_population,),
            evaporation_factor=0.3,
            short_range=(baseline_sr_model,),
        ) for infected_population in mixed_infected_populations(data_registry=data_registry, virus=virus)
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


def _test_dimensions(model: models.ConcetrationModel, acceptable_n_samples: list[int], time, start, stop):
    assert len(model.populations) == len(model.short_range)
    assert isinstance(model.removal_rate(time), np.ndarray)
    assert isinstance(model._normed_concentration_increase_limit(time), np.ndarray)
    assert isinstance(model._normed_concentration_increase(time), np.ndarray)
    assert isinstance(model.normalization_factor(), np.ndarray)
    assert isinstance(model.concentration(time), np.ndarray)
    assert isinstance(model.normed_time_integrated_concentration_increase(start,stop), np.ndarray)
    assert isinstance(model.integrated_concentration(start,stop), np.ndarray)
    assert isinstance(model.short_range_normalization_factors(), np.ndarray)
    assert model.volume().shape == (1, 1) # Not yet implemented as a random variable
    assert model.removal_rate(time).shape in {
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model._normed_concentration_increase_limit(time).shape in {
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model._normed_concentration_increase(time).shape in {
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.normalization_factor().shape in {
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.concentration(time).shape in {
                (len(model.populations)+1, n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.normed_time_integrated_concentration_increase(start,stop).shape in {
                (len(model.populations), n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.integrated_concentration(start,stop).shape in {
                (len(model.populations)+1, n_samples)
                for n_samples in acceptable_n_samples
            }
    assert model.short_range_normalization_factors().shape in {
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
    _test_dimensions(
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
def test_probabilistic_dynamic_model(
    dynamic_mc_model,
    time: float,
    start: float,
    stop: float,
) -> None:
    model = dynamic_mc_model.build_model(SAMPLE_SIZE)
    assert len(model.populations) == 2
    _test_dimensions(model, 
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
def test_mixed_non_dynamic_model(
    non_dynamic_mixed_models,
    time: float,
    start: float,
    stop: float,
) -> None:
    for mc_model in non_dynamic_mixed_models:
        model = mc_model.build_model(SAMPLE_SIZE)
        assert len(model.populations) == 1
        _test_dimensions(
            model,
            acceptable_n_samples=[1, SAMPLE_SIZE],
            time=time,
            start=start,
            stop=stop,
        )
            

# TODO: allow dynamic occupancy where which variables are Monte Carlo samples varies between the populations
# @pytest.mark.parametrize(
#     ("time", "start", "stop"),
#     [
#         (0.0, 0.0, 1.0),
#         (1.0, 0.0, 1.0),
#         (4.0, 1.0, 4.0),
#         (8.0, 4.0, 9.0),
#         (12.0, 8.0, 12.0),
#     ],
# )
# def test_mixed_probabilistic_dynamic_model(
#     dynamic_mixed_model,
#     time: float,
#     start: float,
#     stop: float,
# ) -> None:
#     model = dynamic_mixed_model.build_model(SAMPLE_SIZE)
#     assert len(model.populations) == 7
#     _test_dimensions(
#         model,
#         acceptable_n_samples=[SAMPLE_SIZE],
#         time=time,
#         start=start,
#         stop=stop,
#     )