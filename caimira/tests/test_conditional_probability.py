import numpy as np
import pytest
from retry import retry

import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.models import models
from caimira.calculator.models.dataclass_utils import nested_replace
from caimira.calculator.report import virus_report_data
from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions, expiration_distributions


@pytest.fixture
def baseline_exposure_model(data_registry):
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=50, inside_temp=models.PiecewiseConstant((0., 24.), (298,)), humidity=0.5),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
            )
        ),
        infected=mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus_distributions(data_registry)['SARS_CoV_2_DELTA'],
            mask=models.Mask.types['No mask'],
            activity=activity_distributions(data_registry)['Seated'],
            expiration=expiration_distributions(data_registry)['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_mc,
        short_range=(),
        exposed=mc.Population(
            number=3,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            activity=activity_distributions(data_registry)['Seated'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


@retry(tries=3)
def test_conditional_prob_inf_given_vl_dist(data_registry, baseline_exposure_model):

    viral_loads = np.array([3., 5., 7., 9.,])
    mc_model: models.ExposureModel = baseline_exposure_model.build_model(2_000_000)

    expected_pi_means = []
    expected_lower_percentiles = []
    expected_upper_percentiles = []

    for vl in viral_loads:
        model_vl: models.ExposureModel = nested_replace(
            mc_model, {
                'concentration_model.infected.virus.viral_load_in_sputum' : 10**vl,
            }
        )
        pi = model_vl.infection_probability()/100

        expected_pi_means.append(np.mean(pi))
        expected_lower_percentiles.append(np.quantile(pi, 0.05))
        expected_upper_percentiles.append(np.quantile(pi, 0.95))

    infection_probability = mc_model.infection_probability() / 100
    specific_vl = np.log10(mc_model.concentration_model.infected.virus.viral_load_in_sputum)
    step = 8/100
    actual_pi_means, actual_lower_percentiles, actual_upper_percentiles = (
        virus_report_data.conditional_prob_inf_given_vl_dist(infection_probability, viral_loads, specific_vl, step)
    )

    assert np.allclose(actual_pi_means, expected_pi_means, atol=0.002)
    assert np.allclose(actual_lower_percentiles, expected_lower_percentiles, atol=0.002)
    assert np.allclose(actual_upper_percentiles, expected_upper_percentiles, atol=0.002)
