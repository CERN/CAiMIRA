import numpy as np
import numpy.testing as npt
import pytest

from cara import models

@pytest.mark.parametrize(
    "inside_temp, humidity, expected_halflife, expected_decay_constant",
    [
        [293.15, 0.5, 35.67710693238622, 0.01942834607844098],
        [272.15, 0.7, 96.40459058258793, 0.007189981061805762],
        [300.15, 1., 10.418034697539541, 0.0665333914393324],
        [300.15, 0., 1.1, 0.6301338005090411],
        [np.array([272.15, 300.15]), np.array([0.7, 0.]), 
            np.array([96.40459058258793, 1.1]), np.array([0.007189981061805762, 0.6301338005090411])],
        [np.array([293.15, 300.15]), np.array([0.5, 1.]), 
            np.array([35.67710693238622, 10.418034697539541]), np.array([0.01942834607844098, 0.0665333914393324])]
    ],
)
def test_decay_constant(inside_temp, humidity, expected_halflife, expected_decay_constant):
    npt.assert_equal(models.Virus.types['SARS_CoV_2'].halflife(humidity, inside_temp), 
                     expected_halflife)
    npt.assert_equal(models.Virus.types['SARS_CoV_2'].decay_constant(humidity, inside_temp), 
                     expected_decay_constant)