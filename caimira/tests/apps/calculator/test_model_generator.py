import dataclasses
import re

import numpy as np
import numpy.testing as npt
import pytest
from retry import retry

from caimira.calculator.validators.virus import virus_validator
from caimira.calculator.validators.form_validator import (_hours2timestring, minutes_since_midnight,
                                               _CAST_RULES_FORM_ARG_TO_NATIVE, _CAST_RULES_NATIVE_TO_FORM_ARG)
from caimira.calculator.models import models
from caimira.calculator.models.monte_carlo.data import expiration_distributions
from caimira.calculator.validators.defaults import NO_DEFAULT
from caimira.calculator.store.data_registry import DataRegistry


def test_model_from_dict(baseline_form_data, data_registry):
    form = virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)
    assert isinstance(form.build_model(), models.ExposureModelGroup)


def test_model_from_dict_invalid(baseline_form_data, data_registry):
    baseline_form_data['invalid_item'] = 'foobar'
    with pytest.raises(ValueError, match='Invalid argument "invalid_item" given'):
        virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


@retry(tries=10)
@pytest.mark.parametrize(
    ["mask_type"],
    [
        ["No mask"],
        ["Type I"],
        ["Cloth"],
    ]
)
def test_blend_expiration(data_registry, mask_type):
    SAMPLE_SIZE = 250000
    TOLERANCE = 0.02
    blend = {'Breathing': 2, 'Speaking': 1}
    r = virus_validator.build_expiration(data_registry, blend).build_model(SAMPLE_SIZE)
    mask = models.Mask.types[mask_type]
    expected = (expiration_distributions(data_registry)['Breathing'].build_model(SAMPLE_SIZE).aerosols(mask).mean()*2/3. +
                expiration_distributions(data_registry)['Speaking'].build_model(SAMPLE_SIZE).aerosols(mask).mean()/3.)
    npt.assert_allclose(r.aerosols(mask).mean(), expected, rtol=TOLERANCE)


def test_ventilation_slidingwindow(data_registry: DataRegistry, baseline_form: virus_validator.VirusFormData):
    baseline_form.ventilation_type = 'natural_ventilation'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.window_opening_regime = 'windows_open_periodically'
    baseline_form.window_type = 'window_sliding'
    baseline_form.event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6

    baseline_vent = baseline_form.ventilation()
    assert isinstance(baseline_vent, models.MultipleVentilation)
    baseline_window = baseline_vent.ventilations[0]
    assert isinstance(baseline_window, models.SlidingWindow)

    window = models.SlidingWindow(
        data_registry=data_registry,
        active=models.PeriodicInterval(period=120, duration=10, start=9),
        outside_temp=baseline_window.outside_temp,
        window_height=1.6, opening_length=0.6,
    )

    ach = models.AirChange(
        active=models.PeriodicInterval(period=120, duration=120),
        air_exch=0.25,
    )
    ventilation = models.MultipleVentilation((window, ach))

    assert ventilation == baseline_vent


def test_ventilation_hingedwindow(baseline_form: virus_validator.VirusFormData):
    baseline_form.ventilation_type = 'natural_ventilation'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.window_opening_regime = 'windows_open_periodically'
    baseline_form.window_type = 'window_hinged'
    baseline_form.event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.window_width = 1.
    baseline_form.opening_distance = 0.6

    baseline_vent = baseline_form.ventilation()
    assert isinstance(baseline_vent, models.MultipleVentilation)
    baseline_window = baseline_vent.ventilations[0]
    assert isinstance(baseline_window, models.HingedWindow)

    window = models.HingedWindow(
        active=models.PeriodicInterval(period=120, duration=10, start=9),
        outside_temp=baseline_window.outside_temp,
        window_height=1.6, window_width=1., opening_length=0.6,
    )
    ach = models.AirChange(
        active=models.PeriodicInterval(period=120, duration=120),
        air_exch=0.25,
    )
    ventilation = models.MultipleVentilation((window, ach))

    assert ventilation == baseline_vent


