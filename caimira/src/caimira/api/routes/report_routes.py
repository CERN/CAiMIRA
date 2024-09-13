import json
import traceback
import tornado.web
import sys

from caimira.api.controller.virus_report_controller import submit_virus_form
from caimira.api.controller.co2_report_controller import submit_CO2_form


class BaseReportHandler(tornado.web.RedirectHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)
        self.write({"message": kwargs.get('exc_info')[1].__str__()})


class VirusReportHandler(BaseReportHandler):
    def post(self):
        try:
            form_data = json.loads(self.request.body)
            report_data = submit_virus_form(form_data)

            response_data = {
                "status": "success",
                "message": "Results generated successfully",
                "report_data": report_data,
            }

            self.write(response_data)
        except Exception as e:
            traceback.print_exc()
            self.write_error(status_code=400, exc_info=sys.exc_info())


class CO2ReportHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def post(self):
        try:
            form_data = json.loads(self.request.body)
            report_data = submit_CO2_form(form_data)

            response_data = {
                "status": "success",
                "message": "Results generated successfully",
                "report_data": report_data,
            }

            self.write(response_data)
        except Exception as e:
            traceback.print_exc()
            self.write_error(status_code=400, exc_info=sys.exc_info())
