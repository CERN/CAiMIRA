import typing

# ------------------ Default form values ----------------------

# Used to declare when an attribute of a class must have a value provided, and
# there should be no default value used.
NO_DEFAULT = object()
DEFAULT_MC_SAMPLE_SIZE = 250_000

#: The default values for undefined fields. Note that the defaults here
#: and the defaults in the html form must not be contradictory.
DEFAULTS = {
    'activity_type': 'office',
    'air_changes': 0.,
    'air_supply': 0.,
    'arve_sensors_option': False,
    'specific_breaks': '{}',
    'precise_activity': '{}',
    'calculator_version': NO_DEFAULT,
    'ceiling_height': 0.,
    'conditional_probability_plot': False,
    'conditional_probability_viral_loads': False,
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
    'inside_temp': NO_DEFAULT,
    'location_latitude': NO_DEFAULT,
    'location_longitude': NO_DEFAULT,
    'location_name': NO_DEFAULT,
    'geographic_population': 0,
    'geographic_cases': 0,
    'ascertainment_bias': 'confidence_low',
    'exposure_option': 'p_deterministic_exposure',
    'mask_type': 'Type I',
    'mask_wearing_option': 'mask_off',
    'mechanical_ventilation_type': 'not-applicable',
    'opening_distance': 0.,
    'room_heating_option': False,
    'room_number': NO_DEFAULT,
    'room_volume': 0.,
    'simulation_name': NO_DEFAULT,
    'total_people': NO_DEFAULT,
    'vaccine_option': False,
    'vaccine_booster_option': False,
    'vaccine_type': 'AZD1222_(AstraZeneca)',
    'vaccine_booster_type': 'AZD1222_(AstraZeneca)',
    'ventilation_type': 'no_ventilation',
    'virus_type': 'SARS_CoV_2',
    'volume_type': NO_DEFAULT,
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
    'fetched_service_data': '{}'
}

# ------------------ Activities ----------------------

ACTIVITIES: typing.List[typing.Dict[str, typing.Any]] = [
    # Mostly silent in the office, but 1/3rd of time speaking.
    {'name': 'office', 'activity': 'Seated',
        'expiration': {'Speaking': 1, 'Breathing': 2}},
    {'name': 'smallmeeting', 'activity': 'Seated',
        'expiration': {'Speaking': 1, 'Breathing': None}},
    # Each infected person spends 1/3 of time speaking.
    {'name': 'largemeeting', 'activity': 'Standing',
        'expiration': {'Speaking': 1, 'Breathing': 2}},
    {'name': 'callcentre', 'activity': 'Seated', 'expiration': 'Speaking'},
    # Daytime control room shift, 50% speaking.
    {'name': 'controlroom-day', 'activity': 'Seated',
        'expiration': {'Speaking': 1, 'Breathing': 1}},
    # Nightshift control room, 10% speaking.
    {'name': 'controlroom-night', 'activity': 'Seated',
        'expiration': {'Speaking': 1, 'Breathing': 9}},
    {'name': 'library', 'activity': 'Seated', 'expiration': 'Breathing'},
    # Model 1/2 of time spent speaking in a lab.
    {'name': 'lab', 'activity': 'Light activity',
        'expiration': {'Speaking': 1, 'Breathing': 1}},
    # Model 1/2 of time spent speaking in a workshop.
    {'name': 'workshop', 'activity': 'Moderate activity',
        'expiration': {'Speaking': 1, 'Breathing': 1}},
    {'name': 'training', 'activity': 'Standing', 'expiration': 'Speaking'},
    {'name': 'training_attendee', 'activity': 'Seated', 'expiration': 'Breathing'},
    {'name': 'gym', 'activity': 'Heavy exercise', 'expiration': 'Breathing'},
    {'name': 'household-day', 'activity': 'Light activity',
        'expiration': {'Breathing': 5, 'Speaking': 5}},
    {'name': 'household-night', 'activity': 'Seated',
        'expiration': {'Breathing': 7, 'Speaking': 3}},
    {'name': 'primary-school', 'activity': 'Light activity',
        'expiration': {'Breathing': 5, 'Speaking': 5}},
    {'name': 'secondary-school', 'activity': 'Light activity',
        'expiration': {'Breathing': 7, 'Speaking': 3}},
    {'name': 'university', 'activity': 'Seated',
        'expiration': {'Breathing': 9, 'Speaking': 1}},
    {'name': 'restaurant', 'activity': 'Seated',
        'expiration': {'Breathing': 1, 'Speaking': 9}},
    {'name': 'precise', 'activity': None, 'expiration': None},
]

# ------------------ Validation ----------------------

ACTIVITY_TYPES = [activity['name'] for activity in ACTIVITIES]
COFFEE_OPTIONS_INT = {'coffee_break_0': 0, 'coffee_break_1': 1,
                      'coffee_break_2': 2, 'coffee_break_4': 4}
CONFIDENCE_LEVEL_OPTIONS = {'confidence_low': 10,
                            'confidence_medium': 5, 'confidence_high': 2}
MECHANICAL_VENTILATION_TYPES = {
    'mech_type_air_changes', 'mech_type_air_supply', 'not-applicable'}
MASK_TYPES = {'Type I', 'FFP2', 'Cloth'}
MASK_WEARING_OPTIONS = {'mask_on', 'mask_off'}
MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December',
]
VACCINE_BOOSTER_TYPE = ['AZD1222_(AstraZeneca)', 'Ad26.COV2.S_(Janssen)', 'BNT162b2_(Pfizer)', 'BNT162b2_(Pfizer)_(4th_dose)', 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)',
                        'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)_(4th_dose)', 'CoronaVac_(Sinovac)', 'Coronavac_(Sinovac)', 'Sinopharm',
                        'mRNA-1273_(Moderna)', 'mRNA-1273_(Moderna)_(4th_dose)', 'Other']
VACCINE_TYPE = ['Ad26.COV2.S_(Janssen)', 'Any_mRNA_-_heterologous', 'AZD1222_(AstraZeneca)', 'AZD1222_(AstraZeneca)_and_any_mRNA_-_heterologous', 'AZD1222_(AstraZeneca)_and_BNT162b2_(Pfizer)',
                'BBIBP-CorV_(Beijing_CNBG)', 'BNT162b2_(Pfizer)', 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'CoronaVac_(Sinovac)', 'CoronaVac_(Sinovac)_and_AZD1222_(AstraZeneca)', 'Covishield',
                'mRNA-1273_(Moderna)', 'Sputnik_V_(Gamaleya)', 'CoronaVac_(Sinovac)_and_BNT162b2_(Pfizer)']
VENTILATION_TYPES = {'natural_ventilation',
                     'mechanical_ventilation', 'no_ventilation'}
VIRUS_TYPES = {'SARS_CoV_2', 'SARS_CoV_2_ALPHA', 'SARS_CoV_2_BETA',
               'SARS_CoV_2_GAMMA', 'SARS_CoV_2_DELTA', 'SARS_CoV_2_OMICRON'}
VOLUME_TYPES = {'room_volume_explicit', 'room_volume_from_dimensions'}
WINDOWS_OPENING_REGIMES = {'windows_open_permanently',
                           'windows_open_periodically', 'not-applicable'}
WINDOWS_TYPES = {'window_sliding', 'window_hinged', 'not-applicable'}
