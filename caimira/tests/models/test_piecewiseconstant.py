import numpy as np
import pytest

from caimira.calculator.models import models
from caimira.calculator.models import data


def test_piecewiseconstantfunction_wrongarguments():
    # Number of values should be same as number of transition times (periodic)
    # or 1+number of transition times (non-periodic)
    pytest.raises(ValueError, models.PiecewiseConstant, (0, 1, 2), (0,)) # len(times) == 3, len(values) == 1
    pytest.raises(ValueError, models.PiecewiseConstant, (0,), (0, 0)) # len(times) == 1, len(values) == 2
    # Two transition times cannot be equal
    pytest.raises(ValueError, models.PiecewiseConstant, (0, 2, 2), (0, 0))
    # Unsorted transition times are not allowed
    pytest.raises(ValueError, models.PiecewiseConstant, (2, 0), (0, 0))

    # If vectors, must all be same length.
    with pytest.raises(ValueError, match="All values must have the same shape"):
        models.PiecewiseConstant(
            (0, 8, 16), (np.array([5, 7]), np.array([8, 9, 10])),
        )



@pytest.mark.parametrize(
    "time, expected_value",
    [
        [10, 5],
        [20.5, 8],
        [8, 2],
        [0, 2],
        [24, 8],
        [-1, 2],
        [25, 8],
    ],
)
def test_piecewiseconstant(time, expected_value):
    transition_times = (0, 8, 16, 24)
    values = (2, 5, 8)
    fun = models.PiecewiseConstant(transition_times, values)
    assert fun.value(time) == expected_value


def test_piecewiseconstant_periodic():
    # 24-hour periodic test
    # (0, 12, 18) -> values (1, 2, 3)
    # 0 < t <= 12 -> 1
    # 12 < t <= 18 -> 2
    # 18 < t <= 24 -> 3
    pc = models.PiecewiseConstant((0, 12, 18), (1, 2, 3))

    # Within first period
    assert pc.value(6) == 1
    assert pc.value(12) == 1
    assert pc.value(15) == 2
    assert pc.value(18) == 2
    assert pc.value(21) == 3
    assert pc.value(24) == 3

    # 0 handling (normalized to 24)
    assert pc.value(0) == 3

    # Wrap around to second period (24-48)
    assert pc.value(30) == 1
    assert pc.value(42) == 2
    assert pc.value(48) == 3

    # Negative time
    assert pc.value(-3) == 3
    assert pc.value(-18) == 1


def test_piecewiseconstant_interp():
    transition_times = (0, 8, 16, 24)
    values = (2, 5, 8)
    refined_fun = models.PiecewiseConstant(transition_times, values).refine(refine_factor=2)
    assert refined_fun.transition_times == (0, 4, 8, 12, 16, 20, 24)
    assert refined_fun.values == (2, 3.5, 5, 6.5, 8, 8)


def test_piecewiseconstant_interp_vectorised():
    transition_times = (0, 8, 16, 24)
    values = (np.array([2, 3]), np.array([5, 7]), np.array([8, 9]))
    refined_fun = models.PiecewiseConstant(transition_times, values).refine(refine_factor=2)
    assert refined_fun.transition_times == (0, 4, 8, 12, 16, 20, 24)
    np.testing.assert_almost_equal(
        refined_fun.values, ((2, 3), (3.5, 5), (5, 7), (6.5, 8), (8, 9), (8, 9)),
    )


def test_constantfunction():
    transition_times = (0, 24)
    values = (20,)
    fun = models.PiecewiseConstant(transition_times, values)
    for t in [0, 1, 8, 10, 16, 20.1, 24]:
        assert (fun.value(t) == 20)


@pytest.mark.parametrize(
    "time",
    [0, 1, 8, 10, 16, 20.1, 24],
)
def test_piecewiseconstant_vs_interval(time):
    transition_times = (0, 8, 16, 24)
    values = (0, 1, 0)
    fun = models.PiecewiseConstant(transition_times, values)
    interval = models.SpecificInterval(present_times=[(8,16)])
    assert interval.transition_times() == fun.interval().transition_times()
    assert fun.interval().triggered(time) == interval.triggered(time)


def test_piecewiseconstant_transition_times():
    outside_temp = data.GenevaTemperatures['Jan']
    assert set(outside_temp.transition_times) == outside_temp.interval().transition_times()
