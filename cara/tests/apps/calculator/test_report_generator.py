import pytest

from cara.apps.calculator import model_generator
from cara.apps.calculator import report_generator


@pytest.fixture
def baseline_form_data():
    return model_generator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data):
    return model_generator.FormData.from_dict(baseline_form_data)


def test_generate_report(baseline_form):
    model = baseline_form.build_model()

    report = report_generator.build_report(model, baseline_form)
    assert report != ""
