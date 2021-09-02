import datetime

import dateutil.tz
import numpy as np
import numpy.testing
import pytest

import cara.data.weather as wx


def test_nearest_wx_station():
    melbourne_lat, melbourne_lon = -37.81739, 144.96751
    station_rec = wx.nearest_wx_station(longitude=melbourne_lon, latitude=melbourne_lat)

    station_name = station_rec[1].strip()
    # Note: For Melbourne, the nearest station is 'MELBOURNE REGIONAL OFFICE',
    # but the nearest location with suitable wx data is 'MELBOURNE ESSENDON'
    assert station_name == 'MELBOURNE ESSENDON'


def test_refine():
    source_times = [0, 3, 6, 9, 12, 15, 18, 21]
    data = [0, 30, 60, 90, 120, 90, 60, 30]

    time_bounds, data = wx.refine_hourly_data(source_times, data, 4)

    # Notice that the expected data falls in the mid-point of the
    # expected time bounds.
    np.testing.assert_array_equal(time_bounds, [0., 6., 12., 18., 24.])
    np.testing.assert_array_equal(data, [30., 90., 90., 30.])


def test_refine_offset():
    source_times = [14, 20, 26, 32]
    data = [200., 182, 168, 192]

    time_bounds, data = wx.refine_hourly_data(source_times, data, 6)

    # Notice that the expected data falls in the mid-point of the
    # expected time bounds.
    np.testing.assert_array_equal(time_bounds, [0., 4., 8., 12., 16., 20., 24.])
    np.testing.assert_array_almost_equal(data, [168., 184., 194.666667, 200., 188., 177.333333])


def test_refine_non_monotonic():
    source_times = [14, 20, 2, 8]
    data = [200., 182, 168, 192]

    time_bounds, data = wx.refine_hourly_data(source_times, data, 6)

    # Notice that the expected data falls in the mid-point of the
    # expected time bounds.
    np.testing.assert_array_equal(time_bounds, [0., 4., 8., 12., 16., 20., 24.])
    np.testing.assert_array_almost_equal(data, [168., 184., 194.666667, 200., 188., 177.333333])



def test_timezone_at__out_of_range():
    with pytest.raises(ValueError, match='out of bounds'):
        wx.timezone_at(latitude=88, longitude=181)


@pytest.mark.parametrize(
    ["latitude", "longitude", "expected_tz_name"],
    [
        [6.14275, 46.20833, 'Europe/Zurich'],  # Geneva
        [144.96751, -37.81739, "Australia/Melbourne"],  # Melbourne
        [-176.433333, -44.033333, 'Pacific/Chatham'],  # Chatham Islands
    ]
)
def test_timezone_at__expected(latitude, longitude, expected_tz_name):
    assert wx.timezone_at(latitude=longitude, longitude=latitude) == dateutil.tz.gettz(expected_tz_name)
    assert wx.timezone_at(latitude=0, longitude=-175) == dateutil.tz.gettz('Etc/GMT+12')
    assert wx.timezone_at(latitude=89.8, longitude=-170) == dateutil.tz.gettz('Etc/GMT+11')
