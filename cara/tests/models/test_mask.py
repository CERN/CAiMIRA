
import dataclasses

import numpy as np
import numpy.testing as npt
import pytest

from cara import models

@pytest.mark.parametrize(
    "η_inhale, expected_inhale_efficiency",
    [
        [0.5, 0.5],
        [np.array([0.3, 0.5]), np.array([0.3, 0.5])],
    ],
)
def test_masks_inhale(η_inhale, expected_inhale_efficiency):
    mask = models.Mask(η_inhale=η_inhale,η_exhale=0.95,η_leaks=0.15)
    measuredmask = models.MeasuredMask(η_inhale=η_inhale)
    npt.assert_equal(mask.inhale_efficiency(), 
                     expected_inhale_efficiency)
    npt.assert_equal(measuredmask.inhale_efficiency(),
                     expected_inhale_efficiency)


@pytest.mark.parametrize(
    "η_exhale, η_leaks, expected_exhale_efficiency_small, expected_exhale_efficiency_large",
    [
        [0.95, 0.15, 0., 0.8075],
        [np.array([0.95, 1.]), 0.15, np.zeros(2), np.array([0.8075, 0.85])],
        [0.95, np.array([0.15, 0.]), np.zeros(2), np.array([0.8075, 0.95])],
        [np.array([0.95, 1.]), np.array([0.15, 0.]), np.zeros(2), np.array([0.8075, 1.])],
    ],
)
def test_mask_exhale(η_exhale, η_leaks, expected_exhale_efficiency_small,
                     expected_exhale_efficiency_large):
    mask = models.Mask(η_inhale=0.3,η_exhale=η_exhale,η_leaks=η_leaks)
    # we test one small and one large diameter (resp. 1 and 4 microns)
    npt.assert_equal(mask.exhale_efficiency(1.e-4), 
                     expected_exhale_efficiency_small)
    npt.assert_equal(mask.exhale_efficiency(4.e-4), 
                     expected_exhale_efficiency_large)


@pytest.mark.parametrize(
    "diameter, expected_exhale_efficiency",
    [
        [0.3e-4, 0.],
        [0.7e-4, 0.56711],
        [1.e-4, 0.7149],
        [4.e-4, 0.8167],
    ],
)
def test_measuredmask_exhale(diameter, expected_exhale_efficiency):
    mask = models.MeasuredMask(η_inhale=0.3)
    npt.assert_almost_equal(mask.exhale_efficiency(diameter),
                            expected_exhale_efficiency)

