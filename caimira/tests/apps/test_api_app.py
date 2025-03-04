import os
from tornado.testing import AsyncHTTPTestCase
from caimira.api.app import Application

class TestAPIApp(AsyncHTTPTestCase):
    def get_app(self):
        return Application(debug=True)

    def test_api_app(self):
        response = self.fetch("/")
        assert response.code == 200

    def test_cors(self):
        # test unset env
        response = self.fetch("/", method="OPTIONS", headers={"Origin": "http://example.com"})
        assert response.code == 204
        assert "Access-Control-Allow-Origin" not in response.headers

        # test None and empty value
        os.environ["CAIMIRA_ALLOWED_ORIGINS"] = ""
        response = self.fetch("/", method="OPTIONS", headers={"Origin": "http://example.com"})
        assert response.code == 204
        assert "Access-Control-Allow-Origin" not in response.headers

        # test allowing single domain
        os.environ["CAIMIRA_ALLOWED_ORIGINS"] = "http://example.com"
        response = self.fetch("/", method="OPTIONS", headers={"Origin": "http://example.com"})
        assert response.code == 204
        assert response.headers["Access-Control-Allow-Origin"] == "http://example.com"

        # test allowing multiple domains
        os.environ["CAIMIRA_ALLOWED_ORIGINS"] = "http://example.com, http://example2.com"
        response = self.fetch("/", method="OPTIONS", headers={"Origin": "http://example2.com"})
        assert response.code == 204
        assert response.headers["Access-Control-Allow-Origin"] == "http://example2.com"

        # test `null` value for Origin header
        os.environ["CAIMIRA_ALLOWED_ORIGINS"] = "http://example.com"
        response = self.fetch("/", method="OPTIONS", headers={"Origin": "null"})
        assert response.code == 204
        assert "Access-Control-Allow-Origin" not in response.headers
