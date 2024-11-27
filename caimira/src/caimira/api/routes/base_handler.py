import tornado.web


class BaseRequestHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)
        self.write({"message": kwargs.get('exc_info')[1].__str__()})
        