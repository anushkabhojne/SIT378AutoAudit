"""
AutoAudit Centralised Configuration Management System - Main Application

This module implements the primary FastAPI application for the AutoAudit Configuration Management System,
providing RESTful endpoints for configuration retrieval, management, and real-time updates across the
entire microservices ecosystem.

The application implements enterprise-grade security, comprehensive validation, caching strategies,
and real-time notification capabilities to support high-availability configuration management
requirements for distributed systems.

Author: Senior Lead, AutoAudit
Owner: Backend Team, AutoAudit
"""

import asyncio
import logging
import os
import sys
import time
import traceback
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import redis.asyncio as redis
import asyncpg
from asyncpg.pool import Pool

from config.database import DatabaseManager
from config.cache import CacheManager
from config.models import ConfigurationRequest, ConfigurationResponse, ConfigurationBatch
from config.security import SecurityManager
from config.validation import ValidationEngine
from config.notification import NotificationManager
from config.monitoring import MetricsCollector

from config.exceptions import (
    ConfigurationNotFoundException,
    ValidationError,
    SecurityError,
    CacheError,
    DatabaseError
)

#Configuring structured logging with comprehensive context information
logging.basicConfig(
    
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d',
    
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/config-service/application.log')
    ]
)

logger = logging.getLogger(__name__)

#Initialising Prometheus metrics for comprehensive observability
REQUEST_COUNT = Counter(
    'config_service_requests_total',
    'Total number of configuration service requests',
    ['method', 'endpoint', 'status_code', 'service_name']
)

REQUEST_DURATION = Histogram(
    'config_service_request_duration_seconds',
    'Configuration service request duration in seconds',
    ['method', 'endpoint', 'service_name']
)

CACHE_HIT_RATE = Gauge(
    'config_service_cache_hit_rate',
    'Configuration service cache hit rate percentage'
)

ACTIVE_CONNECTIONS = Gauge(
    'config_service_active_connections',
    'Number of active database connections'
)

CONFIG_RETRIEVAL_ERRORS = Counter(
    'config_service_retrieval_errors_total',
    'Total number of configuration retrieval errors',
    ['error_type', 'service_name']
)

#Initialising OpenTelemetry distributed tracing for comprehensive request tracking
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

#Configuring Jaeger exporter for distributed tracing
jaeger_exporter = JaegerExporter(
    agent_host_name = os.getenv('JAEGER_AGENT_HOST', 'localhost'),
    agent_port = int(os.getenv('JAEGER_AGENT_PORT', '6831')),
    collector_endpoint = os.getenv('JAEGER_COLLECTOR_ENDPOINT'),
)

#Addding span processor for the batch processing of trace data
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

