import dataclasses

import caimira.calculator.report.co2_report_data as co2_rep_data
from caimira.calculator.validators.co2.co2_validator import CO2FormData

@dataclasses.dataclass
class CO2ReportGenerator:
    
    def build_initial_plot(self, form: CO2FormData):
        return co2_rep_data.build_initial_plot(form=form)
    
    def build_fitting_results(self, form: CO2FormData):
        return co2_rep_data.build_fitting_results(form=form)
    