import numpy as np
from cara import models
from cara.data.weather import wx_data, nearest_wx_station

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December',
]

# Load the weather data (temperature in kelvin) for Geneva. 
coordinates = (46.204391, 6.143158)
wx_station_id = nearest_wx_station(longitude=coordinates[1], latitude=coordinates[0])[0]
# average temperature of each month, hour per hour (from midnight to 11 pm)
Geneva_hourly_temperatures_celsius_per_hour = {month.replace(month, MONTH_NAMES[i][:3]): 
											[t - 273.15 for t in temp] for i, (month, temp) 
											in enumerate(wx_data()[wx_station_id].items())}
							
# Geneva hourly temperatures as piecewise constant function (in Kelvin).
GenevaTemperatures_hourly = {
    month: models.PiecewiseConstant(
        # NOTE:  It is important that the time type is float, not np.float, in
        # order to allow hashability (for caching).
        tuple(float(time) for time in range(25)),
        tuple(273.15 + np.array(temperatures)),
    )
    for month, temperatures in Geneva_hourly_temperatures_celsius_per_hour.items()
}


# Same temperatures on a finer temperature mesh (every 6 minutes).
GenevaTemperatures = {
    month: GenevaTemperatures_hourly[month].refine(refine_factor=10)
    for month, temperatures in Geneva_hourly_temperatures_celsius_per_hour.items()
}
