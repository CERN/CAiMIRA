import numpy as np
import numpy.testing as npt
import pytest

import caimira.calculator.models.models as models
import caimira.calculator.models.data as data


def test_no_mask_superspeading_emission_rate(baseline_concentration_model):
    expected_rate = 48500.
    npt.assert_allclose(
        [baseline_concentration_model.infected.emission_rate(float(t)) for t in [0, 1, 4, 4.5, 5, 8, 9]],
        [0, expected_rate, expected_rate, 0, 0, expected_rate, 0],
        rtol=1e-12
    )


@pytest.fixture
def baseline_periodic_window(data_registry):
    return models.SlidingWindow(
        data_registry=data_registry,
        active=models.PeriodicInterval(period=120, duration=15),
        outside_temp=models.PiecewiseConstant((0., 24.), (283,)),
        window_height=1.6, opening_length=0.6,
    )


@pytest.fixture
def baseline_room():
    return models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,)))


@pytest.fixture
def baseline_periodic_hepa():
    return models.HEPAFilter(
        active=models.PeriodicInterval(period=120, duration=15),
        q_air_mech=514.74,
    )


def test_concentrations(baseline_concentration_model):
    # Expected concentrations were computed analytically
    ts = [0, 4, 5, 7, 10]
    concentrations = [baseline_concentration_model.concentration(float(t)) for t in ts]
    npt.assert_allclose(
        concentrations,
        [0.000000e+00, 2.046096e+01, 3.846725e-13, 2.046096e+01, 7.231966e-27],
        rtol=1e-6
    )


def test_smooth_concentrations(baseline_concentration_model):
    # We don't care about the actual concentrations in this test, but rather
    # that the curve itself is smooth.
    dx = 0.002
    dy_limit = 0.2  # Anything more than this (in relative) is a bit steep.
    ts = np.arange(0, 10, dx)
    concentrations = [baseline_concentration_model.concentration(float(t)) for t in ts]
    assert np.abs(np.diff(concentrations)).max()/np.mean(concentrations) < dy_limit


def build_model(data_registry, interval_duration):
    model = models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=75),
        ventilation=models.HEPAFilter(
            active=models.PeriodicInterval(period=120, duration=interval_duration),
            q_air_mech=500.,
        ),
        infected=models.EmittingPopulation(
            data_registry=data_registry,
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0., 4.), (5., 8.))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            known_individual_emission_rate=970 * 50,
            host_immunity=0.,
            # Superspreading event, where ejection factor is fixed based
            # on Miller et al. (2020) - 50 represents the infectious dose.
        ),
        evaporation_factor=0.3,
    )
    return model


def test_concentrations_startup(data_registry):
    # The concentrations should be the same until the beginning of the
    # first time that the ventilation is disabled.
    m1 = build_model(data_registry, interval_duration=120)
    m2 = build_model(data_registry, interval_duration=65)

    assert m1.concentration(1.) == m2.concentration(1.)


def test_r0(baseline_exposure_model):
    # Expected r0 was computed with a trapezoidal integration, using
    # a mesh of 100'000 pts per exposed presence interval.
    r0 = baseline_exposure_model.reproduction_number()
    npt.assert_allclose(r0, 771.380385)


def test_periodic_window(baseline_periodic_window, baseline_room):
    # Interesting transition times for a period of 120 and duration of 15.
    ts = [0, 14/60, 15/60, 16/60, 119/60, 120/60, 121/60, 239/60, 240/60]
    aes = [baseline_periodic_window.air_exchange(baseline_room, t) for t in ts]
    rate = 6.86347
    answers = [0, rate, rate, 0, 0, 0, rate, 0, 0]
    npt.assert_allclose(aes, answers, rtol=1e-5)


