import pytest

from caimira.calculator.models import models
import caimira.calculator.models.data
import caimira.calculator.models.dataclass_utils
from caimira.calculator.validators.virus import virus_validator
from caimira.calculator.store.data_registry import DataRegistry


@pytest.fixture
def baseline_form_data():
    return virus_validator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data, data_registry):
    return virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


@pytest.fixture
def data_registry():
    return DataRegistry()


@pytest.fixture
def baseline_concentration_model(data_registry):
    model = models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(
            volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
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
    exp_model = caimira.calculator.models.dataclass_utils.nested_replace(
        baseline_exposure_model, {
            'concentration_model.ventilation': models.SlidingWindow(
                data_registry=data_registry,
                active=models.PeriodicInterval(2.2 * 60, 1.8 * 60),
                outside_temp=caimira.calculator.models.data.GenevaTemperatures['Jan'],
                window_height=1.6,
                opening_length=0.6,
            )
        })
    return exp_model


@pytest.fixture
def baseline_form_with_sr(baseline_form_data, data_registry):
    form_data_sr = baseline_form_data
    form_data_sr['short_range_option'] = 'short_range_yes'
    form_data_sr['short_range_interactions'] = '{"group_1": [{"expiration": "Shouting", "start_time": "10:30", "duration": 30}]}'
    form_data_sr['short_range_occupants'] = 5
    return virus_validator.VirusFormData.from_dict(form_data_sr, data_registry)
