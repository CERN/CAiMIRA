import numpy as np
import pytest

import cara.models


@pytest.mark.parametrize(
    "override_params", [
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
        {'coefficient_of_infectivity': np.array([0.02, 0.05])},
        {'η_exhale': np.array([0.92, 0.95])},
        {'η_leaks': np.array([0.15, 0.20])},
        {'exhalation_rate': np.array([0.75, 0.81])},
    ]
)
def test_infected_population_vectorisation(override_params):
    defaults = {
        'virus_halflife': 1.1,
        'viral_load_in_sputum': 1e9,
        'coefficient_of_infectivity': 0.02,
        'η_exhale': 0.95,
        'η_leaks': 0.15,
        'exhalation_rate': 0.75,
    }
    defaults.update(override_params)

    office_hours = cara.models.SpecificInterval(present_times=[(8,17)])
    infected = cara.models.InfectedPopulation(
            number=1,
            presence=office_hours,
            mask=cara.models.Mask(
                η_exhale=defaults['η_exhale'],
                η_leaks=defaults['η_leaks'],
                η_inhale=0.3,
            ),
            activity=cara.models.Activity(
                0.51,
                defaults['exhalation_rate'],
            ),
            virus=cara.models.Virus(
                halflife=defaults['virus_halflife'],
                viral_load_in_sputum=defaults['viral_load_in_sputum'],
                coefficient_of_infectivity=defaults['coefficient_of_infectivity'],
            ),
            expiration=cara.models.Expiration(
                ejection_factor=(0.084, 0.009, 0.003, 0.002),
        ),
    )
    emission_rate = infected.emission_rate(10)
    assert isinstance(emission_rate, np.ndarray)
    assert emission_rate.shape == (2, )
