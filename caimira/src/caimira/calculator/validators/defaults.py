# ------------------ Default form values ----------------------

# Used to declare when an attribute of a class must have a value provided, and
# there should be no default value used.
NO_DEFAULT = object()

#: The default values for undefined fields. Note that the defaults here
#: and the defaults in the html form must not be contradictory.
DEFAULTS = {
    'CO2_fitting_result': '{}',
    'activity_type': 'office',
    'air_changes': 0.,
    'air_supply': 0.,
    'arve_sensors_option': False,
    'ascertainment_bias': 'confidence_low',
    'calculator_version': NO_DEFAULT,
    'ceiling_height': 0.,
    'conditional_probability_viral_loads': False,
    'dynamic_exposed_occupancy': '[]',
    'dynamic_infected_occupancy': '[]',
    'event_month': 'January',
    'exposed_coffee_break_option': 'coffee_break_0',
    'exposed_coffee_duration': 5,
    'exposed_finish': '17:30',
    'exposed_lunch_finish': '13:30',
    'exposed_lunch_option': True,
    'exposed_lunch_start': '12:30',
    'exposed_start': '08:30',
    'exposure_option': 'p_deterministic_exposure',
    'floor_area': 0.,
    'geographic_cases': 0,
    'geographic_population': 0,
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
    'mask_type': 'Type I',
    'mask_wearing_option': 'mask_off',
    'mechanical_ventilation_type': 'not-applicable',
    'occupancy_format': 'static',
    'opening_distance': 0.,
    'precise_activity': '{}',
    'room_heating_option': False,
    'room_number': NO_DEFAULT,
    'room_volume': 0.,
    'sensor_in_use': '',
    'short_range_interactions': '[]',
    'short_range_occupants': 0,
    'short_range_option': 'short_range_no',
    'simulation_name': NO_DEFAULT,
    'specific_breaks': '{}',
    'total_people': NO_DEFAULT,
    'vaccine_booster_option': False,
    'vaccine_booster_type': 'AZD1222_(AstraZeneca)',
    'vaccine_option': False,
    'vaccine_type': 'AZD1222_(AstraZeneca)',
    'ventilation_type': 'no_ventilation',
    'virus_type': 'SARS_CoV_2',
    'volume_type': NO_DEFAULT,
    'window_height': 0.,
    'window_opening_regime': 'windows_open_permanently',
    'window_type': 'window_sliding',
    'window_width': 0.,
    'windows_duration': 10.,
    'windows_frequency': 60.,
    'windows_number': 0
}

# ------------------ Activities ----------------------

# ------------------ Validation ----------------------
COFFEE_OPTIONS_INT = {'coffee_break_0': 0, 'coffee_break_1': 1,
                      'coffee_break_2': 2, 'coffee_break_4': 4}
CONFIDENCE_LEVEL_OPTIONS = {'confidence_low': 10,
                            'confidence_medium': 5, 'confidence_high': 2}
MECHANICAL_VENTILATION_TYPES = {
    'mech_type_air_changes', 'mech_type_air_supply', 'not-applicable'}
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
VENTILATION_TYPES = {'from_fitting', 'natural_ventilation', 
                     'mechanical_ventilation', 'no_ventilation'}
VOLUME_TYPES = {'room_volume_explicit', 'room_volume_from_dimensions'}
WINDOWS_OPENING_REGIMES = {'windows_open_permanently',
                           'windows_open_periodically', 'not-applicable'}
WINDOWS_TYPES = {'window_sliding', 'window_hinged', 'not-applicable'}
