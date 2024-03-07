import dataclasses
import logging
import typing
import numpy as np
import ruptures as rpt
import matplotlib.pyplot as plt
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
    fitting_ventilation_type: str

    #: The default values for undefined fields. Note that the defaults here
    #: and the defaults in the html form must not be contradictory.
    _DEFAULTS: typing.ClassVar[typing.Dict[str, typing.Any]] = {
        'CO2_data': '{}',
        'exposed_coffee_break_option': 'coffee_break_0',
        'exposed_coffee_duration': 5,
        'exposed_finish': '17:30',
        'exposed_lunch_finish': '13:30',
        'exposed_lunch_option': True,
        'exposed_lunch_start': '12:30',
        'exposed_start': '08:30',
        'fitting_ventilation_states': '[]',
        'fitting_ventilation_type': 'fitting_natural_ventilation',
        'infected_coffee_break_option': 'coffee_break_0',
        'infected_coffee_duration': 5,
        'infected_dont_have_breaks_with_exposed': False,
        'infected_finish': '17:30',
        'infected_lunch_finish': '13:30',
        'infected_lunch_option': True,
        'infected_lunch_start': '12:30',
        'infected_people': 1,
        'infected_start': '08:30',
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

    @classmethod
    def find_change_points_with_pelt(self, CO2_data: dict):
        """
        Perform change point detection using Pelt algorithm from ruptures library with pen=15.
        Returns a list of tuples containing (index, X-axis value) for the detected significant changes.
        """

        times: list = CO2_data['times']
        CO2_values: list = CO2_data['CO2']

        if len(times) != len(CO2_values):
            raise ValueError("times and CO2 values must have the same length.")

        # Convert the input list to a numpy array for use with the ruptures library
        CO2_np = np.array(CO2_values)

        # Define the model for change point detection (Radial Basis Function kernel)
        model = "rbf"

        # Fit the Pelt algorithm to the data with the specified model
        algo = rpt.Pelt(model=model).fit(CO2_np)

        # Predict change points using the Pelt algorithm with a penalty value of 15
        result = algo.predict(pen=15)

        # Find local minima and maxima
        segments = np.split(np.arange(len(CO2_values)), result)
        merged_segments = [np.hstack((segments[i], segments[i + 1])) for i in range(len(segments) - 1)]
        result_set = set()
        for segment in merged_segments[:-2]:
            result_set.add(times[CO2_values.index(min(CO2_np[segment]))])
            result_set.add(times[CO2_values.index(max(CO2_np[segment]))])
        return list(result_set)

    @classmethod
    def generate_ventilation_plot(self, CO2_data: dict,
                                  transition_times: typing.Optional[list] = None,
                                  predictive_CO2: typing.Optional[list] = None):
            times_values = CO2_data['times']
            CO2_values = CO2_data['CO2']

            fig = plt.figure(figsize=(7, 4), dpi=110)
            plt.plot(times_values, CO2_values, label='Input CO₂')

            if (transition_times):
                for time in transition_times:
                    plt.axvline(x = time, color = 'grey', linewidth=0.5, linestyle='--')
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

    def ventilation_transition_times(self) -> typing.Tuple[float, ...]:
        # Check what type of ventilation is considered for the fitting
        if self.fitting_ventilation_type == 'fitting_natural_ventilation':
            vent_states = self.fitting_ventilation_states
            vent_states.append(self.CO2_data['times'][-1])
            return tuple(vent_states)
        else:
            return tuple((self.CO2_data['times'][0], self.CO2_data['times'][-1]))

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

        all_state_changes=self.population_present_changes(infected_presence, exposed_presence)
        total_people = [infected_population.people_present(stop) + exposed_population.people_present(stop)
                        for _, stop in zip(all_state_changes[:-1], all_state_changes[1:])]

        return models.CO2DataModel(
                data_registry=self.data_registry,
                room_volume=self.room_volume,
                number=models.IntPiecewiseConstant(transition_times=tuple(all_state_changes), values=tuple(total_people)),
                presence=None,
                ventilation_transition_times=self.ventilation_transition_times(),
                times=self.CO2_data['times'],
                CO2_concentrations=self.CO2_data['CO2'],
            )

cast_class_fields(CO2FormData)
