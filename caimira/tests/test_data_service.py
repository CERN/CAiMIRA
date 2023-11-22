import time
import unittest
from unittest.mock import Mock, patch

import jwt

from caimira.store.data_service import DataService


class DataServiceTests(unittest.TestCase):
    def setUp(self):
        # Set up any necessary test data or configurations
        self.credentials = {"email": "test@example.com", "password": "password123"}
        self.data_service = DataService(self.credentials)

    def test_jwt_expiration(self):
        is_valid = self.data_service._is_valid(None)
        self.assertFalse(is_valid)

        now = time.time()

        encoded = jwt.encode({"exp": now - 10}, "very secret", algorithm="HS256")
        is_valid = self.data_service._is_valid(encoded)
        self.assertFalse(is_valid)

        encoded = jwt.encode({"exp": now}, "very secret", algorithm="HS256")
        is_valid = self.data_service._is_valid(encoded)
        self.assertFalse(is_valid)

        encoded = jwt.encode({"exp": now + 10}, "very secret", algorithm="HS256")
        is_valid = self.data_service._is_valid(encoded)
        self.assertTrue(is_valid)

    @patch("requests.post")
    def test_login_successful(self, mock_post):
        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "dummy_token"}
        mock_post.return_value = mock_response

        # Call the login method
        access_token = self.data_service._login()

        # Assert that the access token is returned correctly
        self.assertEqual(access_token, "dummy_token")

        # Verify that the fetch method was called with the expected arguments
        mock_post.assert_called_once_with(
            "https://caimira-data-api.app.cern.ch/login",
            json=dict(email="test@example.com", password="password123"),
            headers={"Content-Type": "application/json"},
        )

    @patch("requests.post")
    def test_login_error(self, mock_post):
        # Mock login error response
        mock_post.return_value = Mock()
        mock_post.return_value.status_code = 500

        # Call the login method
        access_token = self.data_service._login()

        # Assert that the login method returns None in case of an error
        self.assertIsNone(access_token)

    @patch("requests.get")
    @patch.object(DataService, "_login")
    def test_fetch_successful(self, mock_login, mock_get):
        # Mock successful fetch response
        mock_get.return_value = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "dummy_data"}
        # Call the fetch method with a mock access token
        mock_login.return_value = "dummy_token"
        data = self.data_service.fetch()

        # Assert that the data is returned correctly
        self.assertEqual(data, {"data": "dummy_data"})

        # Verify that the fetch method was called with the expected arguments
        mock_get.assert_called_once_with(
            "https://caimira-data-api.app.cern.ch/data",
            headers={
                "Authorization": "Bearer dummy_token",
                "Content-Type": "application/json",
            },
        )

    @patch("requests.get")
    @patch.object(DataService, "_login")
    def test_fetch_error(self, mock_login, mock_get):
        # Mock fetch error response
        mock_get.return_value = Mock()
        mock_get.return_value.status_code = 500

        # Call the fetch method with a mock access token
        mock_login.return_value = "dummy_token"
        data = self.data_service.fetch()

        # Assert that the fetch method returns None in case of an error
        self.assertIsNone(data)
