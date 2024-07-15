import functools


def method_cache(fn):
    """
    A decorator for instance based caching.

    Unlike lru_cache / memoization, this allows us to not have to have the
    instance itself be hashable - only the arguments must be so.

    The cache is stored as a dictionary in a private attribute on the instance
    with the name ``_cache_{func_name}``.

    """
    cache_name = f'_cache_{fn.__name__}'

    @functools.wraps(fn)
    def cached_method(self, *args, **kwargs):
        cache = getattr(self, cache_name, None)
        if cache is None:
            cache = {}
            object.__setattr__(self, cache_name, cache)
        cache_key = hash(args + tuple(kwargs.items()))
        if cache_key not in cache:
            cache[cache_key] = fn(self, *args, **kwargs)
        return cache[cache_key]
    return cached_method
