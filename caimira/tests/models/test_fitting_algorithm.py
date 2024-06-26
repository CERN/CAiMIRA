import numpy as np
import numpy.testing as npt
import pytest

from caimira import models


@pytest.mark.parametrize(
    "activity_type, ventilation_active, air_exch", [
        ['Seated', [8, 12, 13, 17], [0.25, 2.45, 0.25]],
        ['Standing', [8, 10, 11, 12, 17], [1.25, 3.25, 1.45, 0.25]],
        ['Light activity', [8, 12, 17], [1.25, 0.25]],
        ['Moderate activity', [8, 13, 15, 16, 17], [2.25, 0.25, 3.45, 0.25]],
        ['Heavy exercise', [8, 17], [0.25]],
        ['Seated', [8, 17], [0.25]],
        ['Standing', [8, 17], [2.45]],
    ]
)
def test_fitting_algorithm(data_registry, activity_type, ventilation_active, air_exch):
    conc_model = models.CO2ConcentrationModel(
        data_registry = data_registry,
        room=models.Room(
            volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=models.CustomVentilation(models.PiecewiseConstant(
                tuple(ventilation_active), tuple(air_exch))),
        CO2_emitters=models.SimplePopulation(
            number=models.IntPiecewiseConstant(transition_times=tuple(
                [8, 12, 13, 17]), values=tuple([2, 1, 2])),
            presence=None,
            activity=models.Activity.types[activity_type]
        ),
    )

    times = np.linspace(8, 17, 100)
    CO2_concentrations = [
        conc_model.concentration(float(time))
        for time in times
    ]

    # Generate CO2DataModel
    data_model = models.CO2DataModel(
        data_registry=data_registry,
        room_volume=75,
        number=models.IntPiecewiseConstant(transition_times=tuple(
            [8, 12, 13, 17]), values=tuple([2, 1, 2])),
        presence=None,
        ventilation_transition_times=tuple(ventilation_active),
        times=times,
        CO2_concentrations=CO2_concentrations
    )

    fit_parameters = data_model.CO2_fit_params()
    exhalation_rate = fit_parameters['exhalation_rate']
    npt.assert_almost_equal(
        exhalation_rate, conc_model.CO2_emitters.activity.exhalation_rate, decimal=2)

    ventilation_values = fit_parameters['ventilation_values']
    npt.assert_allclose(ventilation_values, air_exch, rtol=1e-2)
    