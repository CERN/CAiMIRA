import numpy as np
import numpy.testing as npt
import pytest

from cara import models

@pytest.mark.parametrize(
    "inside_temp, humidity, expected_halflife, expected_decay_constant",
    [
        [293.15, 0.5, 0.5947447349860315, 1.1654532436949188],
        [272.15, 0.7, 1.6070844193207476, 0.4313072619127947],
        [300.15, 1., 0.17367078830147223, 3.9911558376571805],
        [300.15, 0., 6.43, 0.10779893943389507],
        [np.array([272.15, 300.15]), np.array([0.7, 0.]), 
            np.array([1.60708442, 6.43]), np.array([0.43130726, 0.10779894])],
        [np.array([293.15, 300.15]), np.array([0.5, 1.]), 
            np.array([0.59474473, 0.17367079]), np.array([1.16545324, 3.99115584])]
    ],
)
def test_decay_constant(inside_temp, humidity, expected_halflife, expected_decay_constant):
    npt.assert_almost_equal(models.Virus.types['SARS_CoV_2'].halflife(humidity, inside_temp), 
                    expected_halflife)
    npt.assert_almost_equal(models.Virus.types['SARS_CoV_2'].decay_constant(humidity, inside_temp),
                    expected_decay_constant)