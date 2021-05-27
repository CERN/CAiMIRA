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
    assert e.aerosols(models.Mask.types['No mask']) == (
              e1.aerosols(models.Mask.types['No mask'])/3. +
            2*e2.aerosols(models.Mask.types['No mask'])/3.
    )
