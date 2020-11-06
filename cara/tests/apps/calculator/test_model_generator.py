import pytest

from cara.apps.calculator import model_generator
from cara import models
import numpy as np

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
    room = models.Room(75)
    window = models.WindowOpening(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=models.GenevaTemperatures['Dec'],
        cd_b=0.6, window_height=1.6, opening_length=0.6,
    )
    baseline_form.ventilation_type = 'natural'
    baseline_form.windows_open = '10 min / 2h'
    baseline_form.event_type = 'recurrent_event'
    baseline_form.recurrent_event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([window.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


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


def test_key_validation(baseline_form_data):
    baseline_form_data['activity_type'] = 'invalid key'
    with pytest.raises(ValueError):
        model_generator.FormData.from_dict(baseline_form_data)