from dataclasses import dataclass
import html
import typing

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
    window_height: float
    window_width: float
    windows_number: int
    windows_open: str

    @classmethod
    def from_dict(cls, form_data: typing.Dict) -> "FormData":

        valid_na_values = ['windows_open', 'mechanical_ventilation_type']
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
                             ('windows_open', WINDOWS_OPEN)]
        for key, valid_set in validation_tuples:
            if key not in form_data:
                raise ValueError(f"Missing key {key}")
            if form_data[key] not in valid_set:
                raise ValueError(f"{form_data[key]} is not a valid value for {key}")

        # Don't let arbirtrary unescaped HTML through the net.
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
            window_height=float(form_data['window_height']),
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
                window_interval = models.PeriodicInterval(120, 10)
            else:
                window_interval = always_on

            if self.event_type == 'single_event':
                month_number = int(self.single_event_date.split('/')[1])
                month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month_number - 1]
            else:
                month = self.recurrent_event_month[:3]

            inside_temp = models.PiecewiseConstant((0, 24), (293,))
            outside_temp = data.GenevaTemperatures[month]

            ventilation = models.WindowOpening(
                active=window_interval,
                inside_temp=inside_temp, outside_temp=outside_temp, cd_b=0.6,
                window_height=self.window_height,
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

    def coffee_break_times(self) -> typing.Tuple[typing.Tuple[int, int]]:
        if not self.coffee_breaks:
            return ()
        coffee_period = (self.activity_finish - self.activity_start) // self.coffee_breaks
        coffee_times = []
        for minute in range(self.activity_start, self.activity_finish, coffee_period):
            start = minute + coffee_period // 2
            end = start + self.coffee_duration
            coffee_times.append((start, end))
        return tuple(coffee_times)

    def present_interval(self) -> models.Interval:
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
        time = self.infected_start
        is_present = True
        while time < self.infected_finish:
            if is_present:
                if not leave_times:
                    present_intervals.append((time / 60, self.infected_finish / 60))
                    break

                if leave_times[-1] <= time:
                    leave_times.pop()
                else:
                    new_time = leave_times.pop()
                    present_intervals.append((time / 60, min(new_time, self.infected_finish) / 60))
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


def model_from_form(form: FormData) -> models.ExposureModel:
    # Initializes room with volume either given directly or as product of area and height
    if form.volume_type == 'room_volume':
        volume = form.room_volume
    else:
        volume = form.floor_area * form.ceiling_height
    room = models.Room(volume=volume)

    # Initializes the virus as SARS_Cov_2
    virus = models.Virus.types['SARS_CoV_2']

    # Initializes the mask type if mask wearing is "continuous", otherwise instantiates the mask attribute as
    # the "No mask"-mask
    mask = models.Mask.types[form.mask_type if form.mask_wearing == "continuous" else 'No mask']

    # A dictionary containing the mapping of activities listed in the UI to the activity level and expiration level
    # of the infected and exposed occupants respectively.
    # I.e. (infected_activity, infected_expiration), (exposed_activity, exposed_expiration)

    activity_dict = {'office': (('Seated', 'Talking'), ('Seated', 'Talking')),
                     'training': (('Light exercise', 'Talking'), ('Seated', 'Whispering')),
                     'workshop': (('Light exercise', 'Talking'), ('Light exercise', 'Talking'))}

    (infected_activity, infected_expiration), (exposed_activity, exposed_expiration) = activity_dict[form.activity_type]
    # Converts these strings to Activity and Expiration instances
    infected_activity, exposed_activity = models.Activity.types[infected_activity], models.Activity.types[exposed_activity]
    infected_expiration, exposed_expiration = models.Expiration.types[infected_expiration], models.Expiration.types[exposed_expiration]

    infected_occupants = form.infected_people
    # Defines the number of exposed occupants as the total number of occupants minus the number of infected occupants
    exposed_occupants = form.total_people - infected_occupants

    # Initializes and returns a model with the attributes defined above
    return models.ExposureModel(
        concentration_model=models.ConcentrationModel(
            room=room,
            ventilation=form.ventilation(),
            infected=models.InfectedPopulation(
                number=infected_occupants,
                virus=virus,
                presence=form.present_interval(),
                mask=mask,
                activity=infected_activity,
                expiration=infected_expiration
            ),
        ),
        exposed=models.Population(
            number=exposed_occupants,
            presence=form.present_interval(),
            activity=exposed_activity,
            mask=mask,
        )
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
        'model_version': 'BetaV1.1.0',
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
        'window_width': '2',
        'windows_number': '1',
        'windows_open': 'interval'
    }


ACTIVITY_TYPES = {'office', 'training', 'workshop'}
EVENT_TYPES = {'single_event', 'recurrent_event'}
MECHANICAL_VENTILATION_TYPES = {'air_changes', 'air_supply', 'not-applicable'}
MASK_TYPES = {'Type I', 'FFP2'}
MASK_WEARING = {'continuous', 'removed'}
VENTILATION_TYPES = {'natural', 'mechanical', 'no-ventilation'}
VOLUME_TYPES = {'room_volume', 'room_dimensions'}
WINDOWS_OPEN = {'always', 'interval', 'breaks', 'not-applicable'}


def time_string_to_minutes(time: str) -> int:
    """
    Converts time from string-format to an integer number of minutes after 00:00
    :param time: A string of the form "HH:MM" representing a time of day
    :return: The number of minutes between 'time' and 00:00
    """
    return 60 * int(time[:2]) + int(time[3:])