def test_ventilation_mechanical(baseline_form: virus_validator.VirusFormData):
    room = models.Room(volume=75, inside_temp=models.PiecewiseConstant((0, 24), (293,)))
    mech = models.HVACMechanical(
        active=models.PeriodicInterval(period=120, duration=120),
        q_air_mech=500.,
    )
    baseline_form.ventilation_type = 'mechanical_ventilation'
    baseline_form.mechanical_ventilation_type = 'mech_type_air_supply'
    baseline_form.air_supply = 500.

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose(np.array([mech.air_exchange(room, t)+0.25 for t in ts]),
                               np.array([baseline_form.ventilation().air_exchange(room, t) for t in ts]))


def test_ventilation_airchanges(baseline_form: virus_validator.VirusFormData):
    room = models.Room(75, inside_temp=models.PiecewiseConstant((0, 24), (293,)))
    airchange = models.AirChange(
        active=models.PeriodicInterval(period=120, duration=120),
        air_exch=3.,
    )
    baseline_form.ventilation_type = 'mechanical_ventilation'
    baseline_form.mechanical_ventilation_type = 'mech_type_air_changes'
    baseline_form.air_changes = 3.

    ts = np.linspace(8, 16, 100)
    np.testing.assert_allclose(np.array([airchange.air_exchange(room, t)+0.25 for t in ts]),
                               np.array([baseline_form.ventilation().air_exchange(room, t) for t in ts]))


def test_ventilation_window_hepa(data_registry: DataRegistry, baseline_form: virus_validator.VirusFormData):
    baseline_form.ventilation_type = 'natural_ventilation'
    baseline_form.windows_duration = 10
    baseline_form.windows_frequency = 120
    baseline_form.window_opening_regime = 'windows_open_periodically'
    baseline_form.event_month = 'December'
    baseline_form.window_height = 1.6
    baseline_form.opening_distance = 0.6
    baseline_form.hepa_option = True

    baseline_vent = baseline_form.ventilation()
    assert isinstance(baseline_vent, models.MultipleVentilation)
    baseline_window = baseline_vent.ventilations[0]
    assert isinstance(baseline_window, models.SlidingWindow)

    # Now build the equivalent ventilation instance directly, and compare.
    window = models.SlidingWindow(
        data_registry=data_registry,
        active=models.PeriodicInterval(period=120, duration=10, start=9),
        outside_temp=baseline_window.outside_temp,
        window_height=1.6, opening_length=0.6,
    )
    hepa = models.HEPAFilter(
        active=models.PeriodicInterval(period=120, duration=120),
        q_air_mech=250.,
    )
    ach = models.AirChange(
        active=models.PeriodicInterval(period=120, duration=120),
        air_exch=0.25,
    )
    ventilation = models.MultipleVentilation((window, hepa, ach))

    assert ventilation == baseline_vent


@pytest.mark.parametrize(
    ["activity", "total_people", "infected_people", "error"],
    [
        ['office', 10, 11, "Number of infected people cannot be greater or equal to the number of total people"],
        ['office', 10, 10, "Number of infected people cannot be greater or equal to the number of total people"],
        ['training', 10, 2, "Conference/Training activities are limited to 1 infected."],
    ]
)
def test_infected_less_than_total_people(activity, total_people, infected_people, error,
                                         baseline_form: virus_validator.VirusFormData,
                                         data_registry: DataRegistry):
    baseline_form.activity_type = activity
    baseline_form.total_people = total_people
    baseline_form.infected_people = infected_people
    with pytest.raises(ValueError, match=error):
        baseline_form.validate()


def present_times(interval: models.Interval) -> models.BoundarySequence_t:
    assert isinstance(interval, models.SpecificInterval)
    return interval.present_times


def test_infected_present_intervals(baseline_form: virus_validator.VirusFormData):
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


def test_exposed_present_intervals(baseline_form: virus_validator.VirusFormData):
    baseline_form.exposed_coffee_duration = 15
    baseline_form.exposed_coffee_break_option = 'coffee_break_2'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(17 * 60)
    baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    correct = ((9, 10+37/60), (10+52/60, 12.5), (13.5, 15+7/60), (15+22/60, 17.0))
    assert present_times(baseline_form.exposed_present_interval()) == correct


def test_present_intervals_common_breaks(baseline_form: virus_validator.VirusFormData):
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


def test_present_intervals_split_breaks(baseline_form: virus_validator.VirusFormData):
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