def test_periodic_hepa(baseline_periodic_hepa, baseline_room):
    # Interesting transition times for a period of 120 and duration of 15.
    ts = [0, 14 / 60, 15 / 60, 16 / 60, 119 / 60, 120 / 60, 121 / 60, 239 / 60, 240 / 60]
    rate = 514.74 / 75
    aes = [baseline_periodic_hepa.air_exchange(baseline_room, t) for t in ts]
    answers = [0, rate, rate, 0, 0, 0, rate, 0, 0]
    npt.assert_allclose(aes, answers, rtol=1e-5)


@pytest.mark.parametrize(
    "time, expected_value",
    [
        [0., 0.],
        [1 / 60, 514.74 / 68],
        [14 / 60, 514.74 / 68 + 5.3842316],
        [15 / 60, 514.74 / 68 + 5.3842316],
        [16 / 60, 5.3842316],
        [1., 5.3842316],
        [1.5, 3.7393925],
        [121 / 60, 514.74 / 68 + 3.7393925],
        [2.5, 3.7393925],
    ],
)
def test_multiple_ventilation_HEPA_window(data_registry, baseline_periodic_hepa, time, expected_value):
    room = models.Room(volume=68., inside_temp=models.PiecewiseConstant((0., 24.),(293.15,)))
    tempOutside = models.PiecewiseConstant((0., 1., 2.5),(273.15, 283.15))
    window = models.SlidingWindow(
        data_registry=data_registry,
        active=models.SpecificInterval([(1 / 60, 24.)]),
        outside_temp=tempOutside,
        window_height=1.,opening_length=0.6
    )
    vent = models.MultipleVentilation([window, baseline_periodic_hepa])
    npt.assert_allclose(vent.air_exchange(room,time), expected_value, rtol=1e-5)


def test_multiple_ventilation_HEPA_window_transitions(data_registry, baseline_periodic_hepa):
    tempOutside = models.PiecewiseConstant((0., 1., 2.5),(273.15, 283.15))
    room = models.Room(68, models.PiecewiseConstant((0., 24.),(293.15,)))
    window = models.SlidingWindow(
        data_registry=data_registry,
        active=models.SpecificInterval([(1 / 60, 24.)]),
        outside_temp=tempOutside,
        window_height=1.,opening_length=0.6
    )
    vent = models.MultipleVentilation([window, baseline_periodic_hepa])
    assert set(vent.transition_times(room)) == set([0.0, 1/60, 0.25, 1.0, 2.0, 2.25,
            2.5, 4.0, 4.25, 6.0, 6.25, 8.0, 8.25, 10.0, 10.25, 12.0, 12.25,
            14.0, 14.25, 16.0, 16.25, 18.0, 18.25, 20.0, 20.25, 22.0, 22.25, 24.])


@pytest.mark.parametrize(
    "volume, expected_value",
    [
        [24.5, 500 / 24.5 + 100 / 24.5 + 3.],
        [70, 500 / 70 + 100 / 70 + 3.],
    ],
)
def test_multiple_ventilation_HEPA_HVAC_AirChange(volume, expected_value):
    room = models.Room(volume=volume)
    hepa = models.HEPAFilter(
        active=models.SpecificInterval(((0,24),)),
        q_air_mech=500.,
    )
    hvac = models.HVACMechanical(
        active=models.SpecificInterval(((0,24),)),
        q_air_mech=100.,
    )
    airchange = models.AirChange(
        active=models.SpecificInterval(((0,24),)),
        air_exch=3.,
    )
    vent = models.MultipleVentilation([hepa, hvac, airchange])
    npt.assert_allclose(vent.air_exchange(room,10.),
                        expected_value,rtol=1e-5)


@pytest.mark.parametrize(
    "time, expected_value",
    [
        [8., 5.3842316],
        [16., 3.7393925],
    ],
)
def test_windowopening(data_registry, time, expected_value):
    tempOutside = models.PiecewiseConstant((0., 10., 24.),(273.15, 283.15))
    w = models.SlidingWindow(
        data_registry=data_registry,
        active=models.SpecificInterval([(0., 24.)]),
        outside_temp=tempOutside,
        window_height=1., opening_length=0.6,
    )
    npt.assert_allclose(
        w.air_exchange(models.Room(volume=68, inside_temp=models.PiecewiseConstant((0., 24.), (293.15, ))), time), expected_value, rtol=1e-5
    )


