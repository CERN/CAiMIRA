import pytest

from caimira.apps.calculator import model_generator


@pytest.fixture
def baseline_form_data():
    return model_generator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data, data_registry):
    return model_generator.VirusFormData.from_dict(baseline_form_data, data_registry)


@pytest.fixture
def baseline_form_with_sr(baseline_form_data, data_registry):
    form_data_sr = baseline_form_data
    form_data_sr['short_range_option'] = 'short_range_yes'
    form_data_sr['short_range_interactions'] = '[{"expiration": "Shouting", "start_time": "10:30", "duration": "30"}]'
    form_data_sr['short_range_total_people'] = 5
    return model_generator.VirusFormData.from_dict(form_data_sr, data_registry)