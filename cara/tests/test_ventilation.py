import dataclasses

import pytest

from cara import models


@pytest.fixture
def baseline_window():
    return models.WindowOpening(
            active=models.SpecificInterval(((0, 4), (5, 9))),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            cd_b=0.6, window_height=1.6, opening_length=0.6,
        )


def test_number_of_windows(baseline_window):
    room = models.Room(75)
    two_windows = dataclasses.replace(baseline_window, number_of_windows=2)

    one_window_exchange = baseline_window.air_exchange(room, 1)
    two_window_exchange = two_windows.air_exchange(room, 1)
    assert one_window_exchange != 0
    assert one_window_exchange * 2 == two_window_exchange
