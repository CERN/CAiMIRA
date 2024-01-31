import unittest
from unittest.mock import Mock, patch

from caimira.store.data_service import DataService


class DataServiceTests(unittest.TestCase):
    def setUp(self):
        # Set up any necessary test data or configurations
        self.data_service = DataService.create(host="https://dataservice.example.com")

    @patch("requests.get")
    def test_fetch_successful(self, mock_get):
        # Mock successful fetch response
        mock_get.return_value = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "dummy_data"}
        data = self.data_service._fetch()

        # Assert that the data is returned correctly
        self.assertEqual(data, {"data": "dummy_data"})

        # Verify that the fetch method was called with the expected arguments
        mock_get.assert_called_once_with(
            "https://dataservice.example.com/data",
            headers={
                "Content-Type": "application/json",
            },
        )

    @patch("requests.get")
    def test_fetch_error(self, mock_get):
        # Mock fetch error response
        mock_get.return_value = Mock()
        mock_get.return_value.status_code = 500

        # Call the fetch method
        data = self.data_service._fetch()

        # Assert that the fetch method returns None in case of an error
        self.assertIsNone(data)
