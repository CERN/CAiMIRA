from pathlib import Path

import pytest
import tornado.testing

import cara.apps.calculator
from cara.apps.calculator.report_generator import generate_qr_code


@pytest.fixture
def app():
    return cara.apps.calculator.make_app()


async def test_homepage(http_server_client):
    response = await http_server_client.fetch('/')
    assert response.code == 200


async def test_calculator_form(http_server_client):
    # Both with and without a trailing slash.
    response = await http_server_client.fetch('/calculator')
    assert response.code == 200

    response = await http_server_client.fetch('/calculator/')
    assert response.code == 200


async def test_user_guide(http_server_client):
    resp = await http_server_client.fetch('/calculator/user-guide')
    assert resp.code == 200


@pytest.mark.xfail(reason="about page not yet implemented")
async def test_about(http_server_client):
    resp = await http_server_client.fetch('/about')
    assert resp.code == 200


async def test_404(http_server_client):
    resp = await http_server_client.fetch('/doesnt-exist', raise_error=False)
    assert resp.code == 404


class TestBasicApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return cara.apps.calculator.make_app()

    def test_report(self):
        response = self.fetch('/calculator/baseline-model/result')
        self.assertEqual(response.code, 200)
        assert 'CERN HSE rules' not in response.body.decode()
        assert 'the expected number of new cases is' in response.body.decode()


class TestCernApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        cern_theme = Path(cara.apps.calculator.__file__).parent / 'themes' / 'cern'
        return cara.apps.calculator.make_app(theme_dir=cern_theme)

    def test_report(self):
        response = self.fetch('/calculator/baseline-model/result')
        self.assertEqual(response.code, 200)
        assert 'CERN HSE rules' in response.body.decode()
        assert 'the expected number of new cases is' in response.body.decode()


async def test_qrcode_urls(http_server_client, baseline_form):
    prefix = 'proto://hostname/prefix'
    qr_data = generate_qr_code(prefix, baseline_form)
    expected = f'{prefix}/calculator?exposed_coffee_break_option={baseline_form.exposed_coffee_break_option}&'
    assert qr_data['link'].startswith(expected)

    # We should get a 200 for the link.
    response = await http_server_client.fetch(qr_data['link'].replace(prefix, ''))
    assert response.code == 200

    # And a 302 for the QR url itself. The redirected URL should be the same as
    # in the link.
    assert qr_data['qr_url'].startswith(prefix)
    response = await http_server_client.fetch(
        qr_data['qr_url'].replace(prefix, ''),
        max_redirects=0,
        raise_error=False,
    )
    assert response.code == 302
    assert response.headers['Location'] == qr_data['link'].replace(prefix, '')


async def test_invalid_compressed_url(http_server_client, baseline_form):
    response = await http_server_client.fetch(
        '/_c/invalid-data',
        max_redirects=0,
        raise_error=False,
    )
    assert response.code == 400


class TestError500(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        class ProcessingErrorPage(cara.apps.calculator.BaseRequestHandler):
            def get(self):
                raise ValueError('some unexpected error')
        app = cara.apps.calculator.make_app()
        page = [
            (r'/', ProcessingErrorPage),
        ]
        return tornado.web.Application(page, **app.settings)

    def test_500(self):
        response = self.fetch('/')
        assert response.code == 500
        assert 'Unfortunately an error occurred when processing your request' in response.body.decode()
