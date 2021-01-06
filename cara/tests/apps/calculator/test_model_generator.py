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
    form = model_generator.FormData.from_dict(baseline_form_data)
    assert isinstance(form.build_model(), models.ExposureModel)


def test_blend_expiration():
    blend = {'Breathing': 2, 'Talking': 1}
    r = model_generator.build_expiration(blend)
    expected = models.Expiration(
        (0.13466666666666668, 0.02866666666666667, 0.004333333333333334, 0.005)
    )
    assert r == expected


def test_ventilation_slidingwindow(baseline_form):
    room = models.Room(75)
    window = models.SlidingWindow(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=data.GenevaTemperatures['Dec'],
        window_height=1.6, opening_length=0.6,
    )
    baseline_form.ventilation_type = 'natural'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.windows_open = 'interval'
    baseline_form.window_type = 'sliding'
    baseline_form.event_type = 'recurrent_event'
    baseline_form.recurrent_event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([window.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_hingedwindow(baseline_form):
    room = models.Room(75)
    window = models.HingedWindow(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=data.GenevaTemperatures['Dec'],
        window_height=1.6, window_width=1., opening_length=0.6,
    )
    baseline_form.ventilation_type = 'natural'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.windows_open = 'interval'
    baseline_form.window_type = 'hinged'
    baseline_form.event_type = 'recurrent_event'
    baseline_form.recurrent_event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.window_width = 1.
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
    window = models.SlidingWindow(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=data.GenevaTemperatures['Dec'],
        window_height=1.6, opening_length=0.6,
    )
    hepa = models.HEPAFilter(
        active=models.PeriodicInterval(period=120, duration=120),
        q_air_mech=250.,
    )
    ventilation = models.MultipleVentilation((window,hepa))

    baseline_form.ventilation_type = 'natural'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
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
    correct = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 15+7/60), (15+22/60, 17.0))
    assert baseline_form.exposed_present_interval().present_times == correct


def test_exposed_present_intervals_starting_with_lunch(baseline_form):
    baseline_form.coffee_breaks = 0
    baseline_form.activity_start = baseline_form.lunch_start = 13 * 60
    baseline_form.activity_finish = 18 * 60
    baseline_form.lunch_finish = 14 * 60
    correct = ((14.0, 18.0), )
    assert baseline_form.exposed_present_interval().present_times == correct


def test_exposed_present_intervals_ending_with_lunch(baseline_form):
    baseline_form.coffee_breaks = 0
    baseline_form.activity_start = 11 * 60
    baseline_form.activity_finish = baseline_form.lunch_start = 13 * 60
    baseline_form.lunch_finish = 14 * 60
    correct = ((11.0, 13.0),)
    assert baseline_form.exposed_present_interval().present_times == correct


def test_exposed_present_lunch_end_before_beginning(baseline_form):
    baseline_form.coffee_breaks = 0
    baseline_form.lunch_start = 14 * 60
    baseline_form.lunch_finish = 13 * 60
    with pytest.raises(ValueError):
        baseline_form.validate()


@pytest.fixture
def coffee_break_between_1045_and_1115(baseline_form):
    baseline_form.coffee_breaks = 1
    baseline_form.coffee_duration = 30
    baseline_form.activity_start = 10 * 60
    baseline_form.activity_finish = 12 * 60
    baseline_form.lunch_option = False

    coffee_breaks = baseline_form.coffee_break_times()
    assert coffee_breaks == ((10.75 * 60, 11.25 * 60),)
    return baseline_form


def test_present_before_coffee(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.5 * 60, 11 * 60, breaks=breaks)
    assert interval.boundaries() == ((10.5, 10.75),)


def test_present_after_coffee(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        11 * 60, 11.5 * 60, breaks=breaks)
    assert interval.boundaries() == ((11.25, 11.5),)


def test_present_when_coffee_starts(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.75 * 60, 11.5 * 60, breaks=breaks)
    assert interval.boundaries() == ((11.25, 11.5),)


def test_present_when_coffee_ends(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.5 * 60, 11.25 * 60, breaks=breaks)
    assert interval.boundaries() == ((10.5, 10.75), )


def test_present_only_for_coffee_ends(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.75 * 60, 11.25 * 60, breaks=breaks)
    assert interval.boundaries() == ()


def time2mins(time: str):
    # Convert times like "14:30" to decimal, like 14.5 * 60.
    return int(time.split(':')[0]) * 60 + int(time.split(':')[1])


def hours2time(hours: float):
    # Convert times like 14.5 to strings, like "14:30"
    return f"{int(np.floor(hours)):02d}:{int(np.round((hours % 1) * 60)):02d}"


def assert_boundaries(interval, boundaries_in_time_string_form):
    boundaries = [(hours2time(start), hours2time(end))
                  for start, end in interval.boundaries()]
    assert boundaries == boundaries_in_time_string_form


@pytest.fixture
def breaks_every_25_mins_for_20_mins(baseline_form):
    baseline_form.coffee_breaks = 4
    baseline_form.coffee_duration = 20
    baseline_form.activity_start = time2mins("10:00")
    baseline_form.activity_finish = time2mins("14:10")
    baseline_form.lunch_start = time2mins("11:55")
    baseline_form.lunch_finish = time2mins("12:15")
    baseline_form.lunch_option = True

    breaks = baseline_form.coffee_break_times() + baseline_form.lunch_break_times()
    interval = baseline_form.present_interval(
        baseline_form.activity_start, baseline_form.activity_finish, breaks=breaks,
    )

    assert_boundaries(interval, [
        ('10:00', '10:25'),
        ('10:45', '11:10'),
        ('11:30', '11:55'),
        ('12:15', '12:40'),
        ('13:00', '13:25'),
        ('13:45', '14:10')
    ])
    return baseline_form


def test_present_after_two_breaks_for_small_interval(breaks_every_25_mins_for_20_mins):
    breaks = breaks_every_25_mins_for_20_mins.coffee_break_times() + breaks_every_25_mins_for_20_mins.lunch_break_times()
    # The first two breaks start at 10:25 and 11:10.
    interval = breaks_every_25_mins_for_20_mins.present_interval(
        time2mins("11:35"), time2mins("11:40"), breaks=breaks,
    )
    # Only present for a short duration of a presence period.
    assert_boundaries(interval, [('11:35', '11:40')])


def test_present_only_during_second_break(breaks_every_25_mins_for_20_mins):
    breaks = breaks_every_25_mins_for_20_mins.coffee_break_times() + breaks_every_25_mins_for_20_mins.lunch_break_times()
    # The first two breaks start at 10:25 and 11:10.
    interval = breaks_every_25_mins_for_20_mins.present_interval(
        time2mins("11:15"), time2mins("11:20"), breaks=breaks
    )
    # No presence.
    assert_boundaries(interval, [])


def test_valid_no_lunch(baseline_form):
    # Check that it is valid to have a 0 length lunch if no lunch is selected.
    baseline_form.lunch_option = False
    baseline_form.lunch_start = 0
    baseline_form.lunch_finish = 0
    assert baseline_form.validate() is None


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
    correct = ((9, 9+50/60), (10+20/60, 11+10/60), (11+40/60, 12+30/60))
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
