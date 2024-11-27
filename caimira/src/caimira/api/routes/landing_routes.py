from caimira.api.routes.base_handler import BaseRequestHandler

from caimira import __version__


class LandingPageHandler(BaseRequestHandler):
    def get(self):
        self.write("<h1>Welcome to the CAiMIRA REST API</h1>")
        self.write(f"<h4>Code Version: {__version__}</h4>")
        self.write("<h4>Official GitLab: <a href='https://gitlab.cern.ch/caimira/caimira' target='_blank'>https://gitlab.cern.ch/caimira/caimira</a></h4>")
        self.write("<h4>Documentation: <a href='https://caimira.docs.cern.ch/' target='_blank'>https://caimira.docs.cern.ch/</a><h4>")
