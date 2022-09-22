import numpy as np
from caimira import models
from caimira.data.weather import wx_data, nearest_wx_station

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


# From data available in Results of COVID-19 Vaccine Effectiveness
# Studies: An Ongoing Systematic Review - Updated September 8, 2022.
# https://view-hub.org/resources
vaccine_host_immunity = {
            'janssen': 0.551277778,
            'any_mRNA': 0.93875,
            'astraZeneca': 0.55921875,
            'astraZeneca_mRNA': 0.718571429,
            'astraZeneca_mRNA_pfizer': 0.7865,
            'beijingCNBG': 0.4325,
            'pfizer': 0.62503012,
            'pfizer_moderna': 0.567126761,
            'sinovac': 0.286884615,
            'sinovac_astraZeneca': 0.561333333,
            'covishield': 0.98,
            'moderna': 0.683255814,
            'gamaleya': 0.696,
            'sinovac_pfizer': 0.7965,
        }
vaccine_booster_host_immunity = {
    'booster_janssen': 0.492666667,
    'booster_astraZeneca': 0.672166667,
    'booster_pfizer': 0.612971831,
    'booster_pfizer_moderna': 0.645,
    'booster_sinovac': 0.427857143,
    'booster_moderna': 0.632442105,
}