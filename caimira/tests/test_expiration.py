from dataclasses import dataclass
import typing
import re

import numpy as np
import numpy.testing as npt
from scipy import special as sp
import pytest
from retry import retry

from caimira.calculator.models import models
from caimira.calculator.models.monte_carlo.data import expiration_distribution

sqrt2 = np.sqrt(2.)

@dataclass(frozen=True)
class LognormalmonomialFunction:
    """
    Represents a lognormal distribution function times a monomial
    (A * d**n) * (1 / d) * (1 / (np.sqrt(2 * np.pi) * sigma)) *
            np.exp(-1 * (np.log(d)-logd0)) ** 2 / (2 * sigma ** 2))) 
    """
    # factor in front
    A: float
    
    # exponent (does not have to be an integer)
    n: typing.Union[int,float]

    # offset of the normal distribution (represents the log of a 
    # diameter in microns)
    logd0: float
    
    # "sigma" for the underlying normal distribution
    sigma: float

    def value(self, d):
        return ((self.A * d**self.n) * (1 / d) * (1. / (np.sqrt(2 * np.pi) * self.sigma)) *
                np.exp(-(np.log(d) - self.logd0) ** 2 / (2 * self.sigma ** 2))
                )

    def integrate(self, dmin, dmax):
        ymin = (np.log(dmin)-self.logd0)/(sqrt2*self.sigma) - self.n*self.sigma/sqrt2
        ymax = (np.log(dmax)-self.logd0)/(sqrt2*self.sigma) - self.n*self.sigma/sqrt2
        return ( self.A * np.exp(self.n*self.logd0+(self.n*self.sigma)**2/2) * 
                (sp.erf(ymax)-sp.erf(ymin)) / 2. )

@pytest.fixture
def get_expected_aerosols(BLO_weights):
    Bmode_volume = LognormalmonomialFunction(0.06*np.pi/6.*1e-12,3,0.989541, 0.262364)
    Lmode_volume = LognormalmonomialFunction(0.2*np.pi/6.*1e-12,3,1.38629, 0.506818)
    Omode_volume = LognormalmonomialFunction(0.0010008*np.pi/6.*1e-12,3,4.97673, 0.585005)

    dmin = 0.1
    dmax = 20

    return BLO_weights[0]*Bmode_volume.integrate(dmin,dmax) \
            + BLO_weights[1]*Lmode_volume.integrate(dmin,dmax) \
            + BLO_weights[2]*Omode_volume.integrate(dmin,dmax)



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
    "BLO_weights",
    [
        [(1.,0.,0.)],
        [(1.,1.,1.)],
        [(1.,5.,5.)],
    ],
)
def get_expected_aerosols(data_registry, BLO_weights, expected_aerosols):
    expected_aerosols = expected_aerosols(BLO_weights)
    mask = models.Mask.types['No mask']
    e = expiration_distribution(data_registry, BLO_weights)
    npt.assert_allclose(e.build_model(100000).aerosols(mask).mean(),
                        expected_aerosols, rtol=1e-2)
