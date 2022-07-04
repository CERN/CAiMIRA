import dataclasses
import datetime
import html
import logging
import typing
import ast
import json 

import numpy as np

from cara import models
from cara import data
import cara.data.weather
import cara.monte_carlo as mc
from .. import calculator
from cara.monte_carlo.data import activity_distributions, virus_distributions, mask_distributions, short_range_distances
from cara.monte_carlo.data import expiration_distribution, expiration_BLO_factors, expiration_distributions, short_range_expiration_distributions

LOG = logging.getLogger(__name__)

minutes_since_midnight = typing.NewType('minutes_since_midnight', int)

# Used to declare when an attribute of a class must have a value provided, and
# there should be no default value used.
_NO_DEFAULT = object()
_DEFAULT_MC_SAMPLE_SIZE = 250000


@dataclasses.dataclass
class FormData:
    activity_type: str
    air_changes: float
    air_supply: float
    ceiling_height: float
    exposed_coffee_break_option: str
    exposed_coffee_duration: int
    exposed_finish: minutes_since_midnight
    exposed_lunch_finish: minutes_since_midnight
    exposed_lunch_option: bool
    exposed_lunch_start: minutes_since_midnight
    exposed_start: minutes_since_midnight
    floor_area: float
    hepa_amount: float
    hepa_option: bool
    humidity: str
    infected_coffee_break_option: str               #Used if infected_dont_have_breaks_with_exposed
    infected_coffee_duration: int                   #Used if infected_dont_have_breaks_with_exposed
    infected_dont_have_breaks_with_exposed: bool
    infected_finish: minutes_since_midnight
    infected_lunch_finish: minutes_since_midnight   #Used if infected_dont_have_breaks_with_exposed
    infected_lunch_option: bool                     #Used if infected_dont_have_breaks_with_exposed
    infected_lunch_start: minutes_since_midnight    #Used if infected_dont_have_breaks_with_exposed
    infected_people: int
    infected_start: minutes_since_midnight
    inside_temp: float
    location_name: str
    location_latitude: float
    location_longitude: float
    geographic_population: int
    geographic_cases: int
    geographic_conf_level: str
    p_recurrent_option: str
    mask_type: str
    mask_wearing_option: str
    mechanical_ventilation_type: str
    calculator_version: str
    opening_distance: float
    event_month: str
    room_heating_option: bool
    room_number: str
    room_volume: float
    simulation_name: str
    total_people: int
    ventilation_type: str
    virus_type: str
    volume_type: str
    windows_duration: float
    windows_frequency: float
    window_height: float
    window_type: str
    window_width: float
    windows_number: int
    window_opening_regime: str
    short_range_option: str
    short_range_interactions: list

    #: The default values for undefined fields. Note that the defaults here
    #: and the defaults in the html form must not be contradictory.
    _DEFAULTS: typing.ClassVar[typing.Dict[str, typing.Any]] = {
        'activity_type': 'office',
        'air_changes': 0.,
        'air_supply': 0.,
        'calculator_version': _NO_DEFAULT,
        'ceiling_height': 0.,
        'exposed_coffee_break_option': 'coffee_break_0',
        'exposed_coffee_duration': 5,
        'exposed_finish': '17:30',
        'exposed_lunch_finish': '13:30',
        'exposed_lunch_option': True,
        'exposed_lunch_start': '12:30',
        'exposed_start': '08:30',
        'event_month': 'January',
        'floor_area': 0.,
        'hepa_amount': 0.,
        'hepa_option': False,
        'humidity': '',
        'infected_coffee_break_option': 'coffee_break_0',
        'infected_coffee_duration': 5,
        'infected_dont_have_breaks_with_exposed': False,
        'infected_finish': '17:30',
        'infected_lunch_finish': '13:30',
        'infected_lunch_option': True,
        'infected_lunch_start': '12:30',
        'infected_people': _NO_DEFAULT,
        'infected_start': '08:30',
        'inside_temp': 293.,
        'location_latitude': _NO_DEFAULT,
        'location_longitude': _NO_DEFAULT,
        'geographic_population': _NO_DEFAULT,
        'geographic_cases': _NO_DEFAULT,
        'geographic_conf_level': 'confidence_low',
        'p_recurrent_option': 'p_recurrent_event',
        'location_name': _NO_DEFAULT,
        'mask_type': 'Type I',
        'mask_wearing_option': 'mask_off',
        'mechanical_ventilation_type': 'not-applicable',
        'opening_distance': 0.,
        'room_heating_option': False,
        'room_number': _NO_DEFAULT,
        'room_volume': 0.,
        'simulation_name': _NO_DEFAULT,
        'total_people': _NO_DEFAULT,
        'ventilation_type': 'no_ventilation',
        'virus_type': 'SARS_CoV_2',
        'volume_type': _NO_DEFAULT,
        'window_type': 'window_sliding',
        'window_height': 0.,
        'window_width': 0.,
        'windows_duration': 0.,
        'windows_frequency': 0.,
        'windows_number': 0,
        'window_opening_regime': 'windows_open_permanently',
        'short_range_option': 'short_range_no',
        'short_range_interactions': '[]',
    }

    @classmethod
    def from_dict(cls, form_data: typing.Dict) -> "FormData":
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
            if key in _CAST_RULES_FORM_ARG_TO_NATIVE:
                form_data[key] = _CAST_RULES_FORM_ARG_TO_NATIVE[key](value)

            if key not in cls._DEFAULTS:
                raise ValueError(f'Invalid argument "{html.escape(key)}" given')

        instance = cls(**form_data)
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
                default = cls._DEFAULTS.get(attr, _NO_DEFAULT)
                if default is not _NO_DEFAULT and value in [default, 'not-applicable']:
                    form_dict.pop(attr)
        return form_dict

    def validate(self):
        # Validate time intervals selected by user
        time_intervals = [
            ['exposed_start', 'exposed_finish'],
            ['infected_start', 'infected_finish'],
        ]
        if self.exposed_lunch_option:
            time_intervals.append(['exposed_lunch_start', 'exposed_lunch_finish'])
        if self.infected_dont_have_breaks_with_exposed and self.infected_lunch_option:
            time_intervals.append(['infected_lunch_start', 'infected_lunch_finish'])

        for start_name, end_name in time_intervals:
            start = getattr(self, start_name)
            end = getattr(self, end_name)
            if start > end:
                raise ValueError(
                    f"{start_name} must be less than {end_name}. Got {start} and {end}.")

        validation_tuples = [('activity_type', ACTIVITY_TYPES),    
                             ('exposed_coffee_break_option', COFFEE_OPTIONS_INT), 
                             ('infected_coffee_break_option', COFFEE_OPTIONS_INT),   
                             ('mechanical_ventilation_type', MECHANICAL_VENTILATION_TYPES),
                             ('mask_type', MASK_TYPES),
                             ('mask_wearing_option', MASK_WEARING_OPTIONS),
                             ('ventilation_type', VENTILATION_TYPES),
                             ('virus_type', VIRUS_TYPES),
                             ('volume_type', VOLUME_TYPES),
                             ('window_opening_regime', WINDOWS_OPENING_REGIMES),
                             ('window_type', WINDOWS_TYPES),
                             ('event_month', MONTH_NAMES),
                             ('geographic_conf_level', CONFIDENCE_LEVEL_OPTIONS),]
        for attr_name, valid_set in validation_tuples:
            if getattr(self, attr_name) not in valid_set:
                raise ValueError(f"{getattr(self, attr_name)} is not a valid value for {attr_name}")

        if self.ventilation_type == 'natural_ventilation':
            if self.window_type == 'not-applicable':
                raise ValueError(
                    "window_type cannot be 'not-applicable' if "
                    "ventilation_type is 'natural_ventilation'"
                )
            if self.window_opening_regime == 'not-applicable':
                raise ValueError(
                    "window_opening_regime cannot be 'not-applicable' if "
                    "ventilation_type is 'natural_ventilation'"
                )

        if (self.ventilation_type == 'mechanical_ventilation'
                and self.mechanical_ventilation_type == 'not-applicable'):
            raise ValueError("mechanical_ventilation_type cannot be 'not-applicable' if "
                             "ventilation_type is 'mechanical_ventilation'")

    def build_mc_model(self) -> mc.ExposureModel:
        # Initializes room with volume either given directly or as product of area and height
        if self.volume_type == 'room_volume_explicit':
            volume = self.room_volume
        else:
            volume = self.floor_area * self.ceiling_height
        if self.humidity == '':
            if self.room_heating_option:
                humidity = 0.3
            else:
                humidity = 0.5
        else:
            humidity = float(self.humidity)
        room = models.Room(volume=volume, inside_temp=models.PiecewiseConstant((0, 24), (self.inside_temp,)), humidity=humidity)

        infected_population = self.infected_population()
        
        short_range = []
        if self.short_range_option == "short_range_yes":
            for interaction in self.short_range_interactions:
                short_range.append(mc.ShortRangeModel(
                    expiration=short_range_expiration_distributions[interaction['expiration']],
                    activity=infected_population.activity,
                    presence=self.short_range_interval(interaction),
                    distance=short_range_distances,
                ))

        # Initializes and returns a model with the attributes defined above
        return mc.ExposureModel(
            concentration_model=mc.ConcentrationModel(
                room=room,
                ventilation=self.ventilation(),
                infected=infected_population,
                evaporation_factor=0.3,
            ),
            short_range = tuple(short_range),
            exposed=self.exposed_population(),
            geographical_data=mc.Cases(
                geographic_population=self.geographic_population,
                geographic_cases=self.geographic_cases,
                geographic_conf_level=CONFIDENCE_LEVEL_OPTIONS[self.geographic_conf_level],
            ), 
        )

    def build_model(self, sample_size=_DEFAULT_MC_SAMPLE_SIZE) -> models.ExposureModel:
        return self.build_mc_model().build_model(size=sample_size)

    def tz_name_and_utc_offset(self) -> typing.Tuple[str, float]:
        """
        Return the timezone name (e.g. CET), and offset, in hours, that need to
        be *added* to UTC to convert to the form location's timezone.

        """
        month = MONTH_NAMES.index(self.event_month) + 1
        timezone = cara.data.weather.timezone_at(
            latitude=self.location_latitude, longitude=self.location_longitude,
        )
        # We choose the first of the month for the current year.
        date = datetime.datetime(datetime.datetime.now().year, month, 1)
        name = timezone.tzname(date)
        assert isinstance(name, str)
        utc_offset_td = timezone.utcoffset(date)
        assert isinstance(utc_offset_td, datetime.timedelta)
        utc_offset_hours = utc_offset_td.total_seconds() / 60 / 60
        return name, utc_offset_hours

    def outside_temp(self) -> models.PiecewiseConstant:
        """
        Return the outside temperature as a PiecewiseConstant in the destination
        timezone.

        """
        month = MONTH_NAMES.index(self.event_month) + 1

        wx_station = self.nearest_weather_station()
        temp_profile = cara.data.weather.mean_hourly_temperatures(wx_station[0], month)

        _, utc_offset = self.tz_name_and_utc_offset()

        # Offset the source times according to the difference from UTC (as a
        # result the first data value may no longer be a midnight, and the hours
        # no longer ordered modulo 24).
        source_times = np.arange(24) + utc_offset
        times, temp_profile = cara.data.weather.refine_hourly_data(
            source_times,
            temp_profile,
            npts=24*10,  # 10 steps per hour => 6 min steps
        )
        outside_temp = models.PiecewiseConstant(
            tuple(float(t) for t in times), tuple(float(t) for t in temp_profile),
        )
        return outside_temp

    def ventilation(self) -> models._VentilationBase:
        always_on = models.PeriodicInterval(period=120, duration=120)
        # Initializes a ventilation instance as a window if 'natural_ventilation' is selected, or as a HEPA-filter otherwise
        if self.ventilation_type == 'natural_ventilation':
            if self.window_opening_regime == 'windows_open_periodically':
                window_interval = models.PeriodicInterval(self.windows_frequency, self.windows_duration, min(self.infected_start, self.exposed_start)/60)
            else:
                window_interval = always_on

            outside_temp = self.outside_temp()

            ventilation: models.Ventilation
            if self.window_type == 'window_sliding':
                ventilation = models.SlidingWindow(
                    active=window_interval,
                    outside_temp=outside_temp,
                    window_height=self.window_height,
                    opening_length=self.opening_distance,
                    number_of_windows=self.windows_number,
                )
            elif self.window_type == 'window_hinged':
                ventilation = models.HingedWindow(
                    active=window_interval,
                    outside_temp=outside_temp,
                    window_height=self.window_height,
                    window_width=self.window_width,
                    opening_length=self.opening_distance,
                    number_of_windows=self.windows_number,
                )

        elif self.ventilation_type == "no_ventilation":
            ventilation = models.AirChange(active=always_on, air_exch=0.)
        else:
            if self.mechanical_ventilation_type == 'mech_type_air_changes':
                ventilation = models.AirChange(active=always_on, air_exch=self.air_changes)
            else:
                ventilation = models.HVACMechanical(
                    active=always_on, q_air_mech=self.air_supply)

        # This is a minimal, always present source of ventilation, due
        # to the air infiltration from the outside.
        # See CERN-OPEN-2021-004, p. 12.
        infiltration_ventilation = models.AirChange(active=always_on, air_exch=0.25)
        if self.hepa_option:
            hepa = models.HEPAFilter(active=always_on, q_air_mech=self.hepa_amount)
            return models.MultipleVentilation((ventilation, hepa, infiltration_ventilation))
        else:
            return models.MultipleVentilation((ventilation, infiltration_ventilation))

    def nearest_weather_station(self) -> cara.data.weather.WxStationRecordType:
        """Return the nearest weather station (which has valid data) for this form"""
        return cara.data.weather.nearest_wx_station(
            longitude=self.location_longitude, latitude=self.location_latitude
        )

    def mask(self) -> models.Mask:
        # Initializes the mask type if mask wearing is "continuous", otherwise instantiates the mask attribute as
        # the "No mask"-mask
        if self.mask_wearing_option == 'mask_on':
            mask = mask_distributions[self.mask_type]
        else:
            mask = models.Mask.types['No mask']
        return mask

    def infected_population(self) -> mc.InfectedPopulation:
        # Initializes the virus
        virus = virus_distributions[self.virus_type]

        scenario_activity_and_expiration = {
            'office': (
                'Seated',
                # Mostly silent in the office, but 1/3rd of time speaking.
                {'Speaking': 1, 'Breathing': 2}
            ),
            'controlroom-day': (
                'Seated',
                # Daytime control room shift, 50% speaking.
                {'Speaking': 1, 'Breathing': 1}
            ),
            'controlroom-night': (
                'Seated',
                # Nightshift control room, 10% speaking.
                {'Speaking': 1, 'Breathing': 9}
            ),
            'smallmeeting': (
                'Seated',
                # Conversation of N people is approximately 1/N% of the time speaking.
                {'Speaking': 1, 'Breathing': self.total_people - 1}
            ),
            'largemeeting': (
                'Standing',
                # each infected person spends 1/3 of time speaking.
                {'Speaking': 1, 'Breathing': 2}
            ),
            'callcentre': ('Seated', 'Speaking'),
            'library': ('Seated', 'Breathing'),
            'training': ('Standing', 'Speaking'),
            'training_attendee': ('Seated', 'Breathing'),
            'lab': (
                'Light activity',
                #Model 1/2 of time spent speaking in a lab.
                {'Speaking': 1, 'Breathing': 1}),
            'workshop': (
                'Moderate activity',
                #Model 1/2 of time spent speaking in a workshop.
                {'Speaking': 1, 'Breathing': 1}),
            'gym':('Heavy exercise', 'Breathing'),
        }

        [activity_defn, expiration_defn] = scenario_activity_and_expiration[self.activity_type]
        activity = activity_distributions[activity_defn]
        expiration = build_expiration(expiration_defn)

        infected_occupants = self.infected_people

        infected = mc.InfectedPopulation(
            number=infected_occupants,
            virus=virus,
            presence=self.infected_present_interval(),
            mask=self.mask(),
            activity=activity,
            expiration=expiration,
            host_immunity=0.,
        )
        return infected

    def exposed_population(self) -> mc.Population:
        scenario_activity = {
            'office': 'Seated',
            'controlroom-day': 'Seated',
            'controlroom-night': 'Seated',
            'smallmeeting': 'Seated',
            'largemeeting': 'Seated',
            'callcentre': 'Seated',
            'library': 'Seated',
            'training': 'Seated',
            'training_attendee': 'Seated',
            'workshop': 'Moderate activity',
            'lab':'Light activity',
            'gym':'Heavy exercise',
        }

        activity_defn = scenario_activity[self.activity_type]
        activity = activity_distributions[activity_defn]

        infected_occupants = self.infected_people
        # The number of exposed occupants is the total number of occupants
        # minus the number of infected occupants.
        exposed_occupants = self.total_people - infected_occupants

        exposed = mc.Population(
            number=exposed_occupants,
            presence=self.exposed_present_interval(),
            activity=activity,
            mask=self.mask(),
            host_immunity=0.,
        )
        return exposed

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
        return COFFEE_OPTIONS_INT[self.exposed_coffee_break_option]

    def infected_number_of_coffee_breaks(self) -> int:
        return COFFEE_OPTIONS_INT[self.infected_coffee_break_option]

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
        LOG.debug(f"starting time march at {_hours2timestring(current_time/60)} to {_hours2timestring(finish/60)}")

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
        return self.present_interval(
            self.infected_start, self.infected_finish,
            breaks=self.infected_lunch_break_times() + self.infected_coffee_break_times(),
        )

    def short_range_interval(self, interaction) -> models.SpecificInterval:
        start_time = time_string_to_minutes(interaction['start_time'])
        duration = float(interaction['duration'])
        return models.SpecificInterval(present_times=((start_time/60, (start_time + duration)/60),))

    def exposed_present_interval(self) -> models.Interval:
        return self.present_interval(
            self.exposed_start, self.exposed_finish,
            breaks=self.exposed_lunch_break_times() + self.exposed_coffee_break_times(),
        )


