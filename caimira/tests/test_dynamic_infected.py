import re

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.store.data_registry import DataRegistry

SAMPLE_SIZE = 250000
data_registry = DataRegistry()
interesting_times = models.SpecificInterval(((0.5, 1.), (1.1, 2), (2., 3.), (10., 11.), (13.5, 14.0), (15.5, 16.0),),)

@pytest.fixture
def infected_dynamic_virus():
    virus_types = ['SARS_CoV_2', 'SARS_CoV_2_ALPHA']
    return (mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types[virus_type],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for virus_type in virus_types)

@pytest.fixture
def infected_dynamic_number():
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=n,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for n in range(1, 3)]

@pytest.fixture
def infected_dynamic_presence():
    interesting_times_list = [interesting_times, models.SpecificInterval(((0.5, 1.), (5., 13.)), )]
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for interesting_times in interesting_times_list]

@pytest.fixture
def infected_dynamic_mask():
    mask_types = ['Type I', 'No mask']
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types[mask_type],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for mask_type in mask_types]

@pytest.fixture
def infected_dynamic_activity():
    activity_types = ['Seated', 'Standing']
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types[activity_type],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for activity_type in activity_types]

@pytest.fixture
def infected_dynamic_expiration():
    expiration_types = ['Breathing', 'Speaking']
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types[expiration_type],
            host_immunity=0.,
        ) for expiration_type in expiration_types]

@pytest.fixture
def infected_dynamic_immunity():
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=i,
        ) for i in [0, 0.9]]

@pytest.fixture
def all_infected_populations(infected_dynamic_number, infected_dynamic_presence, infected_dynamic_mask, infected_dynamic_activity, infected_dynamic_expiration, infected_dynamic_immunity):
    return tuple(infected_dynamic_number + infected_dynamic_presence + infected_dynamic_mask + infected_dynamic_activity + infected_dynamic_expiration + infected_dynamic_immunity)

@pytest.fixture
def all_short_range_models():
    return (
        # 2 infected populations in infected_dynamic_number
        (
            mc.ShortRangeModel(
                data_registry=data_registry,
                exposed_identifier="groupA",
                expiration=models.Expiration.types['Breathing'],
                activity=models.Activity.types['Seated'],
                presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                distance=0.854
            ),
            mc.ShortRangeModel(
                data_registry=data_registry,
                exposed_identifier="groupA",
                expiration=models.Expiration.types['Speaking'],
                activity=models.Activity.types['Seated'],
                presence=models.SpecificInterval(present_times=((13.5, 14.0),)),
                distance=0.854
            ),
        ),
        (),
        # 2 infected populations in infected_dynamic_presence
        (),
        (),
        # 2 infected populations in infected_dynamic_mask
        (),
        (),
        # 2 infected populations in infected_dynamic_activity
        (),
        (),
        # 2 infected populations in infected_dynamic_expiration
        (),
        (
            mc.ShortRangeModel(
                data_registry=data_registry,
                exposed_identifier="groupA",
                expiration=models.Expiration.types['Speaking'],
                activity=models.Activity.types['Standing'],
                presence=models.SpecificInterval(present_times=((15.5, 16.0),)),
                distance=0.854
            ),
        ),
        # 2 infected populations in infected_dynamic_immunity
        (),
        (),
        )


def infected_pop(number):
    return mc.InfectedPopulation(
        data_registry=data_registry,
        number=number,
        presence=interesting_times,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Seated'],
        virus=models.Virus.types['SARS_CoV_2'],
        expiration=models.Expiration.types['Breathing'],
        host_immunity=0.,
    )

def get_concentration_model(infected_populations, short_range) -> mc.ViralConcentrationModel:
    return mc.ViralConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        evaporation_factor=0.3,
        infected_populations=infected_populations,
        short_range=short_range,
    )

def get_exposure_model(infected_populations, short_range) -> mc.ExposureModel:
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=get_concentration_model(infected_populations, short_range),
        exposed=mc.Population(
            identifier="groupA",
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12), (13, 17.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )

def test_common_params(infected_dynamic_virus, all_infected_populations, all_short_range_models):
    """
    Check that an error is raised when initializing an ExposureModel with _ViralConcentrationModels 
    with different viruses and rooms.
    """
    with pytest.raises(ValueError):
        get_concentration_model(infected_populations=infected_dynamic_virus, short_range=((),(),),).build_model(1)

    valid_model = get_concentration_model(infected_populations=all_infected_populations, short_range=all_short_range_models).build_model(1)
    assert all([isinstance(c_model, models._ViralConcentrationModel) for c_model in valid_model.single_concentration_models])
    assert isinstance(valid_model.virus, models.Virus)
    assert isinstance(valid_model.room, models.Room)

def test_population_state_change_times(all_infected_populations, all_short_range_models):
    expected_state_changes = [0.5, 1., 1.1, 2., 3., 5., 8.5, 10., 11, 12, 13., 13.5, 14.0, 15.5, 16.0, 17.5]
    model = get_exposure_model(infected_populations=all_infected_populations, short_range=all_short_range_models).build_model(1)
    assert model.population_state_change_times() == expected_state_changes

