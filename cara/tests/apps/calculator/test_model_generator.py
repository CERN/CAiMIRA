import pytest

from cara.apps.calculator import model_generator
from cara import models
from cara import data
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


def test_blend_expiration():
    blend = {'Breathing': 2, 'Talking': 1}
    r = model_generator.build_expiration(blend)
    expected = models.Expiration(
        (0.13466666666666668, 0.02866666666666667, 0.004333333333333334, 0.005)
    )
    assert r == expected


def test_ventilation_window(baseline_form):
    room = models.Room(75)
    window = models.WindowOpening(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=data.GenevaTemperatures['Dec'],
        cd_b=0.6, window_height=1.6, opening_length=0.6,
    )
    baseline_form.ventilation_type = 'natural'
    baseline_form.windows_open = 'interval'
    baseline_form.event_type = 'recurrent_event'
    baseline_form.recurrent_event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([window.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_mechanical(baseline_form):
    room = models.Room(75)
    mech = models.HVACMechanical(
        active=models.PeriodicInterval(period=120, duration=120),
        q_air_mech=500.,
    )
    baseline_form.ventilation_type = 'mechanical'
    baseline_form.mechanical_ventilation_type = 'mechanical'
    baseline_form.air_supply = 500.

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([mech.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_airchanges(baseline_form):
    room = models.Room(75)
    airchange = models.AirChange(
        active=models.PeriodicInterval(period=120, duration=120),
        air_exch=3.,
    )
    baseline_form.ventilation_type = 'mechanical'
    baseline_form.mechanical_ventilation_type = 'air_changes'
    baseline_form.air_changes = 3.

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([airchange.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_window_hepa(baseline_form):
    room = models.Room(75)
    window = models.WindowOpening(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=data.GenevaTemperatures['Dec'],
        cd_b=0.6, window_height=1.6, opening_length=0.6,
    )
    hepa = models.HEPAFilter(
        active=models.PeriodicInterval(period=120, duration=120),
        q_air_mech=250.,
    )
    ventilation = models.MultipleVentilation((window,hepa))

    baseline_form.ventilation_type = 'natural'
    baseline_form.windows_open = 'interval'
    baseline_form.event_type = 'recurrent_event'
    baseline_form.recurrent_event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6
    baseline_form.hepa_option = True

    ts = np.linspace(9, 17, 100)
    np.testing.assert_allclose([ventilation.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_infected_present_intervals(baseline_form):
    baseline_form.coffee_duration = 15
    baseline_form.coffee_breaks = 2
    baseline_form.activity_start = 9 * 60
    baseline_form.activity_finish = 17 * 60
    baseline_form.lunch_start = 12 * 60 + 30
    baseline_form.lunch_finish = 13 * 60 + 30
    baseline_form.infected_start = 10 * 60
    baseline_form.infected_finish = 15 * 60
    correct = ((10, 10+37/60), (10+52/60, 12.5), (13.5, 15.0))
    assert baseline_form.infected_present_interval().present_times == correct


def test_exposed_present_intervals(baseline_form):
    baseline_form.coffee_duration = 15
    baseline_form.coffee_breaks = 2
    baseline_form.activity_start = 9 * 60
    baseline_form.activity_finish = 17 * 60
    baseline_form.lunch_start = 12 * 60 + 30
    baseline_form.lunch_finish = 13 * 60 + 30
    baseline_form.infected_start = 10 * 60
    baseline_form.infected_finish = 15 * 60
    correct = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 15+7/60), (15+22/60, 17.0))
    assert baseline_form.exposed_present_interval().present_times == correct


def test_coffee_lunch_breaks(baseline_form):
    baseline_form.coffee_duration = 30
    baseline_form.coffee_breaks = 4
    baseline_form.activity_start = 9 * 60
    baseline_form.activity_finish = 18 * 60
    baseline_form.lunch_start = 12 * 60 + 30
    baseline_form.lunch_finish = 13 * 60 + 30
    correct = ((9, 9+50/60), (10+20/60, 11+10/60), (11+40/60, 12+30/60),
               (13+30/60, 14+40/60), (15+10/60, 16+20/60), (16+50/60, 18))
    np.testing.assert_allclose(baseline_form.exposed_present_interval().present_times, correct, rtol=1e-14)


def test_coffee_lunch_breaks_unbalance(baseline_form):
    baseline_form.coffee_duration = 30
    baseline_form.coffee_breaks = 2
    baseline_form.activity_start = 9 * 60
    baseline_form.activity_finish = 13 * 60 + 30
    baseline_form.lunch_start = 12 * 60 + 30
    baseline_form.lunch_finish = 13 * 60 + 30
    correct = ((9, 9+50/60), (10+20/60, 11+10/60), (11+40/60, 12+30/60) )
    np.testing.assert_allclose(baseline_form.exposed_present_interval().present_times, correct, rtol=1e-14)


def test_coffee_breaks(baseline_form):
    baseline_form.coffee_duration = 10
    baseline_form.coffee_breaks = 4
    baseline_form.activity_start = 9 * 60
    baseline_form.activity_finish = 10 * 60
    baseline_form.lunch_option = False
    correct = ((9, 9+4/60), (9+14/60, 9+18/60), (9+28/60, 9+32/60), (9+42/60, 9+46/60), (9+56/60, 10))
    np.testing.assert_allclose(baseline_form.exposed_present_interval().present_times, correct, rtol=1e-14)


def test_key_validation(baseline_form_data):
    baseline_form_data['activity_type'] = 'invalid key'
    with pytest.raises(ValueError):
        model_generator.FormData.from_dict(baseline_form_data)
