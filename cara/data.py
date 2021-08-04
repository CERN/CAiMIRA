import numpy as np
from cara import models
import json
import urllib.request
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
import os


#items to pass into this module
calc_location = (46.2044, 6.1432)

#items to return to model 
#w_station

weather_station = ""  #"067000-99999" this is the Cointrin station for Geneva
weather_station_name = ""
weather_debug = True



def location_to_weather_stn(location_loc):
    #expects a tuple (lat, long)
    #returns: weather station ID, weather station name, weather station lat, long
    search_coords = [location_loc[0], location_loc[1]]
    lat=[]
    long=[]
    station_array=[]
    fixed_delimits = [0,12,13, 44,51,60,69,90,91]
    station_file = Path(os.getcwd()+'/cara/hadisd_station_fullinfo_v311_202001p.txt')

    if not station_file.exists():
        if weather_debug:
            print("Local file not found, downloading database of weather stations")
        URL = 'https://www.metoffice.gov.uk/hadobs/hadisd/v311_2020f/files/hadisd_station_fullinfo_v311_202001p.txt'
        req = urllib.request.Request(URL)
        req.add_header('User-Agent', 'urllib/0.1')
        with urllib.request.urlopen(req) as f:
            content = f.read()
        with station_file.open('wt') as fh:
            fh.write(content.decode())

    for line in station_file.open('rt'):
        start_end_positions=zip(fixed_delimits[:-1], fixed_delimits[1:])
        split_vals=[line[start:end] for start, end in start_end_positions]
        station_location = [split_vals[0], split_vals[2], split_vals[3], split_vals[4]]
        station_array.append(station_location)
        lat.append(split_vals[3])
        long.append(split_vals[4])

    tree = cKDTree(np.c_[lat, long])
    dd, ii = tree.query(search_coords, k=[1])

    return (station_array[ii[0]][0], station_array[ii[0]][1], station_array[ii[0]][2], station_array[ii[0]][3])

def location_celcius_per_hour(location):
    #expects a tuple (lat, long)
    #returns a json format set of weather data
    w_station = location_to_weather_stn(location)
    print(os.getcwd())
    with open(Path(os.getcwd()+"/cara/global_weather_set.json"), "r") as json_file:
        weather_dict = json.load(json_file)
    Location_hourly_temperatures_celsius_per_hour = weather_dict[w_station[0]]
    if weather_debug:
            print("weather station name: ", w_station[1])
            print("weather station ref: ", w_station[0])
            print("weather station location: ", w_station[2], " ", w_station[3])
            print(Location_hourly_temperatures_celsius_per_hour)
    return Location_hourly_temperatures_celsius_per_hour


# Geneva hourly temperatures as piecewise constant function (in Kelvin)
Temperatures_hourly = {
    month: models.PiecewiseConstant(tuple(np.arange(25.)),
                             tuple(273.15+np.array(temperatures)))
    for month,temperatures in location_celcius_per_hour(calc_location).items()
}
# same temperatures on a finer temperature mesh
Temperatures = {
    month: Temperatures_hourly[month].refine(refine_factor=4)
    for month,temperatures in location_celcius_per_hour(calc_location).items()
}

