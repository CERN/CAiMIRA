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


# ------- VACCINATION DATA -------

# From data available in Results of COVID-19 Vaccine Effectiveness
# Studies: An Ongoing Systematic Review - Updated September 8, 2022.
# https://view-hub.org/resources
vaccine_primary_host_immunity = {
  'Ad26.COV2.S_(Janssen)': 0.551277778,
  'Any_mRNA_-_heterologous': 0.93875,
  'AZD1222_(AstraZeneca)': 0.55921875,
  'AZD1222_(AstraZeneca)_and_any_mRNA_-_heterologous': 0.718571429,
  'AZD1222_(AstraZeneca)_and_BNT162b2_(Pfizer)': 0.7865,
  'BBIBP-CorV_(Beijing_CNBG)': 0.4325,
  'BNT162b2_(Pfizer)': 0.62503012,
  'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)': 0.567126761,
  'CoronaVac_(Sinovac)': 0.286884615,
  'CoronaVac_(Sinovac)_and_AZD1222_(AstraZeneca)': 0.561333333,
  'Covishield': 0.98,
  'mRNA-1273_(Moderna)': 0.683255814,
  'Sputnik_V_(Gamaleya)': 0.696,
  'CoronaVac_(Sinovac)_and_BNT162b2_(Pfizer)': 0.7965,
}

vaccine_booster_host_immunity = [
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'AZD1222_(AstraZeneca)', 'VE': 0.6353636363636364},
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.7389019607843137},
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'VE': 0.26}, 
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.3846666666666667}, 
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'Sinopharm', 'VE': 0.7346666666666666}, 
  {'primary series vaccine': 'AZD1222_(AstraZeneca)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.8642399999999999}, 
  {'primary series vaccine': 'Ad26.COV2.S_(Janssen)', 'booster vaccine': 'Ad26.COV2.S_(Janssen)', 'VE': 0.615}, 
  {'primary series vaccine': 'Ad26.COV2.S_(Janssen)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.9155000000000001}, 
  {'primary series vaccine': 'Ad26.COV2.S_(Janssen)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.6725}, 
  {'primary series vaccine': 'BBIBP-CorV_(Beijing_CNBG)', 'booster vaccine': 'Ad26.COV2.S_(Janssen)', 'VE': 0.8973333333333333}, 
  {'primary series vaccine': 'BBIBP-CorV_(Beijing_CNBG)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.9283333333333332}, 
  {'primary series vaccine': 'BBIBP-CorV_(Beijing_CNBG)', 'booster vaccine': 'Sinopharm', 'VE': 0.7639999999999999}, 
  {'primary series vaccine': 'BBIBP-CorV_(Beijing_CNBG)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.9526666666666667}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'AZD1222_(AstraZeneca)', 'VE': 0.8960000000000001}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'Ad26.COV2.S_(Janssen)', 'VE': 0.9306666666666666}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.7413183520599251}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.6004285714285714}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'CoronaVac_(Sinovac)', 'VE': 0.121}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'Sinopharm', 'VE': 0.6683333333333333}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.7530214285714285}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)_and_mRNA-1273_(Moderna)', 'VE': 0.645}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_(2_doses)_+_mRNA-1273_(Moderna)_(3rd_dose)', 'booster vaccine': 'mRNA-1273_(Moderna)_(4th_dose)', 'VE': 0.6466666666666667}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_(3_doses)', 'booster vaccine': 'BNT162b2_(Pfizer)_(4th_dose)', 'VE': 0.6068333333333333}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_(3_doses)', 'booster vaccine': 'mRNA-1273_(Moderna)_(4th_dose)', 'VE': 0.498}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.7564285714285713}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.7541721854304636}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.7538571428571429}, 
  {'primary series vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)_(3_doses)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)_(4th_dose)', 'VE': 0.5788888888888889}, 
  {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'AZD1222_(AstraZeneca)', 'VE': 0.9584285714285714}, 
  {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.7631960784313726}, 
  {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'CoronaVac_(Sinovac)', 'VE': 0.7141851851851851}, 
  {'primary series vaccine': 'CoronaVac_(Sinovac)', 'booster vaccine': 'Coronavac_(Sinovac)', 'VE': 0.5107647058823529}, 
  {'primary series vaccine': 'Sputnik_V_(Gamaleya)', 'booster vaccine': 'Ad26.COV2.S_(Janssen)', 'VE': 0.8076666666666666}, 
  {'primary series vaccine': 'Sputnik_V_(Gamaleya)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.936}, 
  {'primary series vaccine': 'Sputnik_V_(Gamaleya)', 'booster vaccine': 'Sinopharm', 'VE': 0.5285}, 
  {'primary series vaccine': 'Sputnik_V_(Gamaleya)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.9366666666666668}, 
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'Ad26.COV2.S_(Janssen)', 'VE': 0.8873333333333333}, 
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)', 'VE': 0.8068636363636363}, 
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'BNT162b2_(Pfizer)_or_mRNA-1273_(Moderna)', 'VE': 0.5692499999999999}, 
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'Sinopharm', 'VE': 0.7739999999999999}, 
  {'primary series vaccine': 'mRNA-1273_(Moderna)', 'booster vaccine': 'mRNA-1273_(Moderna)', 'VE': 0.7141650485436892}, 
  {'primary series vaccine': 'mRNA-1273_(Moderna)_(3_doses)', 'booster vaccine': 'mRNA-1273_(Moderna)_(4th_dose)', 'VE': 0.7066666666666667}]