from cara.models import Model
from dataclasses import dataclass
import typing

from cara import models


@dataclass
class FormData:
    # Number of minutes after 00:00
    activity_start: int
    activity_finish: int
    lunch_start: int
    lunch_finish: int

    activity_type: str
    air_changes: float
    air_supply: float
    ceiling_height: float
    coffee_breaks: int
    coffee_duration: int
    coffee_option: bool
    event_type: str
    floor_area: float
    hepa_option: bool
    infected_people: int
    lunch_option: bool
    mask_wearing: str
    mechanical_ventilation_type: str
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
        # TODO: This fixup is a problem with the form.html.
        for key, value in form_data.items():
            if value == "":
                form_data[key] = "0"

        validation_tuples = [('activity_type', ACTIVITY_TYPES),
                             ('event_type', EVENT_TYPES),
                             ('mechanical_ventilation_type', MECHANICAL_VENTILATION_TYPES),
                             ('mask_wearing', MASK_WEARING),
                             ('ventilation_type', VENTILATION_TYPES),
                             ('volume_type', VOLUME_TYPES),
                             ('windows_open', WINDOWS_OPEN)]
        for key, valid_set in validation_tuples:
            if form_data[key] not in valid_set:
                raise ValueError(f"{form_data[key]} is not a valid value for {key}")

        return cls(
            activity_finish=time_string_to_minutes(form_data['activity_finish']),
            activity_start=time_string_to_minutes(form_data['activity_start']),
            activity_type=form_data['activity_type'],
            air_changes=float(form_data['air_changes']),
            air_supply=float(form_data['air_supply']),
            ceiling_height=float(form_data['ceiling_height']),
            coffee_breaks=int(form_data['coffee_breaks']),
            coffee_duration=int(form_data['coffee_duration']),
            coffee_option=(form_data['coffee_option'] == '1'),
            event_type=form_data['event_type'],
            floor_area=float(form_data['floor_area']),
            hepa_option=(form_data['hepa_option'] == '1'),
            infected_people=int(form_data['infected_people']),
            lunch_finish=time_string_to_minutes(form_data['lunch_finish']),
            lunch_option=(form_data['lunch_option'] == '1'),
            lunch_start=time_string_to_minutes(form_data['lunch_start']),
            mask_wearing=form_data['mask_wearing'],
            mechanical_ventilation_type=form_data['mechanical_ventilation_type'],
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
            windows_open=form_data['windows_open']
        )

    # TODO: Remove the tmp_raw_form_data usage.
    def build_model(self, tmp_raw_form_data) -> Model:
        return model_from_form(self, tmp_raw_form_data)

    def ventilation(self) -> models.Ventilation:
        # Initializes a ventilation instance as a window if 'natural' is selected, or as a HEPA-filter otherwise
        if self.ventilation_type == 'natural':
            if self.windows_open == 'interval':
                period, duration = 120, 10
            elif self.windows_number == 'breaks':
                # TODO: Implement windows open in breaks
                period, duration = 120, 120
            else:
                period, duration = 120, 120

            if self.event_type == 'single_event':
                month_number = int(self.single_event_date.split('/')[1])
                month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month_number - 1]
            else:
                month = self.recurrent_event_month[:3]

            inside_temp = models.PiecewiseConstant((0, 24), (293,))
            outside_temp = models.GenevaTemperatures[month]

            # I multiply the opening width by the number of windows to simulate the correct window area
            ventilation = models.WindowOpening(active=models.PeriodicInterval(period=period, duration=duration),
                                               inside_temp=inside_temp, outside_temp=outside_temp, cd_b=0.6,
                                               window_height=self.window_height,
                                               opening_length=self.opening_distance * self.windows_number)
        else:
            if self.mechanical_ventilation_type == 'air_changes':
                ventilation = models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                               air_exch=self.air_changes)
            else:
                ventilation = models.HVACMechanical(active=models.PeriodicInterval(period=120, duration=120),
                                                    q_air_mech=self.air_supply)

        if self.hepa_option:
            hepa = models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                     q_air_mech=250.)
            return models.MultipleVentilation((ventilation,hepa))
        else:
            return ventilation

    def present_interval(self) -> models.Interval:
        coffee_period = (self.activity_finish - self.activity_start) // self.coffee_breaks
        leave_times = [self.lunch_start]
        enter_times = [self.lunch_finish]
        for minute in range(self.activity_start, self.activity_finish, coffee_period):
            leave_times.append(minute + coffee_period // 2)
            enter_times.append(minute + coffee_period // 2 + self.coffee_duration)

        # These lists represent the times where the infected person leaves or enters the room, respectively, sorted in
        # reverse order. Note that these lists allows the person to "leave" when they should not even be present in the
        # room. The following loop handles this.
        leave_times.sort(reverse=True)
        enter_times.sort(reverse=True)

        # This loop iterates through the lists above, populating present_intervals with (enter, leave) intervals
        # representing the infected person entering and leaving the room. Note that if one of the evenly spaced coffee-
        # breaks happens to coincide with the lunch-break, it is simply ignored.
        is_present = True
        present_intervals = []
        time = self.activity_start
        while time < self.activity_finish:
            if is_present:
                if not leave_times:
                    present_intervals.append((time / 60, self.activity_finish / 60))
                    break

                if leave_times[-1] < time:
                    leave_times.pop()
                else:
                    new_time = leave_times.pop()
                    present_intervals.append((time / 60, min(new_time, self.activity_finish) / 60))
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


def model_from_form(form: FormData, tmp_raw_form_data) -> models.Model:
    d = tmp_raw_form_data

    # TODO: This fixup is a problem with the form.html.
    d['coffee_breaks'] = 1
    d['activity_type'] = 'Training'
    d['lunch_start'] = '12:00'
    d['lunch_finish'] = '13:00'

    # Initializes room with volume either given directly or as product of area and height
    if form.volume_type == 'room_volume':
        volume = form.room_volume
    else:
        volume = form.floor_area * form.ceiling_height
    room = models.Room(volume=volume)

    # Initializes the virus as SARS_Cov_2
    virus = models.Virus.types['SARS_CoV_2']

    # Initializes a mask of type 1 if mask wearing is "continuous", otherwise instantiates the mask attribute as
    # the "No mask"-mask
    mask = models.Mask.types['Type I' if d['mask_wearing'] == "continuous" else 'No mask']

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
    return models.Model(
        room=room,
        ventilation=form.ventilation(),
        infected=models.InfectedPerson(
            virus=virus,
            presence=form.present_interval(),
            mask=mask,
            activity=infected_activity,
            expiration=infected_expiration
        ),
        infected_occupants=infected_occupants,
        exposed_occupants=exposed_occupants,
        exposed_activity=exposed_activity
    )


def baseline_raw_form_data():
    # Note: This isn't a special "baseline". It can be updated as required.
    return {
        'activity_finish': '17:00',
        'activity_start': '09:00',
        'activity_type': 'training',
        'air_changes': '',
        'air_supply': '',
        'ceiling_height': '',
        'coffee_breaks': '5',
        'coffee_duration': '10',
        'coffee_option': '1',
        'event_type': 'single_event',
        'floor_area': '',
        'hepa_option': '0',
        'infected_people': '1',
        'lunch_finish': '13:30',
        'lunch_option': '1',
        'lunch_start': '12:30',
        'mask_wearing': 'removed',
        'mechanical_ventilation_type': 'air_changes',
        'opening_distance': '15',
        'recurrent_event_month': 'January',
        'room_number': 'baseline room',
        'room_volume': '75',
        'simulation_name': 'Baseline simulation',
        'single_event_date': '11/02/2020',
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
MECHANICAL_VENTILATION_TYPES = {'air_changes', 'air_supply'}
MASK_WEARING = {'continuous', 'removed'}
VENTILATION_TYPES = {'natural', 'mechanical'}
VOLUME_TYPES = {'room_volume', 'room_dimensions'}
WINDOWS_OPEN = {'always', 'interval', 'breaks'}


def time_string_to_minutes(time: str) -> int:
    """
    Converts time from string-format to an integer number of minutes after 00:00
    :param time: A string of the form "HH:MM" representing a time of day
    :return: The number of minutes between 'time' and 00:00
    """
    return 60 * int(time[:2]) + int(time[3:])
