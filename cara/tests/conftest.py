from cara import models

import pytest


@pytest.fixture
def baseline_model():
    model = models.ConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0,24),)),
            air_exch=30.,
        ),
        infected=models.InfectedPopulation(
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            expiration=models.Expiration.types['Superspreading event'],
        ),
    )
    return model


@pytest.fixture
def baseline_exposure_model(baseline_model):
    return models.ExposureModel(
        baseline_model,
        exposed=models.Population(
            number=1000,
            presence=baseline_model.infected.presence,
            activity=baseline_model.infected.activity,
            mask=baseline_model.infected.mask,
        ),
        fraction_deposited = 1.,
    )
