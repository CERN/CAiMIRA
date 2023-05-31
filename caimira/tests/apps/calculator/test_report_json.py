import json

import tornado.testing

import caimira.apps.calculator
from caimira.apps.calculator import model_generator

_TIMEOUT = 30.


class TestCalculatorJsonResponse(tornado.testing.AsyncHTTPTestCase):
    def setUp(self):
        super().setUp()
        self.http_client.defaults['request_timeout'] = _TIMEOUT

    def get_app(self):
        return caimira.apps.calculator.make_app()

    @tornado.testing.gen_test(timeout=_TIMEOUT)
    def test_json_response(self):
        response = yield self.http_client.fetch(
            request=self.get_url("/calculator/report-json"),
            method="POST",
            headers={'content-type': 'application/json'},
            body=json.dumps(model_generator.baseline_raw_form_data())
        )
        self.assertEqual(response.code, 200)

        data = json.loads(response.body)
        self.assertIsInstance(data['prob_inf'], float)
        self.assertIsInstance(data['expected_new_cases'], float)

