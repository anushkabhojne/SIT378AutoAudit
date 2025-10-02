"""
Cache Manager for Data Provider

Provides caching functionality to reduce redundant Microsoft Graph API calls.

Author: Senior Lead, AutoAudit
"""

import asyncio
import logging
from typing import Any, Optional
import aioredis

class CacheManager:
    
    def __init__(self, redis_url: str = "redis://localhost", ttl_seconds: int = 300):
        self._redis_url = redis_url
        self._ttl = ttl_seconds
        self._redis = None
        self._logger = logging.getLogger(self.__class__.__name__)

    async def connect(self):
        
        if self._redis is None:
            self._redis = await aioredis.from_url(self._redis_url)
            self._logger.info(f"Connected to Redis at {self._redis_url}")

    async def get(self, key: str) -> Optional[Any]:
        
        if self._redis is None:
            await self.connect()
        
        try:
            data = await self._redis.get(key)
        
            if data:
                self._logger.debug(f"Cache hit for key: {key}")
                return data
        
            else:
                self._logger.debug(f"Cache miss for key: {key}")
                return None
        
        except Exception as e:
            self._logger.error(f"Error getting cache key {key}: {e}")
            return None

    async def set(self, key: str, value: Any):
        
        if self._redis is None:
            await self.connect()
        
        try:
            await self._redis.set(key, value, ex=self._ttl)
            self._logger.debug(f"Cache set for key: {key} with TTL {self._ttl}s")
        
        except Exception as e:
            self._logger.error(f"Error setting cache key {key}: {e}")

    async def close(self):
        
        if self._redis:
            await self._redis.close()
            self._logger.info("Redis connection closed")
