from math import inf
from cachetools import TTLCache, LRUCache, Cache


migration_cache = TTLCache(maxsize=inf, ttl=10.0)
admin_cache = LRUCache(maxsize=inf)
schedule_cache = Cache(maxsize=inf)
quiz_cache = TTLCache(maxsize=inf, ttl=61.0)
