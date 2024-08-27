import dataclasses
import logging
import typing
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import pandas as pd
import re

from caimira import models
from caimira.store.data_registry import DataRegistry
from .form_data import FormData, cast_class_fields
from .defaults import NO_DEFAULT
from .report_generator import img2base64, _figure2bytes

minutes_since_midnight = typing.NewType('minutes_since_midnight', int)

LOG = logging.getLogger(__name__)


@dataclasses.dataclass
class CO2FormData(FormData):
    CO2_data: dict
    fitting_ventilation_states: list
    room_capacity: typing.Optional[int]

    #: The default values for undefined fields. Note that the defaults here
    #: and the defaults in the html form must not be contradictory.
    _DEFAULTS: typing.ClassVar[typing.Dict[str, typing.Any]] = {
        'CO2_data': '{}',
        'fitting_ventilation_states': '[]',
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
        Returns a list of the detected ventilation state changes.
        """
        times: list = self.CO2_data['times']
        CO2_values: list = self.CO2_data['CO2']

        if len(times) != len(CO2_values):
            raise ValueError("times and CO2 values must have the same length.")

        # Calculate minimum interval for peak detection
        diff = times[1] - times[0]
        interval_in_minutes = 30
        distance_points = interval_in_minutes // (diff * 60) # minutes

        # Applying a rolling average to smooth the initial data
        window_size = int(0.01*len(times))  # 1% of the initial points window for smoothing
        smoothed_co2 = pd.Series(CO2_values).rolling(window=window_size, center=True).mean()

        # Find peaks (maxima) in the smoothed data
        distance = distance_points
        peaks, _ = find_peaks(smoothed_co2.values, prominence=100, distance=distance)
        
        # Find valleys (minima) by inverting the smoothed data and applying a smooth factor
        valleys, _ = find_peaks(-smoothed_co2.values, prominence=20, width=int(0.05*len(times)), distance=distance)

        # Extract peak and valley timestamps
        timestamps = np.array(times)
        peak_timestamps = timestamps[peaks]
        valley_timestamps = timestamps[valleys]

        return sorted(np.concatenate((peak_timestamps, valley_timestamps)))

    def generate_ventilation_plot(self,
                                  ventilation_transition_times: typing.Optional[list] = None,
                                  occupancy_transition_times: typing.Optional[list] = None,
                                  predictive_CO2: typing.Optional[list] = None) -> str:
            
            # Plot data (x-axis: times; y-axis: CO2 concentrations)
            times_values: list = self.CO2_data['times']
            CO2_values: list = self.CO2_data['CO2']

            fig = plt.figure(figsize=(7, 4), dpi=110)
            plt.plot(times_values, CO2_values, label='Input CO₂')

            # Add occupancy state changes:
            if (occupancy_transition_times):
                for i, time in enumerate(occupancy_transition_times):
                    plt.axvline(x = time, color = 'grey', linewidth=0.5, linestyle='--', label='Occupancy change (from input)' if i == 0 else None)
            # Add ventilation state changes:
            if (ventilation_transition_times):
                for i, time in enumerate(ventilation_transition_times):
                    if i == 0:
                        label = 'Ventilation change (detected)' if occupancy_transition_times else 'Ventilation state changes'
                    else: label = None
                    plt.axvline(x = time, color = 'red', linewidth=0.5, linestyle='--', label=label)

            if (predictive_CO2):
                plt.plot(times_values, predictive_CO2, label='Predictive CO₂')
            plt.xlabel('Time of day')
            plt.ylabel('Concentration (ppm)')
            plt.legend()
            return img2base64(_figure2bytes(fig))

    def population_present_changes(self, infected_presence: models.Interval, exposed_presence: models.Interval) -> typing.List[float]:
        state_change_times = set(infected_presence.transition_times())
        state_change_times.update(exposed_presence.transition_times())
        return sorted(state_change_times)

    def ventilation_transition_times(self) -> typing.List[float]:
        vent_states = self.fitting_ventilation_states
        last_time_from_input = self.CO2_data['times'][-1]
        if (vent_states and last_time_from_input != vent_states[-1]): # The last time value is always needed for the last ACH interval.
            vent_states.append(last_time_from_input)
        return vent_states

    def build_model(self, size=None) -> models.CO2DataModel: # type: ignore
        size = size or self.data_registry.monte_carlo['sample_size']
        # Build a simple infected and exposed population for the case when presence
        # intervals and number of people are dynamic. Activity type is not needed.
        infected_presence = self.infected_present_interval()
        infected_population = models.SimplePopulation(
            number=self.infected_people,
            presence=infected_presence,
            activity=None, # type: ignore
        )
        exposed_presence = self.exposed_present_interval()
        exposed_population=models.SimplePopulation(
            number=self.total_people - self.infected_people,
            presence=exposed_presence,
            activity=None, # type: ignore
        )

        all_state_changes = self.population_present_changes(infected_presence, exposed_presence)
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
