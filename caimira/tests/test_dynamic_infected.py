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
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types[virus_type],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
            short_range=(),
        ) for virus_type in virus_types]

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
            short_range=(),
        ) for n in range(1, 3)]

@pytest.fixture
def infected_dynamic_presence():
    interesting_times_list = [interesting_times, models.SpecificInterval(([0.5, 1.], [5., 13.]), )]
    return [mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
            short_range=(),
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
            short_range=(),
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
            short_range=(),
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
            short_range=(),
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
            short_range=(),
        ) for i in [0, 0.9]]

@pytest.fixture
def all_lr_infected_populations(infected_dynamic_number, infected_dynamic_presence, infected_dynamic_mask, infected_dynamic_activity, infected_dynamic_expiration, infected_dynamic_immunity):
    return infected_dynamic_number + infected_dynamic_presence + infected_dynamic_mask + infected_dynamic_activity + infected_dynamic_expiration + infected_dynamic_immunity

@pytest.fixture
def invalid_viruses_conc_model_tuple(infected_dynamic_virus):
    """
    Invalid tuple of concentration models because the viruses are different.
    """
    return tuple(mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = infected_population,
        evaporation_factor=0.3,
    ) for infected_population in infected_dynamic_virus)

@pytest.fixture
def invalid_rooms_conc_model_tuple(all_lr_infected_populations):
    """
    Invalid tuple of concentration models because the rooms are different.
    """
    return tuple(mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(vol, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = all_lr_infected_populations[0],
        evaporation_factor=0.3,
    ) for vol in [75,100])

@pytest.fixture
def short_range_models():
    sr_expirations=[models.Expiration.types['Breathing'], models.Expiration.types['Speaking']]
    sr_activities=[models.Activity.types['Seated'], models.Activity.types['Standing']]
    return tuple(mc.ShortRangeModel(
        data_registry=data_registry,
        expiration=sr_expiration,
        activity=sr_activity,
        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
        distance=0.854
        ) for sr_expiration, sr_activity in zip(sr_expirations, sr_activities))

@pytest.fixture
def infected_with_short_range(short_range_models):
    return mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=interesting_times,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
            short_range=short_range_models,
        )

@pytest.fixture
def valid_conc_model_tuple(all_lr_infected_populations):
    return tuple(mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = infected_population,
        evaporation_factor=0.3,
    ) for infected_population in all_lr_infected_populations)

@pytest.fixture
def valid_conc_model_tuple_with_short_range(all_lr_infected_populations, infected_with_short_range):
    return tuple(mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected = infected_population,
        evaporation_factor=0.3,
    ) for infected_population in all_lr_infected_populations+[infected_with_short_range])

