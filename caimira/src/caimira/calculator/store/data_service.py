import logging
import typing
import requests

from ..store.data_registry import DataRegistry

logger = logging.getLogger("DATA")


class DataService:
    """Responsible for fetching data from the data service endpoint."""

    # Cached access token
    _access_token: typing.Optional[str] = None

    def __init__(
        self,
        host: str,
    ):
        self._host = host

    @classmethod
    def create(cls, host: str = "https://caimira-data-api-qa.app.cern.ch"):
        """Factory."""
        return cls(host)

    def _fetch(self):

        headers = {
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