def test_exposed_present_intervals_starting_with_lunch(baseline_form: virus_validator.VirusFormData):
    baseline_form.exposed_coffee_break_option = 'coffee_break_0'
    baseline_form.exposed_start = baseline_form.exposed_lunch_start = minutes_since_midnight(13 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(18 * 60)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(14 * 60)
    correct = ((14.0, 18.0), )
    assert present_times(baseline_form.exposed_present_interval()) == correct


def test_exposed_present_intervals_ending_with_lunch(baseline_form: virus_validator.VirusFormData):
    baseline_form.exposed_coffee_break_option = 'coffee_break_0'
    baseline_form.exposed_start = minutes_since_midnight(11 * 60)
    baseline_form.exposed_finish = baseline_form.exposed_lunch_start = minutes_since_midnight(13 * 60)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(14 * 60)
    correct = ((11.0, 13.0),)
    assert present_times(baseline_form.exposed_present_interval()) == correct


def test_exposed_present_lunch_end_before_beginning(baseline_form: virus_validator.VirusFormData, data_registry: DataRegistry):
    baseline_form.exposed_coffee_break_option = 'coffee_break_0'
    baseline_form.exposed_lunch_start = minutes_since_midnight(14 * 60)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60)
    with pytest.raises(ValueError):
        baseline_form.validate()


@pytest.mark.parametrize(
    "exposed_lunch_start, exposed_lunch_finish",
    [
        [8, 14], # lunch_start before the presence begining
        [19, 20], # lunch_start after the presence finishing
        [7, 8], # lunch_finish before the presence begining
        [9, 20], # lunch_finish after the presence finishing
    ],
)
def test_exposed_presence_lunch_break(baseline_form: virus_validator.VirusFormData, data_registry: DataRegistry, exposed_lunch_start, exposed_lunch_finish):
    baseline_form.exposed_lunch_start = minutes_since_midnight(exposed_lunch_start * 60)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(exposed_lunch_finish * 60)
    with pytest.raises(ValueError, match='exposed lunch break must be within presence times.'):
        baseline_form.validate()


@pytest.mark.parametrize(
    "infected_lunch_start, infected_lunch_finish",
    [
        [8, 14], # lunch_start before the presence begining
        [19, 20], # lunch_start after the presence finishing
        [7, 8], # lunch_finish before the presence begining
        [9, 20], # lunch_finish after the presence finishing
    ],
)
def test_infected_presence_lunch_break(baseline_form: virus_validator.VirusFormData, data_registry: DataRegistry, infected_lunch_start, infected_lunch_finish):
    baseline_form.infected_lunch_start = minutes_since_midnight(infected_lunch_start * 60)
    baseline_form.infected_lunch_finish = minutes_since_midnight(infected_lunch_finish * 60)
    with pytest.raises(ValueError, match='infected lunch break must be within presence times.'):
        baseline_form.validate()


