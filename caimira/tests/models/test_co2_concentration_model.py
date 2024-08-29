import numpy.testing as npt
import numpy as np
import typing
import pytest

from caimira import models
from caimira.apps.calculator.co2_model_generator import CO2FormData


@pytest.fixture
def simple_co2_conc_model(data_registry):
    return models.CO2ConcentrationModel(
        data_registry=data_registry,
        room=models.Room(200, models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.AirChange(models.PeriodicInterval(period=120, duration=120), 0.25),
        CO2_emitters=models.SimplePopulation(
            number=5,
            presence=models.SpecificInterval((([0., 4.], ))),
            activity=models.Activity.types['Seated'],
        ),
    )


@pytest.mark.parametrize(
    "time, expected_co2_concentration", [
        [0., 440.44],
        [1., 914.2487227],
        [2., 1283.251327],
        [3., 1570.630844],
        [4., 1794.442237],
    ]
)
def test_co2_concentration(
    simple_co2_conc_model: models.CO2ConcentrationModel,
    time: float,
    expected_co2_concentration: float,
):
    npt.assert_almost_equal(simple_co2_conc_model.concentration(time), expected_co2_concentration)


def test_integrated_concentration(simple_co2_conc_model):
    c1 = simple_co2_conc_model.integrated_concentration(0, 2)
    c2 = simple_co2_conc_model.integrated_concentration(0, 1)
    c3 = simple_co2_conc_model.integrated_concentration(1, 2)
    assert c1 != 0
    npt.assert_almost_equal(c1, c2 + c3)


@pytest.mark.parametrize(
    "scenario_data, room_volume, max_total_people, start, finish, state_changes", [
        ["office_scenario_1_sensor_data", 102, 4, "14:00", "17:30", (14.78, 15.1, 15.53, 15.87, 16.52, 16.83)],
        ["office_scenario_2_sensor_data", 60, 2, "08:38", "17:30", (10.17, 12.45, 14.5)], # Second should be 12.87
        ["meeting_scenario_1_sensor_data", 83, 3, "09:04", "11:45", (10.37, 11.07)],
        ["meeting_scenario_2_sensor_data", 83, 4, "13:40", "16:40", (14.37, 14.72, 15, 15.33, 15.68, 16.03)]
    ]
)
def test_find_change_points(scenario_data, room_volume, max_total_people, start, finish, state_changes, request):
    '''
    Specific test of the find_change_points method using the
    scipy find_peaks and specific smoothing techniques. Only
    the ventilation state changes are target for detection.
    '''
    CO2_form_model: CO2FormData = CO2FormData(
        CO2_data=request.getfixturevalue(scenario_data),
        fitting_ventilation_states=[],
        exposed_start=start,
        exposed_finish=finish,
        total_people=max_total_people,
        room_volume=room_volume,
    )
    find_points = CO2_form_model.find_change_points()
    assert np.allclose(find_points, state_changes, rtol=1e-2)


@pytest.mark.parametrize(
    "scenario_data, room_volume, occupancy, presence_interval, all_state_changes", [
        ["office_scenario_1_sensor_data", 102, (4,), (14, 17.5), (14, 14.25, 14.78, 15.1, 15.53, 15.87, 16.52, 16.83, 17.5)],
        ["office_scenario_2_sensor_data", 60, (2, 0, 2), (8.62, 11.93, 12.42, 17.5), (8.62, 10.17, 12.45, 14.5, 17.5, 20.)],
        ["meeting_scenario_1_sensor_data", 83, (2, 3, 2, 3), (9.07, 9.32, 9.75, 10.75, 11.75), (9.07, 10.37, 11.07, 11.75)],
        ["meeting_scenario_2_sensor_data", 83, (2, 3, 4), (13.67, 13.75, 15.87, 16.67), (13.67, 14.37, 14.72, 15.00, 15.33, 15.68, 16.03, 16.67)]
    ]
)
def test_predictive_model_accuracy(data_registry, scenario_data, room_volume, occupancy, presence_interval, all_state_changes, request):
    '''
    Specific test corresponding to specific data files of four
    different occurencies (2 office and 2 meeting room scenarios). 
    The room volume, number of people and ventilation transition times 
    correspond to the real occurencies in the simulation days.

    Note that the last time from the input file is considered as a ventilation
    state change.
    '''
    input_fitting_data = request.getfixturevalue(scenario_data)

    fitting_model: models.CO2DataModel = models.CO2DataModel(
        data_registry=data_registry,
        room_volume=room_volume,
        number=models.IntPiecewiseConstant(
            transition_times=presence_interval,
            values=occupancy
        ),
        presence=None,
        ventilation_transition_times=all_state_changes,
        times=input_fitting_data['times'],
        CO2_concentrations=input_fitting_data['CO2'],
    )
    # Get fitting results
    fitting_results: typing.Dict = fitting_model.CO2_fit_params()
    predictive_CO2: typing.List[float] = fitting_results['predictive_CO2']

    def root_mean_square_error_percentage(actual, predicted) -> float:    
        return np.sqrt(np.mean(((actual - predicted) / actual) ** 2)) * 100
    
    # Calculate RMSEP metric
    rmsep = root_mean_square_error_percentage(np.array(input_fitting_data['CO2']), np.array(predictive_CO2))

    acceptable_rmsep = 10 # Threshold of 10% for the accepted error margin
    assert rmsep <= acceptable_rmsep, f"RMSEP {rmsep} exceeds acceptable threshold {acceptable_rmsep}"
    