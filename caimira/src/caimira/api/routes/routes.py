from caimira.api.routes.landing_routes import LandingPageHandler
from caimira.api.routes.report_routes import VirusReportHandler, CO2ReportHandler

routes = [
    (r"/", LandingPageHandler),
    (r"/co2_report", CO2ReportHandler),
    (r"/virus_report", VirusReportHandler),
]