def test_exposed_breaks_length(baseline_form: virus_validator.VirusFormData, data_registry: DataRegistry):
    baseline_form.exposed_coffee_break_option = 'coffee_break_4'
    baseline_form.exposed_coffee_duration = 30
    baseline_form.exposed_start = minutes_since_midnight(10 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(11 * 60)
    baseline_form.exposed_lunch_option = False
    with pytest.raises(ValueError, match='Length of breaks >= Length of exposed presence.'):
        baseline_form.validate()


def test_infected_breaks_length(baseline_form: virus_validator.VirusFormData, data_registry: DataRegistry):
    baseline_form.infected_start = minutes_since_midnight(9 * 60)
    baseline_form.infected_finish = minutes_since_midnight(12 * 60)
    baseline_form.infected_lunch_start = minutes_since_midnight(10 * 60)
    baseline_form.infected_lunch_finish = minutes_since_midnight(11 * 60)
    baseline_form.infected_coffee_break_option = 'coffee_break_4'
    baseline_form.infected_coffee_duration = 30
    with pytest.raises(ValueError, match='Length of breaks >= Length of infected presence.'):
        baseline_form.validate()


@pytest.fixture
def coffee_break_between_1045_and_1115(baseline_form: virus_validator.VirusFormData):
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
def breaks_every_25_mins_for_20_mins(baseline_form: virus_validator.VirusFormData):
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


def test_valid_no_lunch(baseline_form: virus_validator.VirusFormData, data_registry: DataRegistry):
    # Check that it is valid to have a 0 length lunch if no lunch is selected.
    baseline_form.exposed_lunch_option = False
    baseline_form.exposed_lunch_start = minutes_since_midnight(0)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(0)
    assert baseline_form.validate() is None


def test_no_breaks(baseline_form: virus_validator.VirusFormData):
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


def test_coffee_lunch_breaks(baseline_form: virus_validator.VirusFormData):
    baseline_form.exposed_coffee_duration = 30
    baseline_form.exposed_coffee_break_option = 'coffee_break_4'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(18 * 60)
    baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    correct = ((9, 9+50/60), (10+20/60, 11+10/60), (11+40/60, 12+30/60),
               (13+30/60, 14+40/60), (15+10/60, 16+20/60), (16+50/60, 18))
    np.testing.assert_allclose(present_times(baseline_form.exposed_present_interval()), correct, rtol=1e-14)


def test_coffee_lunch_breaks_unbalance(baseline_form: virus_validator.VirusFormData):
    baseline_form.exposed_coffee_duration = 30
    baseline_form.exposed_coffee_break_option = 'coffee_break_2'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(13 * 60 + 30)
    baseline_form.exposed_lunch_start = minutes_since_midnight(12 * 60 + 30)
    baseline_form.exposed_lunch_finish = minutes_since_midnight(13 * 60 + 30)
    correct = ((9, 9+50/60), (10+20/60, 11+10/60), (11+40/60, 12+30/60))
    np.testing.assert_allclose(present_times(baseline_form.exposed_present_interval()), correct, rtol=1e-14)


def test_coffee_breaks(baseline_form: virus_validator.VirusFormData):
    baseline_form.exposed_coffee_duration = 10
    baseline_form.exposed_coffee_break_option = 'coffee_break_4'
    baseline_form.exposed_start = minutes_since_midnight(9 * 60)
    baseline_form.exposed_finish = minutes_since_midnight(10 * 60)
    baseline_form.exposed_lunch_option = False
    correct = ((9, 9+4/60), (9+14/60, 9+18/60), (9+28/60, 9+32/60), (9+42/60, 9+46/60), (9+56/60, 10))
    np.testing.assert_allclose(present_times(baseline_form.exposed_present_interval()), correct, rtol=1e-14)


def test_key_validation(baseline_form_data, data_registry):
    baseline_form_data['activity_type'] = 'invalid key'
    with pytest.raises(ValueError):
        virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


def test_key_validation_natural_ventilation_window_type_na(baseline_form_data, data_registry):
    baseline_form_data['ventilation_type'] = 'natural_ventilation'
    baseline_form_data['window_type'] = 'not-applicable'
    with pytest.raises(ValueError, match='window_type cannot be \'not-applicable\''):
        virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


def test_key_validation_natural_ventilation_window_opening_regime_na(baseline_form_data, data_registry):
    baseline_form_data['ventilation_type'] = 'natural_ventilation'
    baseline_form_data['window_opening_regime'] = 'not-applicable'
    with pytest.raises(ValueError, match='window_opening_regime cannot be \'not-applicable\''):
        virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


def test_natural_ventilation_window_opening_periodically(baseline_form: virus_validator.VirusFormData, data_registry: DataRegistry):
    baseline_form.window_opening_regime = 'windows_open_periodically'
    baseline_form.windows_duration = 20
    baseline_form.windows_frequency = 10
    with pytest.raises(ValueError, match='Duration cannot be bigger than frequency.'):
        baseline_form.validate()


def test_key_validation_mech_ventilation_type_na(baseline_form_data, data_registry):
    baseline_form_data['ventilation_type'] = 'mechanical_ventilation'
    baseline_form_data['mechanical_ventilation_type'] = 'not-applicable'
    with pytest.raises(ValueError, match='mechanical_ventilation_type cannot be \'not-applicable\''):
        virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


def test_key_validation_event_month(baseline_form_data, data_registry):
    baseline_form_data['event_month'] = 'invalid month'
    with pytest.raises(ValueError, match='invalid month is not a valid value for event_month'):
        virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)


