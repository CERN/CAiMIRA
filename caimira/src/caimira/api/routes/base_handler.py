import os
import tornado.web


class CorsHandler(tornado.web.RequestHandler):
    """Handler to manage CORS (Cross-Origin Resource Sharing) configuration.

    This handler implements CORS support by setting appropriate headers for cross-origin requests.
    It checks allowed origins against environment variable CAIMIRA_ALLOWED_ORIGINS and enables
    CORS for matching origins.
    """

    def set_default_headers(self):
        allowed_origins = os.environ.get("CAIMIRA_ALLOWED_ORIGINS", None)
        request_origin = self.request.headers.get("Origin", None)  # can have value `null`
        if allowed_origins and request_origin:
            allowed_origins = [origin.lower().strip() for origin in allowed_origins.split(",")]
            if request_origin.lower() in allowed_origins:
                self.set_header("Access-Control-Allow-Origin", request_origin)

    def options(self, *args):
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_status(204)  # No Content


class BaseRequestHandler(CorsHandler):
    """Base handler for HTTP requests extending CorsHandler.

    This class provides base functionality for handling HTTP requests with CORS support.
    It includes error handling capabilities by overriding the write_error method.
    """

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)
        self.write({"message": kwargs.get('exc_info')[1].__str__()})
