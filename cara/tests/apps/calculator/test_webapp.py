import pytest

from cara.apps.calculator import make_app
from cara.apps.calculator.report_generator import generate_qr_code


@pytest.fixture
def app():
    return make_app()


async def test_homepage(http_server_client):
    response = await http_server_client.fetch('/')
    assert response.code == 200


async def test_calculator(http_server_client):
    # Both with and without a trailing slash.
    response = await http_server_client.fetch('/calculator')
    assert response.code == 200

    response = await http_server_client.fetch('/calculator/')
    assert response.code == 200


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