def test_default_types():
    # Validate that VirusFormData._DEFAULTS are complete and of the correct type.
    # Validate that we have the right types and matching attributes to the DEFAULTS.
    fields = {field.name: field for field in dataclasses.fields(virus_validator.VirusFormData)}
    for field, value in virus_validator.VirusFormData._DEFAULTS.items():
        if field not in fields:
            raise ValueError(f"Unmatched default {field}")

        field_type = fields[field].type
        if not isinstance(field_type, type):
            # Handle typing.NewType definitions.
            field_type = field_type.__supertype__

        if value is NO_DEFAULT:
            continue

        if field in _CAST_RULES_FORM_ARG_TO_NATIVE:
            value = _CAST_RULES_FORM_ARG_TO_NATIVE[field](value)

        if not isinstance(value, field_type):
            raise TypeError(f'{field} has type {field_type}, got {type(value)}')

    for field in fields.values():
        if field.name == "data_registry":
            continue  # Skip the assertion for the "data_registry" field
        assert field.name in virus_validator.VirusFormData._DEFAULTS, f"No default set for field name {field.name}"


def test_form_to_dict(baseline_form):
    full = baseline_form.to_dict(baseline_form)
    stripped = baseline_form.to_dict(baseline_form, strip_defaults=True)
    assert 1 < len(stripped) < len(full)
    assert 'exposed_coffee_break_option' in stripped
    # If we set the value to the default one, it should no longer turn up in the dictionary.
    baseline_form.exposed_coffee_break_option = virus_validator.VirusFormData._DEFAULTS['exposed_coffee_break_option']
    assert 'exposed_coffee_break_option' not in baseline_form.to_dict(baseline_form, strip_defaults=True)


@pytest.mark.parametrize(
    ["longitude", "latitude", "month", "expected_tz_name", "expected_offset"],
    [
        [6.14275, 46.20833, "January", 'CET', 1],  # Geneva, winter
        [6.14275, 46.20833, "May", 'CEST', 2],  # Geneva, summer
        [144.96751, -37.81739, "January", 'AEDT', 11],  # Melbourne, summer time
        [144.96751, -37.81739, "June", 'AEST', 10],  # Melbourne, winter time
        [-176.433333, -44.033333, 'August', '+1245', 12.75],  # Chatham Islands
    ]
)
def test_form_timezone(baseline_form_data, data_registry, longitude, latitude, month, expected_tz_name, expected_offset):
    baseline_form_data['location_latitude'] = latitude
    baseline_form_data['location_longitude'] = longitude
    baseline_form_data['event_month'] = month
    form = virus_validator.VirusFormData.from_dict(baseline_form_data, data_registry)
    name, offset = form.tz_name_and_utc_offset()
    assert name == expected_tz_name
    assert offset == expected_offset


