import dataclasses
import json
import logging

from tornado.httpclient import AsyncHTTPClient, HTTPRequest

LOG = logging.getLogger(__name__)


@dataclasses.dataclass
class DataService():
    '''
    Responsible for establishing a connection to a 
    database through a REST API by handling authentication 
    and fetching data. It utilizes the Tornado web framework
    for asynchronous HTTP requests.
    '''
    # Credentials used for authentication
    credentials: dict

    # Host URL for the CAiMIRA Data Service API
    host: str = 'https://caimira-data-api.app.cern.ch'
    
    async def login(self):
        client_email = self.credentials["data_service_client_email"]
        client_password = self.credentials['data_service_client_password']

        if (client_email == None or client_password == None):
            # If the credentials are not defined, an exception is raised.
            raise Exception("DataService credentials not set")
            
        http_client = AsyncHTTPClient()
        headers = {'Content-type': 'application/json'}
        json_body = { "email": f"{client_email}", "password": f"{client_password}"}

        response = await http_client.fetch(HTTPRequest(
            url=self.host + '/login',
            method='POST',
            headers=headers,
            body=json.dumps(json_body),
        ),
        raise_error=True)

        return json.loads(response.body)['access_token']
    
    async def fetch(self, access_token: str):
        http_client = AsyncHTTPClient()
        headers = {'Authorization': f'Bearer {access_token}'}

        response = await http_client.fetch(HTTPRequest(
            url=self.host + '/data',
            method='GET',
            headers=headers,
        ),
        raise_error=True)

        return json.loads(response.body)
    