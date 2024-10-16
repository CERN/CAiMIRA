from caimira.calculator.validators.co2.co2_validator import CO2FormData
from caimira.calculator.models.models import CO2DataModel


def build_initial_plot(
        form: CO2FormData,
) -> dict:
    '''
    Initial plot with the suggested ventilation state changes. 
    This method receives the form input and returns the CO2
    plot with the respective transition times.
    '''
    CO2model: CO2DataModel = form.build_model()

    occupancy_transition_times = list(CO2model.occupancy.transition_times)

    ventilation_transition_times: list = form.find_change_points()
    # The entire ventilation changes consider the initial and final occupancy state change
    all_vent_transition_times: list = sorted(
        [occupancy_transition_times[0]] +
        [occupancy_transition_times[-1]] +
        ventilation_transition_times)

    vent_plot_img, vent_plot_data = form.generate_ventilation_plot(
        ventilation_transition_times=ventilation_transition_times,
        occupancy_transition_times=occupancy_transition_times
    )

    context = {
        'transition_times': [round(el, 2) for el in all_vent_transition_times],
        'CO2_plot_img': vent_plot_img,
        'CO2_plot_data': vent_plot_data
    }

    return context


def build_fitting_results(
        form: CO2FormData,
) -> dict:
    '''
    Final fitting results with the respective predictive CO2. 
    This method receives the form input and returns the fitting results
    along with the CO2 plot with the predictive CO2.
    '''
    CO2model: CO2DataModel = form.build_model()

    # Ventilation times after user manipulation from the suggested ventilation state change times.
    ventilation_transition_times = list(CO2model.ventilation_transition_times)

    # The result of the following method is a dict with the results of the fitting
    # algorithm, namely the breathing rate and ACH values. It also returns the
    # predictive CO2 result based on the fitting results.
    context = dict(CO2model.CO2_fit_params())

    vent_plot_img, vent_plot_data = form.generate_ventilation_plot(ventilation_transition_times=ventilation_transition_times[:-1],
                                        predictive_CO2=context['predictive_CO2'])

    # Add the transition times and CO2 plot to the results.
    context['transition_times'] = ventilation_transition_times
    context['CO2_plot_img'] = vent_plot_img
    context['CO2_plot_data'] = vent_plot_data

    return context
