import numpy as np
from caimira.calculator.models import models
from .weather import wx_data, nearest_wx_station

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December',
]


def get_hourly_temperatures_celsius_per_hour(coordinates):
    wx_station_id = nearest_wx_station(
        longitude=coordinates[1], latitude=coordinates[0])[0]
    # Average temperature of each month, hour per hour (from midnight to 11 pm)
    return {month.replace(month, MONTH_NAMES[i][:3]):
            [t - 273.15 for t in temp] for i, (month, temp)
            in enumerate(wx_data()[wx_station_id].items())}


# Load the weather data (temperature in kelvin) for Geneva.
geneva_coordinates = (46.204391, 6.143158)
local_hourly_temperatures_celsius_per_hour = get_hourly_temperatures_celsius_per_hour(
    geneva_coordinates)


# Geneva hourly temperatures as piecewise constant function (in Kelvin).
GenevaTemperatures_hourly = {
    month: models.PiecewiseConstant(
        # NOTE:  It is important that the time type is float, not np.float, in
        # order to allow hashability (for caching).
        tuple(float(time) for time in range(25)),
        tuple(273.15 + np.array(temperatures)),
    )
    for month, temperatures in local_hourly_temperatures_celsius_per_hour.items()
}


# Same Geneva temperatures on a finer temperature mesh (every 6 minutes).
GenevaTemperatures = {
    month: GenevaTemperatures_hourly[month].refine(refine_factor=10)
    for month, temperatures in local_hourly_temperatures_celsius_per_hour.items()
}


# ------- VACCINATION DATA -------

# From data available in Results of COVID-19 Vaccine Effectiveness
# Studies: An Ongoing Systematic Review - Updated September 8, 2022.
# https://view-hub.org/resources
vaccine_primary_host_immunity = {
    'AZD1222_(AstraZeneca)': 0.589293,
    'AZD1222_(AstraZeneca)_and_BNT162b2_(Pfizer)': 0.7865,
    'AZD1222_(AstraZeneca)_and_any_mRNA_-_heterologous': 0.81,
    'Ad26.COV2.S_(Janssen)': 0.551278,
    'Any_mRNA_-_heterologous': 0.93875,
    'BBIBP-CorV_(Beijing_CNBG)': 0.4325,
    'BNT162b2_(Pfizer)': 0.660272,
    'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)': 0.586319,
    'CoronaVac_(Sinovac)': 0.317333,
    'CoronaVac_(Sinovac)_and_AZD1222_(AstraZeneca)': 0.472,
    'CoronaVac_(Sinovac)_and_AZD1222_(AstraZeneca)_-_heterologous': 0.74,
    'CoronaVac_(Sinovac)_and_BNT162b2_(Pfizer)': 0.7965,
    'Covishield': 0.98,
    'Sputnik_V_(Gamaleya)': 0.696,
    'mRNA-1273_(Moderna)': 0.730148,
}

vaccine_booster_host_immunity = [
    {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'AZD1222_(AstraZeneca)', 'VE': 0.500429},
    {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.537818},
    {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.284},
    {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.709143},
    {'primary series vaccine': 'Ad26.COV2.S_(Janssen)', 'booster vaccine': 'Ad26.COV2.S_(Janssen)', 'VE': 0.492667},
    {'primary series vaccine': 'Ad26.COV2.S_(Janssen)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.79},
    {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'AZD1222_(AstraZeneca)', 'VE': 0.801},
    {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.60712},
    {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.632633},
    {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.716786},
    {'primary series vaccine': 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'VE': 0.645},
    {'primary series vaccine': 'BNT162b2_(Pfizer)_(3_doses)', 'booster vaccine': 'BNT162b2_(Pfizer)_(4th_dose)', 'VE': 0.962},
    {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'AZD1222_(AstraZeneca)', 'VE': 0.9405},
    {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.690563},
    {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'CoronaVac_(Sinovac)', 'VE': 0.52225},
    {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.842143},
    {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.632633},
    {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.633238}
]
