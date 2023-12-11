import logging
import typing
from datetime import datetime, timedelta, timezone

import jwt
import requests

from caimira.store.data_registry import DataRegistry

logger = logging.getLogger("DATA")


class DataService:
    """Responsible for fetching data from the data service endpoint."""

    # Cached access token
    _access_token: typing.Optional[str] = None

    def __init__(
        self,
        credentials: typing.Dict[str, typing.Optional[str]],
        host: str,
    ):
        self._credentials = credentials
        self._host = host

    @classmethod
    def create(cls, credentials: typing.Dict[str, typing.Optional[str]], host: str = "https://caimira-data-api.app.cern.ch"):
        """Factory."""
        return cls(credentials, host)

    def _is_valid(self, access_token):
        """Return True if the expiration token is still valid."""
        try:
            decoded = jwt.decode(
                access_token, algorithms=["HS256"], options={"verify_signature": False}
            )
            expiration_timestamp = decoded["exp"]
            expiration = datetime.utcfromtimestamp(expiration_timestamp).replace(
                tzinfo=timezone.utc
            )
            now = datetime.now(timezone.utc)
            is_valid = now < expiration - timedelta(
                seconds=5
            )  #  5 seconds time delta to avoid timing issues

            logger.debug(f"Access token expiration: {expiration_timestamp}. Is valid? {is_valid}")

            return is_valid
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired.")
        except jwt.InvalidTokenError:
            logger.warning("JWT token invalid.")
        return False

    def _login(self):
        logger.debug(f"Access token: {self._access_token}")

        if self._access_token and self._is_valid(self._access_token):
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
                logger.debug(f"Obtained new access token: {self._access_token}")
                return self._access_token
            else:
                logger.error(
                    f"Unexpected error on login. Response status code: {response.status_code}, body: f{response.text}"
                )
        except requests.exceptions.RequestException as e:
            logger.exception(e)

    def _fetch(self):
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
                json_body = response.json()
                logger.debug(f"Data service call: {url}. Response: {json_body}")
                return json_body
            else:
                logger.error(
                    f"Unexpected error when fetching data. Response status code: {response.status_code}, body: f{response.text}"
                )
        except requests.exceptions.RequestException as e:
            logger.exception(e)


    def update_registry(self, registry: DataRegistry):
        data = self._fetch()
        if data:
            registry.update(data["data"], version=data["version"])
        else:
            logger.error("Could not fetch fresh data from the data service.")
