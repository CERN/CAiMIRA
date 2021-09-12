import numpy as np
import pytest

import cara.models


@pytest.mark.parametrize(
    "override_params", [
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
        {'exhalation_rate': np.array([0.75, 0.81])},
    ]
)
def test_infected_population_vectorisation(override_params):
    defaults = {
        'viral_load_in_sputum': 1e9,
        'exhalation_rate': 0.75,
    }
    defaults.update(override_params)

    office_hours = cara.models.SpecificInterval(present_times=[(8,17)])
    infected = cara.models.InfectedPopulation(
            number=1,
            presence=office_hours,
            mask=cara.models.Mask(
                factor_exhale=0.95,
                η_inhale=0.3,
            ),
            activity=cara.models.Activity(
                0.51,
                defaults['exhalation_rate'],
            ),
            virus=cara.models.Virus(
                viral_load_in_sputum=defaults['viral_load_in_sputum'],
                infectious_dose=50.,
            ),
            expiration=cara.models._ExpirationBase.types['Breathing'],
    )
    emission_rate = infected.emission_rate(10)
    assert isinstance(emission_rate, np.ndarray)
    assert emission_rate.shape == (2, )
