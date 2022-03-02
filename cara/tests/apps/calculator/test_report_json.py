import json

import tornado.testing

import cara.apps.calculator

_TIMEOUT = 40.


class TestCalculatorJsonResponse(tornado.testing.AsyncHTTPTestCase):
    def setUp(self):
        super().setUp()
        self.http_client.defaults['request_timeout'] = _TIMEOUT

    def get_app(self):
        return cara.apps.calculator.make_app(xsrf_cookies=False)

    @tornado.testing.gen_test(timeout=_TIMEOUT)
    def test_json_response(self):
        response = yield self.http_client.fetch(
            request=self.get_url("/calculator/report-json"),
            method="POST",
            headers={'content-type': 'application/json'},
            body=json.dumps(HTTP_POST_BODY)
        )
        self.assertEqual(response.code, 200)
        self.assertTrue('prob_inf' in json.loads(response.body).keys())


HTTP_POST_BODY = {
    "activity_type": "office",
    "air_changes": "",
    "air_supply": "",
    "calculator_version": "3.3.0",
    "ceiling_height": "2",
    "event_month": "January",
    "exposed_coffee_break_option": "coffee_break_0",
    "exposed_coffee_duration": "5",
    "exposed_finish": "17:30",
    "exposed_lunch_finish": "13:30",
    "exposed_lunch_option": "1",
    "exposed_lunch_start": "12:30",
    "exposed_start": "08:30",
    "floor_area": "20",
    "hepa_amount": "",
    "hepa_option": "0",
    "infected_coffee_break_option": "coffee_break_0",
    "infected_coffee_duration": "5",
    "infected_finish": "17:30",
    "infected_lunch_finish": "13:30",
    "infected_lunch_option": "1",
    "infected_lunch_start": "12:30",
    "infected_people": "1",
    "infected_start": "08:30",
    "location_latitude": "46.20833",
    "location_longitude": "6.14275",
    "location_name": "Geneva, CHE",
    "mask_type": "Type I",
    "mask_wearing_option": "mask_off",
    "opening_distance": "",
    "room_heating_option": "0",
    "room_number": "22E",
    "room_volume": "40",
    "simulation_name": "test4",
    "total_people": "2",
    "ventilation_type": "no_ventilation",
    "virus_type": "SARS_CoV_2_ALPHA",
    "volume_type": "room_volume_from_dimensions",
    "window_height": "",
    "window_opening_regime": "windows_open_permanently",
    "window_type": "window_sliding",
    "window_width": "",
    "windows_duration": "",
    "windows_frequency": "",
    "windows_number": ""
}
