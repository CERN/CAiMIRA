import numpy.testing as npt
import pytest

import cara.models as models


def test_no_mask_aerosols(baseline_model):
    exp = models.Expiration.types['Unmodulated Vocalization']
    npt.assert_allclose(
        exp.aerosols(models.Mask.types['No mask']),
        6.077541e-12,
        rtol=1e-5,
    )


def test_no_mask_emission_rate(baseline_model):
    rate = 167.74011998223307
    npt.assert_allclose(
        [baseline_model.infected.emission_rate(t) for t in [0, 1, 4, 4.5, 5, 8, 9]],
        [rate, rate, rate, 0, rate, rate, 0],
        rtol=1e-5
    )


@pytest.fixture
def baseline_model():
    model = models.Model(
        room=models.Room(volume=75, window_height=1.6, opening_length=0.6),
        ventilation=models.PeriodicWindow(period=120, duration=120, inside_temp=293, outside_temp=283, cd_b=0.6),
        infected=models.InfectedPerson(
            virus=models.Virus.types['SARS_CoV_2'],
            present_times=((0, 4), (5, 8)),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light exercise'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
        infected_occupants=1,
        exposed_occupants=10,
        exposed_activity=models.Activity.types['Light exercise'],
    )
    return model


def test_r0(baseline_model):
    saturated = 2.909312e-01
    ts = [0, 4, 5, 7, 10]
    concentrations = [baseline_model.concentration(t) for t in ts]
    npt.assert_allclose(
        concentrations,
        [0.000000e+00, 2.909211e-01, 1.273836e-04, 2.909210e-01, 5.577662e-08],
        rtol=1e-5
    )
