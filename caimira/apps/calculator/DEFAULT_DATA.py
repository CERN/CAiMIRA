import tornado.web
import typing

# ------------------ Translation ----------------------

_ = tornado.locale.get().translate

# ------------------ Default form values ----------------------

# Used to declare when an attribute of a class must have a value provided, and
# there should be no default value used.
_NO_DEFAULT = object()
_DEFAULT_MC_SAMPLE_SIZE = 250_000
# The calculator version is based on a combination of the model version and the
# semantic version of the calculator itself. The version uses the terms
# "{MAJOR}.{MINOR}.{PATCH}" to describe the 3 distinct numbers constituting a version.
# Effectively, if the model increases its MAJOR version then so too should this
# calculator version. If the calculator needs to make breaking changes (e.g. change
# form attributes) then it can also increase its MAJOR version without needing to
# increase the overall CARA version (found at ``cara.__version__``).
__version__ = "4.4"
_DEFAULTS = {
        'activity_type': 'office',
        'air_changes': 0.,
        'air_supply': 0.,
        'arve_sensors_option': False,
        'specific_breaks': '{}',
        'precise_activity': '{}',
        'calculator_version': __version__,
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
        'infected_people': 1,
        'infected_start': '08:30',
        'inside_temp': _NO_DEFAULT,
        'location_latitude': _NO_DEFAULT,
        'location_longitude': _NO_DEFAULT,
        'location_name': _NO_DEFAULT,
        'geographic_population': 0,
        'geographic_cases': 0,
        'ascertainment_bias': 'confidence_low',
        'exposure_option': 'p_deterministic_exposure',
        'mask_type': 'Type I',
        'mask_wearing_option': 'mask_off',
        'mechanical_ventilation_type': 'not-applicable',
        'opening_distance': 0.,
        'room_heating_option': False,
        'room_number': _NO_DEFAULT,
        'room_volume': 0.,
        'simulation_name': _NO_DEFAULT,
        'total_people': _NO_DEFAULT,
        'vaccine_option': False,
        'vaccine_booster_option': False,
        'vaccine_type': 'AZD1222_(AstraZeneca)',
        'vaccine_booster_type': 'AZD1222_(AstraZeneca)',
        'ventilation_type': 'no_ventilation',
        'virus_type': 'SARS_CoV_2',
        'volume_type': _NO_DEFAULT,
        'window_type': 'window_sliding',
        'window_height': 0.,
        'window_width': 0.,
        'windows_duration': 10.,
        'windows_frequency': 60.,
        'windows_number': 0,
        'window_opening_regime': 'windows_open_permanently',
        'sensor_in_use': '',
        'short_range_option': 'short_range_no',
        'short_range_interactions': '[]',
    }

# ------------------ Activities ----------------------

ACTIVITY_TYPES: typing.List[typing.Dict[str, typing.Any]] = [
    {'id': 'office', 'name': _('Office'), 'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': 2}}, # Mostly silent in the office, but 1/3rd of time speaking.
    {'id': 'smallmeeting', 'name': _('Small meeting (<10 occ.)'), 'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': 2}}, #self.total_people - 1}}, # Conversation of N people is approximately 1/N% of the time speaking.
    {'id': 'largemeeting', 'name': _('Large meeting (>=10 occ.)'), 'activity': 'Standing', 'expiration': {'Speaking': 1, 'Breathing': 2}}, # each infected person spends 1/3 of time speaking.
    {'id': 'callcentre', 'name': _('Call Centre'), 'activity': 'Seated', 'expiration': 'Speaking'},
    {'id': 'controlroom-day', 'name': _('Control Room - Day shift'), 'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': 1}}, # Daytime control room shift, 50% speaking.
    {'id': 'controlroom-night', 'name': _('Control Room - Night shift'), 'activity': 'Seated', 'expiration': {'Speaking': 1, 'Breathing': 9}}, # Nightshift control room, 10% speaking.
    {'id': 'library', 'name': _('Library'), 'activity': 'Seated', 'expiration': 'Breathing'}, 
    {'id': 'lab', 'name': _('Laboratory'), 'activity': 'Light activity', 'expiration': {'Speaking': 1, 'Breathing': 1}}, #Model 1/2 of time spent speaking in a lab.
    {'id': 'workshop', 'name': _('Workshop'), 'activity': 'Moderate activity', 'expiration': {'Speaking': 1, 'Breathing': 1}}, #Model 1/2 of time spent speaking in a workshop.
    {'id': 'training', 'name': _('Conference/Training (speaker infected)'), 'activity': 'Standing', 'expiration': 'Speaking'},
    {'id': 'training_attendee', 'name': _('Conference/Training (attendee infected)'), 'activity': 'Seated', 'expiration': 'Breathing'},
    {'id': 'gym', 'name': _('Gym'), 'activity': 'Heavy exercise', 'expiration': 'Breathing'},
    {'id': 'household-day', 'name': _('Household (day)'), 'activity': 'Light activity', 'expiration': {'Breathing': 5, 'Speaking': 5}},
    {'id': 'household-night', 'name': _('Household (night)'), 'activity': 'Seated', 'expiration': {'Breathing': 7, 'Speaking': 3}},
    {'id': 'primary-school', 'name': _('Primary School'), 'activity': 'Light activity', 'expiration': {'Breathing': 5, 'Speaking': 5}},
    {'id': 'secundary-school', 'name': _('Secundary School'), 'activity': 'Light activity', 'expiration': {'Breathing': 7, 'Speaking': 3}},
    {'id': 'university', 'name': _('University'), 'activity': 'Seated', 'expiration': {'Breathing': 9, 'Speaking': 1}},
    {'id': 'restaurant', 'name': _('Restaurant'), 'activity': 'Seated', 'expiration': {'Breathing': 1, 'Speaking': 9}},
    {'id': 'precise', 'name': _('Precise'), 'activity': '', 'expiration': ''},] #self.generate_precise_activity_expiration() 

