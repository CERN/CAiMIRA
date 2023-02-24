import numpy.testing as npt
import pytest

from caimira import models


@pytest.fixture
def simple_co2_conc_model():
    return models.CO2ConcentrationModel(
        room=models.Room(200, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.AirChange(models.PeriodicInterval(period=120, duration=120), 0.25-(1e-6)),
        CO2_emitters=models.Population(
            number=5,
            presence=models.SpecificInterval((([0., 4.], ))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ),
    )


@pytest.mark.parametrize(
    "time, expected_co2_concentration", [
        [0., 440.44],
        [1., 914.2487227],
        [2., 1283.251327],
        [3., 1570.630844],
        [4., 1794.442237],
    ]
)
def test_co2_concentration(
    simple_co2_conc_model: models.CO2ConcentrationModel,
    time: float,
    expected_co2_concentration: float,
):
    npt.assert_almost_equal(simple_co2_conc_model.concentration(time), expected_co2_concentration)


def test_integrated_concentration(simple_co2_conc_model):
    c1 = simple_co2_conc_model.integrated_concentration(0, 2)
    c2 = simple_co2_conc_model.integrated_concentration(0, 1)
    c3 = simple_co2_conc_model.integrated_concentration(1, 2)
    assert c1 != 0
    npt.assert_almost_equal(c1, c2 + c3)
