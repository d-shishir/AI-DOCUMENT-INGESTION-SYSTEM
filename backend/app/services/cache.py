import time
import threading
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class InMemoryCache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str):
        if not settings.ENABLE_CACHE:
            return None
            
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._misses += 1
                return None
            
            val, expiry = item
            if expiry is not None and time.time() > expiry:
                # Clean up expired item
                del self._cache[key]
                self._misses += 1
                return None
                
            self._hits += 1
            return val

    def set(self, key: str, value, ttl: int = None):
        if not settings.ENABLE_CACHE:
            return
            
        if ttl is None:
            ttl = settings.CACHE_TTL_SECONDS
            
        expiry = time.time() + ttl if ttl > 0 else None
        
        with self._lock:
            self._cache[key] = (value, expiry)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
        logger.info("In-memory cache cleared successfully.")

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

# Global cache instance
cache_store = InMemoryCache()