def build_hourly_dependent_model(
        data_registry,
        month,
        intervals_open=((7.5, 8.5),),
        intervals_presence_infected=((0., 4.), (5., 7.5)),
        artificial_refinement=False,
        temperatures=data.GenevaTemperatures_hourly
):
    if artificial_refinement:
        # 5-fold increase of number of times, WITHOUT interpolation
        # (hence transparent for the results)
        refine_factor = 2
        times_refined = tuple(
            float(t) for t in np.linspace(
                0., 24, refine_factor * len(temperatures[month].values) + 1
            )
        )
        temperatures_refined = tuple(np.hstack(
            [[v] * refine_factor for v in temperatures[month].values]
        ))
        outside_temp = models.PiecewiseConstant(times_refined, temperatures_refined)
    else:
        outside_temp = temperatures[month]

    model = models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293, ))),
        ventilation=models.SlidingWindow(
            data_registry=data_registry,
            active=models.SpecificInterval(intervals_open),
            outside_temp=outside_temp,
            window_height=1.6, opening_length=0.6,
        ),
        infected=models.EmittingPopulation(
            data_registry=data_registry,
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(intervals_presence_infected),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            known_individual_emission_rate=970 * 50,
            host_immunity=0,
        ),
        evaporation_factor=0.3,
    )
    return model


