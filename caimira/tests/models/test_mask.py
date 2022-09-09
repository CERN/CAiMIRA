import numpy as np
import numpy.testing as npt
import pytest

from caimira import models


@pytest.mark.parametrize(
    "η_inhale, expected_inhale_efficiency",
    [
        [0.5, 0.5],
        [np.array([0.3, 0.5]), np.array([0.3, 0.5])],
    ],
)
def test_mask_inhale(η_inhale, expected_inhale_efficiency):
    mask = models.Mask(η_inhale=η_inhale)
    npt.assert_equal(mask.inhale_efficiency(), 
                     expected_inhale_efficiency)


@pytest.mark.parametrize(
    "diameter, factor_exhale, expected_exhale_efficiency",
    [
        [0.3, 1., 0.],
        [0.7, 0.3, 0.56711*0.3],
        [1., 1., 0.7149],
        [4., 0.5, 0.8167*0.5],
        [5., 0., 0.],
    ],
)
def test_mask_exhale(diameter, factor_exhale, expected_exhale_efficiency):
    mask = models.Mask(η_inhale=0.3, factor_exhale=factor_exhale)
    npt.assert_almost_equal(mask.exhale_efficiency(diameter),
                            expected_exhale_efficiency)
