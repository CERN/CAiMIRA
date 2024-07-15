import json
import traceback
import tornado.web

from caimira.api.controller.report_controller import submit_virus_form

class ReportHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

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
            self.set_status(400)
            self.write({"message": str(e)})
