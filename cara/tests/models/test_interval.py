import numpy as np
import pytest

from cara import models


@pytest.mark.parametrize(
    "stop_time, expected_boundaries",
    [
        [1.05, ((0, 1),)],
        [1.8, ((0, 1), (1.1, 1.8))],
        [2., ((0, 1), (1.1, 1.999))],
        [3., ((0, 1), (1.1, 1.999), (2, 3))],
        [-1, ()],
        [4, ((0, 1), (1.1, 1.999), (2, 3))],
    ],
)
def test_interval_truncation(stop_time, expected_boundaries):
    interesting_times = models.SpecificInterval(
        ([0, 1], [1.1, 1.999], [2, 3]), )
    assert interesting_times.generate_truncated_interval(
        stop_time).boundaries() == expected_boundaries
