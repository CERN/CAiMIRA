import numpy as np
import numpy.testing as npt
import pytest

import cara.monte_carlo as mc
from cara import models,data
from cara.monte_carlo.data import activity_distributions, virus_distributions, expiration_distributions, infectious_dose_distribution, viable_to_RNA_ratio_distribution
from cara.apps.calculator.model_generator import build_expiration

# TODO: seed better the random number generators
np.random.seed(2000)
SAMPLE_SIZE = 250000
TOLERANCE = 0.05

# Load the weather data (temperature in kelvin) for Toronto.
toronto_coordinates = (43.667, 79.400)
toronto_hourly_temperatures_celsius_per_hour = data.get_hourly_temperatures_celsius_per_hour(
    toronto_coordinates)


# Toronto hourly temperatures as piecewise constant function (in Kelvin).
TorontoTemperatures_hourly = {
    month: models.PiecewiseConstant(
        # NOTE:  It is important that the time type is float, not np.float, in
        # order to allow hashability (for caching).
        tuple(float(time) for time in range(25)),
        tuple(273.15 + np.array(temperatures)),
    )
    for month, temperatures in toronto_hourly_temperatures_celsius_per_hour.items()
}


# Same Toronto temperatures on a finer temperature mesh (every 6 minutes).
TorontoTemperatures = {
    month: TorontoTemperatures_hourly[month].refine(refine_factor=10)
    for month, temperatures in toronto_hourly_temperatures_celsius_per_hour.items()
}


# references values for infection_probability and expected new cases
# in the following tests, were obtained from the feature/mc branch

@pytest.fixture
def sr_model_mc() -> mc.ShortRangeModel:
    return mc.ShortRangeModel(
        activities=(),
        presence=(),
        expirations=(),
        dilutions=(),
    )

@pytest.fixture
def shared_office_mc(sr_model_mc):
    """
    Corresponds to the 1st line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=50, humidity=0.5),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    active=models.PeriodicInterval(period=120, duration=120),
                    inside_temp=models.PiecewiseConstant((0., 24.), (298,)),
                    outside_temp=data.GenevaTemperatures['Jun'],
                    window_height=1.6,
                    opening_length=0.2,
                ),
                models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
            )
        ),
        infected=mc.InfectedPopulation(
            number=1,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            virus=virus_distributions['SARS_CoV_2_DELTA'],
            mask=models.Mask.types['No mask'],
            activity=activity_distributions['Seated'],
            expiration=build_expiration({'Speaking': 0.33, 'Breathing': 0.67}),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=3,
            presence=mc.SpecificInterval(present_times=((0, 3.5), (4.5, 9))),
            activity=activity_distributions['Seated'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        )
    )


@pytest.fixture
def classroom_mc(sr_model_mc):
    """
    Corresponds to the 2nd line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=160, humidity=0.3),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    active=models.PeriodicInterval(period=120, duration=120),
                    inside_temp=models.PiecewiseConstant((0., 24.), (293,)),
                    outside_temp=TorontoTemperatures['Dec'],
                    window_height=1.6,
                    opening_length=0.2,
                ),
                models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
            )
        ),
        infected=mc.InfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            virus=virus_distributions['SARS_CoV_2_ALPHA'],
            mask=models.Mask.types["No mask"],
            activity=activity_distributions['Light activity'],
            expiration=build_expiration('Speaking'),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=19,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            activity=activity_distributions['Seated'],
            mask=models.Mask.types["No mask"],
            host_immunity=0.,
        ),
    )


@pytest.fixture
def ski_cabin_mc(sr_model_mc):
    """
    Corresponds to the 3rd line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=10, humidity=0.3),
        ventilation=models.MultipleVentilation(
            (models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.0),
            models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25))),
        infected=mc.InfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 20/60),)),
            virus=virus_distributions['SARS_CoV_2_DELTA'],
            mask=models.Mask.types['No mask'],
            activity=activity_distributions['Moderate activity'],
            expiration=build_expiration('Speaking'),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=3,
            presence=models.SpecificInterval(((0, 20/60),)),
            activity=activity_distributions['Moderate activity'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        ),
    )


@pytest.fixture
def skagit_chorale_mc(sr_model_mc):
    """
    Corresponds to the 4th line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988, 
    assuming viral is 10**9 instead of a LogCustomKernel distribution. 
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=810, humidity=0.5),
            ventilation=models.AirChange(
                active=models.PeriodicInterval(period=120, duration=120),
                air_exch=0.7),
            infected=mc.InfectedPopulation(
                number=1,
                presence=models.SpecificInterval(((0, 2.5), )),
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=10**9,
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                mask=models.Mask.types['No mask'],
                activity=activity_distributions['Moderate activity'],
                expiration=build_expiration('Shouting'),
                host_immunity=0.,
            ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=60,
            presence=models.SpecificInterval(((0, 2.5), )),
            activity=activity_distributions['Moderate activity'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
       ),
    )