#Initialising the global application state variables
database_manager: Optional[DatabaseManager] = None
cache_manager: Optional[CacheManager] = None
security_manager: Optional[SecurityManager] = None
validation_engine: Optional[ValidationEngine] = None
notification_manager: Optional[NotificationManager] = None
metrics_collector: Optional[MetricsCollector] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    """
    Application lifespan manager handling startup and shutdown procedures for all
    system components including database connections, cache initialisation, and
    background task management.
    
    This function ensures proper resource allocation during startup and graceful
    cleanup during shutdown, supporting zero-downtime deployment scenarios.
    """
    
    global database_manager, cache_manager, security_manager
    global validation_engine, notification_manager, metrics_collector
    
    logger.info("Initialising the AutoAudit Configuration Service components")
    
    try:
        #Initialising the database connection pool with comprehensive configuration
        database_manager = DatabaseManager(
            host = os.getenv('DATABASE_HOST', 'localhost'),
            port = int(os.getenv('DATABASE_PORT', '5432')),
            database = os.getenv('DATABASE_NAME', 'autoaudit_config'),
            username = os.getenv('DATABASE_USERNAME', 'config_service'),
            password = os.getenv('DATABASE_PASSWORD'),
            pool_min_size = int(os.getenv('DATABASE_POOL_MIN_SIZE', '10')),
            pool_max_size = int(os.getenv('DATABASE_POOL_MAX_SIZE', '50')),
            pool_max_queries = int(os.getenv('DATABASE_POOL_MAX_QUERIES', '50000')),
            pool_max_inactive_connection_lifetime = float(
                os.getenv('DATABASE_POOL_MAX_INACTIVE_CONNECTION_LIFETIME', '300.0')
            )
        )

        await database_manager.initialize()
        logger.info("The database connection pool is initialised successfully")

        #Initialising the Redis cache manager with cluster support and high availability
        cache_manager = CacheManager(
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379'),
            cluster_mode = os.getenv('REDIS_CLUSTER_MODE', 'false').lower() == 'true',
            max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '100')),
            retry_on_timeout = True,
            health_check_interval = int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30')),
            socket_timeout = float(os.getenv('REDIS_SOCKET_TIMEOUT', '5.0')),
            socket_connect_timeout = float(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5.0'))
        )

        await cache_manager.initialize()
        logger.info("The redis cache manager is initialised successfully")

        #Initialising the security manager with comprehensive authentication and authorisation
        security_manager = SecurityManager(
            jwt_secret_key = os.getenv('JWT_SECRET_KEY'),
            jwt_algorithm = os.getenv('JWT_ALGORITHM', 'RS256'),
            
            jwt_access_token_expire_minutes = int(
                os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')
            ),

            azure_ad_tenant_id = os.getenv('AZURE_AD_TENANT_ID'),
            azure_ad_client_id = os.getenv('AZURE_AD_CLIENT_ID'),
            vault_url = os.getenv('VAULT_URL'),
            vault_token = os.getenv('VAULT_TOKEN'),
            vault_mount_point = os.getenv('VAULT_MOUNT_POINT', 'secret')
        )

        await security_manager.initialize()
        logger.info("The security manager is initialised successfully")

        #Initialising the validation engine with comprehensive schema validation
        validation_engine = ValidationEngine(
            schema_registry_url = os.getenv('SCHEMA_REGISTRY_URL'),
            validation_cache_ttl = int(os.getenv('VALIDATION_CACHE_TTL', '3600')),
            enable_strict_validation = os.getenv('ENABLE_STRICT_VALIDATION', 'true').lower() == 'true'
        )

        await validation_engine.initialize()
        logger.info("Validation engine initialized successfully")

        #Initialising the notification manager for real-time configuration updates
        notification_manager = NotificationManager(
            redis_client = cache_manager.get_client(),
            webhook_timeout = float(os.getenv('WEBHOOK_TIMEOUT', '10.0')),
            retry_attempts = int(os.getenv('NOTIFICATION_RETRY_ATTEMPTS', '3')),
            retry_delay = float(os.getenv('NOTIFICATION_RETRY_DELAY', '1.0'))
        )

        await notification_manager.initialize()
        logger.info("The notification manager is initialised successfully")

        #Initialising the metrics collector for comprehensive observability
        metrics_collector = MetricsCollector(
            
            #Using the default registry
            prometheus_registry = None,  
            collection_interval = int(os.getenv('METRICS_COLLECTION_INTERVAL', '15')),
            enable_detailed_metrics = os.getenv('ENABLE_DETAILED_METRICS', 'true').lower() == 'true'
        )

        await metrics_collector.initialie()
        logger.info("The metrics collector is initialised successfully")

        #Starting background tasks for maintenance and monitoring
        asyncio.create_task(cache_maintenance_task())
        asyncio.create_task(metrics_collection_task())
        asyncio.create_task(health_check_task())
        
        logger.info("The AutoAudit Configuration Service startup is completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    
    finally:
        
        #Graceful shutdown procedures
        logger.info("Initiating the AutoAudit Configuration Service's shutdown procedures")
        
        try:
            if notification_manager:
                await notification_manager.shutdown()

            if cache_manager:
                await cache_manager.shutdown()

            if database_manager:
                await database_manager.shutdown()

            if security_manager:
                await security_manager.shutdown()
            
            logger.info("The AutoAudit Configuration Service's shutdown is completed successfully")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            logger.error(traceback.format_exc())

#Initialising the FastAPI application with comprehensive configuration
app = FastAPI(
    title = "AutoAudit Configuration Management Service",
    description = "Enterprise-grade centralised configuration management system for the AutoAudit microservices ecosystem",
    version = "1.0.0",
    docs_url = "/docs",
    redoc_url = "/redoc",
    openapi_url = "/openapi.json",
    lifespan = lifespan,

    middleware=[
        
        #Adding a trusted host middleware for security
        TrustedHostMiddleware(
            allowed_hosts = os.getenv('ALLOWED_HOSTS', '*').split(',')
        ),

        #Adding a GZIP compression for response optimization
        GZipMiddleware(minimum_size = 1000),

        #Adding CORS middleware for cross-origin requests
        CORSMiddleware(
            allow_origins = os.getenv('ALLOWED_ORIGINS', '*').split(','),
            allow_credentials = True,
            allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers = ["*"],
        ),
    ]
)

#Initialising FastAPI instrumentation for OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

#Initialising security dependency for JWT authentication
security = HTTPBearer()

async def authenticate_request(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    
    """
    Authenticate incoming requests using JWT tokens with comprehensive validation
    including signature verification, expiration checking, and scope validation.
    
    Args:
        credentials: HTTP Bearer token credentials from request headers
        
    Returns:
        Dict containing validated token payload with user and service information
        
    Raises:
        HTTPException: For authentication failures including invalid tokens,
                      expired tokens, or insufficient permissions
    """

    try:
        if not security_manager:
            
            raise HTTPException(
                status_code = 503,
                detail = "Security manager is not initialised"
            )
        
        #Validating and decoding the JWT token with comprehensive error handling
        token_payload = await security_manager.validate_token(credentials.credentials)
        
        #Logging the successful authentication for audit purposes
        logger.info(
            f"Request authenticated successfully for service: {token_payload.get('service_name', 'unknown')}",
            
            extra = {
                "service_name": token_payload.get('service_name'),
                "user_id": token_payload.get('user_id'),
                "scopes": token_payload.get('scopes', []),
                "token_expiry": token_payload.get('exp')
            }
        )
        
        return token_payload
        
    except SecurityError as e:
        
        logger.warning(
            f"Authentication failed: {str(e)}",
            
            extra = {
                "error_type": "authentication_failure",
                "token_prefix": credentials.credentials[:20] if credentials.credentials else None
            }
        )

        raise HTTPException(
            status_code = 401,
            detail = f"Authentication failed: {str(e)}"
        )
    
    except Exception as e:
        
        logger.error(
            f"Unexpected authentication error: {str(e)}",
            
            extra = {
                "error_type": "authentication_system_error",
                "traceback": traceback.format_exc()
            }
        )

        raise HTTPException(
            status_code = 500,
            detail = "Internal authentication error"
        )

async def authorize_configuration_access(
    namespace: str,
    environment: str,
    service_name: str,
    token_payload: Dict[str, Any]
) -> bool:
    
    """
    Authorise configuration access based on token scopes and service permissions.
    Implements fine-grained access control for configuration parameters.
    
    Args:
        namespace: Configuration namespace being accessed
        environment: Target environment (dev, staging, production)
        service_name: Name of the service requesting configuration
        token_payload: Validated JWT token payload with permissions
        
    Returns:
        Boolean indicating whether access is authorised
    """

    try:
        #Extracting scopes and service information from the token
        token_scopes = token_payload.get('scopes', [])
        token_service = token_payload.get('service_name')
        user_roles = token_payload.get('roles', [])
        
        #Checking the service-specific access permissions
        if token_service and token_service == service_name:
            return True
        
        #Checking the administrative access permissions
        if 'config:admin' in token_scopes or 'admin' in user_roles:
            return True
        
        #Checking the namespace-specific permissions
        namespace_scope = f'config:{namespace}:read'
        if namespace_scope in token_scopes:
            return True
        
        #Checking the environment-specific permissions for cross-service access
        env_scope = f'config:{environment}:read'
        if env_scope in token_scopes:
            return True
        
        logger.warning(
            f"Configuration access denied for service {service_name} in namespace {namespace}",
            extra = {
                "service_name": service_name,
                "namespace": namespace,
                "environment": environment,
                "token_service": token_service,
                "token_scopes": token_scopes
            }
        )
        
        return False
        
    except Exception as e:
        logger.error(f"Error during authorisation check: {str(e)}")
        return False

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """
    Comprehensive request middleware providing logging, metrics collection,
    error handling, and performance monitoring for all incoming requests.
    
    This middleware captures detailed request information, measures response times,
    and provides correlation IDs for distributed tracing across the microservices ecosystem.
    """
    #Generating a correlation ID for request tracking
    import uuid
    correlation_id = str(uuid.uuid4())
    
    #Extracting the request metadata for logging and metrics
    start_time = time.time()
    method = request.method
    url = str(request.url)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    #Adding a correlation ID to request state for downstream access
    request.state.correlation_id = correlation_id
    
    logger.info(
        f"Request started: {method} {url}",
        
        extra={
            "correlation_id": correlation_id,
            "method": method,
            "url": url,
            "client_ip": client_ip,
            "user_agent": user_agent
        }
    )
    
    try:
        #Processing the request through the application stack
        response = await call_next(request)
        
        #Calculating the request's duration for performance monitoring
        duration = time.time() - start_time
        
        #Extracting the service name from authentication if available
        service_name = "unknown"
        if hasattr(request.state, "token_payload"):
            service_name = request.state.token_payload.get("service_name", "unknown")
        
        #Recording the metrics for monitoring and alerting
        REQUEST_COUNT.labels(
            method = method,
            endpoint = request.url.path,
            status_code = response.status_code,
            service_name = service_name
        ).inc()
        
        REQUEST_DURATION.labels(
            method = method,
            endpoint = request.url.path,
            service_name = service_name
        ).observe(duration)
        
        logger.info(
            f"Request completed: {method} {url} - {response.status_code} ({duration:.3f}s)",
            
            extra = {
                "correlation_id": correlation_id,
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "duration_seconds": duration,
                "service_name": service_name
            }
        )
        
        #Adding the correlation ID to the response headers for client tracking
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
        
    except Exception as e:

        #Handling and logging the request processing errors
        duration = time.time() - start_time
        
        logger.error(
            f"Request failed: {method} {url} - {str(e)} ({duration:.3f}s)",
            
            extra = {
                "correlation_id": correlation_id,
                "method": method,
                "url": url,
                "error": str(e),
                "duration_seconds": duration,
                "traceback": traceback.format_exc()
            }
        )
        
        #Recording the error metrics for monitoring
        CONFIG_RETRIEVAL_ERRORS.labels(
            error_type = "request_processing_error",
            service_name = "unknown"
        ).inc()
        
        #Returning the standardised error response
        return JSONResponse(
            
            status_code = 500,
            
            content = {
                "error": "Internal server error",
                "correlation_id": correlation_id,
                "timestamp": time.time()
            },

            headers = {"X-Correlation-ID": correlation_id}
        )

@app.get("/health")
async def health_check():
    
    """
    Comprehensive health check endpoint providing detailed system status
    including database connectivity, cache availability, and service dependencies.
    
    Returns:
        Dict containing detailed health status for all system components
    """
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "components": {}
    }
    
    try:
        #Checking the database's connectivity and performance
        if database_manager:
            db_health = await database_manager.health_check()
            health_status["components"]["database"] = db_health

        else:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": "The database manager is not initialised"
            }
        
        #Checking the cache's connectivity and performance
        if cache_manager:
            cache_health = await cache_manager.health_check()
            health_status["components"]["cache"] = cache_health
        
        else:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "error": "The cache manager is not initialised"
            }
        
        #Checking the security manager status
        if security_manager:
            security_health = await security_manager.health_check()
            health_status["components"]["security"] = security_health
        
        else:
            health_status["components"]["security"] = {
                "status": "unhealthy",
                "error": "The security manager is not initialised"
            }
        
        #Determine the overall health status based on the component's health
        unhealthy_components = [
            name for name, component in health_status["components"].items()
            if component.get("status") != "healthy"
        ]
        
        if unhealthy_components:
            health_status["status"] = "degraded"
            health_status["unhealthy_components"] = unhealthy_components
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/metrics")
async def metrics_endpoint():
    
    """
    Prometheus metrics endpoint providing comprehensive application and business metrics
    for monitoring, alerting, and capacity planning purposes.
    
    Returns:
        Prometheus-formatted metrics data
    """

    try:
        #Updating the cache hit rate metric
        if cache_manager:
            cache_stats = await cache_manager.get_statistics()
            hit_rate = cache_stats.get("hit_rate", 0.0)
            CACHE_HIT_RATE.set(hit_rate)
        
        #Updating the active connections metric
        if database_manager:
            connection_stats = await database_manager.get_connection_statistics()
            active_connections = connection_stats.get("active_connections", 0)
            ACTIVE_CONNECTIONS.set(active_connections)
        
        #Generating and returning the Prometheus metrics
        return Response(
            content = generate_latest(),
            media_type = CONTENT_TYPE_LATEST
        )
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")

        raise HTTPException(
            status_code = 500,
            detail = "Metrics collection error"
        )

