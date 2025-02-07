import json
import traceback
import sys
from caimira.api.routes.base_handler import BaseRequestHandler
from caimira.api.controller.virus_report_controller import submit_virus_form
from caimira.api.controller.co2_report_controller import request_CO2_transition_times, request_CO2_report


class VirusReportHandler(BaseRequestHandler):
    def post(self):
        try:
            form_data = json.loads(self.request.body)
            arguments = self.request.arguments
            # Report generation parallelism argument
            try:
                report_generation_parallelism = int(arguments['report_generation_parallelism'][0])
            except (ValueError, IndexError, KeyError):
                report_generation_parallelism = None

            report_data = submit_virus_form(form_data, report_generation_parallelism)

            response_data = {
                "status": "success",
                "message": "Results generated successfully",
                "results": report_data,
            }

            self.write(response_data)
        except Exception as e:
            traceback.print_exc()
            self.write_error(status_code=400, exc_info=sys.exc_info())


class CO2SuggestionsHandler(BaseRequestHandler):
    def post(self):
        try:
            form_data = json.loads(self.request.body)
            suggestion_data = request_CO2_transition_times(form_data)

            response_data = {
                "status": "success",
                "message": "Results generated successfully",
                "results": suggestion_data,
            }

            self.write(response_data)
        except Exception as e:
            traceback.print_exc()
            self.write_error(status_code=400, exc_info=sys.exc_info())


class CO2ReportHandler(BaseRequestHandler):
    def post(self):
        try:
            form_data = json.loads(self.request.body)
            report_data = request_CO2_report(form_data)

            response_data = {
                "status": "success",
                "message": "Results generated successfully",
                "results": report_data,
            }

            self.write(response_data)
        except Exception as e:
            traceback.print_exc()
            self.write_error(status_code=400, exc_info=sys.exc_info())
