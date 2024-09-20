import dataclasses
import html
import logging
import typing
import ast
import json
import re

import numpy as np

from .defaults import DEFAULTS, NO_DEFAULT, COFFEE_OPTIONS_INT
from ..models import models
from ..store.data_registry import DataRegistry

LOG = logging.getLogger(__name__)

minutes_since_midnight = typing.NewType('minutes_since_midnight', int)


@dataclasses.dataclass
class FormData:
    # Static occupancy inputs
    exposed_coffee_break_option: str
    exposed_coffee_duration: int
    exposed_finish: minutes_since_midnight
    exposed_lunch_finish: minutes_since_midnight
    exposed_lunch_option: bool
    exposed_lunch_start: minutes_since_midnight
    exposed_start: minutes_since_midnight
    infected_coffee_break_option: str               #Used if infected_dont_have_breaks_with_exposed
    infected_coffee_duration: int                   #Used if infected_dont_have_breaks_with_exposed
    infected_dont_have_breaks_with_exposed: bool
    infected_finish: minutes_since_midnight
    infected_lunch_finish: minutes_since_midnight   #Used if infected_dont_have_breaks_with_exposed
    infected_lunch_option: bool                     #Used if infected_dont_have_breaks_with_exposed
    infected_lunch_start: minutes_since_midnight    #Used if infected_dont_have_breaks_with_exposed
    infected_start: minutes_since_midnight
    infected_people: int
    occupancy_format: str
    room_volume: float
    specific_breaks: dict
    total_people: int

    # Dynamic occupancy inputs
    dynamic_exposed_occupancy: list
    dynamic_infected_occupancy: list

    data_registry: DataRegistry

    _DEFAULTS: typing.ClassVar[typing.Dict[str, typing.Any]] = DEFAULTS

    @classmethod
    def from_dict(cls, form_data: typing.Dict, data_registry: DataRegistry):
        # Take a copy of the form data so that we can mutate it.
        form_data = form_data.copy()
        form_data.pop('_xsrf', None)
        # Don't let arbitrary unescaped HTML through the net.
        for key, value in form_data.items():
            if isinstance(value, str):
                form_data[key] = html.escape(value)

        for key, default_value in cls._DEFAULTS.items():
            if form_data.get(key, '') == '':
                if default_value is NO_DEFAULT:
                    raise ValueError(f"{key} must be specified")
                form_data[key] = default_value

        for key, value in form_data.items():
            if key in _CAST_RULES_FORM_ARG_TO_NATIVE:
                form_data[key] = _CAST_RULES_FORM_ARG_TO_NATIVE[key](value)

            if key not in cls._DEFAULTS:
                raise ValueError(
                    f'Invalid argument "{html.escape(key)}" given')

        instance = cls(**form_data, data_registry=data_registry)
        instance.validate()
        return instance

    @classmethod
    def to_dict(cls, form: "FormData", strip_defaults: bool = False) -> dict:
        form_dict = {
            field.name: getattr(form, field.name)
            for field in dataclasses.fields(form)
        }

        for attr, value in form_dict.items():
            if attr in _CAST_RULES_NATIVE_TO_FORM_ARG:
                form_dict[attr] = _CAST_RULES_NATIVE_TO_FORM_ARG[attr](value)

        if strip_defaults:
            del form_dict['calculator_version']

            for attr, value in list(form_dict.items()):
                default = cls._DEFAULTS.get(attr, NO_DEFAULT)
                if default is not NO_DEFAULT and value in [default, 'not-applicable']:
                    form_dict.pop(attr)
        return form_dict

    def validate_population_parameters(self):
        # Static occupancy is defined.
        if self.occupancy_format == 'static':        
            # Validate number of infected <= number of total people
            if self.infected_people >= self.total_people:
                raise ValueError(
                    'Number of infected people cannot be greater or equal to the number of total people.')

            # Validate time intervals selected by user
            time_intervals = [
                ['exposed_start', 'exposed_finish'],
                ['infected_start', 'infected_finish'],
            ]
            if self.exposed_lunch_option:
                time_intervals.append(
                    ['exposed_lunch_start', 'exposed_lunch_finish'])
            if self.infected_dont_have_breaks_with_exposed and self.infected_lunch_option:
                time_intervals.append(
                    ['infected_lunch_start', 'infected_lunch_finish'])

            for start_name, end_name in time_intervals:
                start = getattr(self, start_name)
                end = getattr(self, end_name)
                if start > end:
                    raise ValueError(
                        f"{start_name} must be less than {end_name}. Got {start} and {end}.")

            def validate_lunch(start, finish):
                lunch_start = getattr(self, f'{population}_lunch_start')
                lunch_finish = getattr(self, f'{population}_lunch_finish')
                return (start <= lunch_start <= finish and
                        start <= lunch_finish <= finish)

            def get_lunch_mins(population):
                lunch_mins = 0
                if getattr(self, f'{population}_lunch_option'):
                    lunch_mins = getattr(
                        self, f'{population}_lunch_finish') - getattr(self, f'{population}_lunch_start')
                return lunch_mins

            def get_coffee_mins(population):
                coffee_mins = 0
                if getattr(self, f'{population}_coffee_break_option') != 'coffee_break_0':
                    coffee_mins = COFFEE_OPTIONS_INT[getattr(
                        self, f'{population}_coffee_break_option')] * getattr(self, f'{population}_coffee_duration')
                return coffee_mins

            def get_activity_mins(population):
                return getattr(self, f'{population}_finish') - getattr(self, f'{population}_start')

            populations = [
                'exposed', 'infected'] if self.infected_dont_have_breaks_with_exposed else ['exposed']
            for population in populations:
                # Validate lunch time within the activity times.
                if (getattr(self, f'{population}_lunch_option') and
                        not validate_lunch(getattr(self, f'{population}_start'), getattr(
                            self, f'{population}_finish'))
                        ):
                    raise ValueError(
                        f"{population} lunch break must be within presence times."
                    )

                # Length of breaks < length of activity
                if (get_lunch_mins(population) + get_coffee_mins(population)) >= get_activity_mins(population):
                    raise ValueError(
                        f"Length of breaks >= Length of {population} presence."
                    )

                for attr_name, valid_set in [('exposed_coffee_break_option', COFFEE_OPTIONS_INT),
                                            ('infected_coffee_break_option', COFFEE_OPTIONS_INT)]:
                    if getattr(self, attr_name) not in valid_set:
                        raise ValueError(
                            f"{getattr(self, attr_name)} is not a valid value for {attr_name}")
        # Dynamic occupancy is defined.
        elif self.occupancy_format == 'dynamic':
            for dynamic_format in (self.dynamic_infected_occupancy, self.dynamic_exposed_occupancy):
                for occupancy in dynamic_format:
                    # Check if each occupancy entry is a dictionary
                    if not isinstance(occupancy, typing.Dict):
                        raise TypeError(f'Each occupancy entry should be in a dictionary format. Got "{type(occupancy)}".')
                    
                    # Check for required keys in each occupancy entry
                    dict_keys = list(occupancy.keys())
                    if "total_people" not in dict_keys:
                        raise TypeError(f'Unable to fetch "total_people" key. Got "{dict_keys}".')
                    else:
                        value = occupancy["total_people"]
                        # Check if the value is a non-negative integer
                        if not isinstance(value, int):
                            raise ValueError(f'Total number of people should be integer. Got "{type(value)}".')
                        elif not value >= 0:
                            raise ValueError(f'Total number of people should be non-negative. Got "{value}".')
                    
                    if "start_time" not in dict_keys:
                        raise TypeError(f'Unable to fetch "start_time" key. Got "{dict_keys}".')
                    if "finish_time" not in dict_keys:
                        raise TypeError(f'Unable to fetch "finish_time" key. Got "{dict_keys}".')

                    # Validate time format for start_time and finish_time
                    for time_key in ["start_time", "finish_time"]:
                        time = occupancy[time_key]
                        if not re.compile("^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$").match(time):
                            raise TypeError(f'Wrong time format - "HH:MM". Got "{time}".')
        else:
            raise ValueError(f"'{self.occupancy_format}' is not a valid value for 'self.occupancy_format'. Accepted values are 'static' or 'dynamic'.")

    def validate(self):
        raise NotImplementedError("Subclass must implement")

    def build_model(self, sample_size: typing.Optional[int] = None):
        raise NotImplementedError("Subclass must implement")

    def _compute_breaks_in_interval(self, start, finish, n_breaks, duration) -> models.BoundarySequence_t:
        break_delay = ((finish - start) -
                       (n_breaks * duration)) // (n_breaks+1)
        break_times = []
        end = start
        for n in range(n_breaks):
            begin = end + break_delay
            end = begin + duration
            break_times.append((begin, end))
        return tuple(break_times)

    def exposed_lunch_break_times(self) -> models.BoundarySequence_t:
        result = []
        if self.exposed_lunch_option:
            result.append((self.exposed_lunch_start,
                          self.exposed_lunch_finish))
        return tuple(result)

    def infected_lunch_break_times(self) -> models.BoundarySequence_t:
        if self.infected_dont_have_breaks_with_exposed:
            result = []
            if self.infected_lunch_option:
                result.append((self.infected_lunch_start,
                              self.infected_lunch_finish))
            return tuple(result)
        else:
            return self.exposed_lunch_break_times()

    def exposed_number_of_coffee_breaks(self) -> int:
        return COFFEE_OPTIONS_INT[self.exposed_coffee_break_option]

    def infected_number_of_coffee_breaks(self) -> int:
        return COFFEE_OPTIONS_INT[self.infected_coffee_break_option]

    def _coffee_break_times(self, activity_start, activity_finish, coffee_breaks, coffee_duration, lunch_start, lunch_finish) -> models.BoundarySequence_t:
        time_before_lunch = lunch_start - activity_start
        time_after_lunch = activity_finish - lunch_finish
        before_lunch_frac = time_before_lunch / \
            (time_before_lunch + time_after_lunch)
        n_morning_breaks = round(coffee_breaks * before_lunch_frac)
        breaks = (
            self._compute_breaks_in_interval(
                activity_start, lunch_start, n_morning_breaks, coffee_duration
            )
            + self._compute_breaks_in_interval(
                lunch_finish, activity_finish, coffee_breaks - n_morning_breaks, coffee_duration
            )
        )
        return breaks

    def exposed_coffee_break_times(self) -> models.BoundarySequence_t:
        exposed_coffee_breaks = self.exposed_number_of_coffee_breaks()
        if exposed_coffee_breaks == 0:
            return ()
        if self.exposed_lunch_option:
            breaks = self._coffee_break_times(self.exposed_start, self.exposed_finish, exposed_coffee_breaks,
                                              self.exposed_coffee_duration, self.exposed_lunch_start, self.exposed_lunch_finish)
        else:
            breaks = self._compute_breaks_in_interval(
                self.exposed_start, self.exposed_finish, exposed_coffee_breaks, self.exposed_coffee_duration)
        return breaks

    def infected_coffee_break_times(self) -> models.BoundarySequence_t:
        if self.infected_dont_have_breaks_with_exposed:
            infected_coffee_breaks = self.infected_number_of_coffee_breaks()
            if infected_coffee_breaks == 0:
                return ()
            if self.infected_lunch_option:
                breaks = self._coffee_break_times(self.infected_start, self.infected_finish, infected_coffee_breaks,
                                                  self.infected_coffee_duration, self.infected_lunch_start, self.infected_lunch_finish)
            else:
                breaks = self._compute_breaks_in_interval(
                    self.infected_start, self.infected_finish, infected_coffee_breaks, self.infected_coffee_duration)
            return breaks
        else:
            return self.exposed_coffee_break_times()

    def generate_specific_break_times(self, breaks_dict: dict, target: str) -> models.BoundarySequence_t:
        break_times = []
        for n in breaks_dict[f'{target}_breaks']:
            # Parse break times.
            begin = time_string_to_minutes(n["start_time"])
            end = time_string_to_minutes(n["finish_time"])
            for time in [begin, end]:
                # For a specific break, the infected and exposed presence is the same.
                if not getattr(self, f'{target}_start') < time < getattr(self, f'{target}_finish'):
                    raise ValueError(
                        f'All breaks should be within the simulation time. Got {time_minutes_to_string(time)}.')

            break_times.append((begin, end))
        return tuple(break_times)

    def present_interval(
            self,
            start: int,
            finish: int,
            breaks: typing.Optional[models.BoundarySequence_t] = None,
    ) -> models.Interval:
        """
        Calculate the presence interval given the start and end times (in minutes), and
        a number of monotonic, non-overlapping, but potentially unsorted, breaks (also in minutes).

        """
        if not breaks:
            # If there are no breaks, the interval is the start and end.
            return models.SpecificInterval(((start/60, finish/60),))

        # Order the breaks by their start-time, and ensure that they are monotonic
        # and that the start of one break happens after the end of another.
        break_boundaries: models.BoundarySequence_t = tuple(
            sorted(breaks, key=lambda break_pair: break_pair[0]))

        for break_start, break_end in break_boundaries:
            if break_start >= break_end:
                raise ValueError("Break ends before it begins.")

        prev_break_end = break_boundaries[0][1]
        for break_start, break_end in break_boundaries[1:]:
            if prev_break_end >= break_start:
                raise ValueError(
                    f"A break starts before another ends ({break_start}, {break_end}, {prev_break_end}).")
            prev_break_end = break_end

        present_intervals = []

        current_time = start
        LOG.debug(
            f"starting time march at {_hours2timestring(current_time/60)} to {_hours2timestring(finish/60)}")

        # As we step through the breaks. For each break there are 6 important cases
        # we must cover. Let S=start; E=end; Bs=Break start; Be=Break end:
        #  1. The interval is entirely before the break. S < E <= Bs < Be
        #  2. The interval straddles the start of the break. S < Bs < E <= Be
        #  3. The break is entirely inside the interval. S < Bs < Be <= E
        #  4. The interval is entirely inside the break. Bs <= S < E <= Be
        #  5. The interval straddles the end of the break. Bs <= S < Be <= E
        #  6. The interval is entirely after the break. Bs < Be <= S < E

        for current_break in break_boundaries:
            if current_time >= finish:
                break

            LOG.debug(f"handling break {_hours2timestring(current_break[0]/60)}-{_hours2timestring(current_break[1]/60)} "
                      f" (current time: {_hours2timestring(current_time/60)})")

            break_s, break_e = current_break
            case1 = finish <= break_s
            case2 = current_time < break_s < finish < break_e
            case3 = current_time < break_s < break_e <= finish
            case4 = break_s <= current_time < finish <= break_e
            case5 = break_s <= current_time < break_e < finish
            case6 = break_e <= current_time

            if case1:
                LOG.debug(f"case 1: interval entirely before break")
                present_intervals.append((current_time / 60, finish / 60))
                LOG.debug(f" + added interval {_hours2timestring(present_intervals[-1][0])} "
                          f"- {_hours2timestring(present_intervals[-1][1])}")
                current_time = finish
            elif case2:
                LOG.debug(f"case 2: interval straddles start of break")
                present_intervals.append((current_time / 60, break_s / 60))
                LOG.debug(f" + added interval {_hours2timestring(present_intervals[-1][0])} "
                          f"- {_hours2timestring(present_intervals[-1][1])}")
                current_time = break_e
            elif case3:
                LOG.debug(f"case 3: break entirely inside interval")
                # We add the bit before the break, but not the bit afterwards,
                # as it may hit another break.
                present_intervals.append((current_time / 60, break_s / 60))
                LOG.debug(f" + added interval {_hours2timestring(present_intervals[-1][0])} "
                          f"- {_hours2timestring(present_intervals[-1][1])}")
                current_time = break_e
            elif case4:
                LOG.debug(f"case 4: interval entirely inside break")
                current_time = finish
            elif case5:
                LOG.debug(f"case 5: interval straddles end of break")
                current_time = break_e
            elif case6:
                LOG.debug(f"case 6: interval entirely after the break")

        if current_time < finish:
            LOG.debug("trailing interval")
            present_intervals.append((current_time / 60, finish / 60))
        return models.SpecificInterval(tuple(present_intervals))

    def infected_present_interval(self) -> models.Interval:
        if self.specific_breaks != {}:  # It means the breaks are specific and not predefined
            breaks = self.generate_specific_break_times(
                breaks_dict=self.specific_breaks, target='exposed')
        else:
            breaks = self.infected_lunch_break_times() + self.infected_coffee_break_times()
        return self.present_interval(
            self.infected_start, self.infected_finish,
            breaks=breaks,
        )

    def exposed_present_interval(self) -> models.Interval:
        if self.specific_breaks != {}:  # It means the breaks are specific and not predefined
            breaks = self.generate_specific_break_times(
                breaks_dict=self.specific_breaks, target='exposed')
        else:
            breaks = self.exposed_lunch_break_times() + self.exposed_coffee_break_times()
        return self.present_interval(
            self.exposed_start, self.exposed_finish,
            breaks=breaks,
        )
    
    def generate_dynamic_occupancy(self, dynamic_occupancy: typing.List[typing.Dict[str, typing.Any]]):
        transition_times = []
        values = []
        for occupancy in dynamic_occupancy:
            start_time = time_string_to_minutes(occupancy['start_time'])/60
            finish_time = time_string_to_minutes(occupancy['finish_time'])/60
            transition_times.extend([start_time, finish_time])
            values.append(occupancy['total_people'])

        unique_transition_times_sorted = np.array(sorted(set(transition_times)))

        if len(values) != len(unique_transition_times_sorted) - 1:
            raise ValueError("Cannot compute dynamic occupancy with the provided inputs.")
        
        population_occupancy: models.IntPiecewiseConstant = models.IntPiecewiseConstant(
            transition_times=tuple(unique_transition_times_sorted),
            values=tuple(values)
        )
        return population_occupancy


