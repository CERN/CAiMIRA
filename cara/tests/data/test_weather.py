import cara.data.weather as wx


def test_nearest_wx_station():
    melbourne_lat, melbourne_lon = -37.81739, 144.96751
    station_rec = wx.nearest_wx_station(longitude=melbourne_lon, latitude=melbourne_lat)

    station_name = station_rec[1].strip()
    # Note: For Melbourne, the nearest station is 'MELBOURNE REGIONAL OFFICE',
    # but the nearest location with suitable wx data is 'MELBOURNE ESSENDON'
    assert station_name == 'MELBOURNE ESSENDON'
