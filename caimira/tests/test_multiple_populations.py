import re

import numpy as np
import numpy.testing as npt
import pytest

from caimira.calculator.models import models

@pytest.fixture
def dummy_multiple_populations() -> models.MultiplePopulations:
    interesting_times1 = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    group1 = models.Population(
        number=1,
        presence=interesting_times1,
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )

    interesting_times2 = models.SpecificInterval(([0.4, 1.], [1.1, 2]), )
    group2 = models.Population(
        number=10,
        presence=interesting_times2,
        mask=models.Mask.types['Cloth'],
        activity=models.Activity.types['Heavy exercise'],
        host_immunity=0.,
    )

    interesting_times3 = models.SpecificInterval(([5., 6.],), )
    group3 = models.Population(
        number=5,
        presence=interesting_times3,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Light activity'],
        host_immunity=0.5,
    )
    return models.MultiplePopulations([group1, group2, group3])


def test_multiple_populations(dummy_multiple_populations):
    assert isinstance(dummy_multiple_populations, models.MultiplePopulations)
    assert isinstance(dummy_multiple_populations.groups, list)
    assert np.all([isinstance(group, models.SimplePopulation) for group in dummy_multiple_populations.groups])


@pytest.mark.parametrize(
    "time, expected_people_present", [
        [0.5, 10],  # Out of range goes to the first state.
        [1., 11],
        [1.1, 0],
        [2., 11],
        [2, 11],
        [2.5, 1],
        [5., 0],
        [6., 5],
        [4., 0],
        [7., 0],
        [0.1, 0],
    ]
)
def test_people_present(time, expected_people_present, dummy_multiple_populations):
    result = dummy_multiple_populations.people_present(time)
    npt.assert_array_equal(result, expected_people_present)

def test_transition_times(dummy_multiple_populations):
    expected_transition_times = sorted(set((0.0, 0.4, 0.5, 1., 1.1, 2, 3., 5, 6)))
    result = dummy_multiple_populations.transition_times()
    npt.assert_array_equal(result, expected_transition_times)
