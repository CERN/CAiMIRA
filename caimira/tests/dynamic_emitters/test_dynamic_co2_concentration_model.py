import re

import numpy as np
import numpy.testing as npt
import pytest
from dataclasses import dataclass

from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry


@pytest.fixture
def dummy_multiple_populations() -> models.MultiplePopulations:
    interesting_times1 = models.SpecificInterval(([0.5, 1.], [1.1, 2], [2., 3.]), )
    population1 = models.Population(
        number=1,
        presence=interesting_times1,
        mask=models.Mask.types['No mask'],
        activity=models.Activity.types['Seated'],
        host_immunity=0.,
    )

    interesting_times2 = models.SpecificInterval(([0.4, 1.], [1.1, 2]), )
    population2 = models.Population(
        number=10,
        presence=interesting_times2,
        mask=models.Mask.types['Cloth'],
        activity=models.Activity.types['Heavy exercise'],
        host_immunity=0.,
    )

    interesting_times3 = models.SpecificInterval(([5., 6.],), )
    population3 = models.Population(
        number=5,
        presence=interesting_times3,
        mask=models.Mask.types['Type I'],
        activity=models.Activity.types['Light activity'],
        host_immunity=0.5,
    )
    return models.MultiplePopulations([population1, population2, population3])

@pytest.fixture
def simple_co2_conc_model(data_registry, dummy_multiple_populations):
    return models.CO2ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(200, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.AirChange(models.PeriodicInterval(period=120, duration=120), 0.25),
        CO2_emitters=dummy_multiple_populations)

def test_dynamic_population(simple_co2_conc_model):
    assert isinstance(simple_co2_conc_model, models.CO2ConcentrationModel)
    assert isinstance(simple_co2_conc_model.population, models.MultiplePopulations)
    assert isinstance(simple_co2_conc_model.population.populations, list)
    assert len(simple_co2_conc_model.population.populations) == 3