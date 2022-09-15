import numpy as np
import pytest

import caimira.models


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

    office_hours = caimira.models.SpecificInterval(present_times=[(8,17)])
    infected = caimira.models.InfectedPopulation(
            number=1,
            presence=office_hours,
            mask=caimira.models.Mask(
                factor_exhale=0.95,
                η_inhale=0.3,
            ),
            activity=caimira.models.Activity(
                0.51,
                defaults['exhalation_rate'],
            ),
            virus=caimira.models.Virus(
                viral_load_in_sputum=defaults['viral_load_in_sputum'],
                infectious_dose=50.,
                viable_to_RNA_ratio = 0.5,
                transmissibility_factor=1.0,
            ),
            expiration=caimira.models._ExpirationBase.types['Breathing'],
            host_immunity=0.,
    )
    emission_rate = infected.emission_rate(10)
    assert isinstance(emission_rate, np.ndarray)
    assert emission_rate.shape == (2, )