def test_occupancy_TypeError(baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = [] # type: ignore
    error = 'The "occupancy" input should be a valid dictionary. Got [].'
    with pytest.raises(TypeError, match=re.escape(error)):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["occupancy", "error"],
    [   
        [
            {"tal_people": 10, "infected": 5, "presence": [{"start_time": "10:00", "finish_time": "11:00"}],},
            'Missing "total_people" key in occupancy group "group_A". Got keys: tal_people, infected, presence.'
        ],
        [
            {"total_people": 10, "infeted": 5, "presence": [{"start_time": "10:00", "finish_time": "11:00"}],},
            'Missing "infected" key in occupancy group "group_A". Got keys: total_people, infeted, presence.'
        ],
        [
            {"total_people": 10, "infected": 5, "pesence": [{"start_time": "10:00", "finish_time": "11:00"}],},
            'Missing "presence" key in occupancy group "group_A". Got keys: total_people, infected, pesence.'
        ],
    ]
)
def test_occupancy_general_params_TypeError(occupancy, error, baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = {"group_A": occupancy}
    with pytest.raises(TypeError, match=re.escape(error)):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["occupancy_presence", "error"],
    [   
        [{"start_time": "10:00", "finish_time": "11:00"}, 'The "presence" parameter in occupancy group "group_A" should be a valid list. Got <class \'dict\'>.'],
        [[], 'The "presence" parameter in occupancy group "group_A" should be a valid, non-empty list. Got [].'],
        [[["start_time", "10:00", "finish_time", "11:00"]], 'Each presence interval should be a valid dictionary. Got <class \'list\'> in occupancy group "group_A".'],
        [[{"art_time": "10:00", "finish_time": "11:00"}], 'Missing "start_time" key in "presence" parameter of occupancy group "group_A". Got keys: art_time, finish_time.'],
        [[{"start_time": "10:00", "ish_time": "11:00"}], 'Missing "finish_time" key in "presence" parameter of occupancy group "group_A". Got keys: start_time, ish_time.'],
    ]
)
def test_occupancy_presence_TypeError(occupancy_presence, error, baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = {
        "group_A": {
            "total_people": 10,
            "infected": 5,
            "presence": occupancy_presence,
        }
    }
    with pytest.raises(TypeError, match=re.escape(error)):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["occupancy_presence", "error"],
    [
        [[{"start_time": "10", "finish_time": "11:00"}], 'Invalid time format found in "presence" parameter of occupancy group "group_A". Expected HH:MM, got 10.'],
        [[{"start_time": "10:00", "finish_time": "11"}], 'Invalid time format found in "presence" parameter of occupancy group "group_A". Expected HH:MM, got 11.'],
    ]
)
def test_occupancy_presence_ValueError(occupancy_presence, error, baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = {
        "group_A": {
            "total_people": 10,
            "infected": 5,
            "presence": occupancy_presence
        }
    }
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["total_people", "error"],
    [
        ["10", 'The "total_people" input in occupancy group "group_A" should be a non-negative integer. Got 10.'],
        [9.8, 'The "total_people" input in occupancy group "group_A" should be a non-negative integer. Got 9.8.'],
        [[10], 'The "total_people" input in occupancy group "group_A" should be a non-negative integer. Got [10].'],
        [-1, 'The "total_people" input in occupancy group "group_A" should be a non-negative integer. Got -1.'],
    ]
)
def test_occupancy_total_people_ValueError(total_people, error, baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = {
        "group_A": {
            "total_people": total_people,
            "infected": 10,
            "presence": [{"start_time": "08:00", "finish_time": "18:00"},],
        },
    }
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["infected", "error"],
    [
        ["10", 'The infected input in occupancy group "group_A" should be a non-negative integer. Got 10.'],
        [9.8, 'The infected input in occupancy group "group_A" should be a non-negative integer. Got 9.8.'],
        [[10], 'The infected input in occupancy group "group_A" should be a non-negative integer. Got [10].'],
        [-1, 'The infected input in occupancy group "group_A" should be a non-negative integer. Got -1.'],
        [30, 'The number of infected people (30) cannot be greater than the total people (20).']
    ]
)
def test_occupancy_infected_ValueError(infected, error, baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = {
        "group_A": {
            "total_people": 20,
            "infected": infected,
            "presence": [{"start_time": "08:00", "finish_time": "18:00"},],
        },
    }
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()
        

def test_occupancy_presence_overlap(baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = {
        "group_A": {
            "total_people": 10,
            "infected": 5,
            "presence": [
                {"start_time": "08:00", "finish_time": "17:00"},
                {"start_time": "13:00", "finish_time": "14:00"},
            ],
        },
    }
    error = (
        'Overlap detected: The entry '
        '{\'start_time\': \'13:00\', \'finish_time\': \'14:00\'}'
        ' overlaps with an already existing entry '
        '({\'start_time\': \'08:00\', \'finish_time\': \'17:00\'}).'
    )
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["short_range_input", "error"],
    [
        [[["expiration", "Shouting", "start_time", "09:00", "duration", 30]], 'Each short-range interaction should be a dictionary. Got <class \'list\'> in occupancy group "group_A".'],
        [[{"expiratio": "Shouting", "start_time": "09:00", "duration": 30}], 'Missing "expiration" key in short-range interaction for occupancy group "group_A". Got keys: expiratio, start_time, duration.'],
        [[{"expiration": "Shouting", "start_tim": "09:00", "duration": 30}], 'Missing "start_time" key in short-range interaction for occupancy group "group_A". Got keys: expiration, start_tim, duration.'],
        [[{"expiration": "Shouting", "start_time": "09:00", "duratio": 30}], 'Missing "duration" key in short-range interaction for occupancy group "group_A". Got keys: expiration, start_time, duratio.'],
    ]
)
def test_short_range_TypeError(short_range_input, error, baseline_form: virus_validator.VirusFormData):
    baseline_form.short_range_option = "short_range_yes"
    baseline_form.short_range_interactions = {"group_A": short_range_input}
    with pytest.raises(TypeError, match=re.escape(error)):
        baseline_form.validate()


def test_short_range_exposure_group(baseline_form: virus_validator.VirusFormData):
    baseline_form.occupancy = {
        "group_A": {
            "total_people": 20,
            "infected": 10,
            "presence": [
                {"start_time": "10:00", "finish_time": "12:00"},
                {"start_time": "13:00", "finish_time": "17:00"},
            ],
        },
        "group_B": {
            "total_people": 20,
            'infected': 10,
            "presence": [
                {"start_time": "10:00", "finish_time": "11:00"},
            ],
        },
    }
    
    # Check for existence of the dictionary key
    baseline_form.short_range_option = 'short_range_yes'
    baseline_form.short_range_interactions = {
        "group_C": [{"expiration": "Shouting", "start_time": "10:30", "duration": 30}],
    }
    error = 'Occupancy group "group_C" referenced in short-range interactions was not found in the occupancy input.'
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()

    # Check if interaction time is within simulation time
    baseline_form.short_range_interactions = {
        "group_A": [{"expiration": "Shouting", "start_time": "18:00", "duration": 30}],
    }
    error = (
        'Short-range interaction {\'expiration\': \'Shouting\', \'start_time\': \'18:00\', \'duration\': 30}'
        ' does not fall within any presence interval in occupancy group "group_A".'
    )
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["short_range_input", "error"],
    [
        [[{"expiration": "Shouting", "start_time": "9", "duration": 30}], 'Invalid time format for start_time in short-range interaction for occupancy group "group_A". Expected HH:MM, got 9.'],
        [[{"expiration": "Whisper", "start_time": "09:00", "duration": 30}], 'Invalid expiration value in short-range interaction for occupancy group "group_A". Got "Whisper".'],
        [[{"expiration": "Shouting", "start_time": "09:00", "duration": -30}], 'The duration value in short-range interaction for occupancy group "group_A" should be a non-negative integer. Got -30.'],
    ]
)
def test_short_range_value_error(short_range_input, error, baseline_form: virus_validator.VirusFormData):
    baseline_form.short_range_option = "short_range_yes"
    baseline_form.short_range_interactions = {"group_A": short_range_input}
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()


