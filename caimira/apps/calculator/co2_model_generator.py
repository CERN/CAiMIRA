import dataclasses
import html
import logging
import typing

from caimira import models
from . import model_generator
from .defaults import DEFAULT_MC_SAMPLE_SIZE, NO_DEFAULT, COFFEE_OPTIONS_INT

minutes_since_midnight = typing.NewType('minutes_since_midnight', int)

LOG = logging.getLogger(__name__)


@dataclasses.dataclass
class CO2FormData(model_generator.FormData):
    CO2_data: dict
    exposed_coffee_break_option: str
    exposed_coffee_duration: int
    exposed_finish: model_generator.minutes_since_midnight
    exposed_lunch_finish: model_generator.minutes_since_midnight
    exposed_lunch_option: bool
    exposed_lunch_start: model_generator.minutes_since_midnight
    exposed_start: model_generator.minutes_since_midnight
    fitting_ventilation_states: list
    fitting_ventilation_type: str
    infected_coffee_break_option: str
    infected_coffee_duration: int
    infected_dont_have_breaks_with_exposed: bool
    infected_finish: model_generator.minutes_since_midnight
    infected_lunch_finish: model_generator.minutes_since_midnight
    infected_lunch_option: bool
    infected_lunch_start: model_generator.minutes_since_midnight
    infected_people: int
    infected_start: model_generator.minutes_since_midnight
    room_volume: float
    specific_breaks: dict
    total_people: int

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

    @classmethod
    def from_dict(self, form_data: typing.Dict) -> "CO2FormData":
        # Take a copy of the form data so that we can mutate it.
        form_data = form_data.copy()
        form_data.pop('_xsrf', None)

        # Don't let arbitrary unescaped HTML through the net.
        for key, value in form_data.items():
            if isinstance(value, str):
                form_data[key] = html.escape(value)

        for key, default_value in self._DEFAULTS.items():
            if form_data.get(key, '') == '':
                if default_value is NO_DEFAULT:
                    raise ValueError(f"{key} must be specified")
                form_data[key] = default_value

        for key, value in form_data.items():
            if key in model_generator._CAST_RULES_FORM_ARG_TO_NATIVE:
                form_data[key] = model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[key](value)

            if key not in self._DEFAULTS:
                raise ValueError(f'Invalid argument "{html.escape(key)}" given')

        instance = self(**form_data)
        instance.validate_population_parameters()
        return instance
    
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

    def build_model(self, size=DEFAULT_MC_SAMPLE_SIZE) -> models.CO2DataModel: # type: ignore
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
                room_volume=self.room_volume,
                number=models.IntPiecewiseConstant(transition_times=tuple(all_state_changes), values=tuple(total_people)),
                presence=None,
                ventilation_transition_times=self.ventilation_transition_times(),
                times=self.CO2_data['times'],
                CO2_concentrations=self.CO2_data['CO2'],
            )          


for _field in dataclasses.fields(CO2FormData):
    if _field.type is minutes_since_midnight:
        model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = model_generator.time_string_to_minutes
        model_generator._CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = model_generator.time_minutes_to_string
    elif _field.type is int:
        model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = model_generator._safe_int_cast
    elif _field.type is float:
        model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = float
    elif _field.type is bool:
        model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = lambda v: v == '1'
        model_generator._CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = int
    elif _field.type is list:
        model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = model_generator.string_to_list
        model_generator._CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = model_generator.list_to_string
    elif _field.type is dict:
        model_generator._CAST_RULES_FORM_ARG_TO_NATIVE[_field.name] = model_generator.string_to_dict
        model_generator._CAST_RULES_NATIVE_TO_FORM_ARG[_field.name] = model_generator.dict_to_string
