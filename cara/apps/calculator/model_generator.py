from dataclasses import dataclass
import html
import typing

import numpy as np

from cara import models
from cara import data


@dataclass
class FormData:
    # Number of minutes after 00:00
    activity_start: int
    activity_finish: int
    lunch_start: int
    lunch_finish: int
    infected_start: int
    infected_finish: int

    activity_type: str
    air_changes: float
    air_supply: float
    ceiling_height: float
    coffee_breaks: int
    coffee_duration: int
    event_type: str
    floor_area: float
    hepa_amount: float
    hepa_option: bool
    infected_people: int
    lunch_option: bool
    mask_type: str
    mask_wearing: str
    mechanical_ventilation_type: str
    model_version: str
    opening_distance: float
    recurrent_event_month: str
    room_number: str
    room_volume: float
    simulation_name: str
    single_event_date: str
    total_people: int
    ventilation_type: str
    volume_type: str
    windows_duration: float
    windows_frequency: float
    window_height: float
    window_type: str
    window_width: float
    windows_number: int
    windows_open: str

    @classmethod
    def from_dict(cls, form_data: typing.Dict) -> "FormData":

        valid_na_values = ['windows_open', 'window_type', 'mechanical_ventilation_type']
        for name in valid_na_values:
            if not form_data.get(name, ''):
                form_data[name] = 'not-applicable'

        for name in ['lunch_start', 'lunch_finish']:
            if not form_data.get(name, ''):
                form_data[name] = '00:00'

        validation_tuples = [('activity_type', ACTIVITY_TYPES),
                             ('event_type', EVENT_TYPES),
                             ('mechanical_ventilation_type', MECHANICAL_VENTILATION_TYPES),
                             ('mask_type', MASK_TYPES),
                             ('mask_wearing', MASK_WEARING),
                             ('ventilation_type', VENTILATION_TYPES),
                             ('volume_type', VOLUME_TYPES),
                             ('windows_open', WINDOWS_OPEN),
                             ('window_type', WINDOWS_TYPES)]
        for key, valid_set in validation_tuples:
            if key not in form_data:
                raise ValueError(f"Missing key {key}")
            if form_data[key] not in valid_set:
                raise ValueError(f"{form_data[key]} is not a valid value for {key}")

        if (form_data['ventilation_type'] == 'natural' and
            form_data['window_type'] == 'not-applicable'):
            raise ValueError("window_type cannot be ''not-applicable'' if "
                             "ventilation_type is ''natural''")

        # Don't let arbitrary unescaped HTML through the net.
        for key, value in form_data.items():
            if isinstance(value, str):
                form_data[key] = html.escape(value)

        # TODO: This fixup is a problem with the form.html.
        for key, value in form_data.items():
            if value == "":
                form_data[key] = "0"

        return cls(
            activity_finish=time_string_to_minutes(form_data['activity_finish']),
            activity_start=time_string_to_minutes(form_data['activity_start']),
            activity_type=form_data['activity_type'],
            air_changes=float(form_data['air_changes']),
            air_supply=float(form_data['air_supply']),
            ceiling_height=float(form_data['ceiling_height']),
            coffee_breaks=int(form_data['coffee_breaks']),
            coffee_duration=int(form_data['coffee_duration']),
            event_type=form_data['event_type'],
            floor_area=float(form_data['floor_area']),
            hepa_amount=float(form_data['hepa_amount']),
            hepa_option=(form_data['hepa_option'] == '1'),
            infected_people=int(form_data['infected_people']),
            lunch_finish=time_string_to_minutes(form_data['lunch_finish']),
            lunch_option=(form_data['lunch_option'] == '1'),
            lunch_start=time_string_to_minutes(form_data['lunch_start']),
            mask_type=form_data['mask_type'],
            mask_wearing=form_data['mask_wearing'],
            mechanical_ventilation_type=form_data['mechanical_ventilation_type'],
            model_version=form_data['model_version'],
            opening_distance=float(form_data['opening_distance']),
            recurrent_event_month=form_data['recurrent_event_month'],
            room_number=form_data['room_number'],
            room_volume=float(form_data['room_volume']),
            simulation_name=form_data['simulation_name'],
            single_event_date=form_data['single_event_date'],
            total_people=int(form_data['total_people']),
            ventilation_type=form_data['ventilation_type'],
            volume_type=form_data['volume_type'],
            windows_duration=float(form_data['windows_duration']),
            windows_frequency=float(form_data['windows_frequency']),
            window_height=float(form_data['window_height']),
            window_type=form_data['window_type'],
            window_width=float(form_data['window_width']),
            windows_number=int(form_data['windows_number']),
            windows_open=form_data['windows_open'],
            infected_start=time_string_to_minutes(form_data['infected_start']),
            infected_finish=time_string_to_minutes(form_data['infected_finish']),
        )

    def build_model(self) -> models.ExposureModel:
        return model_from_form(self)

    def ventilation(self) -> models.Ventilation:
        always_on = models.PeriodicInterval(period=120, duration=120)
        # Initializes a ventilation instance as a window if 'natural' is selected, or as a HEPA-filter otherwise
        if self.ventilation_type == 'natural':
            if self.windows_open == 'interval':
                window_interval = models.PeriodicInterval(self.windows_frequency*60, self.windows_duration)
            else:
                window_interval = always_on

            if self.event_type == 'single_event':
                month_number = int(self.single_event_date.split('/')[1])
                month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month_number - 1]
            else:
                month = self.recurrent_event_month[:3]

            inside_temp = models.PiecewiseConstant((0, 24), (293,))
            outside_temp = data.GenevaTemperatures[month]

            if self.window_type == 'sliding':
                ventilation = models.SlidingWindow(
                    active=window_interval,
                    inside_temp=inside_temp, outside_temp=outside_temp,
                    window_height=self.window_height,
                    opening_length=self.opening_distance,
                    number_of_windows=self.windows_number,
                )
            elif self.window_type == 'hinged':
                ventilation = models.HingedWindow(
                    active=window_interval,
                    inside_temp=inside_temp, outside_temp=outside_temp,
                    window_height=self.window_height,
                    window_width=self.window_width,
                    opening_length=self.opening_distance,
                    number_of_windows=self.windows_number,
                )

        elif self.ventilation_type == "no-ventilation":
            ventilation = models.AirChange(active=always_on, air_exch=0.)
        else:
            if self.mechanical_ventilation_type == 'air_changes':
                ventilation = models.AirChange(active=always_on, air_exch=self.air_changes)
            else:
                ventilation = models.HVACMechanical(
                    active=always_on, q_air_mech=self.air_supply)

        if self.hepa_option:
            hepa = models.HEPAFilter(active=always_on, q_air_mech=self.hepa_amount)
            return models.MultipleVentilation((ventilation,hepa))
        else:
            return ventilation

    def mask(self) -> models.Mask:
        # Initializes the mask type if mask wearing is "continuous", otherwise instantiates the mask attribute as
        # the "No mask"-mask
        mask = models.Mask.types[self.mask_type if self.mask_wearing == "continuous" else 'No mask']
        return mask

    def infected_population(self) -> models.InfectedPopulation:
        # Initializes the virus as SARS_Cov_2
        virus = models.Virus.types['SARS_CoV_2']

        scenario_activity_and_expiration = {
            'office': (
                'Seated',
                # Mostly silent in the office, but 1/3rd of time talking.
                {'Talking': 1, 'Breathing': 2}
            ),
            'meeting': (
                'Seated',
                # Conversation of N people is approximately 1/N% of the time talking.
                {'Talking': 1, 'Breathing': self.total_people - 1}
            ),
            'callcentre': ('Seated', 'Talking'),
            'library': ('Seated', 'Breathing'),
            'training': ('Standing', 'Talking'),
            'lab': (
                'Light activity',
                #Model 1/2 of time spent talking in a lab.
                {'Talking': 1, 'Breathing': 1}),
            'workshop': (
                'Moderate activity',
                #Model 1/2 of time spent talking in a workshop.
                {'Talking': 1, 'Breathing': 1}),
            'gym':('Heavy exercise', 'Breathing'),
        }

        [activity_defn, expiration_defn] = scenario_activity_and_expiration[self.activity_type]
        activity = models.Activity.types[activity_defn]
        expiration = build_expiration(expiration_defn)

        infected_occupants = self.infected_people

        infected = models.InfectedPopulation(
            number=infected_occupants,
            virus=virus,
            presence=self.infected_present_interval(),
            mask=self.mask(),
            activity=activity,
            expiration=expiration
        )
        return infected

    def exposed_population(self) -> models.Population:
        scenario_activity = {
            'office': 'Seated',
            'meeting': 'Seated',
            'callcentre': 'Seated',
            'library': 'Seated',
            'training': 'Seated',
            'workshop': 'Moderate activity',
            'lab':'Light activity',
            'gym':'Heavy exercise',
        }

        activity_defn = scenario_activity[self.activity_type]
        activity = models.Activity.types[activity_defn]

        infected_occupants = self.infected_people
        # The number of exposed occupants is the total number of occupants
        # minus the number of infected occupants.
        exposed_occupants = self.total_people - infected_occupants

        exposed = models.Population(
            number=exposed_occupants,
            presence=self.exposed_present_interval(),
            activity=activity,
            mask=self.mask(),
        )
        return exposed

    def _compute_breaks_in_interval(self, start, finish, n_breaks) -> typing.Tuple[typing.Tuple[int, int]]:
        break_delay = ((finish - start) - (n_breaks * self.coffee_duration)) // (n_breaks+1)
        break_times = []
        end = start
        for n in range(n_breaks):
            begin = end + break_delay
            end = begin + self.coffee_duration
            break_times.append((begin, end))
        return tuple(break_times)

    def coffee_break_times(self) -> typing.Tuple[typing.Tuple[int, int]]:
        if not self.coffee_breaks:
            return ()
        if self.lunch_option:
            time_before_lunch = self.lunch_start - self.activity_start
            time_after_lunch = self.activity_finish - self.lunch_finish
            before_lunch_frac = time_before_lunch / (time_before_lunch + time_after_lunch)
            n_morning_breaks = round(self.coffee_breaks * before_lunch_frac)
            breaks = (
                self._compute_breaks_in_interval(
                    self.activity_start, self.lunch_start, n_morning_breaks
                )
                + self._compute_breaks_in_interval(
                    self.lunch_finish, self.activity_finish, self.coffee_breaks - n_morning_breaks
                )
            )
        else:
            breaks = self._compute_breaks_in_interval(self.activity_start, self.activity_finish, self.coffee_breaks)
        return breaks

    def present_interval(self, start, finish) -> models.Interval:
        leave_times = []
        enter_times = []
        if self.lunch_option:
            leave_times.append(self.lunch_start)
            enter_times.append(self.lunch_finish)

        for coffee_start, coffee_end in self.coffee_break_times():
            leave_times.append(coffee_start)
            enter_times.append(coffee_end)

        # These lists represent the times where the infected person leaves or enters the room, respectively, sorted in
        # reverse order. Note that these lists allows the person to "leave" when they should not even be present in the
        # room. The following loop handles this.
        leave_times.sort(reverse=True)
        enter_times.sort(reverse=True)

        # This loop iterates through the lists above, populating present_intervals with (enter, leave) intervals
        # representing the infected person entering and leaving the room. Note that if one of the evenly spaced coffee-
        # breaks happens to coincide with the lunch-break, it is simply ignored.
        present_intervals = []
        time = start
        is_present = True
        while time < finish:
            if is_present:
                if not leave_times:
                    present_intervals.append((time / 60, finish / 60))
                    break

                if leave_times[-1] <= time:
                    leave_times.pop()
                else:
                    new_time = leave_times.pop()
                    present_intervals.append((time / 60, min(new_time, finish) / 60))
                    is_present = False
                    time = new_time

            else:
                if not enter_times:
                    break

                if enter_times[-1] < time:
                    enter_times.pop()
                else:
                    is_present = True
                    time = enter_times.pop()

        return models.SpecificInterval(tuple(present_intervals))

    def infected_present_interval(self) -> models.Interval:
        return self.present_interval(self.infected_start, self.infected_finish)

    def exposed_present_interval(self) -> models.Interval:
        return self.present_interval(self.activity_start, self.activity_finish)