def build_constant_temp_model(data_registry, outside_temp, intervals_open=((7.5, 8.5),)):
    model = models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.SlidingWindow(
            data_registry=data_registry,
            active=models.SpecificInterval(intervals_open),
            outside_temp=models.PiecewiseConstant((0., 24.), (outside_temp,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=models.EmittingPopulation(
            data_registry=data_registry,
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0., 4.), (5., 7.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            known_individual_emission_rate=970 * 50,
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return model


def build_hourly_dependent_model_multipleventilation(data_registry, month, intervals_open=((7.5, 8.5),)):
    vent = models.MultipleVentilation((
        models.SlidingWindow(
            data_registry=data_registry,
            active=models.SpecificInterval(intervals_open),
            outside_temp=data.GenevaTemperatures[month],
            window_height=1.6, opening_length=0.6,
        ),
        models.HEPAFilter(
            active=models.SpecificInterval(((0., 24.),)),
            q_air_mech=500.,
        ),
    ))
    model = models.ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=vent,
        infected=models.EmittingPopulation(
            data_registry=data_registry,
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0., 4.), (5., 7.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            known_individual_emission_rate=970 * 50,
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return model


@pytest.mark.parametrize(
    "month, temperatures",
    data.local_hourly_temperatures_celsius_per_hour.items(),
)
@pytest.mark.parametrize(
    "time",
    [0.5, 1.2, 2., 3.5, 5., 6.5, 7.5, 7.9, 8.],
)
def test_concentrations_hourly_dep_temp_vs_constant(data_registry, month, temperatures, time):
    # The concentrations should be the same up to 8 AM (time when the
    # temperature changes DURING the window opening).
    m1 = build_hourly_dependent_model(data_registry, month)
    m2 = build_constant_temp_model(data_registry, temperatures[7] + 273.15)
    npt.assert_allclose(m1.concentration(time), m2.concentration(time), rtol=1e-5)

@pytest.mark.parametrize(
    "month, temperatures",
    data.local_hourly_temperatures_celsius_per_hour.items(),
)
@pytest.mark.parametrize(
    "time",
    [0.5, 1.2, 2., 3.5, 5., 6.5, 7.5, 7.9, 8.],
)
def test_concentrations_hourly_dep_temp_startup(data_registry, month, temperatures, time):
    # The concentrations should be the zero up to the first presence time
    # of an infected person.
    m = build_hourly_dependent_model(
        data_registry,
        month,
        ((0., 0.5), (1., 1.5), (4., 4.5), (7.5, 8), ),
        ((8., 12.), ),
    )
    assert m.concentration(time) == 0.


def test_concentrations_hourly_dep_multipleventilation(data_registry):
    m = build_hourly_dependent_model_multipleventilation(data_registry, 'Jan')
    m.concentration(12.)


@pytest.mark.parametrize(
    "month_temp_item",
    data.local_hourly_temperatures_celsius_per_hour.items(),
)
@pytest.mark.parametrize(
    "time",
    [0.5, 1.2, 2., 3.5, 5., 6.5, 7.5, 7.9, 8., 8.5, 9., 12.],
)
def test_concentrations_hourly_dep_adding_artificial_transitions(data_registry, month_temp_item, time):
    month, temperatures = month_temp_item
    # Adding a second opening inside the first one should not change anything
    m1 = build_hourly_dependent_model(data_registry, month, intervals_open=((7.5, 8.5), ))
    m2 = build_hourly_dependent_model(data_registry, month, intervals_open=((7.5, 8.5), (8., 8.1), ))
    npt.assert_allclose(m1.concentration(time), m2.concentration(time), rtol=1e-5)


@pytest.mark.parametrize(
    "time",
    (
        [float(t) for t in np.random.random_sample(10) * 24.]  # type: ignore
        + [float(t) for t in np.arange(0, 24.5, 0.5)]
    ),
)
def test_concentrations_refine_times(data_registry, time):
    month = 'Jan'
    m1 = build_hourly_dependent_model(data_registry, month, intervals_open=((0., 24.),))
    m2 = build_hourly_dependent_model(data_registry, month, intervals_open=((0., 24.),),
                                      artificial_refinement=True)
    npt.assert_allclose(m1.concentration(time), m2.concentration(time), rtol=1e-8)


def build_exposure_model(data_registry, concentration_model, short_range_model):
    infected = concentration_model.infected
    return models.ExposureModel(
        data_registry=data_registry,
        concentration_model=concentration_model,
        short_range=short_range_model,
        exposed=models.Population(
            number=10,
            presence=infected.presence,
            activity=infected.activity,
            mask=infected.mask,
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


# Expected deposited exposure were computed with a trapezoidal integration, using
# a mesh of 100'000 pts per exposed presence interval.
@pytest.mark.parametrize(
    "month, expected_deposited_exposure",
    [
        ['Jan', 359.140499],
        ['Jun', 1385.917562],
    ],
)
def test_exposure_hourly_dep(data_registry, month, expected_deposited_exposure, baseline_sr_model):
    m = build_exposure_model(
        data_registry,
        build_hourly_dependent_model(
            data_registry,
            month,
            intervals_open=((0., 24.), ),
            intervals_presence_infected=((8., 12.), (13., 17.))
        ), baseline_sr_model
    )
    deposited_exposure = m.deposited_exposure()
    npt.assert_allclose(deposited_exposure, expected_deposited_exposure)

# Expected deposited exposure were computed with a trapezoidal integration, using
# a mesh of 100'000 pts per exposed presence interval and 25 pts per hour
# for the temperature discretization.
@pytest.mark.parametrize(
    "month, expected_deposited_exposure",
    [
        ['Jan', 359.983716],
        ['Jun', 1439.267381],
    ],
)
def test_exposure_hourly_dep_refined(data_registry, month, expected_deposited_exposure, baseline_sr_model):
    m = build_exposure_model(
        data_registry,
        build_hourly_dependent_model(
            data_registry,
            month,
            intervals_open=((0., 24.),),
            intervals_presence_infected=((8., 12.), (13., 17.)),
            temperatures=data.GenevaTemperatures,
        ), baseline_sr_model
    )
    deposited_exposure = m.deposited_exposure()
    npt.assert_allclose(deposited_exposure, expected_deposited_exposure, rtol=0.02)
