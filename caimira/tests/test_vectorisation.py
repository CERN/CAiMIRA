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
    model = mc.ConcentrationModel(
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
    return model

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
def non_dynamic_mixed_model_tuple(data_registry, baseline_sr_model):
    virus = models.Virus.types['SARS_CoV_2'] # deterministic
    return (mc.ConcentrationModel(
        data_registry=data_registry,
        room=mc.Room(volume=75, inside_temp=mc.PiecewiseConstant((0., 24.), (293,))),
        ventilation=mc.AirChange(
            active=mc.SpecificInterval(((0., 24.), )),
            air_exch=30.,
        ),
        infected_populations=(infected_population,),
        evaporation_factor=0.3,
        short_range=(baseline_sr_model,),
    ) for infected_population in mixed_infected_populations(data_registry=data_registry, virus=virus))


@pytest.fixture
def dynamic_mixed_model(data_registry, baseline_sr_model):
    virus = virus_distributions(data_registry)['SARS_CoV_2'].build_model(SAMPLE_SIZE) # random
    infected_populations = mixed_infected_populations(data_registry=data_registry, virus=virus)
    model = mc.ConcentrationModel(
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
    return model

def test_deterministic_non_dynamic_model(baseline_concentration_model):
    model = baseline_concentration_model
    assert len(model.populations) == 1
    assert len(model.populations) == len(model.short_range)
    assert isinstance(model.removal_rate(10), np.ndarray)
    assert isinstance(model._normed_concentration_increase(10), np.ndarray)
    assert isinstance(model._normed_concentration_increase_limit(10), np.ndarray)
    assert isinstance(model.normalization_factor(), np.ndarray)
    assert isinstance(model.concentration(10), np.ndarray)
    assert isinstance(model.short_range_normalization_factors(), np.ndarray)
    assert model.removal_rate(10).shape == (len(model.populations), 1)
    assert model._normed_concentration_increase_limit(10).shape == (len(model.populations), 1)
    assert model._normed_concentration_increase(10).shape == (len(model.populations), 1)
    assert model.normalization_factor().shape == (len(model.populations), 1)
    assert model.concentration(10).shape == (len(model.populations), 1)
    assert model.short_range_normalization_factors().shape == (len(model.populations), 1)

def test_probabilistic_dynamic_model(dynamic_mc_model):
    model = dynamic_mc_model.build_model(SAMPLE_SIZE)
    assert len(model.populations) == 2
    assert len(model.populations) == len(model.short_range)
    assert isinstance(model.removal_rate(10), np.ndarray)
    assert isinstance(model._normed_concentration_increase_limit(10), np.ndarray)
    assert isinstance(model._normed_concentration_increase(10), np.ndarray)
    assert isinstance(model.normalization_factor(), np.ndarray)
    assert isinstance(model.concentration(10), np.ndarray)
    assert isinstance(model.short_range_normalization_factors(), np.ndarray)
    assert model.removal_rate(10).shape == (len(model.populations), SAMPLE_SIZE)
    assert model._normed_concentration_increase_limit(10).shape == (len(model.populations), SAMPLE_SIZE)
    assert model._normed_concentration_increase(10).shape == (len(model.populations), SAMPLE_SIZE)
    assert model.normalization_factor().shape == (len(model.populations), SAMPLE_SIZE)
    assert model.concentration(10).shape == (len(model.populations), SAMPLE_SIZE)
    assert model.short_range_normalization_factors().shape == (len(model.populations), SAMPLE_SIZE)

def test_mixed_non_dynamic_model(non_dynamic_mixed_model_tuple):
    for mc_model in non_dynamic_mixed_model_tuple:
        model = mc_model.build_model(SAMPLE_SIZE)
        assert len(model.populations) == 1
        assert len(model.populations) == len(model.short_range)
        assert isinstance(model.removal_rate(10), np.ndarray)
        assert isinstance(model._normed_concentration_increase_limit(10), np.ndarray)
        assert isinstance(model._normed_concentration_increase(10), np.ndarray)
        assert isinstance(model.normalization_factor(), np.ndarray)
        assert isinstance(model.concentration(10), np.ndarray)
        assert isinstance(model.short_range_normalization_factors(), np.ndarray)
        assert model.removal_rate(10).shape in {
            (len(model.populations), SAMPLE_SIZE),
            (len(model.populations), 1)
        }
        assert model._normed_concentration_increase_limit(10).shape in {
            (len(model.populations), SAMPLE_SIZE),
            (len(model.populations), 1)
        }
        assert model._normed_concentration_increase(10).shape in {
            (len(model.populations), SAMPLE_SIZE),
            (len(model.populations), 1)
        }
        assert model.normalization_factor().shape in {
            (len(model.populations), SAMPLE_SIZE),
            (len(model.populations), 1)
        }
        assert model.concentration(10).shape in {
            (len(model.populations), SAMPLE_SIZE),
            (len(model.populations), 1)
        }
        assert model.short_range_normalization_factors().shape in {
            (len(model.populations), SAMPLE_SIZE),
            (len(model.populations), 1)
        }

# TODO(?) allow dynamic occupancy where some populations have MC samples properties and others have deterministic properties
# However, this does not really seem nececary
# def test_mixed_probabilistic_dynamic_model(dynamic_mixed_model):
#     model = dynamic_mixed_model.build_model(SAMPLE_SIZE)
#     assert len(model.populations) == 7
#     assert len(model.populations) == len(model.short_range)
#     assert isinstance(model.removal_rate(10), np.ndarray)
#     assert isinstance(model._normed_concentration_increase_limit(10), np.ndarray)
#     assert isinstance(model._normed_concentration_increase(10), np.ndarray)
#     assert isinstance(model.normalization_factor(), np.ndarray)
#     assert isinstance(model.concentration(10), np.ndarray)
#     assert isinstance(model.short_range_normalization_factors(), np.ndarray)
#     assert model.removal_rate(10).shape == (len(model.populations), SAMPLE_SIZE)
#     assert model._normed_concentration_increase_limit(10).shape == (len(model.populations), SAMPLE_SIZE)
#     assert model._normed_concentration_increase(10).shape == (len(model.populations), SAMPLE_SIZE)
#     assert model.normalization_factor().shape == (len(model.populations), SAMPLE_SIZE)
#     assert model.concentration(10).shape == (len(model.populations), SAMPLE_SIZE)
#     assert model.short_range_normalization_factors().shape == (len(model.populations), SAMPLE_SIZE)