def test_short_range_with_occupancy_format(baseline_form: virus_validator.VirusFormData):
    baseline_form.short_range_option = "short_range_yes"
    baseline_form.short_range_interactions = {"group_A": [{"expiration": "Shouting", "start_time": "07:00", "duration": 30}]}

    # Checks if interaction is defined during simulation time
    error = (
        'Short-range interactions must occur during simulation time. Got'
        ' {\'expiration\': \'Shouting\', \'start_time\': \'07:00\', \'duration\': 30}'
        ' in occupancy group "group_A".'
    )
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()

    # Checks overlap of short-range interactions
    baseline_form.short_range_interactions = {
        "group_A": [{"expiration": "Shouting", "start_time": "10:00", "duration": 30},
                    {"expiration": "Shouting", "start_time": "10:10", "duration": 15}],
    }
    error = (
        'Overlap detected: The entry '
        '{\'expiration\': \'Shouting\', \'start_time\': \'10:10\', \'duration\': 15}'
        ' overlaps with an already existing entry '
        '({\'expiration\': \'Shouting\', \'start_time\': \'10:00\', \'duration\': 30}).'
    )
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()

    # Checks if short_range_option relates with the short_range-interactions input
    baseline_form.short_range_option = "short_range_yes"
    baseline_form.short_range_interactions = {}
    error = (
        'When short_range_option input is set to "short_range_yes", the short_range_interactions '
        'input should not be empty. Got {}.'
    )
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()
    
    # Checks if more than one group is defined (legacy)
    baseline_form.short_range_interactions = {
        "group_A": [{"expiration": "Shouting", "start_time": "10:00", "duration": 30}],
        "group_B": [{"expiration": "Shouting", "start_time": "10:00", "duration": 30}]
    }
    error = (
        'Incompatible number of occupancy groups in the short_range_interactions input. '
        'Got 2 groups when the maximum is 1.'
    )
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()

    # Checks if more than one group is defined
    baseline_form.occupancy = {
        "group_A": {"total_people": 20, "infected": 10, "presence": [
                {"start_time": "10:00", "finish_time": "12:00"},
                {"start_time": "13:00", "finish_time": "17:00"},
            ],
        }
    }
    baseline_form.short_range_interactions = {
        "group_A": [{"expiration": "Shouting", "start_time": "10:00", "duration": 30}],
        "group_B": [{"expiration": "Shouting", "start_time": "10:00", "duration": 30}]
    }
    error = (
        'Incompatible number of occupancy groups in the short_range_interactions input. '
        'Got 2 groups when the maximum is 1 (from the occupancy input).'
    )
    with pytest.raises(ValueError, match=re.escape(error)):
        baseline_form.validate()


