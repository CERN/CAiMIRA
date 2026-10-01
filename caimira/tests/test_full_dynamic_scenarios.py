import pytest
import typing

import numpy as np

import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry
from caimira.calculator.models.monte_carlo.data import (expiration_distributions,
        expiration_BLO_factors,short_range_expiration_distributions,
        short_range_distances,virus_distributions,activity_distributions)

SAMPLE_SIZE = 250_000

@pytest.fixture
def data_registry():
    return DataRegistry()

@pytest.fixture
def mask_exposed_populations():
    return (
        mc.Population(
            identifier="groupA",
            number=5,
            presence=models.SpecificInterval(((8, 12.5), (13.5, 17), )),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ),
        mc.Population(
            identifier="groupB",
            number=5,
            presence=models.SpecificInterval(((8, 12.5), (13.5, 17), )),
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ),
    )

@pytest.fixture
def infected_A(data_registry):
    return mc.InfectedPopulation(
            identifier="groupA",
            data_registry=data_registry,
            number=1,
            presence=models.SpecificInterval(((8, 12.5), (13.5, 17), )),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
    )

@pytest.fixture
def sr_infected_A(data_registry) -> typing.Tuple[mc.ShortRangeModel, ...]:
    return (
        mc.ShortRangeModel(
            data_registry = data_registry,
            exposed_identifier="groupA",
            activity = activity_distributions(data_registry)['Seated'],
            expiration = short_range_expiration_distributions(data_registry)['Speaking'],
            presence = models.SpecificInterval(present_times=((10.75, 11.0),)),
            distance = short_range_distances(data_registry),
        ),
        mc.ShortRangeModel(
            data_registry = data_registry,
            exposed_identifier="groupA",
            activity = activity_distributions(data_registry)['Heavy exercise'],
            expiration = short_range_expiration_distributions(data_registry)['Shouting'],
            presence = models.SpecificInterval(present_times=((11.75, 12.0),)),
            distance = short_range_distances(data_registry),
        ),
        mc.ShortRangeModel(
            data_registry = data_registry,
            exposed_identifier="groupB",
            activity = activity_distributions(data_registry)['Seated'],
            expiration = short_range_expiration_distributions(data_registry)['Breathing'],
            presence = models.SpecificInterval(present_times=((13.75, 14.0),)),
            distance = short_range_distances(data_registry),
        ),
    )

@pytest.fixture
def infected_B(data_registry):
    return mc.InfectedPopulation(
        identifier="groupB",
        data_registry=data_registry,
        number=1,
        presence=models.SpecificInterval(((8, 12.5), (13.5, 17), )),
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Seated'],
        virus=models.Virus.types['SARS_CoV_2'],
        expiration=models.Expiration.types['Breathing'],
        host_immunity=0.,
    )

@pytest.fixture
def sr_infected_B(data_registry) -> typing.Tuple[mc.ShortRangeModel, ...]:
    return (
        mc.ShortRangeModel(
            data_registry = data_registry,
            exposed_identifier="groupA",
            activity = activity_distributions(data_registry)['Seated'],
            expiration = short_range_expiration_distributions(data_registry)['Speaking'],
            presence = models.SpecificInterval(present_times=((9.75, 10.0),)),
            distance = short_range_distances(data_registry),
        ),
        mc.ShortRangeModel(
            data_registry = data_registry,
            exposed_identifier="groupB",
            activity = activity_distributions(data_registry)['Standing'],
            expiration = short_range_expiration_distributions(data_registry)['Speaking'],
            presence = models.SpecificInterval(present_times=((14.75, 15.0),)),
            distance = short_range_distances(data_registry),
        ),
    )

@pytest.fixture
def short_range_models_with_exposed1(data_registry) -> typing.Tuple[mc.ShortRangeModel, ...]:
    return (
        mc.ShortRangeModel(
            data_registry = data_registry,
            exposed_identifier="groupA",
            activity = models.Activity.types['Seated'],
            expiration = short_range_expiration_distributions(data_registry)['Speaking'],
            presence = models.SpecificInterval(present_times=((10.5, 11.0),)),
            distance = 0.854,
        ),
    )

def get_dynamic_mask_exposure_model_group(data_registry, exposed_populations, infected_populations, sr_models):
    concentration_model = mc.ViralConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0., 24.), )),
            air_exch=30.,
        ),
        evaporation_factor=0.3,
        infected_populations=infected_populations,
        short_range=sr_models,
    )
    exposure_models = tuple(
        mc.ExposureModel(
            data_registry=data_registry,
            concentration_model=concentration_model,
            exposed=exposed_population, # TODO: add name
            geographical_data=models.Cases(),
            exposed_to_short_range=exposed_population.number,
        ) for exposed_population in exposed_populations
    )
    return mc.ExposureModelGroup(
            data_registry=data_registry,
            exposure_models = exposure_models,
        )

def test_pi(data_registry, mask_exposed_populations, infected_A, sr_infected_A, infected_B, sr_infected_B):
    exp_model_group = get_dynamic_mask_exposure_model_group(
        data_registry, 
        mask_exposed_populations, 
        (infected_A, infected_B,), 
        (sr_infected_A, sr_infected_B,),
    ).build_model(SAMPLE_SIZE)

    pis = exp_model_group.individual_infection_probability()
    
    assert isinstance(exp_model_group, models.ExposureModelGroup)
    assert len(exp_model_group.exposure_models) == 2
    assert all(isinstance(exp_model, models.ExposureModel) for exp_model in exp_model_group.exposure_models)
    assert len(pis) == len(exp_model_group.exposure_models)
    assert all(0 <= pi.mean() <= 100 for pi in pis)
