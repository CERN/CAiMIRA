import pytest
import os
import re

from caimira.apps.calculator.data_service import DataService

@pytest.fixture
def data_service_enabled():
    return os.environ.get('DATA_SERVICE_ENABLED', 'False').lower() == 'true'

@pytest.fixture
def data_service_credentials():
    return {
        'data_service_client_email': os.environ.get('DATA_SERVICE_CLIENT_EMAIL', None),
        'data_service_client_password': os.environ.get('DATA_SERVICE_CLIENT_PASSWORD', None),
    }    

async def test_fetch_method(data_service_enabled, data_service_credentials):
    if not data_service_enabled:
        return
    
    # Initialize the DataService
    data_service = DataService(data_service_credentials)
    
    if (data_service_credentials["data_service_client_email"] == None or 
        data_service_credentials["data_service_client_password"] == None):
        # Check if an error is thrown
        with pytest.raises(
            Exception,
            match=re.escape("DataService credentials not set")
        ):
            await DataService(data_service_credentials).fetch()

    else:
        # Call the fetch method
        response = await data_service.fetch()

        # Assert the response is not None
        assert response is not None

        # Assert that the response contains data
        assert "data" in response
        assert isinstance(response["data"], dict)
        assert response["data"] is not None