def build_expiration(expiration_definition) -> models.Expiration:
    if isinstance(expiration_definition, str):
        return models.Expiration.types[expiration_definition]
    elif isinstance(expiration_definition, dict):
        return expiration_blend({
            build_expiration(exp): amount
            for exp, amount in expiration_definition.items()
            }
        )


def expiration_blend(expiration_weights: typing.Dict[models.Expiration, int]) -> models.Expiration:
    """
    Combine together multiple types of Expiration, using a weighted mean to
    compute their ejection factor and particle sizes.

    """
    ejection_factor = np.zeros(4)
    particle_sizes = np.zeros(4)

    total_weight = 0
    for expiration, weight in expiration_weights.items():
        total_weight += weight
        ejection_factor += np.array(expiration.ejection_factor) * weight
        particle_sizes += np.array(expiration.particle_sizes) * weight

    return models.Expiration(
        ejection_factor=tuple(ejection_factor/total_weight),
        particle_sizes=tuple(particle_sizes/total_weight),
    )


def model_from_form(form: FormData) -> models.ExposureModel:
    # Initializes room with volume either given directly or as product of area and height
    if form.volume_type == 'room_volume':
        volume = form.room_volume
    else:
        volume = form.floor_area * form.ceiling_height
    room = models.Room(volume=volume)

    # Initializes and returns a model with the attributes defined above
    return models.ExposureModel(
        concentration_model=models.ConcentrationModel(
            room=room,
            ventilation=form.ventilation(),
            infected=form.infected_population(),
        ),
        exposed=form.exposed_population()
    )


