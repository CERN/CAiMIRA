import numpy as np
import numpy.testing as npt
import pytest

import cara.models as models
import cara.data as data


def test_no_mask_aerosols(baseline_model):
    exp = models.Expiration.types['Unmodulated Vocalization']
    npt.assert_allclose(
        exp.aerosols(models.Mask.types['No mask']),
        6.077541e-12,
        rtol=1e-5,
    )


def test_no_mask_emission_rate(baseline_model):
    rate = 167.74011998223307
    npt.assert_allclose(
        [baseline_model.infected.emission_rate(t) for t in [0, 1, 4, 4.5, 5, 8, 9]],
        [0, rate, rate, 0, 0, rate, 0],
        rtol=1e-5
    )


@pytest.fixture
def baseline_model():
    model = models.Model(
        room=models.Room(volume=75),
        ventilation=models.WindowOpening(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0,24),(293,)),
            outside_temp=models.PiecewiseConstant((0,24),(283,)),
            cd_b=0.6, window_height=1.6, opening_length=0.6,
        ),
        infected=models.InfectedPerson(
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light exercise'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
        infected_occupants=1,
        exposed_occupants=10,
        exposed_activity=models.Activity.types['Light exercise'],
    )
    return model


@pytest.fixture
def baseline_periodic_window():
    return models.WindowOpening(
        active=models.PeriodicInterval(period=120, duration=15),
        inside_temp=models.PiecewiseConstant((0,24),(293,)),
        outside_temp=models.PiecewiseConstant((0,24),(283,)),
        cd_b=0.6, window_height=1.6, opening_length=0.6,
    )


@pytest.fixture
def baseline_room():
    return models.Room(volume=75)


@pytest.fixture
def baseline_periodic_hepa():
    return models.HEPAFilter(
        active=models.PeriodicInterval(period=120, duration=15),
        q_air_mech=514.74,
    )


def test_concentrations(baseline_model):
    ts = [0, 4, 5, 7, 10]
    concentrations = [baseline_model.concentration(t) for t in ts]
    npt.assert_allclose(
        concentrations,
        [0.000000e+00, 2.891970e-01, 1.266287e-04, 2.891969e-01, 5.544607e-08],
        rtol=1e-5
    )


def test_smooth_concentrations(baseline_model):
    # We don't care about the actual concentrations in this test, but rather
    # that the curve itself is smooth.
    dx = 0.1
    dy_limit = dx * 2  # Anything more than this is a bit steep.
    ts = np.arange(0, 10, dx)
    concentrations = [baseline_model.concentration(t) for t in ts]
    assert np.abs(np.diff(concentrations)).max() < dy_limit