def build_expiration(expiration_definition) -> mc._ExpirationBase:
    if isinstance(expiration_definition, str):
        return expiration_distributions[expiration_definition]
    elif isinstance(expiration_definition, dict):
        total_weight = sum(expiration_definition.values())
        BLO_factors = np.sum([
            np.array(expiration_BLO_factors[exp_type]) * weight/total_weight
            for exp_type, weight in expiration_definition.items()
            ], axis=0)
        return expiration_distribution(BLO_factors=tuple(BLO_factors))


def baseline_raw_form_data() -> typing.Dict[str, typing.Union[str, float]]:
    # Note: This isn't a special "baseline". It can be updated as required.
    return {
        'activity_type': 'office',
        'air_changes': '',
        'air_supply': '',
        'ceiling_height': '',
        'exposed_coffee_break_option': 'coffee_break_4',
        'exposed_coffee_duration': '10',
        'exposed_finish': '18:00',
        'exposed_lunch_finish': '13:30',
        'exposed_lunch_option': '1',
        'exposed_lunch_start': '12:30',
        'exposed_start': '09:00',
        'floor_area': '',
        'hepa_amount': '250',
        'hepa_option': '0',
        'humidity': '',
        'infected_coffee_break_option': 'coffee_break_4',
        'infected_coffee_duration': '10',
        'infected_dont_have_breaks_with_exposed': '1',
        'infected_finish': '18:00',
        'infected_lunch_finish': '13:30',
        'infected_lunch_option': '1',
        'infected_lunch_start': '12:30',
        'infected_people': '1',
        'infected_start': '09:00',
        'inside_temp': 293.,
        'location_latitude': 46.20833,
        'location_longitude': 6.14275,
        'location_name': 'Geneva',
        'geographic_population': 0,
        'geographic_cases': 0,
        'geographic_conf_level': 'confidence_low',
        'mask_type': 'Type I',
        'mask_wearing_option': 'mask_off',
        'mechanical_ventilation_type': '',
        'calculator_version': calculator.__version__,
        'opening_distance': '0.2',
        'event_month': 'January',
        'room_heating_option': '0',
        'room_number': '123',
        'room_volume': '75',
        'simulation_name': 'Test',
        'total_people': '10',
        'ventilation_type': 'natural_ventilation',
        'virus_type': 'SARS_CoV_2',
        'volume_type': 'room_volume_explicit',
        'windows_duration': '',
        'windows_frequency': '',
        'window_height': '2',
        'window_type': 'window_sliding',
        'window_width': '2',
        'windows_number': '1',
        'window_opening_regime': 'windows_open_permanently',
        'short_range_option': 'short_range_no',
        'short_range_interactions': '[]',
    }


