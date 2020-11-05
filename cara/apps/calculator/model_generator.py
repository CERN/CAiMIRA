from cara.models import Model
from dataclasses import dataclass
import typing

from cara import models


@dataclass
class FormData:
    ceiling_height: float

    @classmethod
    def from_dict(cls, form_data: typing.Dict) -> "FormData":
        # TODO: This fixup is a problem with the form.html.
        form_data['ceiling_height'] = 1

        return cls(
            ceiling_height=float(form_data['ceiling_height']),
        )

    # TODO: Remove the tmp_raw_form_data usage.
    def build_model(self, tmp_raw_form_data) -> Model:
        return model_from_form(self, tmp_raw_form_data)

    def ventilation(self) -> models.Ventilation:
        # TODO
        pass

    def present_interval(self) -> models.Interval:
        # TODO
        pass


def model_from_form(form: FormData, tmp_raw_form_data) -> models.Model:
    d = tmp_raw_form_data

    # TODO: This fixup is a problem with the form.html.
    d['coffee_breaks'] = 1
    d['activity_type'] = 'Training'
    d['lunch_start'] = '12:00'
    d['lunch_finish'] = '13:00'

    # Initializes room with volume either given directly or as product of area and height
    if d['volume_type'] == 'room_volume':
        volume = int(d['room_volume'])
    else:
        volume = int(float(d['floor_area']) * form.ceiling_height)
    room = models.Room(volume=volume)

    # Initializes a ventilation instance as a window if 'natural' is selected, or as a HEPA-filter otherwise
    if d['ventilation_type'] == 'natural':
        if d['windows_open'] == 'always':
            period, duration = 120, 120
        else:
            period, duration = 15, 120
        # I multiply the opening width by the number of windows to simulate the correct window area
        ventilation = models.WindowOpening(active=models.PeriodicInterval(period=period, duration=duration),
                                           inside_temp=293, outside_temp=283, cd_b=0.6,
                                           window_height=float(d['window_height']),
                                           opening_length=float(d['opening_distance']) * int(d['windows_number']))
    else:
        q_air_mech = float(d['air_changes']) if d['air_type'] == 'air_changes' else float(d['air_supply'])
        ventilation = models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                        q_air_mech=q_air_mech)

    # Initializes the virus as SARS_Cov_2
    virus = models.Virus.types['SARS_CoV_2']

    # Defines all of the parameters required to construct a list of intervals where the infected person is present in
    # the room
    activity_start = int(d['activity_start'][:2]) * 60 + int(d['activity_start'][3:])
    activity_finish = int(d['activity_finish'][:2]) * 60 + int(d['activity_finish'][3:])
    lunch_start = int(d['lunch_start'][:2]) * 60 + int(d['lunch_start'][3:])
    lunch_finish = int(d['lunch_finish'][:2]) * 60 + int(d['lunch_finish'][3:])
    coffee_duration = int(d['coffee_duration'])
    coffee_breaks = int(d['coffee_breaks'])
    coffee_period = (activity_finish - activity_start) // coffee_breaks + 1
    leave_times = [lunch_start]
    enter_times = [lunch_finish]
    for minute in range(activity_start, activity_finish, coffee_period):
        leave_times.append(minute)
        enter_times.append(minute + coffee_duration)

    # These lists represent the times where the infected person leaves or enters the room, respectively, sorted in
    # reverse order. Note that these lists allows the person to "leave" when they should not even be present in the room
    # The following loop handles this.
    leave_times.sort(reverse=True)
    enter_times.sort(reverse=True)

    # This loop iterates through the lists above, populating present_intervals with (enter, leave) intervals
    # representing the infected person entering and leaving the room. Note that if one of the evenly spaced coffee-
    # breaks happens to coincide with the lunch-break, it is simply ignored.
    is_present = True
    present_intervals = []
    time = activity_start
    while time < activity_finish:
        if is_present:
            if not leave_times:
                present_intervals.append((time / 60, activity_finish / 60))
                break

            if leave_times[-1] < time:
                leave_times.pop()
            else:
                new_time = leave_times.pop()
                present_intervals.append((time / 60, min(new_time, activity_finish) / 60))
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

    # Initializes a mask of type 1 if mask wearing is "continuous", otherwise instantiates the mask attribute as
    # the "No mask"-mask
    mask = models.Mask.types['Type I' if d['mask_wearing'] == "Continuous" else 'No mask']

    # A dictionary containing the mapping of activities listed in the UI to the activity level and expiration level
    # of the infected and exposed occupants respectively.
    # I.e. (infected_activity, infected_expiration), (exposed_activity, exposed_expiration)

    activity_dict = {'Office/Meeting': (('Seated', 'Talking'), ('Seated', 'Talking')),
                     'Training': (('Light exercise', 'Talking'), ('Seated', 'Whispering')),
                     'Workshop': (('Light exercise', 'Talking'), ('Light exercise', 'Talking'))}

    (infected_activity, infected_expiration), (exposed_activity, exposed_expiration) = activity_dict[d['activity_type']]
    # Converts these strings to Activity and Expiration instances
    infected_activity, exposed_activity = models.Activity.types[infected_activity], models.Activity.types[exposed_activity]
    infected_expiration, exposed_expiration = models.Expiration.types[infected_expiration], models.Expiration.types[exposed_expiration]

    infected_occupants = int(d['infected_people'])
    # Defines the number of exposed occupants as the total number of occupants minus the number of infected occupants
    exposed_occupants = int(d['total_people']) - infected_occupants

    # Initializes and returns a model with the attributes defined above
    return models.Model(
        room=room,
        ventilation=ventilation,
        infected=models.InfectedPerson(
            virus=virus,
            presence=models.SpecificInterval(tuple(present_intervals)),
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
        'coffee_breaks': '',
        'coffee_duration': '1',
        'coffee_option': '0',
        'event_type': 'single_event',
        'floor_area': '',
        'infected_people': '1',
        'lunch_finish': '13:30',
        'lunch_option': '1',
        'lunch_start': '12:30',
        'mask_wearing': 'removed',
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


def time_string_to_minutes(time: str) -> int:
    """
    Converts time from string-format to an integer number of minutes after 00:00
    :param time: A string of the form "HH:MM" representing a time of day
    :return: The number of minutes between 'time' and 00:00
    """
    return 60 * int(time[:2]) + int(time[3:])
