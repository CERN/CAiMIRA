import concurrent.futures
import dataclasses
import typing

from caimira.models import CO2DataModel
from .co2_model_generator import CO2FormData


@dataclasses.dataclass
class CO2ReportGenerator:
    
    def build_initial_plot(
            self,
            form: CO2FormData,
    ) -> dict:
        
        transition_times: list = form.find_change_points_with_pelt()
        ventilation_plot: str = form.generate_ventilation_plot(transition_times)

        context = {
            'CO2_plot': ventilation_plot,
            'transition_times': [round(el, 2) for el in transition_times],
        }

        return context
    
    def build_fitting_results(
            self,
            form: CO2FormData,
    ) -> dict:
        
        CO2model: CO2DataModel = form.build_model()

        # Ventilation times after user manipulation from the suggested ventilation state change times.
        ventilation_transition_times = CO2model.ventilation_transition_times

        # The result of the following method is a dict with the results of the fitting
        # algorithm, namely the breathing rate and ACH values. It also returns the
        # predictive CO2 result based on the fitting results.
        context: typing.Dict = dict(CO2model.CO2_fit_params())

        # Add the transition times and CO2 plot to the results.
        context['transition_times'] = ventilation_transition_times
        context['CO2_plot'] = form.generate_ventilation_plot(transition_times=ventilation_transition_times[:-1], 
                                                       predictive_CO2=context['predictive_CO2'])

        return context
    