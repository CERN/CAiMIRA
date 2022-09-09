import datetime
import functools
import json
from pathlib import Path
import typing

import dateutil.tz
import numpy as np
from scipy.spatial import cKDTree
from timezonefinder import TimezoneFinder


WX_DATA_LOCATION = Path(__file__).absolute().parent
WxStationIdType = str
MonthType = str
# HourlyTempType - 24 temperatures, one for each hour of the day (the average for the given month).
HourlyTempType = typing.List[float]
WxStationRecordType = typing.Tuple[WxStationIdType, str, float, float]


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
            if not np.any(np.isnan(data[station][month])):
                data[station][month] = tuple(
                    273.15 + np.array(data[station][month]))
    return data


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
    coords = np.array([(stn_record[3], stn_record[2])
                      for stn_record in station_data])
    return cKDTree(coords)


def mean_hourly_temperatures(wx_station: str, month: int) -> HourlyTempType:
    """
    Return the mean monthly temperature for the given weather station and month.

    Returns
    -------

    temperatures: List[24 floats]
        A list containing 24 temperature values, one for each hour, in kelvin.
        Index 0 of the result corresponds to hour 00:00 (UTC), and index 23 (the last) to 23:00 (UTC).

    """
    # Note that the current dataset encodes month number as a string.
    return wx_data()[wx_station][str(month)]


def timezone_at(*, latitude: float, longitude: float) -> datetime.tzinfo:
    """Find a timezone for the given location, or raise."""
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    tz = dateutil.tz.gettz(tz_name)
    if tz_name is None or tz is None:
        raise ValueError(
            f"Unable to determine the timezone of given location "
            f"(lat={latitude}, lng={longitude})"
        )
    return tz


def refine_hourly_data(source_times, hourly_data, npts):
    """
    Given times (in hours), where each data point is on the hour,
    interpolate the data to mid-point of the returned boundaries.

    For example:

    >>> time_bounds, data = refine_hourly_data(list(range(24)), list(range(24)), 24)
    >>> len(time_bounds), len(data)
    (25, 24)
    >>> time_bounds
    array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11., 12.,
           13., 14., 15., 16., 17., 18., 19., 20., 21., 22., 23., 24.])
    >>> data
    array([ 0.5,  1.5,  2.5,  3.5,  4.5,  5.5,  6.5,  7.5,  8.5,  9.5, 10.5,
           11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 20.5, 21.5,
           22.5, 11.5])

    The source times need not be monotonic, which allows for data to be
    time-offset shifted. For example:

    >>> time_bounds, data = refine_hourly_data(
    ...     list(range(6, 28)) + [4, 5], list(range(24)), 24)
    >>> data
    array([18.5, 19.5, 20.5, 21.5, 22.5, 11.5,  0.5,  1.5,  2.5,  3.5,  4.5,
            5.5,  6.5,  7.5,  8.5,  9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5,
           16.5, 17.5])

    """
    target_time_boundaries, step = np.linspace(
        0, 24, npts + 1, retstep=True, endpoint=True,
    )
    target_times = target_time_boundaries[:-1] + step / 2
    data = np.interp(target_times, np.array(source_times), hourly_data, period=24)
    return target_time_boundaries, data


def nearest_wx_station(*, longitude: float, latitude: float) -> WxStationRecordType:
    """
    Given a latitude & longitude, return the nearest station with valid weather data.

    """
    ktree = _wx_station_kdtree()
    station_data = list(wx_station_data().values())
    dd, ii = ktree.query((longitude, latitude), k=[1])
    return station_data[ii[0]]