ACTIVITY_TYPES = {'office', 'smallmeeting', 'largemeeting', 'training', 'training_attendee', 'callcentre', 'controlroom-day', 'controlroom-night', 'library', 'workshop', 'lab', 'gym'}
MECHANICAL_VENTILATION_TYPES = {'mech_type_air_changes', 'mech_type_air_supply', 'not-applicable'}
MASK_TYPES = {'Type I', 'FFP2'}
MASK_WEARING_OPTIONS = {'mask_on', 'mask_off'}
VENTILATION_TYPES = {'natural_ventilation', 'mechanical_ventilation', 'no_ventilation'}
VIRUS_TYPES = {'SARS_CoV_2', 'SARS_CoV_2_ALPHA', 'SARS_CoV_2_BETA','SARS_CoV_2_GAMMA', 'SARS_CoV_2_DELTA', 'SARS_CoV_2_OMICRON'}
VOLUME_TYPES = {'room_volume_explicit', 'room_volume_from_dimensions'}
WINDOWS_OPENING_REGIMES = {'windows_open_permanently', 'windows_open_periodically', 'not-applicable'}
WINDOWS_TYPES = {'window_sliding', 'window_hinged', 'not-applicable'}

COFFEE_OPTIONS_INT = {'coffee_break_0': 0, 'coffee_break_1': 1, 'coffee_break_2': 2, 'coffee_break_4': 4}

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December',
]

