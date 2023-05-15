import re

import numpy as np
import numpy.testing as npt
import pytest

from caimira import models
import caimira.dataclass_utils as dc_utils

@pytest.fixture
def full_exposure_model():
    return models.ExposureModel(
        concentration_model=models.ConcentrationModel(
            room=models.Room(volume=100),
            ventilation=models.AirChange(
                active=models.PeriodicInterval(120, 120), air_exch=0.25),
            infected=models.InfectedPopulation(
                number=1,
                presence=models.SpecificInterval(((8, 12), (13, 17), )),
                mask=models.Mask.types['No mask'],
                activity=models.Activity.types['Seated'],
                expiration=models.Expiration.types['Breathing'],
                virus=models.Virus.types['SARS_CoV_2'],
                host_immunity=0.
            ),
        ),
        short_range=(),
        exposed=models.Population(
            number=10,
            presence=models.SpecificInterval(((8, 12), (13, 17), )), 
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.
        ),
        geographical_data=models.Cases(
            geographic_population=50_000,
            geographic_cases=52,
            ascertainment_bias=1,
        ),
    )


@pytest.fixture
def baseline_infected_population_number():
    return models.InfectedPopulation(
        number=models.IntPiecewiseConstant(
            (8, 12, 13, 17), (1, 0, 1)),
        presence=None,
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        virus=models.Virus.types['SARS_CoV_2'],
        expiration=models.Expiration.types['Breathing'],
        host_immunity=0.,
    )


@pytest.fixture
def baseline_exposed_population_number():
    return models.Population(
        number=models.IntPiecewiseConstant(
            (8, 12, 13, 17), (10, 0, 10)),
        presence=None,
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )


@pytest.fixture
def dynamic_infected_single_exposure_model(full_exposure_model, baseline_infected_population_number):
    return dc_utils.nested_replace(full_exposure_model,
        {'concentration_model.infected': baseline_infected_population_number, })


@pytest.fixture
def dynamic_exposed_single_exposure_model(full_exposure_model, baseline_exposed_population_number):
    return dc_utils.nested_replace(full_exposure_model,
        {'exposed': baseline_exposed_population_number, })


@pytest.fixture
def dynamic_population_exposure_model(full_exposure_model, baseline_infected_population_number ,baseline_exposed_population_number):
    return dc_utils.nested_replace(full_exposure_model, {
            'concentration_model.infected': baseline_infected_population_number, 
            'exposed': baseline_exposed_population_number,
    })


@pytest.mark.parametrize(
    "time",
    [4., 8., 10., 12., 13., 14., 16., 20., 24.],
)
def test_population_number(full_exposure_model: models.ExposureModel,
                           baseline_infected_population_number: models.InfectedPopulation, time: float):

    int_population_number: models.InfectedPopulation = full_exposure_model.concentration_model.infected
    piecewise_population_number: models.InfectedPopulation = baseline_infected_population_number

    with pytest.raises(
        TypeError,
        match=f'The presence argument must be an "Interval". Got {type(None)}'
    ):
        dc_utils.nested_replace(
            int_population_number, {'presence': None}
        )

    with pytest.raises(
        TypeError,
        match="The presence argument must be None for a IntPiecewiseConstant number"
    ):
        dc_utils.nested_replace(
            piecewise_population_number, {'presence': models.SpecificInterval(((8, 12), ))}
        )
    
    assert int_population_number.person_present(time) == piecewise_population_number.person_present(time)
    assert int_population_number.people_present(time) == piecewise_population_number.people_present(time)


@pytest.mark.parametrize(
    "time",
    [4., 8., 10., 12., 13., 14., 16., 20., 24.],
)
def test_concentration_model_dynamic_population(full_exposure_model: models.ExposureModel,
                                                dynamic_infected_single_exposure_model: models.ExposureModel,
                                                time: float):

    assert full_exposure_model.concentration(time) == dynamic_infected_single_exposure_model.concentration(time)


@pytest.mark.parametrize("number_of_infected",[1, 2, 3, 4, 5])
@pytest.mark.parametrize("time",[9., 12.5, 16.])
def test_linearity_with_number_of_infected(full_exposure_model: models.ExposureModel,
                        dynamic_infected_single_exposure_model: models.ExposureModel,
                        time: float,
                        number_of_infected: int):
    
    
    static_multiple_exposure_model: models.ExposureModel = dc_utils.nested_replace(
        full_exposure_model,
        {
            'concentration_model.infected.number': number_of_infected,
        }
    )

    npt.assert_almost_equal(static_multiple_exposure_model.concentration(time), dynamic_infected_single_exposure_model.concentration(time) * number_of_infected)
    npt.assert_almost_equal(static_multiple_exposure_model.deposited_exposure(), dynamic_infected_single_exposure_model.deposited_exposure() * number_of_infected)


@pytest.mark.parametrize(
    "time", (8., 9., 10., 11., 12., 13., 14.),
)
def test_dynamic_dose(full_exposure_model, time):

    dynamic_infected: models.ExposureModel = dc_utils.nested_replace(
        full_exposure_model,
        {
            'concentration_model.infected': models.InfectedPopulation(
                number=models.IntPiecewiseConstant(
                    (8, 10, 12, 13, 17), (1, 2, 0, 3)),
                presence=None,
                mask=models.Mask.types['No mask'],
                activity=models.Activity.types['Seated'],
                virus=models.Virus.types['SARS_CoV_2'],
                expiration=models.Expiration.types['Breathing'],
                host_immunity=0.,
            ),
        }
    )

    single_infected: models.ExposureModel = dc_utils.nested_replace(
        full_exposure_model,
        {
            'concentration_model.infected.number': 1,
            'concentration_model.infected.presence': models.SpecificInterval(((8, 10), )),
        }
    )

    two_infected: models.ExposureModel = dc_utils.nested_replace(
        full_exposure_model,
        {
            'concentration_model.infected.number': 2,
            'concentration_model.infected.presence': models.SpecificInterval(((10, 12), )),
        }
    )

    three_infected: models.ExposureModel = dc_utils.nested_replace(
        full_exposure_model,
        {
            'concentration_model.infected.number': 3,
            'concentration_model.infected.presence': models.SpecificInterval(((13, 17), )),
        }
    )

    dynamic_concentration = dynamic_infected.concentration(time)
    dynamic_exposure = dynamic_infected.deposited_exposure()

    static_concentration, static_exposure = zip(*[(model.concentration(time), model.deposited_exposure()) 
                                              for model in (single_infected, two_infected, three_infected)])

    npt.assert_almost_equal(dynamic_concentration, np.sum(static_concentration))
    npt.assert_almost_equal(dynamic_exposure, np.sum(static_exposure))


def test_dynamic_total_probability_rule(
        full_exposure_model: models.ExposureModel,
        dynamic_infected_single_exposure_model: models.ExposureModel,
        dynamic_exposed_single_exposure_model: models.ExposureModel,
        dynamic_population_exposure_model: models.ExposureModel):

    full_model_total_prob_rule = full_exposure_model.total_probability_rule()
    npt.assert_almost_equal(full_model_total_prob_rule,
                            dynamic_population_exposure_model.dynamic_total_probability_rule())
    
    npt.assert_almost_equal(full_model_total_prob_rule,
        dynamic_infected_single_exposure_model.dynamic_total_probability_rule())
    
    npt.assert_almost_equal(full_model_total_prob_rule,
                            dynamic_exposed_single_exposure_model.dynamic_total_probability_rule())
    