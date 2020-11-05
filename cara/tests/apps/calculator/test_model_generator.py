import pytest

from cara.apps.calculator import model_generator


@pytest.fixture
def baseline_form_data():
    return model_generator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data):
    return model_generator.FormData.from_dict(baseline_form_data)


def test_model_from_dict(baseline_form_data):
    model = model_generator.FormData.from_dict(baseline_form_data)
    # TODO:
    # assert model.ventilation == cara.models.Ventilation()


def test_ventilation(baseline_form):
    ventilation = baseline_form.ventilation()
    # TODO:
    # assert ventilation == cara.models.Ventilation()


def test_present_intervals(baseline_form):
    baseline_form.coffee_duration = 15
    baseline_form.coffee_option = True
    baseline_form.coffee_breaks = 4
    baseline_form.activity_start = 9 * 60
    baseline_form.activity_finish = 17 * 60
    baseline_form.lunch_start = 12 * 60 + 30
    baseline_form.lunch_finish = 13 * 60 + 30
    correct = ((9, 10), (10.25, 12), (12.25, 12.5), (13.5, 14), (14.25, 16), (16.25, 17))
    assert baseline_form.present_interval().present_times == correct
