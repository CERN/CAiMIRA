from caimira.api.routes.landing_routes import LandingPageHandler
from caimira.api.routes.report_routes import VirusReportHandler, CO2SuggestionsHandler, CO2ReportHandler

routes = [
    (r"/", LandingPageHandler),
    (r"/co2/transition_times", CO2SuggestionsHandler),
    (r"/co2/report", CO2ReportHandler),
    (r"/virus/report", VirusReportHandler),
]
