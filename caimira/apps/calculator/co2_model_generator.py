import dataclasses
import html
import logging
import typing

from caimira import models
from . import model_generator

minutes_since_midnight = typing.NewType('minutes_since_midnight', int)

LOG = logging.getLogger(__name__)

# Used to declare when an attribute of a class must have a value provided, and
# there should be no default value used.
_NO_DEFAULT = object()


@dataclasses.dataclass
class CO2FormData:
    CO2_data: dict
    specific_breaks: dict
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
    infected_people: int
    infected_start: minutes_since_midnight
    room_volume: float
    total_people: int
    ventilation_type: str
    windows_duration: float
    windows_frequency: float
    window_opening_regime: str

    #: The default values for undefined fields. Note that the defaults here
    #: and the defaults in the html form must not be contradictory.
    _DEFAULTS: typing.ClassVar[typing.Dict[str, typing.Any]] = {
        'CO2_data': '{}',
        'specific_breaks': '{}', # CHECK INTEGRATION WITH WHO
        'exposed_coffee_break_option': 'coffee_break_0',
        'exposed_coffee_duration': 5,
        'exposed_finish': '17:30',
        'exposed_lunch_finish': '13:30',
        'exposed_lunch_option': True,
        'exposed_lunch_start': '12:30',
        'exposed_start': '08:30',
        'infected_coffee_break_option': 'coffee_break_0',
        'infected_coffee_duration': 5,
        'infected_dont_have_breaks_with_exposed': False,
        'infected_finish': '17:30',
        'infected_lunch_finish': '13:30',
        'infected_lunch_option': True,
        'infected_lunch_start': '12:30',
        'infected_people': 1,
        'infected_start': '08:30',
        'room_volume': _NO_DEFAULT,
        'total_people': _NO_DEFAULT,
        'ventilation_type': 'no_ventilation',
        'windows_duration': 10.,
        'windows_frequency': 60.,
        'window_opening_regime': 'windows_open_permanently', 
    }

    @classmethod
    def from_dict(cls, form_data: typing.Dict) -> "CO2FormData":
        # Take a copy of the form data so that we can mutate it.
        form_data = form_data.copy()
        form_data.pop('_xsrf', None)

        # Don't let arbitrary unescaped HTML through the net.
        for key, value in form_data.items():
            if isinstance(value, str):
                form_data[key] = html.escape(value)

        for key, default_value in cls._DEFAULTS.items():
            if form_data.get(key, '') == '':
                if default_value is _NO_DEFAULT:
                    raise ValueError(f"{key} must be specified")
                form_data[key] = default_value

        for key, value in form_data.items():
            if key in model_generator._CAST_RULES_FORM_ARG_TO_NATIVE:
                form_data[key] = model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[key](value)

            if key not in cls._DEFAULTS:
                raise ValueError(f'Invalid argument "{html.escape(key)}" given')

        instance = cls(**form_data)
        # instance.validate()
        return instance

    def build_model(self) -> models.CO2Data:
        population_presence=self.population_present_interval()
        last_time_present = population_presence.boundaries()[-1][-1]
        last_present_time_index = next((index for index, time in enumerate(self.CO2_data['times']) 
                                        if time > last_time_present), len(self.CO2_data['times']))
        return models.CO2Data(
                room_volume=self.room_volume,
                number=self.total_people,
                presence=population_presence,
                ventilation_transition_times=self.ventilation_transition_times(last_time_present),
                times=self.CO2_data['times'][:last_present_time_index],
                CO2_concentrations=self.CO2_data['CO2'][:last_present_time_index],
            ) 

    def _compute_breaks_in_interval(self, start, finish, n_breaks, duration) -> models.BoundarySequence_t:
        break_delay = ((finish - start) - (n_breaks * duration)) // (n_breaks+1)
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
            result.append((self.exposed_lunch_start, self.exposed_lunch_finish))
        return tuple(result)

    def infected_lunch_break_times(self) -> models.BoundarySequence_t:
        if self.infected_dont_have_breaks_with_exposed:
            result = []
            if self.infected_lunch_option:
                result.append((self.infected_lunch_start, self.infected_lunch_finish))
            return tuple(result)
        else:
            return self.exposed_lunch_break_times()

    def exposed_number_of_coffee_breaks(self) -> int:
        return model_generator.COFFEE_OPTIONS_INT[self.exposed_coffee_break_option]

    def infected_number_of_coffee_breaks(self) -> int:
        return model_generator.COFFEE_OPTIONS_INT[self.infected_coffee_break_option]

    def _coffee_break_times(self, activity_start, activity_finish, coffee_breaks, coffee_duration, lunch_start, lunch_finish) -> models.BoundarySequence_t:
        time_before_lunch = lunch_start - activity_start
        time_after_lunch = activity_finish - lunch_finish
        before_lunch_frac = time_before_lunch / (time_before_lunch + time_after_lunch)
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
            breaks = self._coffee_break_times(self.exposed_start, self.exposed_finish, exposed_coffee_breaks, self.exposed_coffee_duration, self.exposed_lunch_start, self.exposed_lunch_finish)
        else:
            breaks = self._compute_breaks_in_interval(self.exposed_start, self.exposed_finish, exposed_coffee_breaks, self.exposed_coffee_duration)
        return breaks

    def infected_coffee_break_times(self) -> models.BoundarySequence_t:
        if self.infected_dont_have_breaks_with_exposed:
            infected_coffee_breaks = self.infected_number_of_coffee_breaks()
            if infected_coffee_breaks == 0:
                return ()
            if self.infected_lunch_option:
                breaks = self._coffee_break_times(self.infected_start, self.infected_finish, infected_coffee_breaks, self.infected_coffee_duration, self.infected_lunch_start, self.infected_lunch_finish)
            else:
                breaks = self._compute_breaks_in_interval(self.infected_start, self.infected_finish, infected_coffee_breaks, self.infected_coffee_duration)
            return breaks
        else:
            return self.exposed_coffee_break_times()

    def generate_specific_break_times(self, population_breaks) -> models.BoundarySequence_t:
        break_times = []
        for n in population_breaks:
            # Parse break times.  
            begin = model_generator.time_string_to_minutes(n["start_time"])
            end = model_generator.time_string_to_minutes(n["finish_time"])
            for time in [begin, end]:
                # For a specific break, the infected and exposed presence is the same.
                if not getattr(self, 'infected_start') < time < getattr(self, 'infected_finish'):
                    raise ValueError(f'All breaks should be within the simulation time. Got {model_generator.time_minutes_to_string(time)}.')

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
        break_boundaries: models.BoundarySequence_t = tuple(sorted(breaks, key=lambda break_pair: break_pair[0]))

        for break_start, break_end in break_boundaries:
            if break_start >= break_end:
                raise ValueError("Break ends before it begins.")

        prev_break_end = break_boundaries[0][1]
        for break_start, break_end in break_boundaries[1:]:
            if prev_break_end >= break_start:
                raise ValueError(f"A break starts before another ends ({break_start}, {break_end}, {prev_break_end}).")
            prev_break_end = break_end

        present_intervals = []

        current_time = start
        LOG.debug(f"starting time march at {model_generator._hours2timestring(current_time/60)} to {model_generator._hours2timestring(finish/60)}")

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

            LOG.debug(f"handling break {model_generator._hours2timestring(current_break[0]/60)}-{model_generator._hours2timestring(current_break[1]/60)} "
                      f" (current time: {model_generator._hours2timestring(current_time/60)})")

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
                LOG.debug(f" + added interval {model_generator._hours2timestring(present_intervals[-1][0])} "
                          f"- {model_generator._hours2timestring(present_intervals[-1][1])}")
                current_time = finish
            elif case2:
                LOG.debug(f"case 2: interval straddles start of break")
                present_intervals.append((current_time / 60, break_s / 60))
                LOG.debug(f" + added interval {model_generator._hours2timestring(present_intervals[-1][0])} "
                          f"- {model_generator._hours2timestring(present_intervals[-1][1])}")
                current_time = break_e
            elif case3:
                LOG.debug(f"case 3: break entirely inside interval")
                # We add the bit before the break, but not the bit afterwards,
                # as it may hit another break.
                present_intervals.append((current_time / 60, break_s / 60))
                LOG.debug(f" + added interval {model_generator._hours2timestring(present_intervals[-1][0])} "
                          f"- {model_generator._hours2timestring(present_intervals[-1][1])}")
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
        if self.specific_breaks != {}: # It means the breaks are specific and not predefined
            breaks = self.generate_specific_break_times(self.specific_breaks['infected_breaks'])
        else:
            breaks = self.infected_lunch_break_times() + self.infected_coffee_break_times()
        return self.present_interval(
            self.infected_start, self.infected_finish,
            breaks=breaks,
        )
    
    def population_present_interval(self) -> models.Interval:
        state_change_times = set(self.infected_present_interval().transition_times())
        state_change_times.update(self.exposed_present_interval().transition_times())
        all_state_changes = sorted(state_change_times)
        return models.SpecificInterval(tuple(zip(all_state_changes[:-1], all_state_changes[1:])))

    def exposed_present_interval(self) -> models.Interval:
        if self.specific_breaks != {}: # It means the breaks are specific and not predefined
            breaks = self.generate_specific_break_times(self.specific_breaks['exposed_breaks'])
        else:
            breaks = self.exposed_lunch_break_times() + self.exposed_coffee_break_times()
        return self.present_interval(
            self.exposed_start, self.exposed_finish,
            breaks=breaks,
        )

    def ventilation_transition_times(self, last_present_time) -> typing.Tuple[float, ...]:
        if self.ventilation_type == 'from_fitting' and self.window_opening_regime == 'windows_open_periodically':
            transition_times = sorted(models.PeriodicInterval(self.windows_frequency, 
                    self.windows_duration, min(self.infected_start, self.exposed_start)/60).transition_times())
            return tuple(filter(lambda x: x < last_present_time, transition_times))
        else:
            return tuple((min(self.infected_start, self.exposed_start)/60, max(self.infected_finish, self.exposed_finish)/60), ) # all day long
