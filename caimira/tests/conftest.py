from caimira import models
import caimira.data
import caimira.dataclass_utils

import pytest

from caimira.store.data_registry import DataRegistry


@pytest.fixture
def data_registry():
    return DataRegistry()

@pytest.fixture
def baseline_concentration_model(data_registry):
    model = models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0., 24.), )),
            air_exch=30.,
        ),
        infected=models.EmittingPopulation(
            data_registry=data_registry,
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0., 4.), (5., 8.))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            known_individual_emission_rate=970 * 50,
            host_immunity=0.,
            # Superspreading event, where ejection factor is fixed based
            # on Miller et al. (2020) - 50 represents the infectious dose.
        ),
        evaporation_factor=0.3,
    )
    return model


@pytest.fixture
def baseline_sr_model():
    return ()


@pytest.fixture
def baseline_exposure_model(data_registry, baseline_concentration_model, baseline_sr_model):
    return models.ExposureModel(
        data_registry=data_registry,
        concentration_model=baseline_concentration_model,
        short_range=baseline_sr_model,
        exposed=models.Population(
            number=1000,
            presence=baseline_concentration_model.infected.presence,
            activity=baseline_concentration_model.infected.activity,
            mask=baseline_concentration_model.infected.mask,
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


@pytest.fixture
def exposure_model_w_outside_temp_changes(data_registry, baseline_exposure_model: models.ExposureModel):
    exp_model = caimira.dataclass_utils.nested_replace(
        baseline_exposure_model, {
            'concentration_model.ventilation': models.SlidingWindow(
                data_registry=data_registry,
                active=models.PeriodicInterval(2.2 * 60, 1.8 * 60),
                outside_temp=caimira.data.GenevaTemperatures['Jan'],
                window_height=1.6,
                opening_length=0.6,
            )
        })
    return exp_model