def _hours2timestring(hours: float):
    # Convert times like 14.5 to strings, like "14:30"
    return f"{int(np.floor(hours)):02d}:{int(np.round((hours % 1) * 60)):02d}"


def time_string_to_minutes(time: str) -> minutes_since_midnight:
    """
    Converts time from string-format to an integer number of minutes after 00:00
    :param time: A string of the form "HH:MM" representing a time of day
    :return: The number of minutes between 'time' and 00:00
    """
    return minutes_since_midnight(60 * int(time[:2]) + int(time[3:]))


def time_minutes_to_string(time: int) -> str:
    """
    Converts time from an integer number of minutes after 00:00 to string-format
    :param time: The number of minutes between 'time' and 00:00
    :return: A string of the form "HH:MM" representing a time of day
    """
    return "{0:0=2d}".format(int(time/60)) + ":" + "{0:0=2d}".format(time % 60)


def string_to_list(s: str) -> list:
    return list(ast.literal_eval(s.replace("&quot;", "\"")))


def list_to_string(l: list) -> str:
    return json.dumps(l)


def string_to_dict(s: str) -> dict:
    return dict(ast.literal_eval(s.replace("&quot;", "\"")))


def dict_to_string(d: dict) -> str:
    return json.dumps(d)


def _safe_int_cast(value) -> int:
    if isinstance(value, int):
        return value
    elif isinstance(value, float) and int(value) == value:
        return int(value)
    elif isinstance(value, str) and value.isdecimal():
        return int(value)
    else:
        raise TypeError(f"Unable to safely cast {value} ({type(value)} type) to int")
    

def _safe_optional_int_cast(value) -> typing.Optional[int]:
    if value is None or value == '':
        return None
    return _safe_int_cast(value)


#: Mapping of field name to a callable which can convert values from form
#: input (URL encoded arguments / string) into the correct type.
_CAST_RULES_FORM_ARG_TO_NATIVE: typing.Dict[str, typing.Callable] = {}

#: Mapping of field name to callable which can convert native type to values
#: that can be encoded to URL arguments.
_CAST_RULES_NATIVE_TO_FORM_ARG: typing.Dict[str, typing.Callable] = {}


def cast_class_fields(cls):
    for _field in dataclasses.fields(cls):
        if _field.type is minutes_since_midnight:
            _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = time_string_to_minutes
            _CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = time_minutes_to_string
        elif _field.type is int:
            _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = _safe_int_cast
        elif _field.type is typing.Optional[int]:
            _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = _safe_optional_int_cast
        elif _field.type is float:
            _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = float
        elif _field.type is bool:
            _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = lambda v: v == '1'
            _CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = int
        elif _field.type is list:
            _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = string_to_list
            _CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = list_to_string
        elif _field.type is dict:
            _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = string_to_dict
            _CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = dict_to_string


cast_class_fields(FormData)
