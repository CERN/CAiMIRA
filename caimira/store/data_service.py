import dataclasses
import json
import logging
import typing

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

    # Cached access token
    _access_token: typing.Optional[str] = None

    def _is_valid(self, access_token):
        # decode access_token
        # check validity
        return False

    async def _login(self):
        if self._is_valid(self._access_token):
            return self._access_token

        # invalid access_token, fetch it again
        client_email = self.credentials["data_service_client_email"]
        client_password = self.credentials['data_service_client_password']

        if (client_email == None or client_password == None):
            # If the credentials are not defined, an exception is raised.
            raise Exception("DataService credentials not set")

        http_client = AsyncHTTPClient()
        headers = {'Content-type': 'application/json'}
        json_body = {"email": f"{client_email}",
                     "password": f"{client_password}"}

        response = await http_client.fetch(HTTPRequest(
            url=self.host + '/login',
            method='POST',
            headers=headers,
            body=json.dumps(json_body),
        ),
            raise_error=True)

        self._access_token = json.loads(response.body)['access_token']
        return self._access_token

    async def fetch(self):
        access_token = await self._login()

        http_client = AsyncHTTPClient()
        headers = {'Authorization': f'Bearer {access_token}'}

        response = await http_client.fetch(HTTPRequest(
            url=self.host + '/data',
            method='GET',
            headers=headers,
        ),
            raise_error=True)

        return json.loads(response.body)
