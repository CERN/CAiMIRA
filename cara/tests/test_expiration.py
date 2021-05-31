import re

import numpy as np
import numpy.testing as npt
import pytest

from cara import models


def test_multiple_wrong_weight_size():
    weights = (1., 2., 3.)
    e_base = models.Expiration((1., 0., 0.))
    with pytest.raises(
            ValueError,
            match=re.escape("expirations and weigths should contain the"
                            "same number of elements")
    ):
        e = models.MultipleExpiration([e_base, e_base], weights)


def test_multiple():
    weights = (1., 1.)
    e1 = models.Expiration((1., 0., 0.))
    e2 = models.Expiration((4., 5., 5.))
    e_expected = models.Expiration((2.5, 2.5, 2.5))
    e = models.MultipleExpiration([e1, e2], weights)
    mask = models.Mask.types['Type I']
    npt.assert_almost_equal(e_expected.aerosols(mask), e.aerosols(mask))


# expected values obtained from another code
@pytest.mark.parametrize(
    "BLO_weights, expected_aerosols",
    [
        [(1.,0.,0.), 1.38924e-12],
        [(1.,1.,1.), 1.07129e-10],
        [(1.,5.,5.), 5.30088e-10],
    ],
)
def test_expiration_aerosols(BLO_weights, expected_aerosols):
    mask = models.Mask.types['No mask']
    e = models.Expiration(BLO_weights)
    npt.assert_allclose(e.aerosols(mask), expected_aerosols, rtol=1e-4)
