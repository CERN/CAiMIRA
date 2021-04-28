import numpy as np
import pytest

import cara.models


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

    always = cara.models.PeriodicInterval(240, 240)  # TODO: This should be a thing on an interval.
    office_hours = cara.models.SpecificInterval(present_times=[(8,17)])
    c_model = cara.models.ConcentrationModel(
        cara.models.Room(defaults['volume']),
        cara.models.AirChange(always, defaults['air_change']),
        cara.models.InfectedPopulation(
            number=1,
            presence=office_hours,
            mask=cara.models.Mask(
                η_exhale=defaults['η_exhale'],
                η_leaks=defaults['η_leaks'],
                η_inhale=defaults['η_inhale'],
            ),
            activity=cara.models.Activity(
                0.51,
                0.75,
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
    )
    e_model = cara.models.ExposureModel(
        concentration_model=c_model,
        exposed=cara.models.Population(
            number=10,
            presence=office_hours,
            activity=c_model.infected.activity,
            mask=c_model.infected.mask,
        )
    )
    expected_new_cases = e_model.expected_new_cases()
    assert isinstance(expected_new_cases, np.ndarray)
    assert expected_new_cases.shape == (2, )
