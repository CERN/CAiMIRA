import re

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass

from caimira.calculator.models.dataclass_utils import nested_replace

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.store.data_registry import DataRegistry

SAMPLE_SIZE = 250000
data_registry = DataRegistry()
interesting_times = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.], [10., 11.]), )

@pytest.fixture
def infected_dynamic_virus():
    virus_types = ['SARS_CoV_2', 'SARS_CoV_2_ALPHA']
    return tuple(mc.InfectedPopulation(
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
    interesting_times_list = [interesting_times, models.SpecificInterval(([0.5, 1.], [5., 13.]), )]
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
def mismated_viruses_conc_model(infected_dynamic_virus):
    """
    Invalid concentration models because the infected populations do not all have the same virus.
    """
    return mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected_populations = infected_dynamic_virus,
        evaporation_factor=0.3,
        short_range=((),)*len(infected_dynamic_virus),
    )

@pytest.fixture
def short_range_models():
    return ( # tuple of 12 = len(all_infected_populations) tuples of ShortRangeModels 
                (
                    mc.ShortRangeModel(
                        data_registry=data_registry,
                        exposed_identifier="groupA",
                        expiration=models.Expiration.types['Breathing'],
                        activity=models.Activity.types['Seated'],
                        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                        distance=0.854
                    ),
                ),
                (
                    mc.ShortRangeModel(
                        data_registry=data_registry,
                        exposed_identifier="groupB",
                        expiration=models.Expiration.types['Speaking'],
                        activity=models.Activity.types['Seated'],
                        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                        distance=0.854
                    ),
                    mc.ShortRangeModel(
                        data_registry=data_registry,
                        exposed_identifier="groupA",
                        expiration=models.Expiration.types['Shouting'],
                        activity=models.Activity.types['Standing'],
                        presence=models.SpecificInterval(present_times=((10.75, 11.0),)),
                        distance=0.854
                    ),
                ),
                (),
                (
                    mc.ShortRangeModel(
                        data_registry=data_registry,
                        exposed_identifier="groupB",
                        expiration=models.Expiration.types['Speaking'],
                        activity=models.Activity.types['Seated'],
                        presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
                        distance=0.854
                    ),
                    mc.ShortRangeModel(
                        data_registry=data_registry,
                        exposed_identifier="groupA",
                        expiration=models.Expiration.types['Breathing'],
                        activity=models.Activity.types['Standing'],
                        presence=models.SpecificInterval(present_times=((11.5, 12.0),)),
                        distance=0.854
                    ),
                ),
                (),
                (),
                (),
                (),
                (),
                (),
                (),
                (),
            )

@pytest.fixture
def dynamic_conc_model(all_infected_populations):
    return mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected_populations = all_infected_populations,
        evaporation_factor=0.3,
        short_range=((),)*len(all_infected_populations),
    )

@pytest.fixture
def separate_conc_models(dynamic_conc_model):
    return (
        nested_replace(
            dynamic_conc_model, {
                "infected_populations": (infected,),
                "short_range": ((),),
            }
        ) for infected in dynamic_conc_model.infected_populations
    )

@pytest.fixture
def dynamic_conc_model_with_short_range(dynamic_conc_model, short_range_models):
    return nested_replace(dynamic_conc_model, {"short_range": short_range_models})

def get_exposure_model(concentration_model) -> mc.ExposureModel:
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_model,
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

def test_common_params(dynamic_conc_model, mismated_viruses_conc_model):
    """
    Check that an error is raised when initializing an ExposureModel with ConcentrationModels 
    with different viruses and rooms.
    """
    with pytest.raises(ValueError):
        mismated_viruses_conc_model.build_model(1)
    valid_model = dynamic_conc_model.build_model(1)
    assert all([isinstance(infected, models.InfectedPopulation) for infected in valid_model.infected_populations])
    assert isinstance(valid_model.virus, models.Virus)
    assert isinstance(valid_model.room, models.Room)

def test_population_state_change_times(dynamic_conc_model):
    expected_state_changes = [0.5, 1., 1.1, 2., 3., 5., 8.5, 10., 11, 12, 13., 17.5]
    model = get_exposure_model(dynamic_conc_model).build_model(1)
    assert model.population_state_change_times() == expected_state_changes

@pytest.mark.parametrize("time", [0., 0.6, 1., 3., 7, 17.])
def test_long_range_concentration(time, dynamic_conc_model, separate_conc_models):
    separate_concentrations = [separate_conc_model.build_model(SAMPLE_SIZE).concentration(time) for separate_conc_model in separate_conc_models]
    concentration = dynamic_conc_model.build_model(SAMPLE_SIZE).concentration(time)
    assert np.all(concentration.shape == separated_conc.shape for separated_conc in separate_concentrations)
    assert np.allclose(concentration, np.vstack(separate_concentrations))
    assert np.allclose(sum(concentration), sum(separate_concentrations))
    assert np.all(concentration >= 0)

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
def test_long_range_deposited_exposure(start, stop, dynamic_conc_model, separate_conc_models):
    separate_deposited_exposures = [get_exposure_model(separate_conc_model).build_model(SAMPLE_SIZE).deposited_exposure_between_bounds(start, stop) for separate_conc_model in separate_conc_models]
    exp_model = get_exposure_model(dynamic_conc_model).build_model(SAMPLE_SIZE)
    deposited_exposure = exp_model.deposited_exposure_between_bounds(start, stop)
    long_range_deposited_exposure = exp_model.long_range_deposited_exposure_between_bounds(start, stop)
    assert np.allclose(deposited_exposure, sum(separate_deposited_exposures))
    assert np.allclose(deposited_exposure, long_range_deposited_exposure) # dynamic_conc_model has no short-range interactions
    assert deposited_exposure >= 0


def test_exposure(dynamic_conc_model, dynamic_conc_model_with_short_range):
    exp_model_no_sr = get_exposure_model(dynamic_conc_model).build_model(SAMPLE_SIZE)
    exp_model_with_sr = get_exposure_model(dynamic_conc_model_with_short_range).build_model(SAMPLE_SIZE)
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
def test_dynamic_exposure(infected_dynamic_number, start, stop):
    short_range_model = (
        mc.ShortRangeModel(
            data_registry=data_registry,
            exposed_identifier="groupA",
            expiration=models.Expiration.types['Breathing'],
            activity=models.Activity.types['Seated'],
            presence=models.SpecificInterval(present_times=((10.5, 11.0),)),
            distance=0.854,
        ),
    )
    conc_model_combined_infected = mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected_populations = (infected_dynamic_number[1],),
        evaporation_factor=0.3,
        short_range=(short_range_model,),
    )

    conc_model_split_infected = mc.ConcentrationModel(
        data_registry=data_registry,
        room = models.Room(75, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation = models.AirChange(interesting_times, 100),
        infected_populations = (infected_dynamic_number[0], infected_dynamic_number[0], ),
        evaporation_factor=0.3,
        short_range=((),short_range_model,),
        )

    non_dynamic_exp_model_with_sr = get_exposure_model(conc_model_combined_infected).build_model(SAMPLE_SIZE) # short-range with just one infected
    dynamic_exp_model_with_sr = get_exposure_model(conc_model_split_infected).build_model(SAMPLE_SIZE) # short-range with just one infected

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