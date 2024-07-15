# """
# Entry point for the CAiMIRA application
# """

import tornado.ioloop
import tornado.web
import tornado.log
from tornado.options import define, options
import logging

from caimira.api.routes.report_routes import ReportHandler

define("port", default=8088, help="Port to listen on", type=int)

logging.basicConfig(format="%(message)s", level=logging.INFO)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/report", ReportHandler),
        ]
        settings = dict(
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)

if __name__ == "__main__":
    app = Application()
    app.listen(options.port)
    logging.info(f"Tornado server is running on port {options.port}")
    tornado.ioloop.IOLoop.current().start()
