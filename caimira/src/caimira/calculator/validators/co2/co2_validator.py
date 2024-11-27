import dataclasses
import logging
import typing
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import pandas as pd
import re

from ..form_validator import FormData, cast_class_fields
from ..defaults import NO_DEFAULT
from ...store.data_registry import DataRegistry
from ...models import models
from ...report.virus_report_data import img2base64, _figure2bytes

minutes_since_midnight = typing.NewType('minutes_since_midnight', int)

LOG = logging.getLogger(__name__)


@dataclasses.dataclass
class CO2FormData(FormData):
    CO2_data: dict
    fitting_ventilation_states: list
    room_capacity: typing.Optional[int]

    # The default values for undefined fields. Note that the defaults here
    # and the defaults in any html form must not be contradictory.
    _DEFAULTS: typing.ClassVar[typing.Dict[str, typing.Any]] = {
        'CO2_data': '{}',
        'dynamic_infected_occupancy': '[]',
        'dynamic_exposed_occupancy': '[]',
        'exposed_coffee_break_option': 'coffee_break_0',
        'exposed_coffee_duration': 5,
        'exposed_finish': '17:30',
        'exposed_lunch_finish': '13:30',
        'exposed_lunch_option': True,
        'exposed_lunch_start': '12:30',
        'exposed_start': '08:30',
        'fitting_ventilation_states': '[]',
        'infected_coffee_break_option': 'coffee_break_0',
        'infected_coffee_duration': 5,
        'infected_dont_have_breaks_with_exposed': False,
        'infected_finish': '17:30',
        'infected_lunch_finish': '13:30',
        'infected_lunch_option': True,
        'infected_lunch_start': '12:30',
        'infected_people': 1,
        'infected_start': '08:30',
        'occupancy_format': 'static',
        'room_capacity': None,
        'room_volume': NO_DEFAULT,
        'specific_breaks': '{}',
        'total_people': NO_DEFAULT,
    }

    def __init__(self, **kwargs):
        # Set default values defined in CO2FormData
        for key, value in self._DEFAULTS.items():
            setattr(self, key, kwargs.get(key, value))

        # Initialize the Data Registry
        self.data_registry = DataRegistry()

    def validate(self):
        # Validate population parameters 
        self.validate_population_parameters()

        # Validate room capacity
        if self.room_capacity:
            if type(self.room_capacity) is not int:
                raise TypeError(f'The room capacity should be a valid integer (> 0). Got {type(self.room_capacity)}.')
            if self.room_capacity <= 0:
                raise TypeError(f'The room capacity should be a valid integer (> 0). Got {self.room_capacity}.')

        # Validate specific inputs - breaks (exposed and infected)
        if self.specific_breaks != {}:
            if type(self.specific_breaks) is not dict:
                raise TypeError('The specific breaks should be in a dictionary.')

            dict_keys = list(self.specific_breaks.keys())
            if "exposed_breaks" not in dict_keys:
                raise TypeError(f'Unable to fetch "exposed_breaks" key. Got "{dict_keys[0]}".')
            if "infected_breaks" not in dict_keys:
                raise TypeError(f'Unable to fetch "infected_breaks" key. Got "{dict_keys[1]}".')

            for population_breaks in ['exposed_breaks', 'infected_breaks']:
                if self.specific_breaks[population_breaks] != []:
                    if type(self.specific_breaks[population_breaks]) is not list:
                        raise TypeError(f'All breaks should be in a list. Got {type(self.specific_breaks[population_breaks])}.')
                    for input_break in self.specific_breaks[population_breaks]:
                        # Input validations.
                        if type(input_break) is not dict:
                            raise TypeError(f'Each break should be a dictionary. Got {type(input_break)}.')
                        dict_keys = list(input_break.keys())
                        if "start_time" not in input_break:
                            raise TypeError(f'Unable to fetch "start_time" key. Got "{dict_keys[0]}".')
                        if "finish_time" not in input_break:
                            raise TypeError(f'Unable to fetch "finish_time" key. Got "{dict_keys[1]}".')
                        for time in input_break.values():
                            if not re.compile("^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$").match(time):
                                raise TypeError(f'Wrong time format - "HH:MM". Got "{time}".')        

    def find_change_points(self) -> list:
        """
        Perform change point detection using scipy library (find_peaks method) with rolling average of data.
        Incorporate existing state change candidates and adjust the result accordingly.
        Returns a list of the detected ventilation transition times, discarding any occupancy state change.
        """
        times: list = self.CO2_data['times']
        CO2_values: list = self.CO2_data['CO2']

        if len(times) != len(CO2_values):
            raise ValueError("times and CO2 values must have the same length.")

        # Time difference between two consecutive time data entries, in seconds
        diff = (times[1] - times[0]) * 3600 # Initial data points in absolute hours, e.g. 14.78

        # Calculate minimum interval for smoothing technique
        smooth_min_interval_in_minutes = 1 # Minimum time difference for smooth technique
        window_size = max(int((smooth_min_interval_in_minutes * 60) // diff), 1)

        # Applying a rolling average to smooth the initial data
        smoothed_co2 = pd.Series(CO2_values).rolling(window=window_size, center=True).mean()

        # Calculate minimum interval for peaks and valleys detection
        peak_valley_min_interval_in_minutes = 15 # Minimum time difference between two peaks or two valleys
        min_distance_points = max(int((peak_valley_min_interval_in_minutes * 60) // diff), 1)

        # Calculate minimum width of datapoints for valley detection
        width_min_interval_in_minutes = 20 # Minimum duration of a valley
        min_valley_width = max(int((width_min_interval_in_minutes * 60) // diff), 1)

        # Find peaks (maxima) in the smoothed data applying the distance factor
        peaks, _ = find_peaks(smoothed_co2.values, prominence=100, distance=min_distance_points)
        
        # Find valleys (minima) by inverting the smoothed data and applying the width and distance factors
        valleys, _ = find_peaks(-smoothed_co2.values, prominence=50, width=min_valley_width, distance=min_distance_points)

        # Extract peak and valley timestamps
        timestamps = np.array(times)
        peak_timestamps = timestamps[peaks]
        valley_timestamps = timestamps[valleys]

        return sorted(np.concatenate((peak_timestamps, valley_timestamps)))

    def generate_ventilation_plot(self,
                                  ventilation_transition_times: typing.Optional[list] = None,
                                  occupancy_transition_times: typing.Optional[list] = None,
                                  predictive_CO2: typing.Optional[list] = None):
            
            # Plot data (x-axis: times; y-axis: CO2 concentrations)
            times_values: list = self.CO2_data['times']
            CO2_values: list = self.CO2_data['CO2']

            fig = plt.figure(figsize=(7, 4), dpi=110)
            plt.plot(times_values, CO2_values, label='CO₂ Data')
            
            # Add predictive CO2
            if (predictive_CO2):
                plt.plot(times_values, predictive_CO2, label='Predictive CO₂')

            # Add ventilation transition times:
            if (ventilation_transition_times):
                for i, time in enumerate(ventilation_transition_times):
                    if i == 0:
                        label = 'Ventilation transition times (suggestion)' if occupancy_transition_times else 'Ventilation transition times'
                    else: label = None
                    plt.axvline(x = time, color = 'red', linewidth=1, linestyle='--', label=label)
            
            # Add occupancy changes (UI):
            if (occupancy_transition_times):
                for i, time in enumerate(occupancy_transition_times):
                    plt.axvline(x = time, color = 'grey', linewidth=1, linestyle='--', label='Occupancy change (from UI)' if i == 0 else None)

            plt.xlabel('Time of day')
            plt.ylabel('Concentration (ppm)')
            plt.legend()

            vent_plot_data = {
                'plot': img2base64(_figure2bytes(fig)),
                'times': times_values,
                'CO2': CO2_values,
                'occ_trans_time': occupancy_transition_times,
                'vent_trans_time': ventilation_transition_times,
                'predictive_CO2': predictive_CO2,
            }

            return img2base64(_figure2bytes(fig)), vent_plot_data

    def population_present_changes(self, infected_presence: models.Interval, exposed_presence: models.Interval) -> typing.List[float]:
        state_change_times = set(infected_presence.transition_times())
        state_change_times.update(exposed_presence.transition_times())
        return sorted(state_change_times)

    def ventilation_transition_times(self) -> typing.Tuple[float]:
        '''
        Check if the last time from the input data is
        included in the ventilation ventilations state.
        Given that the last time is a required state change, 
        if not included, this method adds it.
        '''
        vent_states = self.fitting_ventilation_states
        last_time_from_input = self.CO2_data['times'][-1]
        if (vent_states and last_time_from_input != vent_states[-1]): # The last time value is always needed for the last ACH interval.
            vent_states.append(last_time_from_input)
        return tuple(vent_states)

    def build_model(self, sample_size = None) -> models.CO2DataModel:
        # Build a simple infected and exposed population for the case when presence
        # intervals and number of people are dynamic. Activity type is not needed.
        if self.occupancy_format == 'dynamic':
            if isinstance(self.dynamic_infected_occupancy, typing.List) and len(self.dynamic_infected_occupancy) > 0:
                infected_people = self.generate_dynamic_occupancy(self.dynamic_infected_occupancy)
                infected_presence = None
            else:
                raise TypeError(f'If dynamic occupancy is selected, a populated list of occupancy intervals is expected. Got "{self.dynamic_infected_occupancy}".')
            if isinstance(self.dynamic_exposed_occupancy, typing.List) and len(self.dynamic_exposed_occupancy) > 0:
                exposed_people = self.generate_dynamic_occupancy(self.dynamic_exposed_occupancy)
                exposed_presence = None
            else:
                raise TypeError(f'If dynamic occupancy is selected, a populated list of occupancy intervals is expected. Got "{self.dynamic_exposed_occupancy}".')
        else:
            infected_people = self.infected_people
            exposed_people = self.total_people - self.infected_people
            infected_presence = self.infected_present_interval()
            exposed_presence = self.exposed_present_interval()

        infected_population = models.SimplePopulation(
            number=infected_people,
            presence=infected_presence,
            activity=None, # type: ignore
        )
        exposed_population=models.SimplePopulation(
            number=exposed_people,
            presence=exposed_presence,
            activity=None, # type: ignore
        )
        
        all_state_changes=self.population_present_changes(infected_population.presence_interval(), 
                                                          exposed_population.presence_interval())
        total_people = [infected_population.people_present(stop) + exposed_population.people_present(stop)
                        for _, stop in zip(all_state_changes[:-1], all_state_changes[1:])]

        return models.CO2DataModel(
                data_registry=self.data_registry,
                room=models.Room(volume=self.room_volume, capacity=self.room_capacity),
                occupancy=models.IntPiecewiseConstant(transition_times=tuple(all_state_changes), values=tuple(total_people)),
                ventilation_transition_times=self.ventilation_transition_times(),
                times=self.CO2_data['times'],
                CO2_concentrations=self.CO2_data['CO2'],
            )

cast_class_fields(CO2FormData)