CONFIDENCE_LEVEL_OPTIONS = {'confidence_low': 10, 'confidence_medium': 5, 'confidence_high': 2}


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
    return "{0:0=2d}".format(int(time/60)) + ":" + "{0:0=2d}".format(time%60)


def string_to_list(l: str) -> list:
    return list(ast.literal_eval(l.replace("&quot;", "\"")))


def list_to_string(s: list) -> str:
    return json.dumps(s)


def _safe_int_cast(value) -> int:
    if isinstance(value, int):
        return value
    elif isinstance(value, float) and int(value) == value:
        return int(value)
    elif isinstance(value, str) and value.isdecimal():
        return int(value)
    else:
        raise TypeError(f"Unable to safely cast {value} ({type(value)} type) to int")


#: Mapping of field name to a callable which can convert values from form
#: input (URL encoded arguments / string) into the correct type.
_CAST_RULES_FORM_ARG_TO_NATIVE: typing.Dict[str, typing.Callable] = {}

#: Mapping of field name to callable which can convert native type to values
#: that can be encoded to URL arguments.
_CAST_RULES_NATIVE_TO_FORM_ARG: typing.Dict[str, typing.Callable] = {}


for _field in dataclasses.fields(FormData):
    if _field.type is minutes_since_midnight:
        _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = time_string_to_minutes
        _CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = time_minutes_to_string
    elif _field.type is int:
        _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = _safe_int_cast
    elif _field.type is float:
        _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = float
    elif _field.type is bool:
        _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = lambda v: v == '1'
        _CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = int
    elif _field.type is list:
        _CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = string_to_list
        _CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = list_to_string
