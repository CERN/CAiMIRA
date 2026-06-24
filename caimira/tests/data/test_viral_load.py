import typing

import numpy as np
import numpy.testing as npt
import pytest

from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo as mc_models
from caimira.calculator.validators.virus.virus_validator import build_expiration
from caimira.calculator.models.monte_carlo.data import short_range_expiration_distributions,\
        expiration_distributions, short_range_distances, activity_distributions

SAMPLE_SIZE = 250_000

from caimira.calculator.store.data_registry import DataRegistry
from caimira.calculator.models.monte_carlo.data import virus_distributions, evaluate_vl

#viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2'], 'viral_load_in_sputum', data_registry)

data_registry = DataRegistry()

def test_short_range_infected(data_registry):
    virus_distributions1 = virus_distributions(data_registry)['SARS_CoV_2'].build_model(SAMPLE_SIZE)
    virus_distributions2 = virus_distributions(data_registry)['SARS_CoV_2'].build_model(SAMPLE_SIZE)

    print(virus_distributions1.viral_load_in_sputum.mean()-virus_distributions2.viral_load_in_sputum.mean())

    npt.assert_allclose(
        virus_distributions1.viral_load_in_sputum.mean(),
        virus_distributions2.viral_load_in_sputum.mean(),
        rtol=0.03
        )