def get_exposure_model(concentration_model_tuple) -> mc.ExposureModel:
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_model_tuple,
        exposed=mc.Population(
            number=1,
            presence=models.SpecificInterval(present_times=((8.5, 12), (13, 17.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )

def test_common_params(valid_conc_model_tuple, invalid_viruses_conc_model_tuple, invalid_rooms_conc_model_tuple):
    """
    Check that an error is raised when initializing an ExposureModel with ConcentrationModels 
    with different viruses and rooms.
    """
    with pytest.raises(ValueError):
        get_exposure_model(invalid_viruses_conc_model_tuple).build_model(1)
    with pytest.raises(ValueError):
        get_exposure_model(invalid_rooms_conc_model_tuple).build_model(1)

    valid_model = get_exposure_model(valid_conc_model_tuple).build_model(1)
    assert all([isinstance(c_model, models.ConcentrationModel) for c_model in valid_model.concentration_model])
    assert isinstance(valid_model.virus, models.Virus)
    assert isinstance(valid_model.room, models.Room)

def test_population_state_change_times(valid_conc_model_tuple):
    expected_state_changes = [0.5, 1., 1.1, 2., 3., 5., 8.5, 12, 13., 17.5]
    model = get_exposure_model(valid_conc_model_tuple).build_model(1)
    assert model.population_state_change_times() == expected_state_changes

@pytest.mark.parametrize("time", [0., 0.6, 1., 3., 7, 10.5, 10.7, 11, 17.])
def test_sr_model_concentration(time, valid_conc_model_tuple_with_short_range):
    model = get_exposure_model(valid_conc_model_tuple_with_short_range).build_model(SAMPLE_SIZE)
    concentration = model.concentration(time)
    assert concentration >= 0
    assert isinstance(model.concentration_model[-1].infected.short_range, tuple)
    assert isinstance(model.concentration_model[-1].infected.short_range[0], models.ShortRangeModel)
    assert model.concentration_model[0].infected.short_range == ()
    assert len(model.concentration_model[-1].infected.short_range) == 2
    assert np.all(model.concentration_model[-1].infected.short_range_normalization_factor() >= 0)

@pytest.mark.parametrize("time", [0., 0.6, 1., 3., 7, 17.])
def test_long_range_concentration(time, valid_conc_model_tuple):
    separate_concentrations = [get_exposure_model((valid_conc_model,)).build_model(SAMPLE_SIZE).concentration(time) for valid_conc_model in valid_conc_model_tuple]
    concentration = get_exposure_model(valid_conc_model_tuple).build_model(SAMPLE_SIZE).concentration(time)
    assert np.allclose(concentration, sum(separate_concentrations))
    assert concentration >= 0

@pytest.mark.parametrize(
        "start, stop",
    [
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
def test_long_range_deposited_exposure(start, stop, valid_conc_model_tuple):
    separate_deposited_exposures = [get_exposure_model((valid_conc_model,)).build_model(SAMPLE_SIZE).deposited_exposure_between_bounds(start, stop) for valid_conc_model in valid_conc_model_tuple]
    exp_model = get_exposure_model(valid_conc_model_tuple).build_model(SAMPLE_SIZE)
    deposited_exposure = exp_model.deposited_exposure_between_bounds(start, stop)
    long_range_deposited_exposure = exp_model.long_range_deposited_exposure_between_bounds(start, stop)
    assert np.allclose(deposited_exposure, sum(separate_deposited_exposures))
    assert np.allclose(deposited_exposure, long_range_deposited_exposure) # valid_conc_model_tuple has no short-range interactions
    assert deposited_exposure >= 0

@pytest.mark.parametrize("time", [0., 0.6, 1., 3., 7, 10.5, 10.7, 11, 17.])
def test_sr_model_concentration(time, valid_conc_model_tuple_with_short_range):
    model = get_exposure_model(valid_conc_model_tuple_with_short_range).build_model(SAMPLE_SIZE)
    concentration = model.concentration(time)
    infected = model.concentration_model[0].infected
    expected_infectious_viral_load_in_sputum = (infected.virus.viral_load_in_sputum * infected.fraction_of_infectious_virus())
    assert concentration >= 0
    assert len(model.concentration_model[0].short_range) == 2
    assert np.allclose(model.concentration_model[0].short_range_normalization_factor(), expected_infectious_viral_load_in_sputum * 10**6)

@pytest.mark.parametrize(
        "start, stop",
    [
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
def test_short_range_deposited_exposure(start, stop, valid_conc_model_tuple, valid_conc_model_tuple_with_short_range):
    exp_model_no_sr = get_exposure_model(valid_conc_model_tuple).build_model(SAMPLE_SIZE)
    exp_model_with_sr = get_exposure_model(valid_conc_model_tuple_with_short_range).build_model(SAMPLE_SIZE)
    short_range_deposited_exposure = exp_model_with_sr.deposited_exposure_between_bounds(start, stop)
    long_range_deposited_exposure = exp_model_with_sr.long_range_deposited_exposure_between_bounds(start, stop)
    deposited_exposure_no_sr = exp_model_no_sr.deposited_exposure_between_bounds(start, stop)
    assert np.allclose(deposited_exposure_no_sr, long_range_deposited_exposure)
    assert np.all(short_range_deposited_exposure >= 0)


def test_exposure(valid_conc_model_tuple, valid_conc_model_tuple_with_short_range):
    exp_model_no_sr = get_exposure_model(valid_conc_model_tuple).build_model(SAMPLE_SIZE)
    exp_model_with_sr = get_exposure_model(valid_conc_model_tuple_with_short_range).build_model(SAMPLE_SIZE)
    short_range_deposited_exposure = exp_model_with_sr.deposited_exposure()
    long_range_deposited_exposure = exp_model_no_sr.deposited_exposure()
    assert np.all(long_range_deposited_exposure > 0)
    assert np.all(short_range_deposited_exposure > 0)

def test_p_infection(valid_conc_model_tuple, valid_conc_model_tuple_with_short_range):
    exp_model_no_sr = get_exposure_model(valid_conc_model_tuple).build_model(SAMPLE_SIZE)
    exp_model_with_sr = get_exposure_model(valid_conc_model_tuple_with_short_range).build_model(SAMPLE_SIZE)
    individual_infection_probability_no_sr = exp_model_with_sr.individual_infection_probability()
    individual_infection_probability_with_sr = exp_model_no_sr.individual_infection_probability()
    assert np.all(100 > individual_infection_probability_no_sr > 0)
    assert np.all(100 > individual_infection_probability_with_sr > 0)