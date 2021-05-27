import dataclasses

import pytest

from cara.apps.calculator import model_generator
from cara.apps.calculator.model_generator import _hours2timestring
from cara.apps.calculator.model_generator import minutes_since_midnight
from cara import models
from cara import data
import numpy as np
import numpy.testing as npt


def test_model_from_dict(baseline_form_data):
    form = model_generator.FormData.from_dict(baseline_form_data)
    assert isinstance(form.build_model(), models.ExposureModel)


def test_model_from_dict_invalid(baseline_form_data):
    baseline_form_data['invalid_item'] = 'foobar'
    with pytest.raises(ValueError, match='Invalid argument "invalid_item" given'):
        model_generator.FormData.from_dict(baseline_form_data)


def test_blend_expiration():
    blend = {'Breathing': 2, 'Talking': 1}
    r = model_generator.build_expiration(blend)
    mask = models.Mask.types['Type I']
    expected = models.Expiration(
        (0.13466666666666668, 0.02866666666666667, 0.004333333333333334, 0.005)
    )
    npt.assert_almost_equal(r.aerosols(mask), expected.aerosols(mask))


def test_ventilation_slidingwindow(baseline_form: model_generator.FormData):
    room = models.Room(75)
    window = models.SlidingWindow(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=data.GenevaTemperatures['Dec'],
        window_height=1.6, opening_length=0.6,
    )
    baseline_form.ventilation_type = 'natural_ventilation'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.window_opening_regime = 'windows_open_periodically'
    baseline_form.window_type = 'window_sliding'
    baseline_form.event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([window.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_hingedwindow(baseline_form: model_generator.FormData):
    room = models.Room(75)
    window = models.HingedWindow(
        active=models.PeriodicInterval(period=120, duration=10),
        inside_temp=models.PiecewiseConstant((0, 24), (293,)),
        outside_temp=data.GenevaTemperatures['Dec'],
        window_height=1.6, window_width=1., opening_length=0.6,
    )
    baseline_form.ventilation_type = 'natural_ventilation'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.window_opening_regime = 'windows_open_periodically'
    baseline_form.window_type = 'window_hinged'
    baseline_form.event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.window_width = 1.
    baseline_form.opening_distance = 0.6

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([window.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_mechanical(baseline_form: model_generator.FormData):
    room = models.Room(75)
    mech = models.HVACMechanical(
        active=models.PeriodicInterval(period=120, duration=120),
        q_air_mech=500.,
    )
    baseline_form.ventilation_type = 'mechanical_ventilation'
    baseline_form.mechanical_ventilation_type = 'mech_type_air_supply'
    baseline_form.air_supply = 500.

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([mech.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_airchanges(baseline_form: model_generator.FormData):
    room = models.Room(75)
    airchange = models.AirChange(
        active=models.PeriodicInterval(period=120, duration=120),
        air_exch=3.,
    )
    baseline_form.ventilation_type = 'mechanical_ventilation'
    baseline_form.mechanical_ventilation_type = 'mech_type_air_changes'
    baseline_form.air_changes = 3.

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose([airchange.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def test_ventilation_window_hepa(baseline_form: model_generator.FormData):
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

    baseline_form.ventilation_type = 'natural_ventilation'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.window_opening_regime = 'windows_open_periodically'
    baseline_form.event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6
    baseline_form.hepa_option = True

    ts = np.linspace(9, 17, 100)
    np.testing.assert_allclose([ventilation.air_exchange(room, t) for t in ts],
                               [baseline_form.ventilation().air_exchange(room, t) for t in ts])


def present_times(interval: models.Interval) -> models.BoundarySequence_t:
    assert isinstance(interval, models.SpecificInterval)
    return interval.present_times


def test_infected_present_intervals(baseline_form: model_generator.FormData):
    baseline_form.infected_dont_have_breaks_with_exposed = False
    baseline_form.exposed_coffee_duration = 15
    baseline_form.exposed_coffee_break_option = 'coffee_break_2'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(17 * 60)
    baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    baseline_form.infected_start = minutes_since_midnight(10 * 60)
    baseline_form.infected_finish = minutes_since_midnight(15 * 60)
    correct = ((10, 10+37/60), (10+52/60, 12.5), (13.5, 15.0))
    assert present_times(baseline_form.infected_present_interval()) == correct


def test_exposed_present_intervals(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_duration = 15
    baseline_form.exposed_coffee_break_option = 'coffee_break_2'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(17 * 60)
    baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    correct = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 15+7/60), (15+22/60, 17.0))
    assert present_times(baseline_form.exposed_present_interval()) == correct


def test_present_intervals_common_breaks(baseline_form: model_generator.FormData):
    baseline_form.infected_dont_have_breaks_with_exposed = False
    baseline_form.infected_coffee_duration = baseline_form.exposed_coffee_duration = 15
    baseline_form.infected_coffee_break_option = baseline_form.exposed_coffee_break_option = 'coffee_break_2'
    baseline_form.exposed_lunch_start = baseline_form.infected_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = baseline_form.infected_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(17 * 60)
    baseline_form.infected_start = minutes_since_midnight(9 * 60)
    baseline_form.infected_finish = minutes_since_midnight(16 * 60)
    correct_exposed = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 15+7/60), (15+22/60, 17.0))
    correct_infected = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 15+7/60), (15+22/60, 16.0))
    assert present_times(baseline_form.exposed_present_interval()) == correct_exposed
    assert present_times(baseline_form.infected_present_interval()) == correct_infected


def test_present_intervals_split_breaks(baseline_form: model_generator.FormData):
    baseline_form.infected_dont_have_breaks_with_exposed = True
    baseline_form.infected_coffee_duration = baseline_form.exposed_coffee_duration = 15
    baseline_form.infected_coffee_break_option = baseline_form.exposed_coffee_break_option = 'coffee_break_2'
    baseline_form.infected_lunch_start = baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.infected_lunch_finish = baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(17 * 60)
    baseline_form.infected_start = minutes_since_midnight(9 * 60)
    baseline_form.infected_finish = minutes_since_midnight(16 * 60)
    correct_exposed = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 15+7/60), (15+22/60, 17.0))
    correct_infected = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 14+37/60), (14+52/60, 16.0))
    assert present_times(baseline_form.exposed_present_interval()) == correct_exposed
    assert present_times(baseline_form.infected_present_interval()) == correct_infected


