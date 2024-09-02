import numpy as np
import numpy.testing as npt
import pytest
from retry import retry

import caimira.calculator.models.monte_carlo as mc
from caimira.calculator.models import models, data
from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions, expiration_distributions, infectious_dose_distribution, viable_to_RNA_ratio_distribution
from caimira.calculator.validators.virus.virus_validator import build_expiration

SAMPLE_SIZE = 500_000
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


# References values for infection_probability and expected new cases
# in the following tests, were obtained from the feature/mc branch
@pytest.fixture
def shared_office_mc(data_registry):
    """
    Corresponds to the 1st line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988
    """
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=50, inside_temp=models.PiecewiseConstant((0., 24.), (298,)), humidity=0.5),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    data_registry=data_registry,
                    active=models.PeriodicInterval(period=120, duration=120),
                    outside_temp=data.GenevaTemperatures['Jun'],
                    window_height=1.6,
                    opening_length=0.2,
                ),
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
            expiration=build_expiration(data_registry, {'Speaking': 0.33, 'Breathing': 0.67}),
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


@pytest.fixture
def classroom_mc(data_registry):
    """
    Corresponds to the 2nd line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988
    """
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=160, inside_temp=models.PiecewiseConstant((0., 24.), (293,)), humidity=0.3),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    data_registry=data_registry,
                    active=models.PeriodicInterval(period=120, duration=120),
                    outside_temp=TorontoTemperatures['Dec'],
                    window_height=1.6,
                    opening_length=0.2,
                ),
                models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
            )
        ),
        infected=mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            virus=virus_distributions(data_registry)['SARS_CoV_2_ALPHA'],
            mask=models.Mask.types["No mask"],
            activity=activity_distributions(data_registry)['Light activity'],
            expiration=build_expiration(data_registry, 'Speaking'),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_mc,
        short_range=(),
        exposed=mc.Population(
            number=19,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            activity=activity_distributions(data_registry)['Seated'],
            mask=models.Mask.types["No mask"],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


@pytest.fixture
def ski_cabin_mc(data_registry):
    """
    Corresponds to the 3rd line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988
    """
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=10, humidity=0.3),
        ventilation=models.MultipleVentilation(
            (models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.0),
            models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25))),
        infected=mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=models.SpecificInterval(((0, 20/60),)),
            virus=virus_distributions(data_registry)['SARS_CoV_2_DELTA'],
            mask=models.Mask.types['No mask'],
            activity=activity_distributions(data_registry)['Moderate activity'],
            expiration=build_expiration(data_registry, 'Speaking'),
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
            presence=models.SpecificInterval(((0, 20/60),)),
            activity=activity_distributions(data_registry)['Moderate activity'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


@pytest.fixture
def skagit_chorale_mc(data_registry):
    """
    Corresponds to the 4th line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988,
    assuming viral is 10**9 instead of a LogCustomKernel distribution.
    """
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=810, humidity=0.5),
            ventilation=models.AirChange(
                active=models.PeriodicInterval(period=120, duration=120),
                air_exch=0.7),
            infected=mc.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=models.SpecificInterval(((0, 2.5), )),
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=10**9,
                    infectious_dose=infectious_dose_distribution(),
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution(),
                    transmissibility_factor=1.,
                ),
                mask=models.Mask.types['No mask'],
                activity=activity_distributions(data_registry)['Moderate activity'],
                expiration=build_expiration(data_registry, 'Shouting'),
                host_immunity=0.,
            ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_mc,
        short_range=(),
        exposed=mc.Population(
            number=60,
            presence=models.SpecificInterval(((0, 2.5), )),
            activity=activity_distributions(data_registry)['Moderate activity'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


@pytest.fixture
def bus_ride_mc(data_registry):
    """
    Corresponds to the 5th line of Table 4 in https://doi.org/10.1101/2021.10.14.21264988,
    assuming viral is 5*10**8 instead of a LogCustomKernel distribution.
    """
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=45, humidity=0.5),
            ventilation=models.AirChange(
                active=models.PeriodicInterval(period=120, duration=120),
                air_exch=1.25),
            infected=mc.InfectedPopulation(
                data_registry=data_registry,
                number=1,
                presence=models.SpecificInterval(((0, 1.67), )),
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=5*10**8,
                    infectious_dose=infectious_dose_distribution(),
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution(),
                    transmissibility_factor=1.,
                ),
                mask=models.Mask.types['No mask'],
                activity=activity_distributions(data_registry)['Seated'],
                expiration=build_expiration(data_registry, 'Speaking'),
                host_immunity=0.,
            ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_mc,
        short_range=(),
        exposed=mc.Population(
            number=67,
            presence=models.SpecificInterval(((0, 1.67), )),
            activity=activity_distributions(data_registry)['Seated'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


@pytest.fixture
def gym_mc(data_registry):
    """
    Gym model for testing
    """
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=300, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0., 24.),)),
            air_exch=6,
        ),
        infected=mc.InfectedPopulation(
            data_registry=data_registry,
            number=2,
            virus=virus_distributions(data_registry)['SARS_CoV_2_ALPHA'],
            presence=mc.SpecificInterval(((0., 1.),)),
            mask=models.Mask.types["No mask"],
            activity=activity_distributions(data_registry)['Heavy exercise'],
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
            number=28,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Heavy exercise'],
            mask=concentration_mc.infected.mask,
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


@pytest.fixture
def waiting_room_mc(data_registry):
    """
    Waiting room model for testing
    """
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=100, humidity=0.5),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0., 24.),)),
            air_exch=0.25,
        ),
        infected=mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            virus=virus_distributions(data_registry)['SARS_CoV_2_ALPHA'],
            presence=mc.SpecificInterval(((0., 2.),)),
            mask=models.Mask.types["No mask"],
            activity=activity_distributions(data_registry)['Seated'],
            expiration=build_expiration(data_registry, {'Speaking': 0.3, 'Breathing': 0.7}),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_mc,
        short_range=(),
        exposed=mc.Population(
            number=14,
            presence=concentration_mc.infected.presence,
            activity=models.Activity.types['Seated'],
            mask=concentration_mc.infected.mask,
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


# In the following tests all the initial expected values for emission
# rate were multiplied by the average of the distribution of fraction
# of infected viruses (0.305, for a uniform distribution from 0.01 to 0.6)
# following the change of convention that this ratio should be
# applied at the emission level.
@retry(tries=10)
@pytest.mark.parametrize(
    "mc_model, expected_pi, expected_new_cases, expected_dose, expected_ER_per_person",
    [
        ["shared_office_mc", 5.38, 0.16, 3.350, 1056*0.305],
        ["classroom_mc",     8.21, 1.56, 11.356, 7416*0.305],
        ["ski_cabin_mc",     12.92, 0.39, 21.796, 10231*0.305],
        ["skagit_chorale_mc",61.01, 36.53, 84.730, 190422*0.305],
        ["bus_ride_mc",      10.59, 7.06, 6.650, 5419*0.305],
        ["gym_mc",           0.52, 0.14, 0.249, 1450*0.305/2.], # there are two infected in this case
        ["waiting_room_mc",  1.53, 0.21, 0.844, 929*0.305],
    ]
)
def test_report_models(mc_model, expected_pi, expected_new_cases,
                       expected_dose, expected_ER_per_person, request):
    mc_model = request.getfixturevalue(mc_model)
    exposure_model = mc_model.build_model(size=SAMPLE_SIZE)
    npt.assert_allclose(exposure_model.infection_probability().mean(),
                        expected_pi, rtol=TOLERANCE)
    npt.assert_allclose(exposure_model.expected_new_cases().mean(),
                        expected_new_cases, rtol=TOLERANCE)
    npt.assert_allclose(exposure_model.deposited_exposure().mean(),
                        expected_dose, rtol=TOLERANCE)
    npt.assert_allclose(
        exposure_model.concentration_model.infected.emission_rate_per_person_when_present().mean(),
        expected_ER_per_person, rtol=TOLERANCE)


@retry(tries=10)
@pytest.mark.parametrize(
    "mask_type, month, expected_pi, expected_dose, expected_ER",
    [
        ["No mask", "Jul", 7.689, 10.050, 1034.435*0.305],
        ["Type I",  "Jul", 1.663, 0.938, 193.52*0.305],
        ["FFP2",    "Jul", 0.523, 0.253, 193.52*0.305],
        ["Type I",  "Feb", 0.659, 0.325, 193.52*0.305],
        ["Cloth",   "Feb", 2.653, 1.741, 673.10*0.305],
        ["Cloth",   "Jul", 5.322, 5.064, 673.10*0.305],
    ],
)
def test_small_shared_office_Geneva(data_registry, mask_type, month, expected_pi,
                                    expected_dose, expected_ER):
    concentration_mc = mc.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=33, inside_temp=models.PiecewiseConstant((0., 24.), (293,)), humidity=0.5),
        ventilation=models.MultipleVentilation(
            (
                models.SlidingWindow(
                    data_registry=data_registry,
                    active=models.SpecificInterval(((0., 24.),)),
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
            data_registry=data_registry,
            number=1,
            virus=virus_distributions(data_registry)['SARS_CoV_2_ALPHA'],
            presence=mc.SpecificInterval(((9., 10+2/3), (10+5/6, 12.5), (13.5, 15+2/3), (15+5/6, 18.))),
            mask=models.Mask.types[mask_type],
            activity=activity_distributions(data_registry)['Seated'],
            expiration=build_expiration(data_registry, {'Speaking': 0.33, 'Breathing': 0.67}),
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    exposure_mc = mc.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_mc,
        short_range=(),
        exposed=mc.Population(
            number=1,
            presence=concentration_mc.infected.presence,
            activity=activity_distributions(data_registry)['Seated'],
            mask=concentration_mc.infected.mask,
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )
    exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
    npt.assert_allclose(exposure_model.infection_probability().mean(),
                        expected_pi, rtol=TOLERANCE)
    npt.assert_allclose(exposure_model.deposited_exposure().mean(),
                        expected_dose, rtol=TOLERANCE)
    npt.assert_allclose(
        exposure_model.concentration_model.infected.emission_rate_per_person_when_present().mean(),
        expected_ER, rtol=TOLERANCE)