@pytest.mark.parametrize("time", [0., 0.6, 1., 3., 7, 17.])
def test_long_range_concentration(time, all_infected_populations, all_short_range_models):
    separate_concentration_no_sr = [get_concentration_model(infected_populations=(infected_population,), short_range=((),)).build_model(SAMPLE_SIZE).long_range_concentration(time) for infected_population in all_infected_populations]
    separate_lr_concentrations = [get_concentration_model(infected_populations=(infected_population,), short_range=(short_range_models,)).build_model(SAMPLE_SIZE).long_range_concentration(time) for infected_population, short_range_models in zip(list(all_infected_populations), list(all_short_range_models))]
    concentration_no_sr = get_concentration_model(infected_populations=all_infected_populations, short_range=((),)*len(all_short_range_models)).build_model(SAMPLE_SIZE).concentration(time)
    lr_concentration = get_concentration_model(infected_populations=all_infected_populations, short_range=all_short_range_models).build_model(SAMPLE_SIZE).long_range_concentration(time)
    for model_no_sr, model in zip(separate_concentration_no_sr, separate_lr_concentrations):
        assert np.allclose(model_no_sr, model)
    assert np.allclose(concentration_no_sr, sum(separate_lr_concentrations))
    assert np.allclose(concentration_no_sr, lr_concentration)
    assert lr_concentration >= 0

@pytest.mark.parametrize(
    "start, stop", [
        [0., 1],
        [0.6, 2],
        [1, 3.],
        [1, 7.], 
        [8, 10.],
        [0, 17.],  
        [17, 18.],
        [19, 20.],
    ],
)
def test_deposited_exposure(start, stop, all_infected_populations, all_short_range_models):
    separate_lr_deposited_exposures = [
        get_exposure_model(
            infected_populations=(infected_population,), 
            short_range=((),),
        ).build_model(SAMPLE_SIZE).deposited_exposure_between_bounds(start, stop)
        for infected_population in all_infected_populations
    ]
    exp_model_no_sr = get_exposure_model(
        infected_populations=all_infected_populations, 
        short_range=((),) * len(all_infected_populations),
    ).build_model(SAMPLE_SIZE)
    exp_model_with_sr = get_exposure_model(
        infected_populations=all_infected_populations, 
        short_range=all_short_range_models,
    ).build_model(SAMPLE_SIZE)
    long_range_deposited_exposure0 = exp_model_no_sr.deposited_exposure_between_bounds(start, stop)
    long_range_deposited_exposure1 = exp_model_no_sr.deposited_exposure_between_bounds(start, stop)
    long_range_deposited_exposure2 = exp_model_with_sr.long_range_deposited_exposure_between_bounds(start, stop)
    assert np.allclose(long_range_deposited_exposure0, sum(separate_lr_deposited_exposures))
    assert np.allclose(long_range_deposited_exposure0, long_range_deposited_exposure1) 
    assert np.allclose(long_range_deposited_exposure0, long_range_deposited_exposure2) 
    assert np.all(exp_model_no_sr.deposited_exposure() > 0)
    assert np.all(exp_model_with_sr.deposited_exposure() > 0)
    assert np.all(100 > exp_model_with_sr.individual_infection_probability() > 0)
    assert np.all(100 > exp_model_no_sr.individual_infection_probability() > 0)


@pytest.mark.parametrize(
    "start, stop", [
        [0., 1],
        [0.6, 2],
        [1, 3.],
        [1, 7.], 
        [8, 10.],
        [0, 17.],  
        [17, 18.],
        [19, 20.],
    ],
)
def test_dynamic_exposure(start, stop):
    short_range_model = (mc.ShortRangeModel(
        data_registry=data_registry,
        exposed_identifier="groupA",
        expiration=models.Expiration.types['Breathing'],
        activity=models.Activity.types['Seated'],
        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
        distance=0.854,
        ),
    )
    non_dynamic_exp_model_with_sr = get_exposure_model(
        infected_populations=(infected_pop(2),), 
        short_range=(short_range_model,),
    ).build_model(SAMPLE_SIZE) 
    dynamic_exp_model_with_sr = get_exposure_model(
        infected_populations=(infected_pop(1),infected_pop(1),), 
        short_range=(short_range_model,(),),
    ).build_model(SAMPLE_SIZE) 

    assert np.allclose(
        non_dynamic_exp_model_with_sr.long_range_deposited_exposure_between_bounds(start, stop),
        dynamic_exp_model_with_sr.long_range_deposited_exposure_between_bounds(start, stop)
    )
    assert np.allclose(
        non_dynamic_exp_model_with_sr.deposited_exposure_between_bounds(start, stop),
        dynamic_exp_model_with_sr.deposited_exposure_between_bounds(start, stop)
    )
    assert np.allclose(
            non_dynamic_exp_model_with_sr.deposited_exposure(short_range=False),
            dynamic_exp_model_with_sr.deposited_exposure(short_range=False)
        )
    assert np.allclose(
        non_dynamic_exp_model_with_sr.deposited_exposure(short_range=True),
        dynamic_exp_model_with_sr.deposited_exposure(short_range=True)
    )
    assert np.allclose(
            non_dynamic_exp_model_with_sr.individual_infection_probability(short_range=False),
            dynamic_exp_model_with_sr.individual_infection_probability(short_range=False)
        )
    assert np.allclose(
        non_dynamic_exp_model_with_sr.individual_infection_probability(short_range=True),
        dynamic_exp_model_with_sr.individual_infection_probability(short_range=True)
    )