from cachetools import TTLCache
import typing

from caimira.apps.calculator.data_service import DataService

class GlobalStore():
    def __init__(self, data_service):
        self.data_service = data_service
        self.global_store = {}
        self.cache = TTLCache(maxsize=100, ttl=300)

    # Singleton usage
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init_singleton(*args, **kwargs)
        return cls._instance

    def __init_singleton(self, data_service_instance: DataService):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.global_store = {}
            self.cache = TTLCache(maxsize=100, ttl=300)

    def get_data(self, api_endpoint):
        # Check if data is in cache
        cached_data = self.cache.get(api_endpoint)
        if cached_data:
            return cached_data

        # If not in cache, follow global store procedure
        global_data = self.global_store.get(api_endpoint)
        if global_data:
            # If found in global store, update cache and return
            self.cache[api_endpoint] = global_data
            return global_data

        # If not found in global store, fetch from API        
        data = self.fetch_data_from_api(api_endpoint)

        return data

    async def fetch_data_from_api(self, api_endpoint):
        # Check if data is already in the cache
        cached_data = self.cache.get(api_endpoint)
        if cached_data:
            return cached_data

        # If not in cache, fetch from API
        data = await self.data_service.fetch()

        # Store in global store
        self.global_store[api_endpoint] = data

        # Store in cache
        self.cache[api_endpoint] = data

        return data
    