import pytest
import os
import re
import json

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
    
    if (data_service_credentials["data_service_client_email"] is None or 
        data_service_credentials["data_service_client_password"] is None):
        # Check if an error is thrown
        with pytest.raises(
            Exception,
            match=re.escape("DataService credentials not set")
        ):
            await DataService(data_service_credentials).fetch()
    
    else:
        # Set the credentials
        client_email = data_service_credentials["data_service_client_email"]
        client_password = data_service_credentials["data_service_client_password"]

        # Call the fetch request method
        response = await data_service.fetch_post_request(
            url=data_service.host + '/login',
            json_body={ "email": f"{client_email}", "password": f"{client_password}"}
        )

        # Assert the response is not None
        assert response is not None
        assert response.code == 200

        response_body = json.loads(response.body)

        # Call the get request method
        response = await data_service.fetch_get_request(
            url=data_service.host + '/data',
            headers={'Authorization': f'Bearer {response_body["access_token"]}'},
        )

        # Assert the response is not None
        assert response is not None
        assert response.code == 200

        response_body = json.loads(response.body)

        # Assert that the response contains data
        assert "data" in response_body
        assert isinstance(response_body["data"], dict)
        assert response_body["data"] is not None
