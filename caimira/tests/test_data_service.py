from dataclasses import dataclass

import unittest
from unittest.mock import patch, MagicMock
from tornado.httpclient import HTTPError

from caimira.apps.calculator.data_service import DataService

@dataclass
class MockResponse:
    body: str

class DataServiceTests(unittest.TestCase):
    def setUp(self):
        # Set up any necessary test data or configurations
        self.credentials = {
            "data_service_client_email": "test@example.com",
            "data_service_client_password": "password123"
        }
        self.data_service = DataService(self.credentials)

    @patch('caimira.apps.calculator.data_service.AsyncHTTPClient')
    async def test_login_successful(self, mock_http_client):
        # Mock successful login response
        mock_response = MockResponse('{"access_token": "dummy_token"}')
        mock_fetch = MagicMock(return_value=mock_response)
        mock_http_client.return_value.fetch = mock_fetch

        # Call the login method
        access_token = await self.data_service.login()

        # Assert that the access token is returned correctly
        self.assertEqual(access_token, "dummy_token")

        # Verify that the fetch method was called with the expected arguments
        mock_fetch.assert_called_once_with(
            url='https://caimira-data-api.app.cern.ch/login',
            method='POST',
            headers={'Content-type': 'application/json'},
            body='{"email": "test@example.com", "password": "password123"}'
        )

    @patch('caimira.apps.calculator.data_service.AsyncHTTPClient')
    async def test_login_error(self, mock_http_client):
        # Mock login error response
        mock_fetch = MagicMock(side_effect=HTTPError(500))
        mock_http_client.return_value.fetch = mock_fetch

        # Call the login method
        access_token = await self.data_service.login()

        # Assert that the login method returns None in case of an error
        self.assertIsNone(access_token)

    @patch('caimira.apps.calculator.data_service.AsyncHTTPClient')
    async def test_fetch_successful(self, mock_http_client):
        # Mock successful fetch response
        mock_response = MockResponse('{"data": "dummy_data"}')
        mock_fetch = MagicMock(return_value=mock_response)
        mock_http_client.return_value.fetch = mock_fetch

        # Call the fetch method with a mock access token
        access_token = "dummy_token"
        data = await self.data_service.fetch(access_token)

        # Assert that the data is returned correctly
        self.assertEqual(data, {"data": "dummy_data"})

        # Verify that the fetch method was called with the expected arguments
        mock_fetch.assert_called_once_with(
            url='https://caimira-data-api.app.cern.ch/data',
            method='GET',
            headers={'Authorization': 'Bearer dummy_token'}
        )

    @patch('caimira.apps.calculator.data_service.AsyncHTTPClient')
    async def test_fetch_error(self, mock_http_client):
        # Mock fetch error response
        mock_fetch = MagicMock(side_effect=HTTPError(404))
        mock_http_client.return_value.fetch = mock_fetch

        # Call the fetch method with a mock access token
        access_token = "dummy_token"
        data = await self.data_service.fetch(access_token)

        # Assert that the fetch method returns None in case of an error
        self.assertIsNone(data)