@app.get("/config/{namespace}/{environment}/{service_name}")
async def get_service_configuration(
    namespace: str,
    environment: str,
    service_name: str,
    include_sensitive: bool = False,
    format: str = "json",
    token_payload: Dict[str, Any] = Depends(authenticate_request)
):
    
    """
    Retrieve complete configuration for a specific service in a given namespace and environment.
    
    This endpoint implements hierarchical configuration resolution, caching optimisation,
    and comprehensive security controls for configuration access.
    
    Args:
        namespace: Configuration namespace (e.g., 'autoaudit', 'compliance')
        environment: Target environment (e.g., 'dev', 'staging', 'production')
        service_name: Name of the requesting service
        include_sensitive: Whether to include encrypted sensitive parameters
        format: Response format ('json', 'yaml', 'env')
        token_payload: Validated JWT token payload from authentication
        
    Returns:
        Complete configuration object with resolved parameters

    """
    with tracer.start_as_current_span("get_service_configuration") as span:
        
        #Setting span attributes for distributed tracing
        span.set_attribute("namespace", namespace)
        span.set_attribute("environment", environment)
        span.set_attribute("service_name", service_name)
        span.set_attribute("include_sensitive", include_sensitive)
        
        try:
            #Authorising configuration access based on token permissions
            is_authorized = await authorize_configuration_access(
                namespace, environment, service_name, token_payload
            )
            
            if not is_authorized:
                raise HTTPException(
                    status_code = 403,
                    detail = f"Insufficient permissions to access configuration for {service_name}"
                )
            
            #Generating the cache key for configuration retrieval
            cache_key = f"config:{namespace}:{environment}:{service_name}:{include_sensitive}"
            
            #Attempting to retrieve configuration from cache
            cached_config = await cache_manager.get(cache_key)
            if cached_config:
                logger.info(
                    f"Configuration retrieved from cache for {service_name}",
                    
                    extra = {
                        "namespace": namespace,
                        "environment": environment,
                        "service_name": service_name,
                        "cache_hit": True
                    }
                )
                return cached_config
            
            #Retrieving the configuration from database with hierarchical resolution
            configuration = await database_manager.get_service_configuration(
                namespace = namespace,
                environment = environment,
                service_name = service_name,
                include_sensitive = include_sensitive
            )
            
            if not configuration:
                raise ConfigurationNotFoundException(
                    f"Configuration not found for service {service_name} in {namespace}/{environment}"
                )
            
            #Decrypting sensitive parameters if requested and authorised
            if include_sensitive and security_manager:
                configuration = await security_manager.decrypt_sensitive_parameters(
                    configuration
                )
            
            #Validating the configuration against registered schemas
            if validation_engine:
                await validation_engine.validate_configuration(
                    namespace, service_name, configuration
                )
            
            #Caching the resolved configuration for future requests
            await cache_manager.set(
                cache_key,
                configuration,
                ttl = int(os.getenv('CONFIG_CACHE_TTL', '300'))
            )
            
            #Formatting the response according to the requested format
            if format == "yaml":
                import yaml
                response_content = yaml.dump(configuration, default_flow_style=False)
                return Response(content=response_content, media_type="application/x-yaml")
            
            elif format == "env":
                
                env_content = "\n".join([
                    f"{key}={value}" for key, value in configuration.items()
                    if isinstance(value, (str, int, float, bool))
                ])

                return Response(content=env_content, media_type="text/plain")
            
            logger.info(
                f"Configuration retrieved successfully for {service_name}",
                
                extra = {
                    "namespace": namespace,
                    "environment": environment,
                    "service_name": service_name,
                    "parameter_count": len(configuration),
                    "cache_hit": False
                }
            )
            
            return configuration
            
        except ConfigurationNotFoundException as e:
            
            CONFIG_RETRIEVAL_ERRORS.labels(
                error_type = "configuration_not_found",
                service_name = service_name
            ).inc()
            
            logger.warning(str(e))
            raise HTTPException(status_code= 404, detail = str(e))
            
        except ValidationError as e:
            
            CONFIG_RETRIEVAL_ERRORS.labels(
                error_type = "validation_error",
                service_name = service_name
            ).inc()
            
            logger.error(f"Configuration validation failed: {str(e)}")
            raise HTTPException(status_code = 400, detail = str(e))
            
        except Exception as e:
            
            CONFIG_RETRIEVAL_ERRORS.labels(
                error_type = "system_error",
                service_name = service_name
            ).inc()
            
            logger.error(
                f"Unexpected error retrieving configuration: {str(e)}",
                
                extra = {
                    "namespace": namespace,
                    "environment": environment,
                    "service_name": service_name,
                    "traceback": traceback.format_exc()
                }
            )
            
            raise HTTPException(
                status_code = 500,
                detail = "Internal server error during configuration retrieval"
            )

