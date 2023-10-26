import os
import logging

from caimira.store.data_service import DataService

LOG = logging.getLogger(__name__)


class GlobalStore:
    '''
    Singleton pattern - ensure that there's only one instance of
    GlobalStore throughout the application
    '''

    _instance = None

    def __new__(self):
        if self._instance is None:
            self._instance = super().__new__(self)
            self._instance = {}

        return self._instance

    @classmethod
    async def populate_from_api(self):
        data_service_credentials = {
            'data_service_client_email': os.environ.get('DATA_SERVICE_CLIENT_EMAIL', None),
            'data_service_client_password': os.environ.get('DATA_SERVICE_CLIENT_PASSWORD', None),
        }
        data_service = None
        data_service_enabled = os.environ.get(
            'DATA_SERVICE_ENABLED', 'False').lower() == 'true'
        if data_service_enabled:
            try:
                data_service = DataService(data_service_credentials)
                self._instance = await data_service.fetch()
            except Exception as err:
                error_message = f"Something went wrong with the data service: {str(err)}"
                LOG.error(error_message, exc_info=True)

    @classmethod
    def get_data(self):
        return self._instance
