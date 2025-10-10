"""
AutoAudit Configuration Management System - Cache Manager

This module implements comprehensive Redis-based caching functionality for the AutoAudit
Configuration Management System, providing high-performance distributed caching with
advanced features including cache warming, intelligent invalidation, and comprehensive
monitoring capabilities.

The CacheManager class handles all caching operations including configuration storage,
retrieval, invalidation strategies, pub/sub messaging for real-time updates, and
performance optimisation for distributed microservices architectures.

Author: Senior Lead, AutoAudit
Owner: Backend Team, AutoAudit
"""

import asyncio
import json
import logging
import pickle
import time
import traceback
import hashlib
from typing import Any, Dict, List, Optional, Union, Set, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import msgpack

from .exceptions import CacheError
from .models import CacheStatistics, CacheInvalidationEvent

#Configuring module-specific logging with detailed context
logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    
    """
    Cache configuration parameters with comprehensive Redis connection and performance settings.
    
    This dataclass encapsulates all Redis connection parameters, clustering configuration,
    performance tuning settings, and operational parameters required for enterprise-grade
    distributed caching operations.
    """

    redis_url: str
    cluster_mode: bool = False
    max_connections: int = 100
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, int] = None
    decode_responses: bool = False
    encoding: str = 'utf-8'
    encoding_errors: str = 'strict'
    connection_pool_class: type = ConnectionPool
    
    def __post_init__(self):
        
        """Initialise default socket keepalive options for optimal connection management."""

        if self.socket_keepalive_options is None:
            
            self.socket_keepalive_options = {
                'TCP_KEEPIDLE': 1,
                'TCP_KEEPINTVL': 3,
                'TCP_KEEPCNT': 5
            }

