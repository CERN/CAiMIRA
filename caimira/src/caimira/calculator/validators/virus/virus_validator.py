import dataclasses
import datetime
import logging
import typing
import re

import numpy as np

from caimira import __version__ as calculator_version
from ..form_validator import FormData, cast_class_fields, time_string_to_minutes
from ..defaults import (DEFAULTS, CONFIDENCE_LEVEL_OPTIONS,
                        MECHANICAL_VENTILATION_TYPES, MASK_WEARING_OPTIONS, MONTH_NAMES, VACCINE_BOOSTER_TYPE, VACCINE_TYPE,
                        VENTILATION_TYPES, VOLUME_TYPES, WINDOWS_OPENING_REGIMES, WINDOWS_TYPES)
from ...models import models, data, monte_carlo as mc
from ...models.monte_carlo.data import activity_distributions, virus_distributions, mask_distributions, short_range_distances
from ...models.monte_carlo.data import expiration_distribution, expiration_BLO_factors, expiration_distributions, short_range_expiration_distributions

LOG = logging.getLogger("MODEL")

minutes_since_midnight = typing.NewType('minutes_since_midnight', int)


@dataclasses.dataclass
class VirusFormData(FormData):
    ascertainment_bias: str
    activity_type: str
    air_changes: float
    air_supply: float
    arve_sensors_option: bool
    calculator_version: str
    ceiling_height: float
    CO2_fitting_result: dict
    conditional_probability_viral_loads: bool
    event_month: str
    exposure_option: str
    floor_area: float
    geographic_cases: int
    geographic_population: int
    hepa_amount: float
    hepa_option: bool
    humidity: str
    inside_temp: float
    location_latitude: float
    location_longitude: float
    location_name: str
    mask_type: str
    mask_wearing_option: str
    mechanical_ventilation_type: str
    opening_distance: float
    precise_activity: dict
    room_heating_option: bool
    room_number: str
    sensor_in_use: str
    short_range_interactions: list
    short_range_occupants: int
    short_range_option: str
    simulation_name: str
    vaccine_booster_option: bool
    vaccine_booster_type: str
    vaccine_option: bool
    vaccine_type: str
    ventilation_type: str
    virus_type: str
    volume_type: str
    window_height: float
    window_opening_regime: str
    window_type: str
    window_width: float
    windows_duration: float
    windows_frequency: float
    windows_number: int

    _DEFAULTS: typing.ClassVar[typing.Dict[str, typing.Any]] = DEFAULTS

    def validate(self):
        # Validate population parameters 
        self.validate_population_parameters()

        validation_tuples = [('activity_type', self.data_registry.population_scenario_activity.keys()),
                             ('ascertainment_bias', CONFIDENCE_LEVEL_OPTIONS),
                             ('event_month', MONTH_NAMES),
                             ('mechanical_ventilation_type', MECHANICAL_VENTILATION_TYPES),
                             ('mask_type', list(mask_distributions(self.data_registry).keys())),
                             ('mask_wearing_option', MASK_WEARING_OPTIONS),
                             ('vaccine_type', VACCINE_TYPE),
                             ('vaccine_booster_type', VACCINE_BOOSTER_TYPE),
                             ('ventilation_type', VENTILATION_TYPES),
                             ('virus_type', list(virus_distributions(self.data_registry).keys())),
                             ('volume_type', VOLUME_TYPES),
                             ('window_opening_regime', WINDOWS_OPENING_REGIMES),
                             ('window_type', WINDOWS_TYPES)]

        for attr_name, valid_set in validation_tuples:
            if getattr(self, attr_name) not in valid_set:
                raise ValueError(
                    f"{getattr(self, attr_name)} is not a valid value for {attr_name}")

        # Validate number of infected people == 1 when activity is Conference/Training.
        if self.activity_type == 'training' and self.infected_people > 1:
            raise ValueError(
                'Conference/Training activities are limited to 1 infected.')

        # Validate ventilation parameters
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
            if (self.window_opening_regime == 'windows_open_periodically' and
                    self.windows_duration > self.windows_frequency):
                raise ValueError(
                    'Duration cannot be bigger than frequency.'
                )

        if (self.ventilation_type == 'mechanical_ventilation'
                and self.mechanical_ventilation_type == 'not-applicable'):
            raise ValueError("mechanical_ventilation_type cannot be 'not-applicable' if "
                             "ventilation_type is 'mechanical_ventilation'")

        # Validate specific inputs - breaks (exposed and infected)
        if self.specific_breaks != {}:
            if type(self.specific_breaks) is not dict:
                raise TypeError(
                    'The specific breaks should be in a dictionary.')

            dict_keys = list(self.specific_breaks.keys())
            if "exposed_breaks" not in dict_keys:
                raise TypeError(
                    f'Unable to fetch "exposed_breaks" key. Got "{dict_keys[0]}".')
            if "infected_breaks" not in dict_keys:
                raise TypeError(
                    f'Unable to fetch "infected_breaks" key. Got "{dict_keys[1]}".')

            for population_breaks in ['exposed_breaks', 'infected_breaks']:
                if self.specific_breaks[population_breaks] != []:
                    if type(self.specific_breaks[population_breaks]) is not list:
                        raise TypeError(
                            f'All breaks should be in a list. Got {type(self.specific_breaks[population_breaks])}.')
                    for input_break in self.specific_breaks[population_breaks]:
                        # Input validations.
                        if type(input_break) is not dict:
                            raise TypeError(
                                f'Each break should be a dictionary. Got {type(input_break)}.')
                        dict_keys = list(input_break.keys())
                        if "start_time" not in input_break:
                            raise TypeError(
                                f'Unable to fetch "start_time" key. Got "{dict_keys[0]}".')
                        if "finish_time" not in input_break:
                            raise TypeError(
                                f'Unable to fetch "finish_time" key. Got "{dict_keys[1]}".')
                        for time in input_break.values():
                            if not re.compile("^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$").match(time):
                                raise TypeError(
                                    f'Wrong time format - "HH:MM". Got "{time}".')

        # Validate specific inputs - precise activity
        if self.precise_activity != {}:
            if type(self.precise_activity) is not dict:
                raise TypeError(
                    'The precise activities should be in a dictionary.')

            dict_keys = list(self.precise_activity.keys())
            if "physical_activity" not in dict_keys:
                raise TypeError(
                    f'Unable to fetch "physical_activity" key. Got "{dict_keys[0]}".')
            if "respiratory_activity" not in dict_keys:
                raise TypeError(
                    f'Unable to fetch "respiratory_activity" key. Got "{dict_keys[1]}".')

            if type(self.precise_activity['physical_activity']) is not str:
                raise TypeError(
                    'The physical activities should be a single string.')

            if type(self.precise_activity['respiratory_activity']) is not list:
                raise TypeError(
                    'The respiratory activities should be in a list.')

            total_percentage = 0
            for respiratory_activity in self.precise_activity['respiratory_activity']:
                if type(respiratory_activity) is not dict:
                    raise TypeError(
                        'Each respiratory activity should be defined in a dictionary.')
                dict_keys = list(respiratory_activity.keys())
                if "type" not in dict_keys:
                    raise TypeError(
                        f'Unable to fetch "type" key. Got "{dict_keys[0]}".')
                if "percentage" not in dict_keys:
                    raise TypeError(
                        f'Unable to fetch "percentage" key. Got "{dict_keys[1]}".')
                total_percentage += respiratory_activity['percentage']

            if total_percentage != 100:
                raise ValueError(
                    f'The sum of all respiratory activities should be 100. Got {total_percentage}.')

        # Validate number of people with short-range interactions
        if self.occupancy_format == "static": max_occupants_for_sr = self.total_people - self.infected_people
        else: max_occupants_for_sr = np.max(np.array([entry["total_people"] for entry in self.dynamic_exposed_occupancy]))
        if self.short_range_occupants > max_occupants_for_sr:
            raise ValueError(
                f'The total number of occupants having short-range interactions ({self.short_range_occupants}) should be lower than the exposed population ({max_occupants_for_sr}).'
            )
        
        # Validate short-range interactions interval
        if self.short_range_option == "short_range_yes":
            for interaction in self.short_range_interactions:
                # Check if presence is within long-range exposure
                presence = self.short_range_interval(interaction)
                if (self.occupancy_format == 'dynamic'):
                    long_range_start = min(time_string_to_minutes(self.dynamic_infected_occupancy[0]['start_time']), 
                                            time_string_to_minutes(self.dynamic_exposed_occupancy[0]['start_time']))
                    long_range_stop = max(time_string_to_minutes(self.dynamic_infected_occupancy[-1]['finish_time']), 
                                            time_string_to_minutes(self.dynamic_exposed_occupancy[-1]['finish_time']))
                else:
                    long_range_start = min(self.infected_start, self.exposed_start)
                    long_range_stop = max(self.infected_finish, self.exposed_finish)
                if not (long_range_start/60 <= presence.present_times[0][0] <= long_range_stop/60 and 
                        long_range_start/60 <= presence.present_times[0][-1] <= long_range_stop/60):
                    raise ValueError(f"Short-range interactions should be defined during simulation time. Got {interaction}")

    def initialize_room(self) -> models.Room:
        # Initializes room with volume either given directly or as product of area and height
        if self.volume_type == 'room_volume_explicit':
            volume = self.room_volume
        else:
            volume = self.floor_area * self.ceiling_height

        if self.arve_sensors_option == False:
            if self.room_heating_option:
                humidity = self.data_registry.room['humidity_with_heating']
            else:
                humidity = self.data_registry.room['humidity_without_heating']
            inside_temp = self.data_registry.room['inside_temp']
        else:
            humidity = float(self.humidity)
            inside_temp = self.inside_temp

        return models.Room(volume=volume, inside_temp=models.PiecewiseConstant((0, 24), (inside_temp,)), humidity=humidity) # type: ignore

    def build_mc_model(self) -> mc.ExposureModel:
        room = self.initialize_room()
        ventilation: models._VentilationBase = self.ventilation()
        infected_population: models.InfectedPopulation = self.infected_population()
        short_range = []
        if self.short_range_option == "short_range_yes":
            for interaction in self.short_range_interactions:
                short_range.append(mc.ShortRangeModel(
                    data_registry=self.data_registry,
                    expiration=short_range_expiration_distributions(
                        self.data_registry)[interaction['expiration']],
                    activity=infected_population.activity,
                    presence=self.short_range_interval(interaction),
                    distance=short_range_distances(self.data_registry),
                ))

        return mc.ExposureModel(
            data_registry=self.data_registry,
            concentration_model=mc.ConcentrationModel(
                data_registry=self.data_registry,
                room=room,
                ventilation=ventilation,
                infected=infected_population,
                evaporation_factor=0.3,
            ),
            short_range=tuple(short_range),
            exposed=self.exposed_population(),
            geographical_data=mc.Cases(
                geographic_population=self.geographic_population,
                geographic_cases=self.geographic_cases,
                ascertainment_bias=CONFIDENCE_LEVEL_OPTIONS[self.ascertainment_bias],
            ),
            exposed_to_short_range=self.short_range_occupants,
        )

    def build_model(self, sample_size=None) -> models.ExposureModel:
        sample_size = sample_size or self.data_registry.monte_carlo['sample_size']
        return self.build_mc_model().build_model(size=sample_size)

    def build_CO2_model(self, sample_size=None) -> models.CO2ConcentrationModel:
        sample_size = sample_size or self.data_registry.monte_carlo['sample_size']
        infected_population: models.InfectedPopulation = self.infected_population(
        ).build_model(sample_size)
        exposed_population: models.Population = self.exposed_population().build_model(sample_size)

        state_change_times = set(
            infected_population.presence_interval().transition_times())
        state_change_times.update(
            exposed_population.presence_interval().transition_times())
        transition_times = sorted(state_change_times)

        total_people = [infected_population.people_present(stop) + exposed_population.people_present(stop)
                        for _, stop in zip(transition_times[:-1], transition_times[1:])]

        if (self.activity_type == 'precise'):
            activity_defn, _ = self.generate_precise_activity_expiration()
        else:
            activity_defn = self.data_registry.population_scenario_activity[
                self.activity_type]['activity']

        population = mc.SimplePopulation(
            number=models.IntPiecewiseConstant(transition_times=tuple(
                transition_times), values=tuple(total_people)),
            presence=None,
            activity=activity_distributions(self.data_registry)[activity_defn],
        )

        # Builds a CO2 concentration model based on model inputs
        return mc.CO2ConcentrationModel(
            data_registry=self.data_registry,
            room=self.initialize_room(),
            ventilation=self.ventilation(),
            CO2_emitters=population,
        ).build_model(size=sample_size)

    def tz_name_and_utc_offset(self) -> typing.Tuple[str, float]:
        """
        Return the timezone name (e.g. CET), and offset, in hours, that need to
        be *added* to UTC to convert to the form location's timezone.

        """
        month = MONTH_NAMES.index(self.event_month) + 1
        timezone = data.weather.timezone_at(
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
        temp_profile = data.weather.mean_hourly_temperatures(
            wx_station=wx_station[0], month=MONTH_NAMES.index(self.event_month) + 1)

        _, utc_offset = self.tz_name_and_utc_offset()

        # Offset the source times according to the difference from UTC (as a
        # result the first data value may no longer be a midnight, and the hours
        # no longer ordered modulo 24).
        source_times = np.arange(24) + utc_offset
        times, temp_profile = data.weather.refine_hourly_data(
            source_times,
            temp_profile,
            npts=24*10,  # 10 steps per hour => 6 min steps
        )
        outside_temp = models.PiecewiseConstant(
            tuple(float(t) for t in times), tuple(float(t)
                                                  for t in temp_profile),
        )
        return outside_temp

    def ventilation(self) -> models._VentilationBase:
        always_on = models.PeriodicInterval(period=120, duration=120)
        periodic_interval = models.PeriodicInterval(self.windows_frequency, self.windows_duration,
                                                    min(self.infected_start, self.exposed_start)/60)
        if self.ventilation_type == 'from_fitting':
            ventilations = []
            transition_times = self.CO2_fitting_result['transition_times']
            for index, (start, stop) in enumerate(zip(transition_times[:-1], transition_times[1:])):
                ventilations.append(models.AirChange(active=models.SpecificInterval(present_times=((start, stop), )),
                                                     air_exch=self.CO2_fitting_result['ventilation_values'][index]))
            return models.MultipleVentilation(tuple(ventilations))

        # Initializes a ventilation instance as a window if 'natural_ventilation' is selected, or as a HEPA-filter otherwise
        if self.ventilation_type == 'natural_ventilation':
            if self.window_opening_regime == 'windows_open_periodically':
                window_interval = periodic_interval
            else:
                window_interval = always_on

            outside_temp = self.outside_temp()

            ventilation: models.Ventilation
            if self.window_type == 'window_sliding':
                ventilation = models.SlidingWindow(
                    data_registry=self.data_registry,
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
                ventilation = models.AirChange(
                    active=always_on, air_exch=self.air_changes)
            else:
                ventilation = models.HVACMechanical(
                    active=always_on, q_air_mech=self.air_supply)

        # This is a minimal, always present source of ventilation, due
        # to the air infiltration from the outside.
        # See CERN-OPEN-2021-004, p. 12.
        residual_vent: float = self.data_registry.ventilation['infiltration_ventilation'] # type: ignore
        infiltration_ventilation = models.AirChange(
            active=always_on, air_exch=residual_vent)
        if self.hepa_option:
            hepa = models.HEPAFilter(
                active=always_on, q_air_mech=self.hepa_amount)
            return models.MultipleVentilation((ventilation, hepa, infiltration_ventilation))
        else:
            return models.MultipleVentilation((ventilation, infiltration_ventilation))

    def nearest_weather_station(self) -> data.weather.WxStationRecordType:
        """Return the nearest weather station (which has valid data) for this form"""
        return data.weather.nearest_wx_station(
            longitude=self.location_longitude, latitude=self.location_latitude
        )

    def mask(self) -> models.Mask:
        # Initializes the mask type if mask wearing is "continuous", otherwise instantiates the mask attribute as
        # the "No mask"-mask
        if self.mask_wearing_option == 'mask_on':
            mask = mask_distributions(self.data_registry)[self.mask_type]
        else:
            mask = models.Mask.types['No mask']
        return mask

    def generate_precise_activity_expiration(self) -> typing.Tuple[typing.Any, ...]:
        # It means the precise activity is not defined by a specific input.
        if self.precise_activity == {}:
            return ()
        respiratory_dict = {}
        for respiratory_activity in self.precise_activity['respiratory_activity']:
            respiratory_dict[respiratory_activity['type']
                             ] = respiratory_activity['percentage']

        return (self.precise_activity['physical_activity'], respiratory_dict)

    def infected_population(self) -> mc.InfectedPopulation:
        # Initializes the virus
        virus = virus_distributions(self.data_registry)[self.virus_type]

        # Occupancy
        if self.occupancy_format == 'dynamic':
            if isinstance(self.dynamic_infected_occupancy, typing.List) and len(self.dynamic_infected_occupancy) > 0:
                # If dynamic occupancy is defined, the generator will parse and validate the
                # respective input to a format readable by the model - `IntPiecewiseConstant`.
                infected_occupancy = self.generate_dynamic_occupancy(self.dynamic_infected_occupancy)
                infected_presence = None
            else:
                raise TypeError(f'If dynamic occupancy is selected, a populated list of occupancy intervals is expected. Got "{self.dynamic_infected_occupancy}".')
        else:
            # The number of exposed occupants is the total number of occupants
            # minus the number of infected occupants.
            infected_occupancy = self.infected_people
            infected_presence = self.infected_present_interval()

        # Activity and expiration
        activity_defn = self.data_registry.population_scenario_activity[self.activity_type]['activity']
        expiration_defn = self.data_registry.population_scenario_activity[self.activity_type]['expiration']
        if (self.activity_type == 'smallmeeting'):
            # Conversation of N people is approximately 1/N% of the time speaking.
            total_people: int = max(infected_occupancy.values) if self.occupancy_format == 'dynamic' else self.total_people
            expiration_defn = {'Speaking': 1, 'Breathing': total_people - 1}
        elif (self.activity_type == 'precise'):
            activity_defn, expiration_defn = self.generate_precise_activity_expiration()

        activity = activity_distributions(self.data_registry)[activity_defn]
        expiration = build_expiration(self.data_registry, expiration_defn)

        infected = mc.InfectedPopulation(
            data_registry=self.data_registry,
            number=infected_occupancy,
            presence=infected_presence,
            virus=virus,
            mask=self.mask(),
            activity=activity,
            expiration=expiration,
            # Vaccination status does not affect the infected population (for now)
            host_immunity=0.,
        )
        return infected

    def exposed_population(self) -> mc.Population:
        activity_defn = (self.precise_activity['physical_activity']
                         if self.activity_type == 'precise'
                         else str(self.data_registry.population_scenario_activity[self.activity_type]['activity']))
        activity = activity_distributions(self.data_registry)[activity_defn]

        if self.occupancy_format == 'dynamic':
            if isinstance(self.dynamic_exposed_occupancy, typing.List) and len(self.dynamic_exposed_occupancy) > 0:
                # If dynamic occupancy is defined, the generator will parse and validate the
                # respective input to a format readable by the model - IntPiecewiseConstant.
                exposed_occupancy = self.generate_dynamic_occupancy(self.dynamic_exposed_occupancy)
                exposed_presence = None
            else:
                raise TypeError(f'If dynamic occupancy is selected, a populated list of occupancy intervals is expected. Got "{self.dynamic_exposed_occupancy}".')
        else:
            # The number of exposed occupants is the total number of occupants
            # minus the number of infected occupants.
            exposed_occupancy = self.total_people - self.infected_people
            exposed_presence = self.exposed_present_interval()

        if (self.vaccine_option):
            if (self.vaccine_booster_option and self.vaccine_booster_type != 'Other'):
                host_immunity = [vaccine['VE'] for vaccine in data.vaccine_booster_host_immunity if
                                 vaccine['primary series vaccine'] == self.vaccine_type and
                                 vaccine['booster vaccine'] == self.vaccine_booster_type][0]
            else:
                host_immunity = data.vaccine_primary_host_immunity[self.vaccine_type]
        else:
            host_immunity = 0.

        exposed = mc.Population(
            number=exposed_occupancy,
            presence=exposed_presence,
            activity=activity,
            mask=self.mask(),
            host_immunity=host_immunity,
        )
        return exposed

    def short_range_interval(self, interaction) -> models.SpecificInterval:
        start_time = time_string_to_minutes(interaction['start_time'])
        duration = float(interaction['duration'])
        return models.SpecificInterval(present_times=((start_time/60, (start_time + duration)/60),))


def build_expiration(data_registry, expiration_definition) -> mc._ExpirationBase:
    if isinstance(expiration_definition, str):
        return expiration_distributions(data_registry)[expiration_definition]
    elif isinstance(expiration_definition, dict):
        total_weight = sum(expiration_definition.values())
        BLO_factors = np.sum([
            np.array(expiration_BLO_factors(data_registry)
                     [exp_type]) * weight/total_weight
            for exp_type, weight in expiration_definition.items()
        ], axis=0)
        return expiration_distribution(data_registry=data_registry, BLO_factors=tuple(BLO_factors))


def baseline_raw_form_data() -> typing.Dict[str, typing.Union[str, float]]:
    # Note: This isn't a special "baseline". It can be updated as required.
    return {
        'activity_type': 'office',
        'air_changes': '',
        'air_supply': '',
        'ascertainment_bias': 'confidence_low',
        'calculator_version': calculator_version,
        'ceiling_height': '',
        'conditional_probability_viral_loads': '0',
        'dynamic_exposed_occupancy': '[]',
        'dynamic_infected_occupancy': '[]',
        'event_month': 'January',
        'exposed_coffee_break_option': 'coffee_break_4',
        'exposed_coffee_duration': '10',
        'exposed_finish': '18:00',
        'exposed_lunch_finish': '13:30',
        'exposed_lunch_option': '1',
        'exposed_lunch_start': '12:30',
        'exposed_start': '09:00',
        'floor_area': '',
        'geographic_cases': 0,
        'geographic_population': 0,
        'hepa_amount': '250',
        'hepa_option': '0',
        'humidity': '0.5',
        'infected_coffee_break_option': 'coffee_break_4',
        'infected_coffee_duration': '10',
        'infected_dont_have_breaks_with_exposed': '1',
        'infected_finish': '18:00',
        'infected_lunch_finish': '13:30',
        'infected_lunch_option': '1',
        'infected_lunch_start': '12:30',
        'infected_people': '1',
        'infected_start': '09:00',
        'inside_temp': '293.',
        'location_latitude': 46.20833,
        'location_longitude': 6.14275,
        'location_name': 'Geneva',
        'mask_type': 'Type I',
        'mask_wearing_option': 'mask_off',
        'mechanical_ventilation_type': '',
        'occupancy_format': 'static',
        'opening_distance': '0.2',
        'room_heating_option': '0',
        'room_number': '123',
        'room_volume': '75',
        'short_range_interactions': '[]',
        'short_range_option': 'short_range_no',
        'simulation_name': 'Test',
        'total_people': '10',
        'vaccine_booster_option': '0',
        'vaccine_booster_type': 'AZD1222_(AstraZeneca)',
        'vaccine_option': '0',
        'vaccine_type': 'Ad26.COV2.S_(Janssen)',
        'ventilation_type': 'natural_ventilation',
        'virus_type': 'SARS_CoV_2',
        'volume_type': 'room_volume_explicit',
        'window_height': '2',
        'window_opening_regime': 'windows_open_permanently',
        'window_type': 'window_sliding',
        'window_width': '2',
        'windows_duration': '10',
        'windows_frequency': '60',
        'windows_number': '1',
    }

cast_class_fields(VirusFormData)
