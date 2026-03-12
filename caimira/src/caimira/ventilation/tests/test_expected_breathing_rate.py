import numpy as np
import pytest
import numpy.testing as npt

from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry

import caimira.ventilation.deterministic_emitters as de

data_registry = DataRegistry()


@pytest.mark.parametrize(
    "log_mean, log_std, expected",
    [
        [0, 0, 1],
        [1, 1, np.exp(1.5)],
        [-1, 1, np.exp(-0.5)],
        [-1, 2, np.exp(1.)],
    ]
)
def test_expected_breathing_rate(log_mean, log_std, expected):
    result = de.expected_breathing_rate(log_mean, log_std)
    npt.assert_almost_equal(result, expected)

@pytest.mark.parametrize(
    "activity_type, expected_breathing_rate",
    [
        ["Seated", np.exp(-0.6872121723362303 + 0.10498338229297108**2 / 2)],
        ["Standing", np.exp(-0.5742377578494785 + 0.09373162411398223**2 / 2)],
        ["Light activity", np.exp(0.21380242785625422 + 0.09435378091059601**2 / 2)],
        ["Moderate activity", np.exp(0.551771330362601 + 0.1894616357138137**2 / 2)],
        ["Heavy exercise", np.exp(1.1644665696723049 + 0.21744554768657565**2 / 2)],
    ]
)
def test_deterministic_population(activity_type, expected_breathing_rate):
    det_pop = de.DeterministicPopulation(
            number=1,
            presence=models.SpecificInterval(present_times=((10, 10.333),)),
            activity=de.deterministic_activity_distributions(data_registry)[activity_type],
        )
    assert isinstance(det_pop.activity, de.DeterministicActivity)
    assert isinstance(det_pop.activity.exhalation_rate, float)
    assert isinstance(det_pop.activity.inhalation_rate, float)
    npt.assert_almost_equal(det_pop.activity.inhalation_rate, expected_breathing_rate)
    npt.assert_almost_equal(det_pop.activity.exhalation_rate, expected_breathing_rate)