class CacheManager:
    
    """
    Comprehensive Redis-based cache management class providing enterprise-grade distributed
    caching with advanced features including intelligent cache warming, hierarchical invalidation,
    pub/sub messaging, and comprehensive performance monitoring.
    
    This class implements all caching operations required for configuration management including
    multi-level caching strategies, automatic failover, cluster support, and detailed analytics
    for performance optimisation and capacity planning.
    """

    def __init__(self, redis_url: str, cluster_mode: bool = False, max_connections: int = 100,
                 retry_on_timeout: bool = True, health_check_interval: int = 30,
                 socket_timeout: float = 5.0, socket_connect_timeout: float = 5.0):
        
        """
        Initialise CacheManager with comprehensive Redis configuration parameters.
        
        Args:
            redis_url: Redis connection URL (redis://host:port or redis+cluster://host:port)
            cluster_mode: Enable Redis Cluster mode for horizontal scaling
            max_connections: Maximum number of connections in the connection pool
            retry_on_timeout: Enable automatic retry on timeout errors
            health_check_interval: Health check interval in seconds
            socket_timeout: Socket operation timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
        """

        self.config = CacheConfig(
            redis_url = redis_url,
            cluster_mode = cluster_mode,
            max_connections = max_connections,
            retry_on_timeout = retry_on_timeout,
            health_check_interval = health_check_interval,
            socket_timeout = socket_timeout,
            socket_connect_timeout = socket_connect_timeout
        )
        
        #Initialising the Redis client and connection management
        self._client: Optional[Union[redis.Redis, RedisCluster]] = None
        self._pubsub_client: Optional[redis.Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None
        
        #Initialising the caching statistics and performance metrics
        self._statistics = CacheStatistics(
            hits = 0,
            misses = 0,
            sets = 0,
            deletes = 0,
            evictions = 0,
            expired_keys = 0,
            memory_usage = 0,
            connection_count = 0,
            average_response_time = 0.0,
            error_count = 0
        )
        
        #Initialising cache warming and maintenance tracking
        self._cache_warming_patterns = {}
        self._invalidation_subscribers = {}
        self._maintenance_tasks = set()
        
        #Initialising the performance optimization settings

        #Compressing values larger than 1KB
        self._compression_threshold = 1024  

        #Using MessagePack for efficient serialisation
        self._serialization_method = 'msgpack'  

        #Default 5-minute TTL
        self._default_ttl = 300  

        #10MB max value size
        self._max_value_size = 10 * 1024 * 1024  
        
        logger.info(
            f"CacheManager initialized with Redis URL: {redis_url}",
            
            extra = {
                "cluster_mode": cluster_mode,
                "max_connections": max_connections,
                "health_check_interval": health_check_interval
            }
        )

    async def initialize(self) -> None:
        
        """
        Initialise Redis connections and perform cache system validation.
        
        This method establishes Redis connections, validates cluster configuration,
        initialises pub/sub channels, and prepares the cache system for operations.
        
        Raises:
            CacheError: If cache initialization fails
        """

        try:
            logger.info("Initialising the Redis cache connections")
            
            #Parsing the Redis URL and extracting the connection parameters
            redis_params = self._parse_redis_url(self.config.redis_url)
            
            #Initialising the connection pool with comprehensive configuration
            if self.config.cluster_mode:
                
                #Initialising the Redis Cluster client for distributed caching
                self._client = RedisCluster(
                    host=redis_params['host'],
                    port=redis_params['port'],
                    password = redis_params.get('password'),
                    socket_timeout = self.config.socket_timeout,
                    socket_connect_timeout = self.config.socket_connect_timeout,
                    socket_keepalive = self.config.socket_keepalive,
                    socket_keepalive_options = self.config.socket_keepalive_options,
                    health_check_interval = self.config.health_check_interval,
                    retry_on_timeout = self.config.retry_on_timeout,
                    decode_responses = self.config.decode_responses,
                    encoding = self.config.encoding,
                    encoding_errors = self.config.encoding_errors
                )
                
                self._client = redis.Redis(connection_pool=self._connection_pool)
            
            #Testing Redis connectivity with comprehensive validation
            await self._validate_redis_connection()
            
            #Initialising the pub/sub client for real-time invalidation notifications
            await self._initialize_pubsub()
            
            #Initialising the cache warming mechanisms
            await self._initialize_cache_warming()
            
            #Starting background maintenance tasks
            await self._start_maintenance_tasks()
            
            logger.info("Redis cache initialization completed successfully")
            
        except RedisError as e:
            
            logger.error(
                f"Redis connection error during initialization: {str(e)}",
                
                extra = {
                    "redis_url": self.config.redis_url,
                    "cluster_mode": self.config.cluster_mode,
                    "traceback": traceback.format_exc()
                }
            )

            raise CacheError(f"Cache initialisation failed: {str(e)}")
            
        except Exception as e:
            
            logger.error(
                f"Unexpected error during cache initialisation: {str(e)}",
                
                extra = {
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )

            raise CacheError(f"Cache initialisation failed: {str(e)}")

    def _parse_redis_url(self, redis_url: str) -> Dict[str, Any]:
        
        """
        Parse Redis URL into connection parameters with comprehensive validation.
        
        Args:
            redis_url: Redis connection URL in standard format
            
        Returns:
            Dictionary containing parsed connection parameters
        """

        from urllib.parse import urlparse
        
        parsed = urlparse(redis_url)
        
        if parsed.scheme not in ['redis', 'redis+cluster', 'rediss']:
            raise CacheError(f"Unsupported Redis URL scheme: {parsed.scheme}")
        
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 6379,
            'password': parsed.password,
            'db': int(parsed.path.lstrip('/')) if parsed.path else 0,
            'ssl': parsed.scheme == 'rediss'
        }

    async def _validate_redis_connection(self) -> None:
        
        """
        Validate Redis connection with comprehensive connectivity and functionality testing.
        
        Raises:
            CacheError: If Redis connection validation fails
        """

        try:
            #Testing basic connectivity
            pong_response = await self._client.ping()
            
            if pong_response != True:
                raise CacheError("Redis ping test failed")
            
            #Testing basic operations
            test_key = "autoaudit:cache:health_check"
            test_value = "connection_test"
            
            await self._client.set(test_key, test_value, ex=60)
            retrieved_value = await self._client.get(test_key)
            
            if retrieved_value.decode('utf-8') != test_value:
                raise CacheError("Redis read/write test failed")
            
            await self._client.delete(test_key)
            
            #Testing Redis info and configuration
            info = await self._client.info()
            redis_version = info.get('redis_version', 'unknown')
            memory_usage = info.get('used_memory_human', 'unknown')
            
            logger.info(
                f"Redis connection validated successfully",
                
                extra = {
                    "redis_version": redis_version,
                    "memory_usage": memory_usage,
                    "connected_clients": info.get('connected_clients', 0)
                }
            )
            
        except RedisError as e:
            raise CacheError(f"Redis connection validation failed: {str(e)}")

    async def _initialize_pubsub(self) -> None:
        
        """
        Initialise Redis pub/sub client for real-time cache invalidation notifications.
        
        This method sets up dedicated pub/sub connections for broadcasting and receiving
        cache invalidation events across the distributed system.
        """

        try:
            
            #Creating a dedicated pub/sub client to avoid blocking the main client
            if self.config.cluster_mode:
                
                #Cluster mode requires special handling for pub/sub
                self._pubsub_client = self._client
            
            else:
                self._pubsub_client = redis.Redis(connection_pool=self._connection_pool)
            
            #Testing the pub/sub functionality
            pubsub = self._pubsub_client.pubsub()
            await pubsub.subscribe('autoaudit:cache:test')
            
            #Publishing a test message
            await self._pubsub_client.publish('autoaudit:cache:test', 'initialization_test')
            
            #Verifying the message's receipt
            message = await pubsub.get_message(timeout=5.0)
            if message and message['type'] == 'message':
                logger.info("Pub/sub functionality validated successfully")
            
            await pubsub.unsubscribe('autoaudit:cache:test')
            await pubsub.close()
            
        except Exception as e:
            logger.warning(f"Pub/sub initialization warning: {str(e)}")
            #Pub/sub failure is non-fatal but reduces functionality

    async def _initialize_cache_warming(self) -> None:
        
        """
        Initialise cache warming patterns and preload frequently accessed data.
        
        This method sets up cache warming strategies for configuration data that is
        frequently accessed, reducing cache misses and improving response times.
        """
        
        try:
            #Defining cache warming patterns for configuration data
            self._cache_warming_patterns = {
                'config:*:production:*': {'ttl': 600, 'priority': 'high'},
                'config:autoaudit:*': {'ttl': 300, 'priority': 'medium'},
                'config:compliance:*': {'ttl': 300, 'priority': 'medium'},
                'config:security:*': {'ttl': 180, 'priority': 'high'}
            }
            
            logger.info(
                f"Cache warming patterns initialized: {len(self._cache_warming_patterns)} patterns"
            )
            
        except Exception as e:
            logger.warning(f"Cache warming initialization warning: {str(e)}")

    async def _start_maintenance_tasks(self) -> None:
        
        """
        Start background maintenance tasks for cache optimization and monitoring.
        
        This method initializes background tasks for cache cleanup, statistics collection,
        and performance optimization.
        """
        
        try:
            #Starting statistics collection
            stats_task = asyncio.create_task(self._statistics_collection_task())
            self._maintenance_tasks.add(stats_task)
            
            #Starting cache cleanup
            cleanup_task = asyncio.create_task(self._cache_cleanup_task())
            self._maintenance_tasks.add(cleanup_task)
            
            #Start memory monitoring
            memory_task = asyncio.create_task(self._memory_monitoring_task())
            self._maintenance_tasks.add(memory_task)
            
            logger.info(f"Started {len(self._maintenance_tasks)} background maintenance tasks")
            
        except Exception as e:
            logger.error(f"Error starting maintenance tasks: {str(e)}")

    async def get(self, key: str, default: Any = None) -> Any:
        
        """
        Retrieve value from cache with comprehensive error handling and performance tracking.
        
        Args:
            key: Cache key for value retrieval
            default: Default value if key not found
            
        Returns:
            Cached value or default if key not found
        """
        
        start_time = time.time()
        
        try:
            #Validating the key format and size
            self._validate_cache_key(key)
            
            #Retrieving value from Redis
            cached_data = await self._client.get(key)
            
            if cached_data is None:
                self._statistics.misses += 1
                logger.debug(f"Cache miss for key: {key}")
                return default
            
            #Deserialising the cached data
            value = await self._deserialize_value(cached_data)
            
            self._statistics.hits += 1
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            
            logger.debug(
                f"Cache hit for key: {key} ({response_time:.3f}s)",
                extra = {"key": key, "response_time": response_time}
            )
            
            return value
            
        except RedisError as e:
            self._statistics.error_count += 1
            
            logger.error(
                f"Redis error retrieving key '{key}': {str(e)}",
                
                extra = {
                    "key": key,
                    "error_type": type(e).__name__,
                    "response_time": time.time() - start_time
                }
            )
            return default
            
        except Exception as e:
            self._statistics.error_count += 1
            
            logger.error(
                f"Unexpected error retrieving key '{key}': {str(e)}",
                
                extra={
                    "key": key,
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  nx: bool = False, xx: bool = False) -> bool:
        
        """
        Store value in cache with comprehensive serialization and error handling.
        
        Args:
            key: Cache key for value storage
            value: Value to store in cache
            ttl: Time-to-live in seconds (uses default if not specified)
            nx: Only set if key doesn't exist
            xx: Only set if key already exists
            
        Returns:
            Boolean indicating success of set operation
        """

        start_time = time.time()
        
        try:
            
            #Validating the key and value
            self._validate_cache_key(key)
            serialized_value = await self._serialize_value(value)
            
            #Checking the value size limits
            if len(serialized_value) > self._max_value_size:
                
                logger.warning(
                    f"Value size exceeds limit for key '{key}': {len(serialized_value)} bytes"
                )

                return False
            
            #Using the default TTL if not specified
            effective_ttl = ttl or self._default_ttl
            
            #Performing set operation with appropriate flags
            if nx and xx:
                raise ValueError("Cannot specify both nx = True and xx = True")
            
            elif nx:
                result = await self._client.set(key, serialized_value, ex = effective_ttl, nx = True)

            elif xx:
                result = await self._client.set(key, serialized_value, ex = effective_ttl, xx = True)

            else:
                result = await self._client.set(key, serialized_value, ex = effective_ttl)
            
            if result:
                self._statistics.sets += 1
                response_time = time.time() - start_time
                self._update_response_time(response_time)
                
                logger.debug(
                    f"Cache set successful for key: {key} (TTL: {effective_ttl}s, {response_time:.3f}s)",
                    
                    extra = {
                        "key": key,
                        "ttl": effective_ttl,
                        "value_size": len(serialized_value),
                        "response_time": response_time
                    }
                )
                
                #Triggering the cache invalidation notification
                await self._notify_cache_set(key, effective_ttl)
            
            return bool(result)
            
        except RedisError as e:
            self._statistics.error_count += 1
            
            logger.error(
                f"Redis error setting key '{key}': {str(e)}",
                
                extra = {
                    "key": key,
                    "error_type": type(e).__name__,
                    "response_time": time.time() - start_time
                }
            )

            return False
            
        except Exception as e:
            self._statistics.error_count += 1
            
            logger.error(
                f"Unexpected error setting key '{key}': {str(e)}",
                
                extra = {
                    "key": key,
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            return False

    async def delete(self, *keys: str) -> int:
        
        """
        Delete one or more keys from cache with invalidation notifications.
        
        Args:
            keys: Variable number of cache keys to delete
            
        Returns:
            Number of keys successfully deleted
        """

        try:
            if not keys:
                return 0
            
            #Validating all keys before deletion
            for key in keys:
                self._validate_cache_key(key)
            
            #Performing bulk deletion
            deleted_count = await self._client.delete(*keys)
            
            self._statistics.deletes += deleted_count
            
            if deleted_count > 0:
                #Notifying subscribers about cache invalidation
                await self._notify_cache_invalidation(list(keys))
                
                logger.debug(
                    f"Deleted {deleted_count} cache keys: {keys[:5]}{'...' if len(keys) > 5 else ''}"
                )
            
            return deleted_count
            
        except RedisError as e:
            self._statistics.error_count += 1
            logger.error(f"Redis error deleting keys: {str(e)}")
            return 0
            
        except Exception as e:
            self._statistics.error_count += 1
            logger.error(f"Unexpected error deleting keys: {str(e)}")
            return 0

    async def invalidate_pattern(self, pattern: str) -> int:
        
        """
        Invalidate all cache keys matching a pattern with comprehensive cleanup.
        
        Args:
            pattern: Redis pattern for key matching (supports * and ? wildcards)
            
        Returns:
            Number of keys invalidated
        """

        try:
            #Finding all keys matching the pattern
            matching_keys = []
            
            if self.config.cluster_mode:
                
                #Handling cluster mode pattern matching across all nodes
                for node in self._client.get_nodes():
                    node_keys = await node.keys(pattern)
                    
                    matching_keys.extend([key.decode() if isinstance(key, bytes) else key 
                                        for key in node_keys])
            
            else:
                #Single node pattern matching
                keys = await self._client.keys(pattern)
                matching_keys = [key.decode() if isinstance(key, bytes) else key for key in keys]
            
            if not matching_keys:
                return 0
            
            #Deleting matching keys in batches for performance
            batch_size = 100
            total_deleted = 0
            
            for i in range(0, len(matching_keys), batch_size):
                batch = matching_keys[i:i + batch_size]
                deleted = await self.delete(*batch)
                total_deleted += deleted
            
            logger.info(
                f"Invalidated {total_deleted} cache keys matching pattern: {pattern}",
                
                extra = {
                    "pattern": pattern,
                    "invalidated_count": total_deleted
                }
            )
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error invalidating pattern '{pattern}': {str(e)}")
            return 0

    def _validate_cache_key(self, key: str) -> None:
        
        """
        Validate cache key format and constraints.
        
        Args:
            key: Cache key to validate
            
        Raises:
            ValueError: If key format is invalid
        """

        if not key or not isinstance(key, str):
            raise ValueError("Cache key must be a non-empty string")
        
        if len(key) > 250:
            raise ValueError("Cache key exceeds maximum length of 250 characters")
        
        #Checking for invalid characters that might cause issues
        invalid_chars = ['\r', '\n', '\t', ' ']
        
        if any(char in key for char in invalid_chars):
            raise ValueError("Cache key contains invalid characters")

    async def _serialize_value(self, value: Any) -> bytes:
        
        """
        Serialise value for cache storage with compression optimisation.
        
        Args:
            value: Value to serialise
            
        Returns:
            Serialised bytes ready for cache storage
        """

        try:
            if self._serialization_method == 'msgpack':
                serialized = msgpack.packb(value, use_bin_type = True)

            else:
                #Fallback to pickle for complex objects
                serialized = pickle.dumps(value, protocol = pickle.HIGHEST_PROTOCOL)
            
            #Applying compression for large values
            if len(serialized) > self._compression_threshold:
                
                import gzip
                compressed = gzip.compress(serialized)
                
                #Adding a compression marker
                return b'GZIP:' + compressed
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialisation error: {str(e)}")
            raise CacheError(f"Failed to serialise value: {str(e)}")

    async def _deserialize_value(self, data: bytes) -> Any:
        
        """
        Deserialise tje cached data with decompression support.
        
        Args:
            data: Serialised data from cache
            
        Returns:
            Deserialised Python object
        """
        
        try:
            #Checking for the compression marker
            if data.startswith(b'GZIP:'):
                import gzip

                #Removes the 'GZIP:' prefix
                data = gzip.decompress(data[5:])  
            
            if self._serialization_method == 'msgpack':
                return msgpack.unpackb(data, raw=False)
            
            else:
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialisation error: {str(e)}")
            raise CacheError(f"Failed to deserialise value: {str(e)}")

    async def _notify_cache_set(self, key: str, ttl: int) -> None:
        
        """
        Notify subscribers about cache set operations.
        
        Args:
            key: Cache key that was set
            ttl: Time-to-live for the cached value
        """

        try:
            event = {
                'type': 'SET',
                'key': key,
                'ttl': ttl,
                'timestamp': time.time()
            }
            
            await self._pubsub_client.publish(
                'autoaudit:cache:events',
                json.dumps(event)
            )
            
        except Exception as e:
            logger.warning(f"Failed to publish cache set notification: {str(e)}")

    async def _notify_cache_invalidation(self, keys: List[str]) -> None:
        
        """
        Notify subscribers about cache invalidation events.
        
        Args:
            keys: List of cache keys that were invalidated
        """

        try:
            event = {
                'type': 'INVALIDATE',
                'keys': keys,
                'timestamp': time.time()
            }
            
            await self._pubsub_client.publish(
                'autoaudit:cache:invalidation',
                json.dumps(event)
            )
            
        except Exception as e:
            logger.warning(f"Failed to publish cache invalidation notification: {str(e)}")

    def _update_response_time(self, response_time: float) -> None:
        
        """
        Update running average response time for performance monitoring.
        
        Args:
            response_time: Response time for the completed operation
        """

        #Using exponentially weighted moving average for response time

        #Smoothing factor
        alpha = 0.1  

        if self._statistics.average_response_time == 0:
            self._statistics.average_response_time = response_time
        
        else:
            self._statistics.average_response_time = (
                alpha * response_time + (1 - alpha) * self._statistics.average_response_time
            )

    async def get_statistics(self) -> Dict[str, Any]:
        
        """
        Retrieve comprehensive cache statistics for monitoring and optimisation.
        
        Returns:
            Dictionary containing detailed cache performance statistics
        """

        try:
            #Calculating the hit rate
            total_requests = self._statistics.hits + self._statistics.misses
            hit_rate = (self._statistics.hits / total_requests * 100) if total_requests > 0 else 0
            
            #Getting Redis' memory info
            info = await self._client.info('memory')
            memory_usage = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            return {
                'hits': self._statistics.hits,
                'misses': self._statistics.misses,
                'hit_rate': round(hit_rate, 2),
                'sets': self._statistics.sets,
                'deletes': self._statistics.deletes,
                'evictions': self._statistics.evictions,
                'error_count': self._statistics.error_count,
                'average_response_time': round(self._statistics.average_response_time * 1000, 2),  # ms
                'memory_usage': memory_usage,
                'max_memory': max_memory,
                'memory_utilization': round((memory_usage / max_memory * 100), 2) if max_memory > 0 else 0,
                'connection_count': self._statistics.connection_count
            }
            
        except Exception as e:
            logger.error(f"Error retrieving cache statistics: {str(e)}")
            return {'error': str(e)}

    async def health_check(self) -> Dict[str, Any]:
        
        """
        Perform comprehensive cache health check with performance validation.
        
        Returns:
            Dictionary containing detailed health status and performance metrics
        """

        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {}
        }
        
        try:
            #Testing basic connectivity
            start_time = time.time()
            pong_response = await self._client.ping()
            connectivity_time = time.time() - start_time
            
            if pong_response != True:
                health_status['status'] = 'unhealthy'
                
                health_status['checks']['connectivity'] = {
                    'status': 'unhealthy',
                    'error': 'Ping test failed'
                }

                return health_status
            
            health_status['checks']['connectivity'] = {
                'status': 'healthy',
                'response_time_ms': round(connectivity_time * 1000, 2)
            }
            
            #Testing basic operations
            test_key = f"autoaudit:health:{int(time.time())}"
            test_value = {'health_check': True, 'timestamp': time.time()}
            
            set_success = await self.set(test_key, test_value, ttl=60)
            
            if not set_success:
                health_status['status'] = 'degraded'
                
                health_status['checks']['operations'] = {
                    'status': 'unhealthy',
                    'error': 'Set operation failed'
                }
            
            else:
                retrieved_value = await self.get(test_key)
                
                if retrieved_value != test_value:
                    health_status['status'] = 'degraded'
                    
                    health_status['checks']['operations'] = {
                        'status': 'unhealthy',
                        'error': 'Get operation returned incorrect value'
                    }
                
                else:
                    await self.delete(test_key)
                    
                    health_status['checks']['operations'] = {
                        'status': 'healthy'
                    }
            
            #Checking memory usage
            info = await self._client.info('memory')
            memory_usage = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            if max_memory > 0:
                memory_utilization = memory_usage / max_memory
                
                if memory_utilization > 0.9:
                    health_status['status'] = 'degraded'
                    
                    health_status['checks']['memory'] = {
                        'status': 'warning',
                        'utilization_percent': round(memory_utilization * 100, 2),
                        'warning': 'High memory utilization'
                    }
                
                else:
                    health_status['checks']['memory'] = {
                        'status': 'healthy',
                        'utilization_percent': round(memory_utilization * 100, 2)
                    }
            
            #Checking the connection pool status
            if hasattr(self._client, 'connection_pool') and self._connection_pool:
                
                pool_info = {
                    'created_connections': self._connection_pool.created_connections,
                    'available_connections': len(self._connection_pool._available_connections),
                    'in_use_connections': len(self._connection_pool._in_use_connections)
                }
                
                health_status['checks']['connection_pool'] = {
                    'status': 'healthy',
                    'pool_info': pool_info
                }
            
        except RedisError as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = f"Redis error: {str(e)}"
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = f"Health check error: {str(e)}"
        
        return health_status

    async def perform_maintenance(self) -> None:
        
        """
        Perform comprehensive cache maintenance including cleanup and optimisation.
        
        This method performs various maintenance operations including expired key cleanup,
        memory optimisation, and statistics updates.
        """

        try:
            logger.debug("Starting cache maintenance operations")
            
            #Updating the statistics from the Redis info
            await self._update_statistics_from_redis()
            
            #Performing memory optimisation if needed
            await self._optimize_memory_usage()
            
            #Cleaning up expired keys if running in single-node mode
            if not self.config.cluster_mode:
                await self._cleanup_expired_keys()
            
            logger.debug("Cache maintenance completed successfully")
            
        except Exception as e:
            logger.error(f"Cache maintenance error: {str(e)}")

    async def _statistics_collection_task(self) -> None:
        
        """Background task for continuous statistics collection and monitoring."""

        while True:
            try:
                await self._update_statistics_from_redis()

                #Updating the stats every 30 seconds
                await asyncio.sleep(30)  

            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Statistics collection error: {str(e)}")

                #Longer interval on error
                await asyncio.sleep(60)  

    async def _cache_cleanup_task(self) -> None:
        
        """Background task for cache cleanup and optimisation."""

        while True:
            try:
                await self.perform_maintenance()

                #Running maintenance every 5 minutes
                await asyncio.sleep(300)  

            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
                await asyncio.sleep(300)

    async def _memory_monitoring_task(self) -> None:
        """Background task for memory usage monitoring and alerting."""

        while True:
            try:
                
                info = await self._client.info('memory')
                memory_usage = info.get('used_memory', 0)
                max_memory = info.get('maxmemory', 0)
                
                if max_memory > 0:
                    utilization = memory_usage / max_memory
                    
                    if utilization > 0.8:
                        
                        logger.warning(
                            f"High cache memory utilization: {utilization:.1%}",
                            extra={'memory_usage': memory_usage, 'max_memory': max_memory}
                        )
                
                #Checking the memory every minute
                await asyncio.sleep(60)  
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Memory monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def verify_health(self) -> None:
        
        """
        Verify cache health with automatic recovery procedures for common issues.
        
        Raises:
            CacheError: If critical health issues cannot be resolved
        """
        
        health_status = await self.health_check()
        
        if health_status['status'] not in ['healthy']:
            logger.warning(f"Cache health check failed: {health_status}")
            
            #Attempting basic recovery procedures
            try:
                
                #Reseting the connection if there are connectivity issues
                if 'connectivity' in health_status.get('checks', {}) and \
                   health_status['checks']['connectivity'].get('status') != 'healthy':
                    await self._reset_connections()
                
                #Re-checking the health after the recovery attempt
                health_status = await self.health_check()
                
                if health_status['status'] != 'healthy':
                    raise CacheError(f"Cache health verification failed: {health_status}")
                    
            except Exception as e:
                raise CacheError(f"Cache health verification and recovery failed: {str(e)}")

    async def _reset_connections(self) -> None:
        
        """Reset Redis connections as part of recovery procedures."""

        try:
            logger.info("Resetting Redis connections for recovery")
            
            if self._client:
                await self._client.close()
            
            await self.initialize()
            logger.info("Redis connections reset successfully")
            
        except Exception as e:
            logger.error(f"Connection reset failed: {str(e)}")
            raise

    async def get_client(self) -> Union[redis.Redis, RedisCluster]:
        
        """
        Get the Redis client instance for advanced operations.
        
        Returns:
            Redis client instance
        """

        if not self._client:
            raise CacheError("Cache client not initialised")
        
        return self._client