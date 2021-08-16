import numpy as np
import numpy.testing as npt
import pytest

import cara.monte_carlo as mc
from cara import models,data
from cara.monte_carlo.data import activity_distributions, virus_distributions

# TODO: seed better the random number generators
np.random.seed(2000)
SAMPLE_SIZE = 50000
TOLERANCE = 0.05

# references values for infection_probability and expected new cases
# in the following tests, were obtained from the feature/mc branch

@pytest.fixture
def shared_office_mc():
    """
    Corresponds to the 1st line of Table 5 in CERN-OPEN-2021-04, but
    speaking 30% of the time (instead of 1/3)
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=50, humidity=0.3),
        ventilation=models.MultipleVentilation(
            (
                models.SlidingWindow(
                    active=models.PeriodicInterval(period=120, duration=10),
                    inside_temp=models.PiecewiseConstant((0, 24), (293,)),
                    outside_temp=models.PiecewiseConstant((0, 24), (283,)),
                    window_height=1.6, opening_length=0.6,
                ),
                models.AirChange(
                    active=models.SpecificInterval(((0,24),)),
                    air_exch=0.25,
                ),
            ),
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2_B117'],
            presence=mc.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
            mask=models.Mask(η_inhale=0.3),
            activity=activity_distributions['Seated'],
            expiration=models.MultipleExpiration(
                    expirations=(models.Expiration.types['Talking'],
                                 models.Expiration.types['Breathing']),
                    weights=(0.3, 0.7)),
        ),
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        exposed=mc.Population(
            number=3,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Seated'],
            mask=concentration_mc.infected.mask,
        ),
    )


@pytest.fixture
def classroom_mc():
    """
    Corresponds to the 2nd line of Table 5 in CERN-OPEN-2021-04
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=160, humidity=0.3),
        ventilation=models.MultipleVentilation(
            (
                models.SlidingWindow(
                    active=models.PeriodicInterval(period=120, duration=10),
                    inside_temp=models.PiecewiseConstant((0, 24), (293,)),
                    outside_temp=models.PiecewiseConstant((0, 24), (283,)),
                    window_height=1.6, opening_length=0.6,
                ),
                models.AirChange(
                    active=models.SpecificInterval(((0,24),)),
                    air_exch=0.25,
                ),
            ),
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2_B117'],
            presence=mc.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            mask=models.Mask.types['No mask'],
            activity=activity_distributions['Light activity'],
            expiration=models.Expiration.types['Talking'],
        ),
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        exposed=mc.Population(
            number=19,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Seated'],
            mask=concentration_mc.infected.mask,
        ),
    )


@pytest.fixture
def ski_cabin_mc():
    """
    Corresponds to the 3rd line of Table 5 in CERN-OPEN-2021-04
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=10, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0,24),)),
            air_exch=0,
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2_B117'],
            presence=mc.SpecificInterval(((0, 1/3),)),
            mask=models.Mask(η_inhale=0.3),
            activity=activity_distributions['Moderate activity'],
            expiration=models.Expiration.types['Talking'],
        ),
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        exposed=mc.Population(
            number=3,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Moderate activity'],
            mask=concentration_mc.infected.mask,
        ),
    )


@pytest.fixture
def gym_mc():
    """
    Corresponds to the 4th line of Table 5 in CERN-OPEN-2021-04,
    but there the expected number of cases is wrongly reported as 0.56
    while it should be 0.63.
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=300, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0,24),)),
            air_exch=6,
        ),
        infected=mc.InfectedPopulation(
            number=2,
            virus=virus_distributions['SARS_CoV_2_B117'],
            presence=mc.SpecificInterval(((0, 1),)),
            mask=models.Mask.types["No mask"],
            activity=activity_distributions['Heavy exercise'],
            expiration=models.Expiration.types['Breathing'],
        ),
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        exposed=mc.Population(
            number=28,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Heavy exercise'],
            mask=concentration_mc.infected.mask,
        ),
    )