def baseline_raw_form_data():
    # Note: This isn't a special "baseline". It can be updated as required.
    return {
        'activity_finish': '18:00',
        'activity_start': '09:00',
        'activity_type': 'office',
        'air_changes': '',
        'air_supply': '',
        'ceiling_height': '',
        'coffee_breaks': '4',
        'coffee_duration': '10',
        'event_type': 'recurrent_event',
        'floor_area': '',
        'hepa_amount': '250',
        'hepa_option': '0',
        'infected_finish': '18:00',
        'infected_people': '1',
        'infected_start': '09:00',
        'lunch_finish': '13:30',
        'lunch_option': '1',
        'lunch_start': '12:30',
        'mask_type': 'Type I',
        'mask_wearing': 'removed',
        'mechanical_ventilation_type': '',
        'model_version': 'v1.2.0',
        'opening_distance': '0.2',
        'recurrent_event_month': 'January',
        'room_number': '123',
        'room_volume': '75',
        'simulation_name': 'Test',
        'single_event_date': '',
        'total_people': '10',
        'ventilation_type': 'natural',
        'volume_type': 'room_volume',
        'window_height': '2',
        'window_type': 'sliding',
        'window_width': '2',
        'windows_number': '1',
        'windows_open': 'always'
    }


ACTIVITY_TYPES = {'office', 'meeting', 'training', 'callcentre', 'library', 'workshop', 'lab', 'gym'}
EVENT_TYPES = {'single_event', 'recurrent_event'}
MECHANICAL_VENTILATION_TYPES = {'air_changes', 'air_supply', 'not-applicable'}
MASK_TYPES = {'Type I', 'FFP2'}
MASK_WEARING = {'continuous', 'removed'}
VENTILATION_TYPES = {'natural', 'mechanical', 'no-ventilation'}
VOLUME_TYPES = {'room_volume', 'room_dimensions'}
WINDOWS_OPEN = {'always', 'interval', 'not-applicable'}
WINDOWS_TYPES = {'sliding', 'hinged', 'not-applicable'}


def time_string_to_minutes(time: str) -> int:
    """
    Converts time from string-format to an integer number of minutes after 00:00
    :param time: A string of the form "HH:MM" representing a time of day
    :return: The number of minutes between 'time' and 00:00
    """
    return 60 * int(time[:2]) + int(time[3:])
