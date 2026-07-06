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
interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )

@pytest.fixture
def infected_dynamic_virus():
    virus_types = ['SARS_CoV_2', 'SARS_CoV_2_ALPHA']
    return [models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types[virus_type],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for virus_type in virus_types]

@pytest.fixture
def infected_dynamic_number():
    return [models.InfectedPopulation(
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
    interesting_times_list = [interesting_times, models.SpecificInterval(([0.5, 1.], [5., 13.]), )]
    return [models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for interesting_times in interesting_times_list]

@pytest.fixture
def infected_dynamic_mask():
    mask_types = ['Type I', 'No mask']
    return [models.InfectedPopulation(
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
    return [models.InfectedPopulation(
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
    return [models.InfectedPopulation(
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
    return [models.InfectedPopulation(
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
    return infected_dynamic_number + infected_dynamic_presence + infected_dynamic_mask + infected_dynamic_activity + infected_dynamic_expiration + infected_dynamic_immunity

@pytest.fixture
def invalid_viruses_conc_model_list(infected_dynamic_virus):
    """
    Invalid list of concentration models because the viruses are different.
    """
    return [mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = infected_population,
        evaporation_factor=0.3,
    ) for infected_population in infected_dynamic_virus]

@pytest.fixture
def invalid_rooms_conc_model_list(all_infected_populations):
    """
    Invalid list of concentration models because the rooms are different.
    """
    return [mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(vol, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = all_infected_populations[0],
        evaporation_factor=0.3,
    ) for vol in [75,100]]

@pytest.fixture
def short_range_models():
    sr_expirations=[models.Expiration.types['Breathing'], models.Expiration.types['Speaking']]
    sr_activities=[models.Activity.types['Seated'], models.Activity.types['Standing']]
    return tuple([mc.ShortRangeModel(
        data_registry=data_registry,
        expiration=sr_expiration,
        activity=sr_activity,
        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
        distance=0.854
        ) for sr_expiration, sr_activity in zip(sr_expirations, sr_activities)])

@pytest.fixture
def valid_conc_model_list(all_infected_populations):
    return [mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = infected_population,
        evaporation_factor=0.3,
        short_range=(),
    ) for infected_population in all_infected_populations]

@pytest.fixture
def valid_conc_model_list_with_short_range(all_infected_populations, short_range_models):
    return [mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = infected_population,
        evaporation_factor=0.3,
        short_range=short_range_models,
    ) for infected_population in all_infected_populations]

def get_exposure_model(concentration_model_list) -> mc.ExposureModel:
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_model_list,
        exposed=mc.Population(
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12), (13, 17.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
        exposed_to_short_range=1,
    )

def test_common_params(valid_conc_model_list, invalid_viruses_conc_model_list, invalid_rooms_conc_model_list):
    """
    Check that an error is raised when initializing an ExposureModel with ConcentrationModels 
    with different viruses and rooms.
    """
    with pytest.raises(ValueError):
        get_exposure_model(invalid_viruses_conc_model_list).build_model(1)
    with pytest.raises(ValueError):
        get_exposure_model(invalid_rooms_conc_model_list).build_model(1)

    valid_model = get_exposure_model(valid_conc_model_list).build_model(1)
    assert all([isinstance(c_model, models.ConcentrationModel) for c_model in valid_model.concentration_model_list])
    assert isinstance(valid_model.virus, models.Virus)
    assert isinstance(valid_model.room, models.Room)

def test_population_state_change_times(valid_conc_model_list):
    expected_state_changes = [0.5, 1., 1.1, 2., 3., 5., 8.5, 12, 13., 17.5]
    model = get_exposure_model(valid_conc_model_list).build_model(1)
    assert model.population_state_change_times() == expected_state_changes

@pytest.mark.parametrize("time", [0., 0.6, 1., 3., 7, 10.5, 10.7, 11, 17.])
def test_sr_model_concentration(time, valid_conc_model_list_with_short_range):
    model = get_exposure_model(valid_conc_model_list_with_short_range).build_model(SAMPLE_SIZE)
    concentration = model.concentration(time)
    assert concentration >= 0
    assert len(model.concentration_model[0].short_range) == 2
    assert np.all(model.concentration_model[0].short_range_normalization_factor() >= 0)

@pytest.mark.parametrize("time", [0., 0.6, 1., 3., 7, 17.])
def test_lr_concentration(time, valid_conc_model_list):
    separate_concentrations = [get_exposure_model(valid_conc_model).build_model(SAMPLE_SIZE).concentration(time) for valid_conc_model in valid_conc_model_list]
    concentration = get_exposure_model(valid_conc_model_list).build_model(SAMPLE_SIZE).concentration(time)
    assert np.allclose(concentration, sum(separate_concentrations))
    assert concentration >= 0

@pytest.mark.parametrize(
        "start, stop",
    [
        [0., 1],
        [0.6, 2],
        [1, 3.],
        [1, 7.], 
        [0, 17.],  
    ],
)
def test_deposited_exposure(start, stop, valid_conc_model_list):
    separate_deposited_exposures = [get_exposure_model(valid_conc_model).build_model(SAMPLE_SIZE).deposited_exposure_between_bounds(start, stop) for valid_conc_model in valid_conc_model_list]
    deposited_exposure = get_exposure_model(valid_conc_model_list).build_model(SAMPLE_SIZE).deposited_exposure_between_bounds(start, stop)
    assert np.allclose(deposited_exposure, sum(separate_deposited_exposures))
    assert deposited_exposure >= 0

def test_exposure_with_shortrange_and_distributions(valid_conc_model_list, short_range_model_list):
    model = get_exposure_model(valid_conc_model_list, short_range_model_list).build_model(SAMPLE_SIZE)
    assert isinstance(model.deposited_exposure(), np.ndarray)
    assert isinstance(model.infection_probability(), np.ndarray)

