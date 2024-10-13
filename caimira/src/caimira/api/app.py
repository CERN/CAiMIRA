# """
# Entry point for the CAiMIRA application
# """

import argparse
import tornado.ioloop
import tornado.web
import tornado.log
import logging

from caimira.api.routes.report_routes import VirusReportHandler, CO2ReportHandler

logging.basicConfig(format="%(message)s", level=logging.INFO)


class Application(tornado.web.Application):
    def __init__(self, debug):
        handlers = [
            (r"/co2_report", CO2ReportHandler),
            (r"/virus_report", VirusReportHandler),
        ]
        settings = dict(
            debug=debug,
        )
        super().__init__(handlers, **settings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-debug", help="Don't enable debug mode",
        action="store_false",
    )
    parser.add_argument(
        "--port",
        help="The port to listen on",
        default="8081"
    )
    args = parser.parse_args()
    debug = args.no_debug

    app = Application(debug=debug)
    app.listen(args.port)
    logging.info(f"Tornado API server is running on port {args.port}")
    tornado.ioloop.IOLoop.current().start()
