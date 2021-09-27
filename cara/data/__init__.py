import numpy as np
from cara import models

# TODO: The values in this module to be removed and instead use the cara.data.weather functionality.

# average temperature of each month, hour per hour (from midnight to 11 pm)
Geneva_hourly_temperatures_celsius_per_hour = {
    'Jan': [1.3, 1.1, 1.0, 1.0, 0.8, 0.8, 0.9, 0.9, 1.1, 1.8, 2.6,
    3.3, 3.8, 4.2, 4.4, 4.4, 3.9, 3.2, 2.8, 2.4, 2.1, 1.9, 1.6, 1.4],
    'Feb': [1.6, 1.3, 1.1, 1.0, 0.8, 0.7, 0.9, 0.8, 1.5, 2.8, 3.8, 
    4.7, 5.4, 6.0, 6.3, 6.4, 6.0, 5.1, 4.3, 3.6, 3.1, 2.8, 2.3, 1.9],
    'Mar': [4.8, 4.3, 3.9, 3.7, 3.4, 3.2, 3.3, 3.9, 5.6, 6.9, 8.1, 9.0, 
    9.9, 10.6, 11.0, 11.1, 10.8, 10.1, 8.9, 7.8, 7.0, 6.5, 5.8, 5.2],
    'Apr': [8.0, 7.4, 6.9, 6.8, 6.3, 6.1, 6.9, 8.4, 9.8, 10.9, 12.0, 12.9,
    13.7, 14.3, 14.7, 14.8, 14.6, 14.0, 13.0, 11.6, 10.7, 10.0, 9.2, 8.5],
    'May': [11.9, 11.3, 10.8, 10.6, 10.2, 10.4, 11.9, 13.2, 14.3, 15.4, 16.4,
    17.3, 18.1, 18.6, 18.9, 19.0, 18.7, 18.2, 17.3, 15.9, 14.7, 13.9, 13.1, 12.4],
    'Jun': [15.4, 14.7, 14.3, 14.1, 13.6, 14.1, 15.7, 17.0, 18.2, 19.2, 20.2,
    21.2, 22.0, 22.6, 22.9, 23.0, 22.7, 22.2, 21.5, 20.0, 18.6, 17.7, 16.8, 16.0],
    'Jul': [17.4, 16.8, 16.3, 16.1, 15.5, 15.8, 17.5, 18.9, 20.2, 21.3, 22.4,
    23.4, 24.4, 24.9, 25.3, 25.5, 25.2, 24.7, 23.9, 22.3, 20.8, 19.8, 18.8, 18.0],
    'Aug': [17.1, 16.4, 15.9, 15.7, 15.2, 15.1, 16.3, 18.1, 19.6, 20.8, 22.0, 
    23.0, 23.9, 24.5, 25.0, 25.2, 24.9, 24.2, 23.1, 21.2, 20.0, 19.1, 18.2, 17.5],
    'Sep': [13.4, 12.9, 12.5, 12.4, 12.0, 11.9, 12.3, 13.6, 15.1, 16.3, 17.4, 
    18.4, 19.2, 19.8, 20.2, 20.2, 19.9, 19.0, 17.5, 16.2, 15.5, 14.9, 14.1, 13.6],
    'Oct': [9.7, 9.4, 9.2, 9.2, 8.9, 8.9, 9.1, 9.4, 10.6, 11.7, 12.6, 13.5, 
    14.2, 14.6, 14.9, 14.8, 14.1, 13.0, 12.1, 11.4, 10.9, 10.6, 10.1, 9.7],
    'Nov': [5.1, 4.8, 4.7, 4.8, 4.5, 4.6, 4.7, 4.7, 5.3, 6.3, 7.0,
    7.7, 8.3, 8.6, 8.7, 8.5, 7.7, 7.0, 6.6, 6.1, 5.8, 5.6, 5.3, 5.0],
    'Dec': [2.2, 2.0, 1.9, 1.9, 1.7, 1.7, 1.8, 1.7, 1.9, 2.6, 3.3,
    4.0, 4.5, 4.8, 4.9, 4.7, 4.1, 3.6, 3.3, 3.0, 2.8, 2.7, 2.4, 2.2]
 }


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