@pytest.fixture
def waiting_room_mc():
    """
    Corresponds to the 5th line of Table 5 in CERN-OPEN-2021-04, but
    speaking 30% of the time (instead of 20%)
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=100, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0,24),)),
            air_exch=0.25,
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2_B117'],
            presence=mc.SpecificInterval(((0, 2),)),
            mask=models.Mask.types["No mask"],
            activity=activity_distributions['Seated'],
            expiration=models.MultipleExpiration(
                    expirations=(models.Expiration.types['Talking'],
                                 models.Expiration.types['Breathing']),
                    weights=(0.3, 0.7)),
        ),
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        exposed=mc.Population(
            number=14,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Seated'],
            mask=concentration_mc.infected.mask,
        ),
    )


@pytest.fixture
def skagit_chorale_mc():
    """
    Corresponds to the 6th line of Table 5 in CERN-OPEN-2021-04, but
    infection probability should be 29.8% instead of 32%, and number of
    new cases 17.9 instead of 21.
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=810, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0,24),)),
            air_exch=0.7,
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2'],
            presence=mc.SpecificInterval(((0, 2.5),)),
            mask=models.Mask.types["No mask"],
            activity=activity_distributions['Light activity'],
            expiration=models.Expiration((5., 5., 5.)),
        ),
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        exposed=mc.Population(
            number=60,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Moderate activity'],
            mask=concentration_mc.infected.mask,
        ),
    )


@pytest.mark.parametrize(
    "mc_model, expected_pi, expected_new_cases, expected_dose, expected_ER",
    [
        ["shared_office_mc", 10.7, 0.32, 57.24, 654],
        ["classroom_mc",     36.1, 6.85, 780.0, 28464],
        ["ski_cabin_mc",     16.3, 0.49, 35.94, 7404],
        ["gym_mc",           2.25, 0.63, 0.7842, 984],
        ["waiting_room_mc",  9.72, 1.36, 34.26, 3534],
        ["skagit_chorale_mc",29.9, 17.9, 190.0, 141400],
    ]
)
def test_report_models(mc_model, expected_pi, expected_new_cases,
                       expected_dose, expected_ER, request):
    mc_model = request.getfixturevalue(mc_model)
    exposure_model = mc_model.build_model(size=SAMPLE_SIZE)
    npt.assert_allclose(exposure_model.infection_probability().mean(),
                        expected_pi, rtol=TOLERANCE)
    npt.assert_allclose(exposure_model.expected_new_cases().mean(),
                        expected_new_cases, rtol=TOLERANCE)
    npt.assert_allclose(exposure_model.exposure().mean(),
                        expected_dose, rtol=TOLERANCE)
    npt.assert_allclose(
        exposure_model.concentration_model.infected.emission_rate_when_present().mean(),
        expected_ER, rtol=TOLERANCE)


@pytest.mark.parametrize(
    "mask_type, month, expected_pi, expected_dose, expected_ER",
    [
        ["No mask", "7", 30.0, 405.84, 3894],
        ["Type I",  "7", 10.2, 73.38, 702],
        ["FFP2",    "7", 4.0, 73.38, 702],
        ["Type I",  "2", 4.25, 21.42, 702],
    ],
)
def test_small_shared_office_Geneva(mask_type, month, expected_pi,
                                    expected_dose, expected_ER):
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=33, humidity=0.5),
        ventilation=models.MultipleVentilation(
            (
                models.SlidingWindow(
                    active=models.SpecificInterval(((0,24),)),
                    inside_temp=models.PiecewiseConstant((0, 24), (293,)),
                    outside_temp=data.Temperatures[month],
                    window_height=1.5, opening_length=0.2,
                ),
                models.AirChange(
                    active=models.SpecificInterval(((0,24),)),
                    air_exch=0.25,
                ),
            ),
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2_B117'],
            presence=mc.SpecificInterval(((9, 10+2/3), (10+5/6, 12.5), (13.5, 15+2/3), (15+5/6, 18))),
            mask=models.Mask.types[mask_type],
            activity=activity_distributions['Seated'],
            expiration=models.MultipleExpiration(
                    expirations=(models.Expiration.types['Talking'],
                                 models.Expiration.types['Breathing']),
                    weights=(0.33, 0.67)),
        ),
    )
    exposure_mc = mc.ExposureModel(
        concentration_model=concentration_mc,
        exposed=mc.Population(
            number=1,
            presence=concentration_mc.infected.presence,
            activity=activity_distributions['Seated'],
            mask=concentration_mc.infected.mask,
        ),
    )
    exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
    npt.assert_allclose(exposure_model.infection_probability().mean(),
                        expected_pi, rtol=TOLERANCE)
    npt.assert_allclose(exposure_model.exposure().mean(),
                        expected_dose, rtol=TOLERANCE)
    npt.assert_allclose(
        exposure_model.concentration_model.infected.emission_rate_when_present().mean(),
        expected_ER, rtol=TOLERANCE)
