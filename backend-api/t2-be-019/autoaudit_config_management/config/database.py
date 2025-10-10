"""
AutoAudit Configuration Management System - Database Manager

This module implements comprehensive database management functionality for the AutoAudit
Configuration Management System, providing high-performance PostgreSQL integration with
connection pooling, transaction management, and advanced querying capabilities.

The DatabaseManager class handles all database operations including configuration storage,
retrieval, hierarchical resolution, audit logging, and schema management with enterprise-grade
reliability and performance optimization.

Author: Senior Lead, AutoAudit 
Owner, Backend Team, AutoAudit
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from asyncpg.exceptions import PostgresError, InterfaceError
import sqlparse
from cryptography.fernet import Fernet

from .exceptions import DatabaseError, ConfigurationNotFoundException, ValidationError
from .models import ConfigurationParameter, ConfigurationAuditLog, ServiceRegistration

#Configuring module-specific logging with detailed formatting
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    
    """
    Database configuration parameters with comprehensive connection and performance settings.
    
    This dataclass encapsulates all database connection parameters, connection pool settings,
    and performance optimisation parameters required for enterprise-grade database operations.
    """
    
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_min_size: int = 10
    pool_max_size: int = 50
    pool_max_queries: int = 50000
    pool_max_inactive_connection_lifetime: float = 300.0
    command_timeout: float = 60.0
    server_settings: Dict[str, str] = None
    ssl_context: Optional[Any] = None
    connection_class: type = Connection

    def __post_init__(self):
        """Initialising the default server settings for optimal PostgreSQL performance."""
        if self.server_settings is None:
            
            self.server_settings = {
                'application_name': 'autoaudit_config_service',
                'timezone': 'UTC',
                'search_path': 'public,config',
                'statement_timeout': '60s',
                'idle_in_transaction_session_timeout': '300s',
                'shared_preload_libraries': 'pg_stat_statements',
                'track_activity_query_size': '2048'
            }

class DatabaseManager:
    
    """
    Comprehensive database management class providing enterprise-grade PostgreSQL integration
    with connection pooling, transaction management, performance optimisation, and comprehensive
    error handling for the AutoAudit Configuration Management System.
    
    This class implements all database operations required for configuration management including
    hierarchical configuration resolution, audit logging, schema management, and performance
    monitoring with support for high-availability deployment scenarios.
    """

    def __init__(self, host: str, port: int, database: str, username: str, password: str,
                 pool_min_size: int = 10, pool_max_size: int = 50,
                 pool_max_queries: int = 50000,
                 pool_max_inactive_connection_lifetime: float = 300.0,
                 command_timeout: float = 60.0):
        
        """
        Initialising the DatabaseManager with comprehensive configuration parameters.
        
        Args:
            host: PostgreSQL server hostname or IP address
            port: PostgreSQL server port number
            database: Target database name
            username: Database authentication username
            password: Database authentication password
            pool_min_size: Minimum number of connections in the pool
            pool_max_size: Maximum number of connections in the pool
            pool_max_queries: Maximum number of queries per connection
            pool_max_inactive_connection_lifetime: Connection timeout in seconds
            command_timeout: Individual command timeout in seconds
        """

        self.config = DatabaseConfig(
            host = host,
            port = port,
            database = database,
            username = username,
            password = password,
            pool_min_size = pool_min_size,
            pool_max_size = pool_max_size,
            pool_max_queries = pool_max_queries,
            pool_max_inactive_connection_lifetime = pool_max_inactive_connection_lifetime,
            command_timeout = command_timeout
        )
        
        #Initialising the connection pool and management variables
        self._pool: Optional[Pool] = None
        
        self._connection_statistics = {
            'active_connections': 0,
            'idle_connections': 0,
            'total_queries_executed': 0,
            'average_query_time': 0.0,
            'failed_connections': 0,
            'connection_errors': []
        }
        
        #Initialising schema management and migration tracking
        self._schema_version = None
        self._migration_lock = asyncio.Lock()
        
        logger.info(
            f"DatabaseManager initialized for {database}@{host}:{port}",
            
            extra = {
                "host": host,
                "port": port,
                "database": database,
                "pool_min_size": pool_min_size,
                "pool_max_size": pool_max_size
            }
        )

    async def initialize(self) -> None:
        
        """
        Initialising the database connection pool and perform schema validation.
        
        This method establishes the connection pool, validates database schema,
        performs necessary migrations, and prepares the database for operations.
        
        Raises:
            DatabaseError: If database initialisation fails
        """
        
        try:
            logger.info("Initialising the database connection pool")
            
            #Creating the connection pool with comprehensive error handling
            self._pool = await asyncpg.create_pool(
                host = self.config.host,
                port = self.config.port,
                user = self.config.username,
                password = self.config.password,
                database = self.config.database,
                min_size = self.config.pool_min_size,
                max_size = self.config.pool_max_size,
                max_queries = self.config.pool_max_queries,
                max_inactive_connection_lifetime = self.config.pool_max_inactive_connection_lifetime,
                command_timeout = self.config.command_timeout,
                server_settings = self.config.server_settings,
                connection_class = self.config.connection_class
            )
            
            #Validating the pool's creation and testing its connectivity
            if not self._pool:
                raise DatabaseError("Failed to create database connection pool")
            
            #Performing an initial connectivity test
            async with self._pool.acquire() as connection:
                result = await connection.fetchval("SELECT version()")
                logger.info(f"Database connection established successfully: {result}")
            
            #Initialising the database schema and performing migrations
            await self._initialize_schema()
            await self._perform_migrations()
            
            #Creating database indexes for optimal performance
            await self._create_performance_indexes()
            
            #Initialising the monitoring and statistics collection
            await self._initialize_monitoring()
            
            logger.info("Database initialization completed successfully")
            
        except PostgresError as e:
            
            logger.error(
                f"PostgreSQL error during initialisation: {str(e)}",
                
                extra = {
                    "error_code": e.pgcode,
                    "error_detail": e.pgerror,
                    "traceback": traceback.format_exc()
                }
            )
            
            raise DatabaseError(f"Database initialization failed: {str(e)}")
            
        except Exception as e:
            
            logger.error(
                f"Unexpected error during database initialisation: {str(e)}",
                
                extra = {
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            raise DatabaseError(f"Database initialisation failed: {str(e)}")

    async def _initialize_schema(self) -> None:
        
        """
        Initialise the database schema with comprehensive table structures for configuration management.
        
        This method creates all necessary tables, constraints, and database objects required
        for configuration management operations including hierarchical structures, audit trails,
        and performance optimisation indexes.
        """

        schema_sql = """
        -- Create configuration management schema
        CREATE SCHEMA IF NOT EXISTS config;
        
        -- Enable necessary extensions for advanced functionality
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
        CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
        
        -- Create configuration namespaces table for organizational structure
        CREATE TABLE IF NOT EXISTS config.namespaces (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by VARCHAR(255),
            metadata JSONB DEFAULT '{}'::jsonb
        );
        
        -- Create environments table for deployment stage management
        CREATE TABLE IF NOT EXISTS config.environments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            priority INTEGER DEFAULT 0,
            is_production BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by VARCHAR(255),
            metadata JSONB DEFAULT '{}'::jsonb
        );
        
        -- Create services table for service registration and management
        CREATE TABLE IF NOT EXISTS config.services (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            namespace_id UUID NOT NULL REFERENCES config.namespaces(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            service_type VARCHAR(100) DEFAULT 'microservice',
            health_check_endpoint VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by VARCHAR(255),
            metadata JSONB DEFAULT '{}'::jsonb,
            UNIQUE(namespace_id, name)
        );
        
        -- Create configuration parameters table with hierarchical support
        CREATE TABLE IF NOT EXISTS config.parameters (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            namespace_id UUID NOT NULL REFERENCES config.namespaces(id) ON DELETE CASCADE,
            environment_id UUID REFERENCES config.environments(id) ON DELETE CASCADE,
            service_id UUID REFERENCES config.services(id) ON DELETE CASCADE,
            key VARCHAR(500) NOT NULL,
            value TEXT,
            value_type VARCHAR(50) DEFAULT 'string',
            is_sensitive BOOLEAN DEFAULT FALSE,
            is_encrypted BOOLEAN DEFAULT FALSE,
            encryption_key_id VARCHAR(255),
            description TEXT,
            validation_schema JSONB,
            tags VARCHAR(255)[],
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by VARCHAR(255),
            version INTEGER DEFAULT 1,
            metadata JSONB DEFAULT '{}'::jsonb
        );
        
        -- Create configuration audit log table for comprehensive change tracking
        CREATE TABLE IF NOT EXISTS config.audit_log (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            parameter_id UUID REFERENCES config.parameters(id) ON DELETE SET NULL,
            operation VARCHAR(50) NOT NULL,
            old_value TEXT,
            new_value TEXT,
            changed_by VARCHAR(255),
            changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            client_ip INET,
            user_agent TEXT,
            correlation_id UUID,
            reason TEXT,
            metadata JSONB DEFAULT '{}'::jsonb
        );
        
        -- Create configuration snapshots table for versioning and rollback
        CREATE TABLE IF NOT EXISTS config.snapshots (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            namespace_id UUID NOT NULL REFERENCES config.namespaces(id),
            environment_id UUID REFERENCES config.environments(id),
            service_id UUID REFERENCES config.services(id),
            snapshot_data JSONB NOT NULL,
            snapshot_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by VARCHAR(255),
            description TEXT,
            tags VARCHAR(255)[],
            metadata JSONB DEFAULT '{}'::jsonb
        );
        
        -- Create configuration validation rules table
        CREATE TABLE IF NOT EXISTS config.validation_rules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            namespace_id UUID NOT NULL REFERENCES config.namespaces(id),
            service_id UUID REFERENCES config.services(id),
            parameter_pattern VARCHAR(500) NOT NULL,
            validation_type VARCHAR(50) NOT NULL,
            validation_config JSONB NOT NULL,
            error_message TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by VARCHAR(255)
        );
        
        -- Create database schema version tracking table
        CREATE TABLE IF NOT EXISTS config.schema_migrations (
            id SERIAL PRIMARY KEY,
            version INTEGER NOT NULL UNIQUE,
            description TEXT NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            applied_by VARCHAR(255),
            checksum VARCHAR(64)
        );
        
        -- Create updated_at trigger function for automatic timestamp updates
        CREATE OR REPLACE FUNCTION config.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Apply updated_at triggers to relevant tables
        DO $$
        BEGIN
            
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_namespaces_updated_at') THEN
                CREATE TRIGGER update_namespaces_updated_at 
                BEFORE UPDATE ON config.namespaces
                FOR EACH ROW EXECUTE FUNCTION config.update_updated_at_column();
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_environments_updated_at') THEN
                CREATE TRIGGER update_environments_updated_at 
                BEFORE UPDATE ON config.environments
                FOR EACH ROW EXECUTE FUNCTION config.update_updated_at_column();
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_services_updated_at') THEN
                CREATE TRIGGER update_services_updated_at 
                BEFORE UPDATE ON config.services
                FOR EACH ROW EXECUTE FUNCTION config.update_updated_at_column();
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_parameters_updated_at') THEN
                CREATE TRIGGER update_parameters_updated_at 
                BEFORE UPDATE ON config.parameters
                FOR EACH ROW EXECUTE FUNCTION config.update_updated_at_column();
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_validation_rules_updated_at') THEN
                CREATE TRIGGER update_validation_rules_updated_at 
                BEFORE UPDATE ON config.validation_rules
                FOR EACH ROW EXECUTE FUNCTION config.update_updated_at_column();
            END IF;

        END $;
        """
        
        try:
            async with self._pool.acquire() as connection:
                
                #Executing the schema creation with comprehensive error handling
                await connection.execute(schema_sql)
                logger.info("Database schema initialized successfully")
                
        except PostgresError as e:
            logger.error(f"PostgreSQL schema initialisation error: {str(e)}")
            raise DatabaseError(f"Schema initialisation failed: {str(e)}")

    async def _perform_migrations(self) -> None:
        
        """
        Execute database migrations to ensure schema currency and data integrity.
        
        This method checks the current schema version and applies necessary migrations
        to bring the database schema up to the current version required by the application.
        """

        try:
            async with self._pool.acquire() as connection:
                
                #Checking the current schema version
                current_version = await connection.fetchval(
                    "SELECT COALESCE(MAX(version), 0) FROM config.schema_migrations"
                )
                
                #Current schema version
                required_version = 1  
                
                if current_version < required_version:
                    logger.info(f"Applying database migrations from version {current_version} to {required_version}")
                    
                    #Applying migration version 1 if needed
                    if current_version < 1:
                        await self._apply_migration_v1(connection)
                    
                    logger.info(f"Database migrations completed successfully")

                else:
                    logger.info(f"Database schema is current (version {current_version})")
                    
        except Exception as e:
            logger.error(f"Migration execution failed: {str(e)}")
            raise DatabaseError(f"Database migration failed: {str(e)}")

    async def _apply_migration_v1(self, connection: Connection) -> None:
        
        """
        Apply migration version 1 - Initial schema and default data setup.
        
        Args:
            connection: Active database connection for migration execution
        """

        migration_sql = """
        -- Insert default namespaces for AutoAudit ecosystem
        INSERT INTO config.namespaces (name, description, created_by) VALUES 
        ('autoaudit', 'Core AutoAudit application configuration', 'system'),
        ('compliance', 'Compliance framework configuration', 'system'),
        ('security', 'Security service configuration', 'system'),
        ('monitoring', 'Monitoring and observability configuration', 'system')
        ON CONFLICT (name) DO NOTHING;
        
        -- Insert default environments
        INSERT INTO config.environments (name, description, priority, is_production, created_by) VALUES
        ('development', 'Development environment configuration', 1, FALSE, 'system'),
        ('testing', 'Testing environment configuration', 2, FALSE, 'system'),
        ('staging', 'Staging environment configuration', 3, FALSE, 'system'),
        ('production', 'Production environment configuration', 4, TRUE, 'system')
        ON CONFLICT (name) DO NOTHING;
        
        -- Record migration application
        INSERT INTO config.schema_migrations (version, description, applied_by, checksum)
        VALUES (1, 'Initial schema setup with default data', 'system', 'v1_initial_schema');
        """
        
        await connection.execute(migration_sql)
        logger.info("Migration v1 applied successfully")

    async def _create_performance_indexes(self) -> None:
        
        """
        Create database indexes optimised for configuration management query patterns.
        
        This method creates specialised indexes to optimise common query patterns including
        hierarchical configuration resolution, audit log searching, and performance monitoring queries.
        """

        index_sql = """
        -- Indexes for configuration parameter lookups
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parameters_namespace_env_service 
        ON config.parameters (namespace_id, environment_id, service_id, key);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parameters_key_lookup 
        ON config.parameters (key) WHERE is_sensitive = FALSE;
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parameters_priority 
        ON config.parameters (priority DESC, created_at DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parameters_tags 
        ON config.parameters USING GIN (tags);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parameters_metadata 
        ON config.parameters USING GIN (metadata);
        
        -- Indexes for audit log queries
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_parameter_time 
        ON config.audit_log (parameter_id, changed_at DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_user_time 
        ON config.audit_log (changed_by, changed_at DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_correlation 
        ON config.audit_log (correlation_id);
        
        -- Indexes for snapshot queries
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_snapshots_namespace_env_service 
        ON config.snapshots (namespace_id, environment_id, service_id, created_at DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_snapshots_hash 
        ON config.snapshots (snapshot_hash);
        
        -- Indexes for validation rules
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_validation_rules_namespace_service 
        ON config.validation_rules (namespace_id, service_id) WHERE is_active = TRUE;
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_validation_rules_pattern 
        ON config.validation_rules (parameter_pattern) WHERE is_active = TRUE;
        """
        
        try:
            async with self._pool.acquire() as connection:
                await connection.execute(index_sql)
                logger.info("Performance indexes created successfully")
                
        except PostgresError as e:
            
            #Index creation failures are non-fatal but should be logged
            logger.warning(f"Some indexes may not have been created: {str(e)}")

    async def _initialize_monitoring(self) -> None:
        
        """
        Initialise the database monitoring and statistics collection for performance optimisation.
        
        This method sets up monitoring queries and initializes statistics collection
        for ongoing performance analysis and optimisation.
        """

        try:
            async with self._pool.acquire() as connection:
                # Enable query statistics if available
                await connection.execute("SELECT pg_stat_statements_reset()")
                
                # Initialize connection statistics
                self._connection_statistics['initialized_at'] = datetime.now(timezone.utc)
                
                logger.info("Database monitoring initialised successfully")
                
        except Exception as e:
            logger.warning(f"Database monitoring initialisation warning: {str(e)}")

    async def get_service_configuration(
        self, 
        namespace: str, 
        environment: str, 
        service_name: str,
        include_sensitive: bool = False
    ) -> Dict[str, Any]:
        
        """
        Retrieve complete configuration for a service with hierarchical resolution.
        
        This method implements hierarchical configuration resolution following the priority order:
        1. Service-specific parameters
        2. Environment-specific parameters  
        3. Namespace-specific parameters
        4. Global parameters
        
        Args:
            namespace: Configuration namespace name
            environment: Target environment name
            service_name: Service name for configuration retrieval
            include_sensitive: Whether to include sensitive parameters
            
        Returns:
            Dictionary containing resolved configuration parameters
            
        Raises:
            ConfigurationNotFoundException: If no configuration found
            DatabaseError: If database operation fails
        """

        try:
            async with self._pool.acquire() as connection:
                
                #Building a hierarchical query with proper parameter resolution
                query = """
                WITH namespace_info AS (
                    SELECT id as namespace_id FROM config.namespaces WHERE name = $1
                ),
                environment_info AS (
                    SELECT id as environment_id FROM config.environments WHERE name = $2
                ),
                service_info AS (
                    SELECT s.id as service_id 
                    FROM config.services s
                    JOIN namespace_info n ON s.namespace_id = n.namespace_id
                    WHERE s.name = $3
                ),
                hierarchical_config AS (
                    SELECT 
                        p.key,
                        p.value,
                        p.value_type,
                        p.is_sensitive,
                        p.is_encrypted,
                        p.encryption_key_id,
                        p.description,
                        p.metadata,
                        CASE 
                            WHEN p.service_id IS NOT NULL THEN 1
                            WHEN p.environment_id IS NOT NULL THEN 2
                            WHEN p.namespace_id IS NOT NULL THEN 3
                            ELSE 4
                        END as priority_level,
                        ROW_NUMBER() OVER (
                            PARTITION BY p.key 
                            ORDER BY 
                                CASE 
                                    WHEN p.service_id IS NOT NULL THEN 1
                                    WHEN p.environment_id IS NOT NULL THEN 2
                                    WHEN p.namespace_id IS NOT NULL THEN 3
                                    ELSE 4
                                END,
                                p.priority DESC,
                                p.created_at DESC
                        ) as rn
                    FROM config.parameters p
                    CROSS JOIN namespace_info n
                    CROSS JOIN environment_info e
                    LEFT JOIN service_info s ON TRUE
                    WHERE 
                        p.namespace_id = n.namespace_id
                        AND (
                            p.service_id = s.service_id
                            OR p.environment_id = e.environment_id
                            OR (p.environment_id IS NULL AND p.service_id IS NULL)
                        )
                        AND ($4 = TRUE OR p.is_sensitive = FALSE)
                )
                SELECT 
                    key,
                    value,
                    value_type,
                    is_sensitive,
                    is_encrypted,
                    encryption_key_id,
                    description,
                    metadata
                FROM hierarchical_config 
                WHERE rn = 1
                ORDER BY key;
                """
                
                #Executing the hierarchical configuration query
                rows = await connection.fetch(
                    query, namespace, environment, service_name, include_sensitive
                )
                
                if not rows:
                    raise ConfigurationNotFoundException(
                        f"No configuration found for service '{service_name}' in namespace '{namespace}' environment '{environment}'"
                    )
                
                #Processing the configuration parameters with type conversion and validation
                configuration = {}
                sensitive_parameters = []
                
                for row in rows:
                    key = row['key']
                    value = row['value']
                    value_type = row['value_type']
                    is_sensitive = row['is_sensitive']
                    is_encrypted = row['is_encrypted']
                    
                    #Converting the value based on type specification
                    converted_value = await self._convert_parameter_value(value, value_type)
                    
                    #Tracking the sensitive parameters for audit logging
                    if is_sensitive:
                        sensitive_parameters.append(key)
                        
                    #Storing the encrypted parameters for later decryption if requested
                    if is_encrypted and include_sensitive:
                        
                        configuration[key] = {
                            'value': converted_value,
                            'encrypted': True,
                            'encryption_key_id': row['encryption_key_id']
                        }

                    else:
                        configuration[key] = converted_value
                
                #Logging the configuration retrieval for audit purposes
                await self._log_configuration_access(
                    connection, namespace, environment, service_name,
                    len(configuration), len(sensitive_parameters)
                )
                
                logger.info(
                    f"Configuration retrieved for {service_name}: {len(configuration)} parameters",
                    
                    extra = {
                        "namespace": namespace,
                        "environment": environment,
                        "service_name": service_name,
                        "parameter_count": len(configuration),
                        "sensitive_count": len(sensitive_parameters)
                    }
                )
                
                return configuration
                
        except ConfigurationNotFoundException:
            raise
        
        except PostgresError as e:
            
            logger.error(
                f"Database error retrieving configuration: {str(e)}",
                
                extra = {
                    "namespace": namespace,
                    "environment": environment,
                    "service_name": service_name,
                    "error_code": e.pgcode
                }
            )

            raise DatabaseError(f"Configuration retrieval failed: {str(e)}")
        
        except Exception as e:
            
            logger.error(
                f"Unexpected error retrieving configuration: {str(e)}",
                
                extra = {
                    "namespace": namespace,
                    "environment": environment,
                    "service_name": service_name,
                    "traceback": traceback.format_exc()
                }
            )
            raise DatabaseError(f"Configuration retrieval failed: {str(e)}")

    async def _convert_parameter_value(self, value: str, value_type: str) -> Any:
        
        """
        Convert parameter value from string to appropriate Python type based on value_type specification.
        
        Args:
            value: String representation of the parameter value
            value_type: Type specification for conversion
            
        Returns:
            Converted value in appropriate Python type
        """

        if value is None:
            return None
            
        try:
            if value_type == 'string':
                return value
            
            elif value_type == 'integer':
                return int(value)
            
            elif value_type == 'float':
                return float(value)
            
            elif value_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'on')
            
            elif value_type == 'json':
                return json.loads(value)
            
            elif value_type == 'list':
                return json.loads(value) if value.startswith('[') else value.split(',')
            
            elif value_type == 'dict':
                return json.loads(value)
            
            else:
                logger.warning(f"Unknown value type '{value_type}', returning as string")
                return value
                
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Error converting value '{value}' to type '{value_type}': {str(e)}")
            return value

    async def _log_configuration_access(
        self, 
        connection: Connection,
        namespace: str, 
        environment: str, 
        service_name: str,
        parameter_count: int,
        sensitive_count: int
    ) -> None:
        
        """
        Log configuration access for audit trail and security monitoring.
        
        Args:
            connection: Active database connection
            namespace: Configuration namespace accessed
            environment: Environment accessed
            service_name: Service name that accessed configuration
            parameter_count: Total number of parameters accessed
            sensitive_count: Number of sensitive parameters accessed
        """
        
        try:
            
            await connection.execute("""
                INSERT INTO config.audit_log 
                (operation, changed_by, metadata, correlation_id)
                VALUES ($1, $2, $3, $4)
            """,

            'CONFIG_ACCESS',
            service_name,
            
            json.dumps({
                'namespace': namespace,
                'environment': environment,
                'service_name': service_name,
                'parameter_count': parameter_count,
                'sensitive_count': sensitive_count,
                'access_timestamp': datetime.now(timezone.utc).isoformat()
            }),

            #Correlation ID would come from the request's context
            None  
            )
            
        except Exception as e:
            #Audit logging failures should not prevent configuration retrieval
            logger.warning(f"Failed to log configuration access: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        
        """
        Perform comprehensive database health check including connectivity, performance, and resource utilisation.
        
        Returns:
            Dictionary containing detailed health status and performance metrics
        """

        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': {}
        }
        
        try:
            if not self._pool:
                health_status['status'] = 'unhealthy'
                health_status['error'] = 'Connection pool not initialized'
                return health_status
            
            #Testing basic connectivity with timeout
            start_time = time.time()
            
            async with asyncio.timeout(5.0):
                
                async with self._pool.acquire() as connection:
                    #Testing basic query execution
                    result = await connection.fetchval("SELECT 1")
                    
                    if result != 1:
                        raise DatabaseError("Basic query test failed")
                    
                    #Testing database-specific functionality
                    await connection.fetchval("SELECT COUNT(*) FROM config.namespaces")
                    
            connectivity_time = time.time() - start_time
            
            health_status['checks']['connectivity'] = {
                'status': 'healthy',
                'response_time_seconds': round(connectivity_time, 3)
            }
            
            #Checking the connection pool's statistics
            pool_stats = {
                'size': self._pool.get_size(),
                'min_size': self._pool.get_min_size(),
                'max_size': self._pool.get_max_size(),
                'idle_connections': self._pool.get_idle_size()
            }
            
            health_status['checks']['connection_pool'] = {
                'status': 'healthy',
                'statistics': pool_stats
            }
            
            #Checking for any connection pool issues
            if pool_stats['size'] >= pool_stats['max_size'] * 0.9:
                health_status['checks']['connection_pool']['status'] = 'warning'
                health_status['checks']['connection_pool']['warning'] = 'Connection pool near capacity'
            
        except asyncio.TimeoutError:
            health_status['status'] = 'unhealthy'
            
            health_status['checks']['connectivity'] = {
                'status': 'unhealthy',
                'error': 'Database connectivity timeout'
            }

        except Exception as e:
            health_status['status'] = 'unhealthy'
            
            health_status['checks']['connectivity'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return health_status

    async def get_connection_statistics(self) -> Dict[str, Any]:
        
        """
        Retrieve comprehensive connection pool and database performance statistics.
        
        Returns:
            Dictionary containing detailed connection and performance statistics
        """

        if not self._pool:
            return {'error': 'Connection pool not initialized'}
        
        try:
            
            stats = {
                'pool_size': self._pool.get_size(),
                'pool_min_size': self._pool.get_min_size(),
                'pool_max_size': self._pool.get_max_size(),
                'idle_connections': self._pool.get_idle_size(),
                'active_connections': self._pool.get_size() - self._pool.get_idle_size(),
                'total_queries_executed': self._connection_statistics.get('total_queries_executed', 0),
                'average_query_time': self._connection_statistics.get('average_query_time', 0.0),
                'failed_connections': self._connection_statistics.get('failed_connections', 0)
            }
            
            #Getting additional database statistics if available
            try:
                async with self._pool.acquire() as connection:
                    
                    #Querying the database's statistics
                    db_stats = await connection.fetchrow("""
                        SELECT 
                            numbackends as active_backends,
                            xact_commit as committed_transactions,
                            xact_rollback as rolled_back_transactions,
                            blks_read as blocks_read,
                            blks_hit as blocks_hit,
                            tup_returned as tuples_returned,
                            tup_fetched as tuples_fetched
                        FROM pg_stat_database 
                        WHERE datname = current_database()
                    """)
                    
                    if db_stats:
                        stats.update(dict(db_stats))
                        
                        #Calculating the cache hit ratio
                        if db_stats['blocks_read'] + db_stats['blocks_hit'] > 0:
                            
                            stats['cache_hit_ratio'] = db_stats['blocks_hit'] / (
                                db_stats['blocks_read'] + db_stats['blocks_hit']
                            )
                        
            except Exception as e:
                logger.warning(f"Could not retrieve extended database statistics: {str(e)}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving connection statistics: {str(e)}")
            return {'error': str(e)}

    async def verify_health(self) -> None:
        
        """
        Perform health verification with automatic recovery procedures for common issues.
        
        This method performs comprehensive health checks and attempts automatic recovery
        for detected issues including connection pool problems and performance degradation.
        
        Raises:
            DatabaseError: If critical health issues cannot be resolved
        """

        try:
            health_status = await self.health_check()
            
            if health_status['status'] != 'healthy':
                logger.warning(f"Database health check failed: {health_status}")
                
                #Attempting automatic recovery procedures
                await self._attempt_recovery()
                
                #Re-checking the health after the recovery attempt
                health_status = await self.health_check()
                
                if health_status['status'] != 'healthy':
                    raise DatabaseError(f"Database health verification failed: {health_status}")
                    
        except Exception as e:
            logger.error(f"Health verification failed: {str(e)}")
            raise DatabaseError(f"Database health verification failed: {str(e)}")

    async def _attempt_recovery(self) -> None:
        
        """
        Attempt automatic recovery from common database issues.
        
        This method implements recovery procedures for connection pool issues,
        performance degradation, and other recoverable database problems.
        """
        
        try:
            #Resetting the connection pool if it appears to be in a bad state
            if self._pool:
                
                pool_stats = {
                    'size': self._pool.get_size(),
                    'max_size': self._pool.get_max_size(),
                    'idle_connections': self._pool.get_idle_size()
                }
                
                #If the pool is at capacity with no idle connections, attempting recovery
                if (pool_stats['size'] >= pool_stats['max_size'] and 
                    pool_stats['idle_connections'] == 0):
                    logger.info("Attempting connection pool recovery")
                    
                    #Closing and recreating the connection pool
                    await self._pool.close()
                    await self.initialize()
                    
                    logger.info("Connection pool recovery completed")
                    
        except Exception as e:
            logger.error(f"Database recovery attempt failed: {str(e)}")

    async def shutdown(self) -> None:
        
        """
        Gracefully shutdown database connections and cleanup resources.
        
        This method ensures all connections are properly closed and resources
        are cleaned up before application shutdown.
        """
        
        try:
            if self._pool:
                logger.info("Closing database connection pool")
                await self._pool.close()
                self._pool = None
                logger.info("Database connection pool closed successfully")
                
        except Exception as e:
            logger.error(f"Error during database shutdown: {str(e)}")
            raise DatabaseError(f"Database shutdown failed: {str(e)}")