import functools
import json
from pathlib import Path
import typing

import numpy as np
from scipy.spatial import cKDTree

from cara import models


WX_DATA_LOCATION = Path(__file__).absolute().parent


WxStationIdType = str
MonthType = str
# HourlyTempType - 24 temperatures, one for each hour of the day (the average for the given month).
HourlyTempType = typing.List[float]


@functools.lru_cache()
def wx_data() -> typing.Dict[WxStationIdType, typing.Dict[MonthType, HourlyTempType]]:
    """
    Load the weather data (temperature in kelvin).

    The data is structured by station location, and for each station location, by month.

    """
    with (WX_DATA_LOCATION / 'global_weather_set.json').open("r") as json_file:
        data = json.load(json_file)

    for station in list(data.keys()):
        for month in list(data[station].keys()):
            data[station][month] = tuple(273.15 + np.array(data[station][month]))
    return data


WxStationRecordType = typing.Tuple[WxStationIdType, str, float, float]


@functools.lru_cache()
def wx_station_data() -> typing.Dict[WxStationIdType, WxStationRecordType]:
    """
    Return a dictionary of ``station-id: station records``, where station records
    are of the form ``(station-id, station-name, station-latitude, station-longitude)``.

    The stations returned are guaranteed to have valid weather data.

    """
    weather_data = wx_data()
    station_data = {}
    fixed_delimits = [0, 12, 13, 44, 51, 60, 69, 90, 91]
    station_file = WX_DATA_LOCATION / 'hadisd_station_fullinfo_v311_202001p.txt'

    for line in station_file.open('rt'):
        start_end_positions = zip(fixed_delimits[:-1], fixed_delimits[1:])
        split_vals = [line[start:end] for start, end in start_end_positions]
        station_location = (
            split_vals[0], split_vals[2], float(split_vals[3]), float(split_vals[4]),
        )
        # We only consider stations with weather data, don't include the rest.
        if split_vals[0] in weather_data:
            station_data[split_vals[0]] = station_location
    return station_data


@functools.lru_cache()
def _wx_station_kdtree() -> cKDTree:
    """Build a kd-tree of wx station longitude & latitudes (note the coordinate order)"""
    station_data = wx_station_data().values()
    coords = np.array([(stn_record[3], stn_record[2]) for stn_record in station_data])
    return cKDTree(coords)


def mean_hourly_temperatures(wx_station: str, month: int) -> HourlyTempType:
    """
    Return the mean monthly temperature for the given weather station and month.

    Returns
    -------

    temperatures: List[24 floats]
        A list containing 24 temperature values, one for each hour, in kelvin.
        Index 0 of the result corresponds to hour 00:00-01:00, and index 23 (the last) to 23:00-00:00.

    """
    # Note that the current dataset encodes month number as a string.
    return wx_data()[wx_station][str(month)]


def hourly_to_piecewise(hourly_data: HourlyTempType) -> models.PiecewiseConstant:
    """
    Transform a list of 24 floats into a :class:`cara.models.PiecewiseConstant`.

    """
    pc = models.PiecewiseConstant(
        # NOTE:  It is important that the time type is float, not np.float, in
        # order to allow hashability (for caching).
        tuple(float(time) for time in range(25)),
        tuple(hourly_data),
    )
    return pc


def nearest_wx_station(*, longitude: float, latitude: float) -> WxStationRecordType:
    """
    Given a latitude & longitude, return the nearest station with valid weather data.

    """
    ktree = _wx_station_kdtree()
    station_data = list(wx_station_data().values())
    dd, ii = ktree.query((longitude, latitude), k=[1])
    return station_data[ii[0]]
