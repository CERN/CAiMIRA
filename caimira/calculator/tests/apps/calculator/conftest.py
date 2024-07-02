import pytest

from caimira.calculator.validators.virus import virus_validator


@pytest.fixture
def baseline_form_data():
    return virus_validator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data, data_registry):
    return virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


@pytest.fixture
def baseline_form_with_sr(baseline_form_data, data_registry):
    form_data_sr = baseline_form_data
    form_data_sr['short_range_option'] = 'short_range_yes'
    form_data_sr['short_range_interactions'] = '[{"expiration": "Shouting", "start_time": "10:30", "duration": "30"}]'
    form_data_sr['short_range_occupants'] = 5
    return virus_validator.VirusFormData.from_dict(form_data_sr, data_registry)
