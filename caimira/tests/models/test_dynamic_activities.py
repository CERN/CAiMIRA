import numpy as np
import numpy.testing as npt
import pytest

from caimira import models
import caimira.dataclass_utils as dc_utils


@pytest.fixture
def full_exposure_model(data_registry):
    return models.ExposureModel(
        data_registry=data_registry,
        concentration_model=models.ConcentrationModel(
            data_registry=data_registry,
            room=models.Room(volume=100),
            ventilation=models.AirChange(
                active=models.PeriodicInterval(120, 120),
                air_exch=0.25,
            ),
            infected=models.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=models.SpecificInterval(
                    present_times=((8, 12), (13, 17), )),
                mask=models.Mask.types['No mask'],
                activity=models.Activity.types['Seated'],
                expiration=models.Expiration.types['Breathing'],
                virus=models.Virus.types['SARS_CoV_2'],
                host_immunity=0.,
            ),
            evaporation_factor=0.3,
        ),
        short_range=(),
        exposed=models.Population(
            number=10,
            presence=models.SpecificInterval(
                present_times=((8, 12), (13, 17), )),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ),
        geographical_data=(),
    )


@pytest.fixture
def baseline_infected_activity(data_registry):
    seated_activity = models.Activity.types['Seated']
    return models.InfectedPopulation(
        data_registry=data_registry,
        number=1,
        presence=models.SpecificInterval(present_times=((8, 12), (13, 17), )),
        mask=models.Mask.types['No mask'],
        activity=models.ActivityPiecewiseConstant(
            transition_times=(8, 12, 13, 17),
            values=(seated_activity, seated_activity, seated_activity),
        ),
        virus=models.Virus.types['SARS_CoV_2'],
        expiration=models.Expiration.types['Breathing'],
        host_immunity=0.,
    )


@pytest.fixture
def baseline_exposed_activity():
    seated_activity = models.Activity.types['Seated']
    return models.Population(
        number=10,
        presence=models.SpecificInterval(present_times=((8, 12), (13, 17), )),
        mask=models.Mask.types['No mask'],
        activity=models.ActivityPiecewiseConstant(
            transition_times=(8, 12, 13, 17),
            values=(seated_activity, seated_activity, seated_activity),
        ),
        host_immunity=0.,
    )


@pytest.fixture
def dynamic_infected_activity(full_exposure_model, baseline_infected_activity):
    return dc_utils.nested_replace(full_exposure_model,
                                   {'concentration_model.infected': baseline_infected_activity, })


@pytest.fixture
def dynamic_exposed_activity(full_exposure_model, baseline_exposed_activity):
    return dc_utils.nested_replace(full_exposure_model,
                                   {'exposed': baseline_exposed_activity, })


@pytest.fixture
def dynamic_population_activity(full_exposure_model, baseline_infected_activity, baseline_exposed_activity):
    return dc_utils.nested_replace(full_exposure_model, {
        'concentration_model.infected': baseline_infected_activity,
        'exposed': baseline_exposed_activity,
    })


@pytest.mark.parametrize(
    "time",
    [4., 8., 10., 12., 13., 14., 16., 20., 24.],
)
def test_concentration_model_dynamic_activity(full_exposure_model: models.ExposureModel,
                                              dynamic_infected_activity: models.ExposureModel,
                                              time: float):

    assert full_exposure_model.concentration(
        time) == dynamic_infected_activity.concentration(time)