def build_model(interval_duration):
    model = models.Model(
        room=models.Room(volume=75),
        ventilation=models.HEPAFilter(
            active=models.PeriodicInterval(period=120, duration=interval_duration),
            q_air_mech=500.,
        ),
        infected=models.InfectedPerson(
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light exercise'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
        infected_occupants=1,
        exposed_occupants=10,
        exposed_activity=models.Activity.types['Light exercise'],
    )
    return model


def test_concentrations_startup(baseline_model):
    # The concentrations should be the same until the beginning of the
    # first time that the ventilation is disabled.
    m1 = build_model(interval_duration=120)
    m2 = build_model(interval_duration=65)

    assert m1.concentration(1.) == m2.concentration(1.)


def test_r0(baseline_model):
    p = baseline_model.infection_probability()
    npt.assert_allclose(p, 93.196908)


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
def test_multiple_ventilation_HEPA_window(baseline_periodic_hepa, time, expected_value):
    room = models.Room(volume=68.)
    tempOutside = models.PiecewiseConstant((0., 1., 2.5),(273.15, 283.15))
    tempInside = models.PiecewiseConstant((0., 24.),(293.15,))
    window = models.WindowOpening(active=models.SpecificInterval([(1 / 60, 24.)]),
                inside_temp=tempInside,outside_temp=tempOutside,
                window_height=1.,opening_length=0.6)
    vent = models.MultipleVentilation([window, baseline_periodic_hepa])
    npt.assert_allclose(vent.air_exchange(room,time), expected_value, rtol=1e-5)


def test_multiple_ventilation_HEPA_window_transitions(baseline_periodic_hepa):
    room = models.Room(volume=68.)
    tempOutside = models.PiecewiseConstant((0., 1., 2.5),(273.15, 283.15))
    tempInside = models.PiecewiseConstant((0., 24.),(293.15,))
    window = models.WindowOpening(active=models.SpecificInterval([(1 / 60, 24.)]),
                inside_temp=tempInside,outside_temp=tempOutside,
                window_height=1.,opening_length=0.6)
    vent = models.MultipleVentilation([window, baseline_periodic_hepa])
    assert set(vent.transition_times()) == set([0.0, 1/60, 0.25, 1.0, 2.0, 2.25,
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


def test_expiration_aerosols():
    mask = models.Mask.types['Type I']
    exp1 = models.Expiration((0.751, 0.139, 0.0139, 0.059),
                            particle_sizes = (0.8e-4, 1.8e-4, 3.5e-4, 5.5e-4))
    exp2 = models.Expiration((0.059, 0.0139, 0.751, 0.139),
                            particle_sizes = (5.5e-4, 3.5e-4, 0.8e-4, 1.8e-4))
    npt.assert_allclose(exp1.aerosols(mask), exp2.aerosols(mask), rtol=1e-5)


def test_piecewiseconstantfunction_wrongarguments():
    # number of values should be 1+number of transition times
    pytest.raises(ValueError,models.PiecewiseConstant,(0,1),(0,0))
    pytest.raises(ValueError,models.PiecewiseConstant,(0,),(0,0))
    # two transition times cannot be equal
    pytest.raises(ValueError,models.PiecewiseConstant,(0,2,2),(0,0))
    # unsorted transition times are not allowed
    pytest.raises(ValueError,models.PiecewiseConstant,(2,0),(0,0))


@pytest.mark.parametrize(
    "time, expected_value",
    [
        [10, 5],
        [20.5, 8],
        [8, 2],
        [0, 2],
        [24, 8],
        [-1, 2],
        [25, 8],
    ],
)
def test_piecewiseconstant(time, expected_value):
    transition_times = (0, 8, 16, 24)
    values = (2, 5, 8)
    fun = models.PiecewiseConstant(transition_times,values)
    assert fun.value(time) == expected_value


def test_piecewiseconstant_interp():
    transition_times = (0, 8, 16, 24)
    values = (2, 5, 8)
    fun = models.PiecewiseConstant(transition_times,values)
    refined_fun = models.PiecewiseConstant(transition_times,values).refine(refine_factor=2)
    assert refined_fun.transition_times == (0, 4, 8, 12, 16, 20 ,24)
    assert refined_fun.values == (2, 3.5, 5, 6.5, 8, 8)


def test_constantfunction():
    transition_times = (0,24)
    values = (20,)
    fun = models.PiecewiseConstant(transition_times,values)
    for t in [0,1,8,10,16,20.1,24]:
        assert (fun.value(t) == 20)


@pytest.mark.parametrize(
    "time",
    [0,1,8,10,16,20.1,24],
)
def test_piecewiseconstant_vs_interval(time):
    transition_times = (0,8,16,24)
    values = (0,1,0)
    fun = models.PiecewiseConstant(transition_times,values)
    interval = models.SpecificInterval(present_times=[(8,16)])
    assert interval.transition_times() == fun.interval().transition_times()
    assert fun.interval().triggered(time) == interval.triggered(time)


def test_piecewiseconstant_transition_times():
    outside_temp=data.GenevaTemperatures['Jan']
    assert set(outside_temp.transition_times) == outside_temp.interval().transition_times()


@pytest.mark.parametrize(
    "time, expected_value",
    [
        [8., 5.3842316],
        [16., 3.7393925],
    ],
)
def test_windowopening(time, expected_value):
    tempOutside = models.PiecewiseConstant((0,10,24),(273.15,283.15))
    tempInside = models.PiecewiseConstant((0,24),(293.15,))
    w = models.WindowOpening(active=models.SpecificInterval([(0,24)]),
                inside_temp=tempInside,outside_temp=tempOutside,
                window_height=1.,opening_length=0.6)
    npt.assert_allclose(w.air_exchange(models.Room(volume=68),time),
                        expected_value,rtol=1e-5)


def build_hourly_dependent_model(month, intervals_open=((7.5, 8.5),),
                    intervals_presence_infected=((0, 4), (5, 7.5)),refine=False):
    if refine:
        times_refined = tuple(np.linspace(0.,24,241))
        temperatures_refined = tuple(np.hstack([[v]*10 for v in data.GenevaTemperatures_hourly[month].values]))
        outside_temp=models.PiecewiseConstant(times_refined,temperatures_refined)
    else:
        outside_temp=data.GenevaTemperatures_hourly[month]

    model = models.Model(
        room=models.Room(volume=75),
        ventilation=models.WindowOpening(
            active=models.SpecificInterval(intervals_open),
            inside_temp=models.PiecewiseConstant((0,24),(293,)),
            outside_temp=outside_temp,
            cd_b=0.6, window_height=1.6, opening_length=0.6,
        ),
        infected=models.InfectedPerson(
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(intervals_presence_infected),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light exercise'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
        infected_occupants=1,
        exposed_occupants=10,
        exposed_activity=models.Activity.types['Light exercise'],
    )
    return model


def build_constant_temp_model(outside_temp, intervals_open=((7.5, 8.5),)):
    model = models.Model(
        room=models.Room(volume=75),
        ventilation=models.WindowOpening(
            active=models.SpecificInterval(intervals_open),
            inside_temp=models.PiecewiseConstant((0,24),(293,)),
            outside_temp=models.PiecewiseConstant((0,24),(outside_temp,)),
            cd_b=0.6, window_height=1.6, opening_length=0.6,
        ),
        infected=models.InfectedPerson(
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0, 4), (5, 7.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light exercise'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
        infected_occupants=1,
        exposed_occupants=10,
        exposed_activity=models.Activity.types['Light exercise'],
    )
    return model


def build_hourly_dependent_model_multipleventilation(month, intervals_open=((7.5, 8.5),)):
    vent = models.MultipleVentilation((
        models.WindowOpening(
            active=models.SpecificInterval(intervals_open),
            inside_temp=models.PiecewiseConstant((0,24),(293,)),
            outside_temp=data.GenevaTemperatures[month],
            cd_b=0.6, window_height=1.6, opening_length=0.6,
        ),
        models.HEPAFilter(
        active=models.SpecificInterval(((0,24),)),
        q_air_mech=500.,
        )))
    model = models.Model(
        room=models.Room(volume=75),
        ventilation=vent,
        infected=models.InfectedPerson(
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0, 4), (5, 7.5))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light exercise'],
            expiration=models.Expiration.types['Unmodulated Vocalization'],
        ),
        infected_occupants=1,
        exposed_occupants=10,
        exposed_activity=models.Activity.types['Light exercise'],
    )
    return model


@pytest.mark.parametrize(
    "month, temperatures",
    data.Geneva_hourly_temperatures_celsius_per_hour.items(),
)
@pytest.mark.parametrize(
    "time",
    [0.5, 1.2, 2., 3.5, 5., 6.5, 7.5, 7.9, 8.],
)
def test_concentrations_hourly_dep_temp_vs_constant(month, temperatures, time):
    # The concentrations should be the same up to 8 AM (time when the 
    # temperature changes DURING the window opening).
    m1 = build_hourly_dependent_model(month)
    m2 = build_constant_temp_model(temperatures[7]+273.15)
    npt.assert_allclose(m1.concentration(time), m2.concentration(time), rtol=1e-5)

@pytest.mark.parametrize(
    "month, temperatures",
    data.Geneva_hourly_temperatures_celsius_per_hour.items(),
)
@pytest.mark.parametrize(
    "time",
    [0.5, 1.2, 2., 3.5, 5., 6.5, 7.5, 7.9, 8.],
)
def test_concentrations_hourly_dep_temp_startup(month, temperatures, time):
    # The concentrations should be the zero up to the first presence time
    # of an infecter person.
    m = build_hourly_dependent_model(month,((0.,0.5),(1,1.5),(4,4.5),(7.5,8)),
                        ((8,12.),))
    assert m.concentration(time) == 0.


def test_concentrations_hourly_dep_multipleventilation():
    m = build_hourly_dependent_model_multipleventilation('Jan')
    m.concentration(12.)


@pytest.mark.parametrize(
    "month_temp_item",
    data.Geneva_hourly_temperatures_celsius_per_hour.items(),
)
@pytest.mark.parametrize(
    "time",
    [0.5, 1.2, 2., 3.5, 5., 6.5, 7.5, 7.9, 8., 8.5, 9., 12.],
)
def test_concentrations_hourly_dep_adding_artificial_transitions(month_temp_item, time):
    month, temperatures = month_temp_item
    # Adding a second opening inside the first one should not change anything
    m1 = build_hourly_dependent_model(month,intervals_open=((7.5, 8.5),))
    m2 = build_hourly_dependent_model(month,intervals_open=((7.5, 8.5),(8.,8.1)))
    npt.assert_allclose(m1.concentration(time), m2.concentration(time), rtol=1e-5)


@pytest.mark.parametrize(
    "time",
    list(np.random.random_sample(20)*24.)+list(np.arange(0,24.5,0.5)),
)
def test_concentrations_refine_times(time):
    month = 'Jan'
    m1 = build_hourly_dependent_model(month,intervals_open=((0, 24),))
    m2 = build_hourly_dependent_model(month,intervals_open=((0, 24),),refine=True)
    npt.assert_allclose(m1.concentration(time), m2.concentration(time), rtol=1e-8)