def test_exposed_present_intervals_starting_with_lunch(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_break_option = 'coffee_break_0'
    baseline_form.exposed_start = baseline_form.exposed_lunch_start = minutes_since_midnight(13 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(18 * 60)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(14 * 60)
    correct = ((14.0, 18.0), )
    assert present_times(baseline_form.exposed_present_interval()) == correct


def test_exposed_present_intervals_ending_with_lunch(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_break_option = 'coffee_break_0'
    baseline_form.exposed_start = minutes_since_midnight(11 * 60)
    baseline_form.exposed_finish = baseline_form.exposed_lunch_start = minutes_since_midnight(13 * 60)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(14 * 60)
    correct = ((11.0, 13.0),)
    assert present_times(baseline_form.exposed_present_interval()) == correct


def test_exposed_present_lunch_end_before_beginning(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_break_option = 'coffee_break_0'
    baseline_form.exposed_lunch_start = minutes_since_midnight(14 * 60)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60)
    with pytest.raises(ValueError):
        baseline_form.validate()


@pytest.fixture
def coffee_break_between_1045_and_1115(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_break_option = 'coffee_break_1'
    baseline_form.exposed_coffee_duration = 30
    baseline_form.exposed_start = minutes_since_midnight(10 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(12 * 60)
    baseline_form.exposed_lunch_option = False
    coffee_breaks = baseline_form.exposed_coffee_break_times()
    assert coffee_breaks == ((10.75 * 60, 11.25 * 60),)
    return baseline_form


def test_present_before_coffee(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.exposed_coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.5 * 60, 11 * 60, breaks=breaks)
    assert interval.boundaries() == ((10.5, 10.75),)


def test_present_after_coffee(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.exposed_coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        11 * 60, 11.5 * 60, breaks=breaks)
    assert interval.boundaries() == ((11.25, 11.5),)


def test_present_when_coffee_starts(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.exposed_coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.75 * 60, 11.5 * 60, breaks=breaks)
    assert interval.boundaries() == ((11.25, 11.5),)


def test_present_when_coffee_ends(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.exposed_coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.5 * 60, 11.25 * 60, breaks=breaks)
    assert interval.boundaries() == ((10.5, 10.75), )


def test_present_only_for_coffee_ends(coffee_break_between_1045_and_1115):
    breaks = coffee_break_between_1045_and_1115.exposed_coffee_break_times()
    interval = coffee_break_between_1045_and_1115.present_interval(
        10.75 * 60, 11.25 * 60, breaks=breaks)
    assert interval.boundaries() == ()


def time2mins(time: str) -> minutes_since_midnight:
    # Convert times like "14:30" to decimal, like 14.5 * 60.
    return minutes_since_midnight(int(time.split(':')[0]) * 60 + int(time.split(':')[1]))


def assert_boundaries(interval, boundaries_in_time_string_form):
    boundaries = [(_hours2timestring(start), _hours2timestring(end))
                  for start, end in interval.boundaries()]
    assert boundaries == boundaries_in_time_string_form


@pytest.fixture
def breaks_every_25_mins_for_20_mins(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_break_option = 'coffee_break_4'
    baseline_form.exposed_coffee_duration = 20
    baseline_form.exposed_start = time2mins("10:00")
    baseline_form.exposed_finish = time2mins("14:10")
    baseline_form.exposed_lunch_start = time2mins("11:55")
    baseline_form.exposed_lunch_finish = time2mins("12:15")
    baseline_form.exposed_lunch_option = True

    breaks = baseline_form.exposed_coffee_break_times() + baseline_form.exposed_lunch_break_times()
    interval = baseline_form.present_interval(
        baseline_form.exposed_start, baseline_form.exposed_finish, breaks=breaks,
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
    breaks = breaks_every_25_mins_for_20_mins.exposed_coffee_break_times() + breaks_every_25_mins_for_20_mins.exposed_lunch_break_times()
    # The first two breaks start at 10:25 and 11:10.
    interval = breaks_every_25_mins_for_20_mins.present_interval(
        time2mins("11:35"), time2mins("11:40"), breaks=breaks,
    )
    # Only present for a short duration of a presence period.
    assert_boundaries(interval, [('11:35', '11:40')])


def test_present_only_during_second_break(breaks_every_25_mins_for_20_mins):
    breaks = breaks_every_25_mins_for_20_mins.exposed_coffee_break_times() + breaks_every_25_mins_for_20_mins.exposed_lunch_break_times()
    # The first two breaks start at 10:25 and 11:10.
    interval = breaks_every_25_mins_for_20_mins.present_interval(
        time2mins("11:15"), time2mins("11:20"), breaks=breaks
    )
    # No presence.
    assert_boundaries(interval, [])


def test_valid_no_lunch(baseline_form: model_generator.FormData):
    # Check that it is valid to have a 0 length lunch if no lunch is selected.
    baseline_form.exposed_lunch_option = False
    baseline_form.exposed_lunch_start = minutes_since_midnight(0)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(0)
    assert baseline_form.validate() is None


def test_no_breaks(baseline_form: model_generator.FormData):
    # Check that the times are correct in the absence of breaks.
    baseline_form.infected_dont_have_breaks_with_exposed = False
    baseline_form.exposed_lunch_option = False
    baseline_form.exposed_coffee_break_option = 'coffee_break_0'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(17 * 60)
    baseline_form.infected_start = minutes_since_midnight(10 * 60)
    baseline_form.infected_finish = minutes_since_midnight(15 * 60)
    exposed_correct = ((9, 17),)
    infected_correct = ((10, 15),)
    assert present_times(baseline_form.exposed_present_interval()) == exposed_correct
    assert present_times(baseline_form.infected_present_interval()) == infected_correct


def test_coffee_lunch_breaks(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_duration = 30
    baseline_form.exposed_coffee_break_option = 'coffee_break_4'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(18 * 60)
    baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    correct = ((9, 9+50/60), (10+20/60, 11+10/60), (11+40/60, 12+30/60),
               (13+30/60, 14+40/60), (15+10/60, 16+20/60), (16+50/60, 18))
    np.testing.assert_allclose(present_times(baseline_form.exposed_present_interval()), correct, rtol=1e-14)


def test_coffee_lunch_breaks_unbalance(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_duration = 30
    baseline_form.exposed_coffee_break_option = 'coffee_break_2'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(13 * 60 + 30)
    baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    correct = ((9, 9+50/60), (10+20/60, 11+10/60), (11+40/60, 12+30/60))
    np.testing.assert_allclose(present_times(baseline_form.exposed_present_interval()), correct, rtol=1e-14)


def test_coffee_breaks(baseline_form: model_generator.FormData):
    baseline_form.exposed_coffee_duration = 10
    baseline_form.exposed_coffee_break_option = 'coffee_break_4'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(10 * 60)
    baseline_form.exposed_lunch_option = False
    correct = ((9, 9+4/60), (9+14/60, 9+18/60), (9+28/60, 9+32/60), (9+42/60, 9+46/60), (9+56/60, 10))
    np.testing.assert_allclose(present_times(baseline_form.exposed_present_interval()), correct, rtol=1e-14)


def test_key_validation(baseline_form_data):
    baseline_form_data['activity_type'] = 'invalid key'
    with pytest.raises(ValueError):
        model_generator.FormData.from_dict(baseline_form_data)


def test_key_validation_natural_ventilation_window_type_na(baseline_form_data):
    baseline_form_data['ventilation_type'] = 'natural_ventilation'
    baseline_form_data['window_type'] = 'not-applicable'
    with pytest.raises(ValueError, match='window_type cannot be \'not-applicable\''):
        model_generator.FormData.from_dict(baseline_form_data)


def test_key_validation_natural_ventilation_window_opening_regime_na(baseline_form_data):
    baseline_form_data['ventilation_type'] = 'natural_ventilation'
    baseline_form_data['window_opening_regime'] = 'not-applicable'
    with pytest.raises(ValueError, match='window_opening_regime cannot be \'not-applicable\''):
        model_generator.FormData.from_dict(baseline_form_data)


def test_key_validation_mech_ventilation_type_na(baseline_form_data):
    baseline_form_data['ventilation_type'] = 'mechanical_ventilation'
    baseline_form_data['mechanical_ventilation_type'] = 'not-applicable'
    with pytest.raises(ValueError, match='mechanical_ventilation_type cannot be \'not-applicable\''):
        model_generator.FormData.from_dict(baseline_form_data)


def test_default_types():
    # Validate that FormData._DEFAULTS are complete and of the correct type.
    # Validate that we have the right types and matching attributes to the DEFAULTS.
    fields = {field.name: field for field in dataclasses.fields(model_generator.FormData)}
    for field, value in model_generator.FormData._DEFAULTS.items():
        if field not in fields:
            raise ValueError(f"Unmatched default {field}")

        field_type = fields[field].type
        if not isinstance(field_type, type):
            # Handle typing.NewType definitions.
            field_type = field_type.__supertype__

        if value is model_generator._NO_DEFAULT:
            continue

        if field in model_generator._CAST_RULES_FORM_ARG_TO_NATIVE:
            value = model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[field](value)

        if not isinstance(value, field_type):
            raise TypeError(f'{field} has type {field_type}, got {type(value)}')

    for field in fields.values():
        assert field.name in model_generator.FormData._DEFAULTS, f"No default set for field name {field.name}"


def test_form_to_dict(baseline_form):
    full = baseline_form.to_dict(baseline_form)
    stripped = baseline_form.to_dict(baseline_form, strip_defaults=True)
    assert 1 < len(stripped) < len(full)
    assert 'exposed_coffee_break_option' in stripped
    # If we set the value to the default one, it should no longer turn up in the dictionary.
    baseline_form.exposed_coffee_break_option = model_generator.FormData._DEFAULTS['exposed_coffee_break_option']
    assert 'exposed_coffee_break_option' not in baseline_form.to_dict(baseline_form, strip_defaults=True)
