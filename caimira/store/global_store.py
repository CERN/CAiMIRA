import os

from caimira.store.data_service import DataService


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
            data_service = DataService(data_service_credentials)
            self._instance = await data_service.fetch()
        else:
            print('Data service not enabled.')

    @classmethod
    def get_data(self):
        return self._instance
