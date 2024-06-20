import re

import numpy as np
import numpy.testing as npt
import pytest
from retry import retry

from caimira.calculator.models import models
from caimira.calculator.models.monte_carlo.data import expiration_distribution


def test_multiple_wrong_weight_size():
    weights = (1., 2., 3.)
    e_base = models.Expiration(2.5)
    with pytest.raises(
            ValueError,
            match=re.escape("expirations and weigths must contain the"
                            "same number of elements")
    ):
        e = models.MultipleExpiration([e_base, e_base], weights)


def test_multiple_wrong_diameters():
    weights = (1., 2., 3.)
    e1 = models.Expiration(np.array([1., 1.]))
    e2 = models.Expiration(1.)
    e3 = models.Expiration(2.)
    with pytest.raises(
            ValueError,
            match=re.escape("diameters must all be scalars")
    ):
        e = models.MultipleExpiration([e1, e2, e3], weights)


def test_multiple():
    weights = (1., 1.)
    mask = models.Mask.types['Type I']
    e1 = models.Expiration.types['Breathing']
    e2 = models.Expiration.types['Singing']
    aerosol_expected = (e1.aerosols(mask) + e2.aerosols(mask))/2.
    e = models.MultipleExpiration([e1, e2], weights)
    npt.assert_almost_equal(aerosol_expected, e.aerosols(mask))


@retry(tries=10)
# Expected values obtained from analytical formulas
@pytest.mark.parametrize(
    "BLO_weights, expected_aerosols",
    [
        [(1.,0.,0.), 8.33551e-13],
        [(1.,1.,1.), 2.20071e-11],
        [(1.,5.,5.), 1.06701e-10],
    ],
)
def test_expiration_aerosols(data_registry, BLO_weights, expected_aerosols):
    mask = models.Mask.types['No mask']
    e = expiration_distribution(data_registry, BLO_weights)
    npt.assert_allclose(e.build_model(100000).aerosols(mask).mean(),
                        expected_aerosols, rtol=1e-2)