# ------------------ Validation ----------------------

MECHANICAL_VENTILATION_TYPES = {'mech_type_air_changes', 'mech_type_air_supply', 'not-applicable'}
MASK_TYPES = {'Type I', 'FFP2', 'Cloth'}
MASK_WEARING_OPTIONS = {'mask_on', 'mask_off'}
VENTILATION_TYPES = {'natural_ventilation', 'mechanical_ventilation', 'no_ventilation'}
VIRUS_TYPES = {'SARS_CoV_2', 'SARS_CoV_2_ALPHA', 'SARS_CoV_2_BETA','SARS_CoV_2_GAMMA', 'SARS_CoV_2_DELTA', 'SARS_CoV_2_OMICRON'}
VOLUME_TYPES = {'room_volume_explicit', 'room_volume_from_dimensions'}
WINDOWS_OPENING_REGIMES = {'windows_open_permanently', 'windows_open_periodically', 'not-applicable'}
WINDOWS_TYPES = {'window_sliding', 'window_hinged', 'not-applicable'}
COFFEE_OPTIONS_INT = {'coffee_break_0': 0, 'coffee_break_1': 1, 'coffee_break_2': 2, 'coffee_break_4': 4}
CONFIDENCE_LEVEL_OPTIONS = {'confidence_low': 10, 'confidence_medium': 5, 'confidence_high': 2}
MONTH_NAMES = {
    'January' : _('January'), 'February' : _('February'), 'March' : _('March'), 'April' : _('April'), 'May' : _('May'), 'June' :_('June'), 'July' : _('July'),
    'August' : _('August'), 'September' : _('September'), 'October': _('October'), 'November' : _('November'), 'December' : _('December'),
}
VACCINE_TYPE = ['Ad26.COV2.S_(Janssen)', 'Any_mRNA_-_heterologous', 'AZD1222_(AstraZeneca)', 'AZD1222_(AstraZeneca)_and_any_mRNA_-_heterologous', 'AZD1222_(AstraZeneca)_and_BNT162b2_(Pfizer)',
    'BBIBP-CorV_(Beijing_CNBG)', 'BNT162b2_(Pfizer)', 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'CoronaVac_(Sinovac)', 'CoronaVac_(Sinovac)_and_AZD1222_(AstraZeneca)', 'Covishield',
    'mRNA-1273_(Moderna)', 'Sputnik_V_(Gamaleya)', 'CoronaVac_(Sinovac)_and_BNT162b2_(Pfizer)']
VACCINE_BOOSTER_TYPE = ['AZD1222_(AstraZeneca)', 'Ad26.COV2.S_(Janssen)', 'BNT162b2_(Pfizer)', 'BNT162b2_(Pfizer)_(4th_dose)', 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)',
    'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)_(4th_dose)', 'CoronaVac_(Sinovac)', 'Coronavac_(Sinovac)', 'Sinopharm',
    'mRNA-1273_(Moderna)', 'mRNA-1273_(Moderna)_(4th_dose)', 'Other']

# ------------------ Text ----------------------

TOOLTIPS = {
    'virus_data': _('Choose the SARS-CoV-2 Variant of Concern (VOC) and select the vaccine type taken by the majority of the exposed population.'),
    'room_data': _('The area you wish to study (choose one of the 2 options). Indicate if a central (radiator-type) heating system is in use.'),
    'room_data_cern': _('The area you wish to study (choose one of the 2 options). Use GIS Portal or measure. Also indicate if a central (radiator-type) heating system is in use.'),
    'ventilation_data': _('The available means of venting / filtration of indoor spaces.'),
    'face_masks': _('Masks worn at workstations or removed when a 2m physical distance is respected and proper venting is ensured.'),
    'event_data': _('"The total no. of occupants in the room.\nDeterministic exposure: add no. occupants that are infected.\nProbabilistic exposure: event at a given time & location (e.g. meeting or conference), considering the incidence rate in that area."'),
    'activity_breaks': _('Input breaks that, by default, are the same for infected/exposed person(s) unless specified otherwise.'),
    'window_open': _('Permanently or periodically - e.g. open the window for 10 minutes (duration) every 60 minutes (frequency).'),
}

PLACEHOLDERS = {
    'simulation_name': _('E.g. Workshop without masks'),
    'room_number': _('E.g. 17/R-033'),
    'room_volume': _('Room volume'),
    'room_floor_area': _('Room floor area'),
    'ceiling_height': _('Room ceiling height'),
    'air_supply': _('Flow rate'),
    'air_changes': _('Air exchange'),
    'windows_number': _('Number'),
    'window_height': _('Height'),
    'window_width': _('Width'),
    'opening_distance': _('Opening distance'),
    'hepa_amount': _('Flow rate'),
    'total_people': _('Number'),
    'geographic_population': _('Inhabitants'),
    'geographic_cases': _('Cases (#7-day rolling avg)'),
}
