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
        geographical_data=(),
    )


@pytest.fixture
def baseline_infected_population_number():
    return models.InfectedPopulation(
        number=models.IntPiecewiseContant(
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
        number=models.IntPiecewiseContant(
            (8, 12, 13, 17), (1, 0, 1)),
        presence=None,
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )

@pytest.mark.parametrize(
    "time",
    [4., 8., 10., 12., 13., 14., 16., 20., 24.],
)
def test_population_number(full_exposure_model: models.ExposureModel,
                           baseline_infected_population_number: models.InfectedPopulation, time: float):

    int_population_number: models.InfectedPopulation = full_exposure_model.concentration_model.infected
    assert isinstance(int_population_number.number, int)
    assert isinstance(int_population_number.presence, models.Interval)

    piecewise_population_number: models.InfectedPopulation = baseline_infected_population_number
    assert isinstance(piecewise_population_number.number,
                      models.IntPiecewiseContant)
    assert piecewise_population_number.presence is None
    
    assert int_population_number.person_present(time) == piecewise_population_number.person_present(time)
    assert int_population_number.people_present(time) == piecewise_population_number.people_present(time)


@pytest.mark.parametrize(
    "time",
    [4., 8., 10., 12., 13., 14., 16., 20., 24.],
)
def test_concentration_model_dynamic_population(full_exposure_model: models.ExposureModel,
                                                baseline_infected_population_number: models.InfectedPopulation,
                                                baseline_exposed_population_number: models.Population,
                                                time: float):

    dynamic_model: models.ExposureModel = dc_utils.nested_replace(
        full_exposure_model,
        {
            'concentration_model.infected': baseline_infected_population_number,
            'exposed': baseline_exposed_population_number,
        }
    )
    assert full_exposure_model.concentration(time) == dynamic_model.concentration(time)