async def cache_maintenance_task():
    
    """
    Background task for cache maintenance including expired key cleanup,
    memory optimisation, and cache statistics collection.
    """
    
    while True:
        try:
            if cache_manager:
                await cache_manager.perform_maintenance()

            #Running maintenance every 5 minutes
            await asyncio.sleep(300)  

        except Exception as e:
            logger.error(f"Cache maintenance task error: {str(e)}")

            #Shorter retry interval on error
            await asyncio.sleep(60)  

async def metrics_collection_task():
    
    """
    Background task for custom metrics collection and business intelligence
    gathering supporting operational monitoring and capacity planning.
    """
    
    while True:
        try:
            if metrics_collector:
                await metrics_collector.collect_custom_metrics()
            
            #Collecting metrics every minute
            await asyncio.sleep(60)  
        
        except Exception as e:
            logger.error(f"Metrics collection task error: {str(e)}")
            await asyncio.sleep(60)

async def health_check_task():
    
    """
    Background task for continuous health monitoring of system components
    with automated alerting and self-healing capabilities where possible.
    """
    
    while True:
        try:
            #Performing comprehensive system health checks
            if database_manager:
                await database_manager.verify_health()

            if cache_manager:
                await cache_manager.verify_health()
            
            #Health check every 30 seconds
            await asyncio.sleep(30)  

        except Exception as e:
            logger.error(f"Health check task error: {str(e)}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    #Development server configuration - not for production use
    uvicorn.run(
        "main:app",
        host = "0.0.0.0",
        port = 8000,
        log_level = "info",
        reload = True,
        access_log = True
    )