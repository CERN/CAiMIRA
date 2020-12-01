from cara import models

import pytest


@pytest.fixture
def baseline_model():
    model = models.ConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.WindowOpening(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0,24),(293,)),
            outside_temp=models.PiecewiseConstant((0,24),(283,)),
            discharge_coefficient=0.6, window_height=1.6, opening_length=0.6,
        ),
        infected=models.InfectedPopulation(
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
    )
    return model


@pytest.fixture
def baseline_exposure_model(baseline_model):
    return models.ExposureModel(
        baseline_model,
        exposed=models.Population(
            number=10,
            presence=baseline_model.infected.presence,
            activity=baseline_model.infected.activity,
            mask=baseline_model.infected.mask,
        )
    )