def test_population_generation_from_occupancy(baseline_form: virus_validator.VirusFormData):
    # Checks the correct translation of the occupancy data into the right exposure and infected models
    baseline_form.occupancy = {
        "group_A": {
            "total_people": 5,
            "infected": 2,
            "presence": [
                    {"start_time": "09:00", "finish_time": "12:00"},
                    {"start_time": "13:00", "finish_time": "17:00"},
                ],
        },
        "group_B": {
            "total_people": 3,
                "infected": 1,
                "presence": [
                        {"start_time": "09:00", "finish_time": "10:00"},
                        {"start_time": "11:00", "finish_time": "12:00"},
                    ],
        },
    }

    exposure_model_group: models.ExposureModelGroup = baseline_form.build_model()
    
    # Assert that from this occupancy input, two ExposureModels are created
    assert len(exposure_model_group.exposure_models) == 2
    assert all(isinstance(model, models.ExposureModel) for model in exposure_model_group.exposure_models)
    
    first_group = exposure_model_group.exposure_models[0]
    second_group = exposure_model_group.exposure_models[1]

    # Assert the exposed population generation (number and presence) from the occupancy input
    # Type checks
    assert isinstance(first_group.exposed, models.Population)
    assert isinstance(first_group.exposed.number, int)
    assert isinstance(first_group.exposed.presence, models.Interval)

    assert isinstance(second_group.exposed, models.Population)
    assert isinstance(second_group.exposed.number, int)
    assert isinstance(second_group.exposed.presence, models.Interval)

    # Value checks
    assert first_group.exposed.number == 3
    assert tuple(first_group.exposed.presence.transition_times()) == (9, 12, 13, 17)
    assert first_group.exposed.presence.boundaries() == ((9, 12), (13, 17))
    
    assert second_group.exposed.number == 2
    assert tuple(second_group.exposed.presence.transition_times()) == (9, 10, 11, 12)
    assert second_group.exposed.presence.boundaries() == ((9, 10), (11, 12))
    
    # Assert that the infected population is the same for all the models
    # Type checks
    assert isinstance(first_group.concentration_model.infected, models.InfectedPopulation)
    assert isinstance(second_group.concentration_model.infected, models.InfectedPopulation)
    # Value checks
    assert first_group.concentration_model.infected.number == second_group.concentration_model.infected.number
    assert first_group.concentration_model.infected.presence == second_group.concentration_model.infected.presence
    
    # Assert the infected population generation (number and presence) from the occupancy input
    for infected_obj in [first_group.concentration_model.infected, second_group.concentration_model.infected]:
        # Type checks
        assert isinstance(infected_obj.number, models.IntPiecewiseConstant)
        assert infected_obj.presence is None
        # Value checks
        assert infected_obj.number.interval().boundaries() == ((9, 10), (10, 11), (11, 12), (13, 17))
        assert infected_obj.number.transition_times == (9, 10, 11, 12, 13, 17)
        assert infected_obj.number.values == (3, 2, 3, 0, 2)    
