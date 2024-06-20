import pytest

from caimira.calculator.validators.virus import virus_validator


@pytest.fixture
def baseline_form_data():
    return virus_validator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data, data_registry):
    return virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)
