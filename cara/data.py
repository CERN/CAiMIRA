import numpy as np
from cara import models
import json
import urllib.request
from pathlib import Path
from scipy.spatial import cKDTree
import os
import typing

weather_debug = False


def location_to_weather_stn(location_loc):
    # expects a tuple (lat, long)
    # returns: weather station ID, weather station name, weather station lat, long
    search_coords = location_loc.split(',')
    lat = []
    long = []
    station_array = []
    fixed_delimits = [0, 12, 13, 44, 51, 60, 69, 90, 91]
    station_file = Path(
        os.getcwd()+'/cara/hadisd_station_fullinfo_v311_202001p.txt')

    for line in station_file.open('rt'):
        start_end_positions = zip(fixed_delimits[:-1], fixed_delimits[1:])
        split_vals = [line[start:end] for start, end in start_end_positions]
        station_location = [split_vals[0],
                            split_vals[2], split_vals[3], split_vals[4]]
        station_array.append(station_location)
        lat.append(split_vals[3])
        long.append(split_vals[4])

    tree = cKDTree(np.c_[lat, long])
    dd, ii = tree.query(search_coords, k=[1])

    return (station_array[ii[0]][0], station_array[ii[0]][1], station_array[ii[0]][2], station_array[ii[0]][3])


def location_celcius_per_hour(location: object) -> typing.Dict[str, typing.List[float]]:
    # expects a tuple (lat, long)
    # returns a json format set of weather data
    w_station = location_to_weather_stn(location)
    with open(Path(os.getcwd()+"/cara/global_weather_set.json"), "r") as json_file:
        weather_dict = json.load(json_file)
    Location_hourly_temperatures_celsius_per_hour = weather_dict[w_station[0]]
    if weather_debug:
        print(location)
        print("weather station name: ", w_station[1])
        print("weather station ref: ", w_station[0])
        print("weather station location: ", w_station[2], " ", w_station[3])
        print(Location_hourly_temperatures_celsius_per_hour)
    return Location_hourly_temperatures_celsius_per_hour


# initialise with Geneva, change if location is different.
local_tempatures = {
    '1': [0.2, -0.3, -0.5, -0.9, -1.1, -1.4, -1.5, -1.5, -1.1, 0.1, 1.5,
          2.8, 3.8, 4.4, 4.5, 4.4, 4.4, 3.9, 3.1, 2.7, 2.2, 1.7, 1.5, 1.1],
    '2': [0.9, 0.3, 0.0, -0.5, -0.7, -1.1, -1.2, -1.1, -0.7, 0.8, 2.5,
          4.2, 5.4, 6.2, 6.3, 6.2, 6.1, 5.5, 4.5, 4.1, 3.5, 2.8, 2.5, 2.0],
    '3': [4.2, 3.5, 3.1, 2.5, 2.1, 1.6, 1.5, 1.6, 2.2, 4.0, 6.3, 8.4,
          10.0, 11.1, 11.2, 11.1, 11.0, 10.2, 8.9, 8.3, 7.5, 6.7, 6.3, 5.6],
    '4': [7.4, 6.7, 6.2, 5.5, 5.2, 4.7, 4.5, 4.6, 5.3, 7.2, 9.6, 11.9,
          13.7, 14.8, 14.9, 14.8, 14.7, 13.8, 12.4, 11.8, 10.9, 10.1, 9.6, 8.9],
    '5': [11.8, 11.1, 10.6, 9.9, 9.5, 8.9, 8.8, 8.9, 9.6, 11.6, 14.2, 16.6,
          18.4, 19.6, 19.7, 19.6, 19.4, 18.6, 17.1, 16.5, 15.6, 14.6, 14.2, 13.4],
    '6': [15.2, 14.4, 13.9, 13.2, 12.7, 12.2, 12.0, 12.1, 12.8, 15.0, 17.7,
          20.2, 22.1, 23.3, 23.5, 23.4, 23.2, 22.3, 20.8, 20.1, 19.1, 18.2, 17.7, 16.9],
    '7': [17.6, 16.7, 16.1, 15.3, 14.9, 14.3, 14.1, 14.2, 15.0, 17.3, 20.2,
          23.0, 25.0, 26.3, 26.5, 26.4, 26.2, 25.2, 23.6, 22.8, 21.8, 20.8, 20.2, 19.4],
    '8': [17.1, 16.2, 15.7, 14.9, 14.5, 13.9, 13.7, 13.8, 14.6, 16.9, 19.7,
          22.4, 24.4, 25.6, 25.8, 25.7, 25.5, 24.5, 22.9, 22.2, 21.2, 20.2, 19.7, 18.9],
    '9': [13.4, 12.7, 12.2, 11.5, 11.2, 10.7, 10.5, 10.6, 11.3, 13.2, 15.6,
          17.9, 19.6, 20.8, 20.9, 20.8, 20.7, 19.8, 18.4, 17.8, 16.9, 16.1, 15.6, 14.9],
    '10': [9.4, 8.8, 8.5, 7.9, 7.6, 7.2, 7.1, 7.2, 7.7, 9.3, 11.2, 13.0,
           14.4, 15.3, 15.4, 15.3, 15.2, 14.5, 13.4, 12.9, 12.2, 11.6, 11.2, 10.6],
    '11': [4.0, 3.6, 3.3, 2.9, 2.6, 2.3, 2.2, 2.2, 2.7, 3.9, 5.5, 6.9, 8.0,
           8.7, 8.8, 8.7, 8.7, 8.1, 7.2, 6.8, 6.3, 5.7, 5.5, 5.0],
    '12': [1.4, 1.0, 0.8, 0.4, 0.2, -0.0, -0.1, -0.1, 0.3, 1.3, 2.6, 3.8,
           4.7, 5.2, 5.3, 5.2, 5.2, 4.7, 4.0, 3.7, 3.2, 2.8, 2.6, 2.2]
}


# Geneva hourly temperatures as piecewise constant function (in Kelvin)
Temperatures_hourly = {
    month: models.PiecewiseConstant(tuple(np.arange(25.)),
                                    tuple(273.15+np.array(temperatures)))
    for month, temperatures in local_tempatures.items()
}
# same temperatures on a finer temperature mesh
Temperatures = {
    month: Temperatures_hourly[month].refine(refine_factor=10)
    for month, temperatures in local_tempatures.items()
}
