import re

import numpy as np
import numpy.testing as npt
import pytest

from cara import models


def test_multiple_wrong_weight_size():
    weights = (1., 2., 3.)
    e_base = models.Expiration((0.084, 0.009, 0.003, 0.002))
    with pytest.raises(
            ValueError,
            match=re.escape("expirations and weigths should contain the"
                            "same number of elements")
    ):
        e = models.MultipleExpiration([e_base, e_base], weights)


def test_multiple():
    weights = (1., 2.)
    e1 = models.Expiration((0.03, 0.02, 0.01, 0.005))
    e2 = models.Expiration((0.05, 0.04, 0.03, 0.01))
    e = models.MultipleExpiration([e1, e2], weights)
    mask = models.Mask.types['No mask']
    assert e.aerosols(mask) == e1.aerosols(mask)/3. + 2*e2.aerosols(mask)/3.


def test_multiple_BLO():
    weights = (1., 1.)
    e1 = models.ExpirationBLO((1., 0., 0.))
    e2 = models.ExpirationBLO((4., 5., 5.))
    e_expected = models.ExpirationBLO((2.5, 2.5, 2.5))
    e = models.MultipleExpiration([e1, e2], weights)
    mask = models.Mask.types['Type I']
    assert e_expected.aerosols(mask) == e.aerosols(mask)