@pytest.fixture
def bus_ride_mc(sr_model_mc):
    """
    Corresponds to the 5th line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988, 
    assuming viral is 5*10**8 instead of a LogCustomKernel distribution. 
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=45, humidity=0.5),
            ventilation=models.AirChange(
                active=models.PeriodicInterval(period=120, duration=120),
                air_exch=1.25),
            infected=mc.InfectedPopulation(
                number=1,
                presence=models.SpecificInterval(((0, 1.67), )),
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=5*10**8,
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                mask=models.Mask.types['No mask'],
                activity=activity_distributions['Seated'],
                expiration=build_expiration('Speaking'),
                host_immunity=0.,
            ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=67,
            presence=models.SpecificInterval(((0, 1.67), )),
            activity=activity_distributions['Seated'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
       ),
    )


@pytest.fixture
def gym_mc(sr_model_mc):
    """
    Gym model for testing
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=300, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0., 24.),)),
            air_exch=6,
        ),
        infected=mc.InfectedPopulation(
            number=2,
            virus=virus_distributions['SARS_CoV_2_ALPHA'],
            presence=mc.SpecificInterval(((0., 1.),)),
            mask=models.Mask.types["No mask"],
            activity=activity_distributions['Heavy exercise'],
            expiration=expiration_distributions['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=28,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Heavy exercise'],
            mask=concentration_mc.infected.mask,
            host_immunity=0.,
        ),
    )


@pytest.fixture
def waiting_room_mc(sr_model_mc):
    """
    Waiting room model for testing
    """
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=100, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0., 24.),)),
            air_exch=0.25,
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2_ALPHA'],
            presence=mc.SpecificInterval(((0., 2.),)),
            mask=models.Mask.types["No mask"],
            activity=activity_distributions['Seated'],
            expiration=build_expiration({'Speaking': 0.3, 'Breathing': 0.7}),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=14,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Seated'],
            mask=concentration_mc.infected.mask,
            host_immunity=0.,
        ),
    )


@pytest.mark.parametrize(
    "mc_model, expected_pi, expected_new_cases, expected_dose, expected_ER",
    [
        ["shared_office_mc", 6.03, 0.18, 3.198, 809],
        ["classroom_mc",     9.5, 1.85, 9.478, 5624],
        ["ski_cabin_mc",     16.0, 0.5, 17.315, 7966],
        ["skagit_chorale_mc",65.7, 40.0, 102.213, 190422],
        ["bus_ride_mc",      12.0, 8.0, 7.65, 5419],
        ["gym_mc",           0.45, 0.13, 0.208, 1145],
        ["waiting_room_mc",  1.59, 0.22, 0.821, 737],
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
    npt.assert_allclose(exposure_model.deposited_exposure().mean(),
                        expected_dose, rtol=TOLERANCE)
    npt.assert_allclose(
        exposure_model.concentration_model.infected.emission_rate_when_present().mean(),
        expected_ER, rtol=TOLERANCE)


@pytest.mark.parametrize(
    "mask_type, month, expected_pi, expected_dose, expected_ER",
    [
        ["No mask", "Jul", 9.52, 9.920, 809],
        ["Type I",  "Jul", 1.7, 0.913, 149],
        ["FFP2",    "Jul", 0.51, 0.239, 149],
        ["Type I",  "Feb", 0.57, 0.272, 162],
    ],
)
def test_small_shared_office_Geneva(mask_type, month, expected_pi,
                                    expected_dose, expected_ER, sr_model_mc):
    concentration_mc = mc.ConcentrationModel(
        room=models.Room(volume=33, humidity=0.5),
        ventilation=models.MultipleVentilation(
            (
                models.SlidingWindow(
                    active=models.SpecificInterval(((0., 24.),)),
                    inside_temp=models.PiecewiseConstant((0., 24.), (293,)),
                    outside_temp=data.GenevaTemperatures[month],
                    window_height=1.5, opening_length=0.2,
                ),
                models.AirChange(
                    active=models.SpecificInterval(((0., 24.),)),
                    air_exch=0.25,
                ),
            ),
        ),
        infected=mc.InfectedPopulation(
            number=1,
            virus=virus_distributions['SARS_CoV_2_ALPHA'],
            presence=mc.SpecificInterval(((9., 10+2/3), (10+5/6, 12.5), (13.5, 15+2/3), (15+5/6, 18.))),
            mask=models.Mask.types[mask_type],
            activity=activity_distributions['Seated'],
            expiration=build_expiration({'Speaking': 0.33, 'Breathing': 0.67}),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    exposure_mc = mc.ExposureModel(
        concentration_model=concentration_mc,
        short_range=sr_model_mc,
        exposed=mc.Population(
            number=1,
            presence=concentration_mc.infected.presence,
            activity=activity_distributions['Seated'],
            mask=concentration_mc.infected.mask,
            host_immunity=0.,
        ),
    )
    exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
    npt.assert_allclose(exposure_model.infection_probability().mean(),
                        expected_pi, rtol=TOLERANCE)
    npt.assert_allclose(exposure_model.deposited_exposure().mean(),
                        expected_dose, rtol=TOLERANCE)
    npt.assert_allclose(
        exposure_model.concentration_model.infected.emission_rate_when_present().mean(),
        expected_ER, rtol=TOLERANCE)
