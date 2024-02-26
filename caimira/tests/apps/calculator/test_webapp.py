import os
from pathlib import Path

import pytest
import tornado.testing

import caimira.apps.calculator
from caimira.apps.calculator.report_generator import generate_permalink

_TIMEOUT = float(os.environ.get("CAIMIRA_TESTS_CALCULATOR_TIMEOUT", 10.))


@pytest.fixture
def app():
    return caimira.apps.calculator.make_app()


async def test_homepage(http_server_client):
    response = await http_server_client.fetch('/')
    assert response.code == 200


async def test_calculator_form(http_server_client):
    # Both with and without a trailing slash.
    response = await http_server_client.fetch('/calculator')
    assert response.code == 200

    response = await http_server_client.fetch('/calculator/')
    assert response.code == 200


async def test_404(http_server_client):
    resp = await http_server_client.fetch('/doesnt-exist', raise_error=False)
    assert resp.code == 404


class TestBasicApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return caimira.apps.calculator.make_app()

    @tornado.testing.gen_test(timeout=_TIMEOUT)
    def test_report(self):
        requests = [
            self.http_client.fetch(self.get_url('/calculator/baseline-model/result')),
            # At the same time, request a non-report page (to check whether the report is blocking).
            self.http_client.fetch(self.get_url('/calculator/')),
        ]
        response = yield requests[0]
        other_response = yield requests[1]

        def end_time(resp):
            return resp.start_time + resp.request_time

        # The start time is before the other request,
        # but the end time is after the other request (because it takes longer
        # to process a report than a simple page).
        assert response.start_time < other_response.start_time
        assert end_time(response) > end_time(other_response)

        self.assertEqual(response.code, 200)
        assert 'CERN HSE' not in response.body.decode()
        assert 'expected number of new cases is' in response.body.decode()


class TestCernApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        cern_theme = Path(caimira.apps.calculator.__file__).parent.parent / 'themes' / 'cern'
        return caimira.apps.calculator.make_app(theme_dir=cern_theme)

    @tornado.testing.gen_test(timeout=_TIMEOUT)
    def test_report(self):
        response = yield self.http_client.fetch(self.get_url('/calculator/baseline-model/result'))
        self.assertEqual(response.code, 200)
        assert 'expected number of new cases is' in response.body.decode()


class TestOpenApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return caimira.apps.calculator.make_app(calculator_prefix="/mycalc")

    @tornado.testing.gen_test(timeout=_TIMEOUT)
    def test_report(self):
        response = yield self.http_client.fetch(self.get_url('/mycalc/baseline-model/result'))
        self.assertEqual(response.code, 200)

    def test_calculator_404(self):
        response = self.fetch('/calculator')
        assert response.code == 404


async def test_permalink_urls(http_server_client, baseline_form):
    base_url = 'proto://hostname/prefix'
    permalink_data = generate_permalink(base_url, lambda: "", lambda: "/calculator", baseline_form)
    expected = f'{base_url}/calculator?exposed_coffee_break_option={baseline_form.exposed_coffee_break_option}&'
    assert permalink_data['link'].startswith(expected)

    # We should get a 200 for the link.
    response = await http_server_client.fetch(permalink_data['link'].replace(base_url, ''))
    assert response.code == 200

    # And a 302 for the QR url itself. The redirected URL should be the same as
    # in the link.
    assert permalink_data['shortened'].startswith(base_url)
    response = await http_server_client.fetch(
        permalink_data['shortened'].replace(base_url, ''),
        max_redirects=0,
        raise_error=False,
    )
    assert response.code == 302
    assert response.headers['Location'] == permalink_data['link'].replace(base_url, '')


async def test_invalid_compressed_url(http_server_client, baseline_form):
    response = await http_server_client.fetch(
        '/_c/invalid-data',
        max_redirects=0,
        raise_error=False,
    )
    assert response.code == 400


class TestError500(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        class ProcessingErrorPage(caimira.apps.calculator.BaseRequestHandler):
            def get(self):
                raise ValueError('some unexpected error')
        app = caimira.apps.calculator.make_app()
        page = [
            (r'/', ProcessingErrorPage),
        ]
        return tornado.web.Application(page, **app.settings)

    def test_500(self):
        response = self.fetch('/')
        assert response.code == 500
        assert 'Unfortunately an error occurred when processing your request' in response.body.decode()


class TestCERNGenericPage(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        cern_theme = Path(caimira.apps.calculator.__file__).parent.parent / 'themes' / 'cern'
        app = caimira.apps.calculator.make_app(theme_dir=cern_theme)
        pages = [
            (r'/calculator/user-guide', caimira.apps.calculator.GenericExtraPage, {'active_page': 'calculator/user-guide', 'filename': 'userguide.html.j2'}),
            (r'/about', caimira.apps.calculator.GenericExtraPage, {'active_page': 'about', 'filename': 'about.html.j2'}),
        ]

        return tornado.web.Application(pages, **app.settings)

    @tornado.testing.gen_test(timeout=_TIMEOUT)
    def test_user_guide(self):
        response = yield self.http_client.fetch(self.get_url('/calculator/user-guide'))
        self.assertEqual(response.code, 200)

    @tornado.testing.gen_test(timeout=_TIMEOUT)
    def test_about(self):
        response = yield self.http_client.fetch(self.get_url('/about'))
        self.assertEqual(response.code, 200)

    def test_calculator_404(self):
        response = self.fetch('/calculator')
        assert response.code == 404
