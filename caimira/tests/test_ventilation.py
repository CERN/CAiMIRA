import dataclasses

import numpy as np
import numpy.testing as npt
import pytest

from caimira import models


@pytest.fixture
def baseline_slidingwindow(data_registry):
    return models.SlidingWindow(
            data_registry=data_registry,
            active=models.SpecificInterval(((0, 4), (5, 9))),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        )


@pytest.fixture
def baseline_hingedwindow():
    return models.HingedWindow(
            active=models.SpecificInterval(((0, 4), (5, 9))),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6, window_width=1.,
        )


def test_number_of_windows(baseline_slidingwindow):
    room = models.Room(volume=75, inside_temp=models.PiecewiseConstant((0, 24), (293,)))
    two_windows = dataclasses.replace(baseline_slidingwindow, number_of_windows=2)

    one_window_exchange = baseline_slidingwindow.air_exchange(room, 1)
    two_window_exchange = two_windows.air_exchange(room, 1)
    assert one_window_exchange != 0
    assert one_window_exchange * 2 == two_window_exchange


@pytest.mark.parametrize(
    "window_width, expected_discharge_coefficient",
    [
        [0.5, 0.447],
        [1., 0.379],
        [2., 0.328],
        [4., 0.308],
    ],
)
def test_hinged_window(baseline_hingedwindow, window_width,
                       expected_discharge_coefficient):
    hinged_window = dataclasses.replace(baseline_hingedwindow,
                                        window_width=window_width)

    npt.assert_allclose(hinged_window.discharge_coefficient,
                        expected_discharge_coefficient, rtol=1e-2)


@pytest.mark.parametrize(
    "override_params", [
        {'window_height': np.array([0.15, 0.20, 0.25])},
        {'window_width': np.array([0.15, 0.20, 0.25])},
        {'opening_length': np.array([0.15, 0.20, 0.25])},
        {'outside_temp': models.PiecewiseConstant(
            (0, 2, 3), (np.array([20, 30, 28]), np.array([25, 30, 27]))
        )},
    ]
)
def test_hinged_window_vectorisation(override_params):
    defaults = {
        'window_height': 0.15,
        'window_width': 0.15,
        'opening_length': 0.15,
        'outside_temp': models.PiecewiseConstant((0, 2, 3), (10, 15)),
    }
    defaults.update(override_params)
    room = models.Room(volume=75, inside_temp=models.PiecewiseConstant((0, 2, 3), (20, 25)))
    t = 0.5
    window = models.HingedWindow(models.PeriodicInterval(60, 30), **defaults)
    if {'window_height', 'opening_length', 'window_width'}.intersection(override_params):
        assert isinstance(window.discharge_coefficient, np.ndarray)
    else:
        assert isinstance(window.discharge_coefficient, float)

    assert isinstance(window.air_exchange(room, t), np.ndarray)


def test_sliding_window(baseline_slidingwindow):
    assert baseline_slidingwindow.discharge_coefficient == 0.6


def test_hvac_mechanical_vectorisation():
    room = models.Room(volume=50)
    interval = models.SpecificInterval(((0, 4), (5, 9)))
    t = 0.5
    q_air_mech = np.array([250., 500.])
    v = models.HVACMechanical(interval,q_air_mech)
    assert isinstance(v.air_exchange(room, t), np.ndarray)
    npt.assert_array_equal(v.air_exchange(room, t),
                        np.array([250/room.volume, 500/room.volume]))


def test_hepa_filter_vectorisation():
    room = models.Room(volume=50)
    interval = models.SpecificInterval(((0, 4), (5, 9)))
    t = 0.5
    q_air_mech = np.array([250., 500.])
    v = models.HEPAFilter(interval,q_air_mech)
    assert isinstance(v.air_exchange(room, t), np.ndarray)
    npt.assert_array_equal(v.air_exchange(room, t),
                        np.array([250/room.volume, 500/room.volume]))


def test_multiple(baseline_slidingwindow, baseline_hingedwindow):
    v = models.MultipleVentilation([baseline_hingedwindow, baseline_slidingwindow])
    room = models.Room(75)
    t = 1
    assert v.air_exchange(room, t) == (
            baseline_slidingwindow.air_exchange(room, t) +
            baseline_hingedwindow.air_exchange(room, t)
    )


def test_multiple_vectorisation():
    interval = models.SpecificInterval(((0, 4), (5, 9)))
    v1 = models.AirChange(interval, np.arange(10))
    v2 = models.AirChange(interval, np.arange(5))
    v3 = models.AirChange(interval, 10)

    room = models.Room(75)
    t_active = 2
    t_inactive = 4.5

    assert models.MultipleVentilation([v1, v2]).air_exchange(room, t_inactive) == 0
    with pytest.raises(ValueError, match='operands could not be broadcast together'):
        models.MultipleVentilation([v1, v2]).air_exchange(room, t_active)

    r = models.MultipleVentilation([v2, v3]).air_exchange(room, t_active)
    assert isinstance(r, np.ndarray)
    np.testing.assert_array_equal(r, [10, 11, 12, 13, 14])
