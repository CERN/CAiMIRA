import re

import numpy as np
import numpy.testing as npt
import pytest

from cara import models


def test_multiple_wrong_weight_size():
    weights = (1., 2., 3.)
    e_base = models.Expiration(2.5)
    with pytest.raises(
            ValueError,
            match=re.escape("expirations and weigths should contain the"
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
            match=re.escape("diameters should all be scalars")
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


# expected values obtained from another code
@pytest.mark.parametrize(
    "expiration_type, expected_aerosols",
    [
        ['Breathing', 1.38924e-12],
        ['Talking', 1.07129e-10],
        ['Shouting', 5.30088e-10],
    ],
)
def test_expiration_aerosols(expiration_type, expected_aerosols):
    mask = models.Mask.types['No mask']
    e = models._ExpirationBase.types[expiration_type]
    npt.assert_allclose(e.aerosols(mask), expected_aerosols, rtol=1e-4)
