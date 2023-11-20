import logging
import os
import typing

import requests

from .configuration import config

logger = logging.getLogger(__name__)


class DataService:
    """Responsible for fetching data from the data service endpoint."""

    # Cached access token
    _access_token: typing.Optional[str] = None

    def __init__(
        self,
        credentials: typing.Dict[str, str],
        host: str = "https://caimira-data-api.app.cern.ch",
    ):
        self._credentials = credentials
        self._host = host

    def _is_valid(self, access_token):
        # decode access_token
        # check validity
        return False

    def _login(self):
        if self._is_valid(self._access_token):
            return self._access_token

        # invalid access_token, fetch it again
        client_email = self._credentials["email"]
        client_password = self._credentials["password"]

        if client_email == None or client_password == None:
            # If the credentials are not defined, an exception is raised.
            raise Exception("DataService credentials not set")

        url = f"{self._host}/login"
        headers = {"Content-Type": "application/json"}
        json_body = dict(email=client_email, password=client_password)

        try:
            response = requests.post(url, json=json_body, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                self._access_token = response.json()["access_token"]
                return self._access_token
            else:
                logger.error(
                    f"Unexpected error on login. Response status code: {response.status_code}, body: f{response.text}"
                )
        except requests.exceptions.RequestException as e:
            logger.exception(e)

    def fetch(self):
        access_token = self._login()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{self._host}/data"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Unexpected error when fetching data. Response status code: {response.status_code}, body: f{response.text}"
                )
        except requests.exceptions.RequestException as e:
            logger.exception(e)


def update_configuration():
    data_service_enabled = os.environ.get("DATA_SERVICE_ENABLED", "False")
    is_enabled = data_service_enabled.lower() == "true"
    if is_enabled:
        credentials = {
            "email": os.environ.get("DATA_SERVICE_CLIENT_EMAIL", None),
            "password": os.environ.get("DATA_SERVICE_CLIENT_PASSWORD", None),
        }
        data_service = DataService(credentials)
        data = data_service.fetch()
        if data:
            config.update(data["data"])
        else:
            logger.error("Could not fetch fresh data from the data service.")
