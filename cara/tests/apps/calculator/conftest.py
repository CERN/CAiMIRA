import pytest

from cara.apps.calculator import model_generator


@pytest.fixture
def baseline_form_data():
    return model_generator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data):
    return model_generator.FormData.from_dict(baseline_form_data)
