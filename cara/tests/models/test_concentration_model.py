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
    ]
)
def test_concentration_model_vectorisation(override_params):
    defaults = {
        'volume': 75,
        'air_change': 100,
        'virus_halflife': 1.1,
        'viral_load_in_sputum': 1e9,
        'coefficient_of_infectivity': 0.02,
        'η_exhale': 0.95,
        'η_leaks': 0.15,
    }
    defaults.update(override_params)

    always = cara.models.PeriodicInterval(240, 240)  # TODO: This should be a thing on an interval.
    c_model = cara.models.ConcentrationModel(
        cara.models.Room(defaults['volume']),
        cara.models.AirChange(always, defaults['air_change']),
        cara.models.InfectedPopulation(
            number=1,
            presence=always,
            mask=cara.models.Mask(
                η_exhale=defaults['η_exhale'],
                η_leaks=defaults['η_leaks'],
                η_inhale=0.3,
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
    concentrations = c_model.concentration(10)
    assert isinstance(concentrations, np.ndarray)
    assert concentrations.shape == (2, )
