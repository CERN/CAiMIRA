import numpy as np
import pytest

from cara import models
from cara import data


def test_piecewiseconstantfunction_wrongarguments():
    # number of values should be 1+number of transition times
    pytest.raises(ValueError, models.PiecewiseConstant, (0, 1), (0, 0))
    pytest.raises(ValueError, models.PiecewiseConstant, (0,), (0, 0))
    # two transition times cannot be equal
    pytest.raises(ValueError, models.PiecewiseConstant, (0, 2, 2), (0, 0))
    # unsorted transition times are not allowed
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
