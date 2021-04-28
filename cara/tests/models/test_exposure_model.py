import numpy as np
import pytest

import cara.models

def exposure_model_from_params(params):
    always = cara.models.PeriodicInterval(240, 240)  # TODO: This should be a thing on an interval.
    office_hours = cara.models.SpecificInterval(present_times=[(8,17)])
    c_model = cara.models.ConcentrationModel(
        cara.models.Room(params['volume']),
        cara.models.AirChange(always, params['air_change']),
        cara.models.InfectedPopulation(
            number=1,
            presence=office_hours,
            mask=cara.models.Mask(
                η_exhale=params['η_exhale'],
                η_leaks=params['η_leaks'],
                η_inhale=params['η_inhale'],
            ),
            activity=cara.models.Activity(
                0.51,
                0.75,
            ),
            virus=cara.models.Virus(
                halflife=params['virus_halflife'],
                viral_load_in_sputum=params['viral_load_in_sputum'],
                coefficient_of_infectivity=params['coefficient_of_infectivity'],
            ),
            expiration=cara.models.Expiration(
                ejection_factor=(0.084, 0.009, 0.003, 0.002),
            ),
        )
    )
    return cara.models.ExposureModel(
        concentration_model=c_model,
        exposed=cara.models.Population(
            number=10,
            presence=office_hours,
            activity=c_model.infected.activity,
            mask=c_model.infected.mask,
        )
    )

@pytest.mark.parametrize(
    "override_params", [
        {'volume': np.array([100, 120])},
        {'air_change': np.array([100, 120])},
        {'virus_halflife': np.array([1.1, 1.5])},
        {'viral_load_in_sputum': np.array([5e8, 1e9])},
        {'coefficient_of_infectivity': np.array([0.02, 0.05])},
        {'η_exhale': np.array([0.92, 0.95])},
        {'η_leaks': np.array([0.15, 0.20])},
        {'η_inhale': np.array([0.3, 0.35])},
    ]
)
def test_exposure_model_vectorisation(override_params):
    defaults = {
        'volume': 75,
        'air_change': 100,
        'virus_halflife': 1.1,
        'viral_load_in_sputum': 1e9,
        'coefficient_of_infectivity': 0.02,
        'η_exhale': 0.95,
        'η_leaks': 0.15,
        'η_inhale': 0.3,
    }
    defaults.update(override_params)

    e_model = exposure_model_from_params(defaults)
    expected_new_cases = e_model.expected_new_cases()
    assert isinstance(expected_new_cases, np.ndarray)
    assert expected_new_cases.shape == (2, )

