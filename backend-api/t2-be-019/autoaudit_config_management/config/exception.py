"""
AutoAudit Configuration Management System - Exception Classes

This module defines comprehensive exception classes for the AutoAudit Configuration
Management System, providing structured error handling with detailed error information,
context tracking, and recovery guidance for all system components.

The exception hierarchy provides specific exception types for different error scenarios
including database errors, cache failures, validation errors, security violations,
and system-level failures with comprehensive error context and recovery procedures.

Author: Senior Lead, AutoAudit
Owner: Backend Team, AutoAudit
"""

import traceback
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone

class AutoAuditConfigException(Exception):
    
    """
    Base exception class for all AutoAudit Configuration Management System exceptions.
    
    Provides comprehensive error context, structured error information, and integration
    with monitoring and alerting systems for enterprise-grade error management.
    
    This base class establishes the foundation for consistent error handling patterns
    across the entire configuration management system with support for error correlation,
    recovery procedures, and detailed operational context.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        retry_after: Optional[int] = None,
        recovery_suggestions: Optional[List[str]] = None,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        
        """
        Initialise base exception with comprehensive error context and metadata.
        
        Args:
            message: Primary error message describing the failure
            error_code: Structured error code for programmatic error handling
            details: Dictionary containing detailed error context and parameters
            correlation_id: Request correlation identifier for distributed tracing
            retry_after: Suggested retry delay in seconds for transient failures
            recovery_suggestions: List of actionable recovery recommendations
            component: System component where the error originated
            operation: Specific operation that failed
            original_exception: Original exception that caused this error
        """
        
        super().__init__(message)
        
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.correlation_id = correlation_id
        self.retry_after = retry_after
        self.recovery_suggestions = recovery_suggestions or []
        self.component = component
        self.operation = operation
        self.original_exception = original_exception
        
        #Adding a timestamp and error tracking information
        self.timestamp = datetime.now(timezone.utc)
        self.stack_trace = traceback.format_exc() if traceback.format_exc() != 'NoneType: None\n' else None
        
        #Adding the original exception details, if available
        if original_exception:
            
            self.details.update({
                'original_error_type': type(original_exception).__name__,
                'original_error_message': str(original_exception),
                'original_error_args': getattr(original_exception, 'args', [])
            })
    
    def to_dict(self) -> Dict[str, Any]:
        
        """
        Convert the exception to dictionary format for logging and API responses.
        
        Returns:
            Dictionary containing comprehensive error information suitable for
            structured logging, API responses, and monitoring systems.
        """

        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'correlation_id': self.correlation_id,
            'retry_after': self.retry_after,
            'recovery_suggestions': self.recovery_suggestions,
            'component': self.component,
            'operation': self.operation,
            'timestamp': self.timestamp.isoformat(),
            'exception_type': type(self).__name__,
            'stack_trace': self.stack_trace
        }
    
    def __str__(self) -> str:
        
        """Return formatted error message with context information."""
        
        context_parts = []
        
        if self.component:
            context_parts.append(f"Component: {self.component}")
        
        if self.operation:
            context_parts.append(f"Operation: {self.operation}")
        
        if self.error_code:
            context_parts.append(f"Code: {self.error_code}")
        
        context_str = f" ({', '.join(context_parts)})" if context_parts else ""
        
        return f"{self.message}{context_str}"

class DatabaseError(AutoAuditConfigException):
    
    """
    Exception raised for database-related errors including connection failures,
    query execution errors, transaction failures, and data integrity violations.
    
    This exception provides specialised handling for PostgreSQL-specific errors
    with connection recovery procedures and query optimization recommendations.
    """
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        postgres_code: Optional[str] = None,
        connection_info: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialise database exception with PostgreSQL-specific error context.
        
        Args:
            message: Database error message
            query: SQL query that caused the error
            parameters: Query parameters that were used
            postgres_code: PostgreSQL error code (SQLSTATE)
            connection_info: Database connection information
            **kwargs: Additional parameters passed to base exception
        """
        details = kwargs.get('details', {})
        
        if query:
            details['query'] = query[:500] + '...' if len(query) > 500 else query
        
        if parameters:
            #Sanitising sensitive parameters for logging
            sanitized_params = self._sanitize_parameters(parameters)
            details['parameters'] = sanitized_params
        
        if postgres_code:
            details['postgres_code'] = postgres_code
            details['postgres_category'] = self._categorize_postgres_error(postgres_code)
        
        if connection_info:
            details['connection_info'] = connection_info
        
        #Adding database-specific recovery suggestions
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        recovery_suggestions.extend(self._get_database_recovery_suggestions(postgres_code))
        
        super().__init__(
            message=message,
            details=details,
            component="database",
            recovery_suggestions=recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions']}
        )
    
    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        
        """Sanitise database parameters by masking sensitive values."""
        
        sensitive_keys = ['password', 'secret', 'token', 'key', 'auth']
        sanitized = {}
        
        for key, value in parameters.items():
            
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = '[MASKED]'
            
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _categorize_postgres_error(self, postgres_code: str) -> str:
        
        """Categorise PostgreSQL error codes into logical groups."""
        
        if not postgres_code:
            return "unknown"
        
        code_categories = {
            '08': 'connection_exception',
            '23': 'integrity_constraint_violation',
            '25': 'invalid_transaction_state',
            '40': 'transaction_rollback',
            '42': 'syntax_error_or_access_rule_violation',
            '53': 'insufficient_resources',
            '57': 'operator_intervention',
            '58': 'system_error'
        }
        
        category_prefix = postgres_code[:2]
        return code_categories.get(category_prefix, 'other_error')
    
    def _get_database_recovery_suggestions(self, postgres_code: str) -> List[str]:
        
        """Get recovery suggestions based on PostgreSQL error codes."""
        
        if not postgres_code:
            return []
        
        suggestions_map = {
            '08': [
                "Check database connection parameters and network connectivity",
                "Verify database server is running and accepting connections",
                "Review connection pool configuration and limits",
                "Check firewall rules and network security groups"
            ],

            '23': [
                "Review data integrity constraints and foreign key relationships",
                "Validate input data before database operations",
                "Check for duplicate key violations and unique constraints",
                "Implement proper data validation at application level"
            ],

            '25': [
                "Ensure proper transaction management and commit/rollback procedures",
                "Review transaction isolation levels and locking behavior",
                "Check for deadlock conditions and resolve transaction conflicts"
            ],

            '40': [
                "Implement retry logic with exponential backoff for transient failures",
                "Review transaction timeout settings and adjust if necessary",
                "Analyse deadlock patterns and optimize query execution order"
            ],

            '42': [
                "Validate SQL syntax and query structure",
                "Check database user permissions and access rights",
                "Review table and column names for correctness",
                "Ensure proper SQL parameterization to prevent injection"
            ],
            '53': [
                "Monitor database resource usage (CPU, memory, disk space)",
                "Scale database resources or optimize resource-intensive queries",
                "Review connection pool limits and adjust based on capacity",
                "Implement query optimisation and indexing strategies"
            ],

            '57': [
                "Check database server logs for administrative actions",
                "Coordinate with database administrators for maintenance windows",
                "Implement graceful degradation for planned maintenance"
            ],

            '58': [
                "Check database server hardware and system resources",
                "Review database server logs for system-level errors",
                "Contact database administrator or system administrator",
                "Implement database failover procedures if available"
            ]
        }
        
        category_prefix = postgres_code[:2]

        return suggestions_map.get(category_prefix, [
            "Review database logs for detailed error information",
            "Contact database administrator for assistance",
            "Implement retry logic for transient database failures"

class CacheError(AutoAuditConfigException):
    
    """
    Exception raised for cache-related errors including Redis connection failures,
    serialisation errors, cache invalidation issues, and performance problems.
    
    This exception provides specialised handling for distributed caching scenarios
    with cache recovery procedures and performance optimisation recommendations.
    """
    
    def __init__(
        self,
        message: str,
        cache_operation: Optional[str] = None,
        cache_key: Optional[str] = None,
        redis_error_type: Optional[str] = None,
        connection_info: Optional[Dict[str, Any]] = None,
        **kwargs
    ):

        """
        Initialise cache exception with Redis-specific error context.
        
        Args:
            message: Cache error message
            cache_operation: Cache operation that failed (get, set, delete, etc.)
            cache_key: Cache key involved in the operation
            redis_error_type: Type of Redis error that occurred
            connection_info: Redis connection information
            **kwargs: Additional parameters passed to base exception
        """

        details = kwargs.get('details', {})
        
        if cache_operation:
            details['cache_operation'] = cache_operation
        
        if cache_key:
            #Truncating long cache keys for logging
            details['cache_key'] = cache_key[:100] + '...' if len(cache_key) > 100 else cache_key
        
        if redis_error_type:
            details['redis_error_type'] = redis_error_type
        
        if connection_info:
            details['connection_info'] = connection_info
        
        #Adding cache-specific recovery suggestions
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        
        recovery_suggestions.extend([
            "Check Redis server connectivity and cluster status",
            "Verify cache configuration and connection parameters",
            "Monitor Redis memory usage and eviction policies",
            "Implement cache circuit breaker patterns for resilience",
            "Consider cache warming strategies for critical data"
        ])
        
        super().__init__(
            message = message,
            details = details,
            component = "cache",
            recovery_suggestions = recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions']}
        )

class ConfigurationNotFoundException(AutoAuditConfigException):
    
    """
    Exception raised when requested configuration parameters are not found
    in the hierarchical configuration structure.
    
    This exception provides context about the configuration lookup process
    and suggestions for resolving missing configuration scenarios.
    """
    
    def __init__(
        self,
        message: str,
        namespace: Optional[str] = None,
        environment: Optional[str] = None,
        service_name: Optional[str] = None,
        parameter_key: Optional[str] = None,
        searched_locations: Optional[List[str]] = None,
        **kwargs
    ):
        
        """
        Initialise configuration not found exception with lookup context.
        
        Args:
            message: Configuration not found error message
            namespace: Namespace that was searched
            environment: Environment that was searched
            service_name: Service name that was searched
            parameter_key: Specific parameter key that was not found
            searched_locations: List of locations that were searched
            **kwargs: Additional parameters passed to base exception
        """

        details = kwargs.get('details', {})
        
        if namespace:
            details['namespace'] = namespace
        
        if environment:
            details['environment'] = environment
        
        if service_name:
            details['service_name'] = service_name
        
        if parameter_key:
            details['parameter_key'] = parameter_key
        
        if searched_locations:
            details['searched_locations'] = searched_locations
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        
        recovery_suggestions.extend([
            "Verify configuration namespace and environment names",
            "Check if configuration parameters are defined in parent scopes",
            "Review service registration and configuration hierarchy",
            "Ensure configuration parameters are not expired or inactive",
            "Check configuration access permissions and scopes"
        ])
        
        super().__init__(
            message = message,
            error_code = "CONFIG_NOT_FOUND",
            details = details,
            component = "configuration",
            recovery_suggestions=recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions']}
        )

class ValidationError(AutoAuditConfigException):
    
    """
    Exception raised for configuration validation failures including schema
    validation errors, business rule violations, and data format issues.
    
    This exception provides detailed validation context with specific error
    locations and remediation guidance for configuration corrections.
    """
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        parameter_key: Optional[str] = None,
        validation_rule: Optional[str] = None,
        schema_version: Optional[str] = None,
        **kwargs
    ):
        
        """
        Initialise validation exception with detailed validation context.
        
        Args:
            message: Validation error message
            validation_errors: List of specific validation errors
            parameter_key: Parameter key that failed validation
            validation_rule: Validation rule that was violated
            schema_version: Schema version used for validation
            **kwargs: Additional parameters passed to base exception
        """
        
        details = kwargs.get('details', {})
        
        if validation_errors:
            details['validation_errors'] = validation_errors
            details['error_count'] = len(validation_errors)
        
        if parameter_key:
            details['parameter_key'] = parameter_key
        
        if validation_rule:
            details['validation_rule'] = validation_rule
        
        if schema_version:
            details['schema_version'] = schema_version
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        
        recovery_suggestions.extend([
            "Review configuration parameter values against schema requirements",
            "Check data types and format constraints for parameters",
            "Validate business rules and dependency requirements",
            "Ensure required parameters are provided with valid values",
            "Review validation schema documentation and examples"
        ])
        
        super().__init__(
            message = message,
            error_code = "VALIDATION_ERROR",
            details = details,
            component = "validation",
            recovery_suggestions = recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions']}
        )

class SecurityError(AutoAuditConfigException):
    
    """
    Exception raised for security-related errors including authentication failures,
    authorisation violations, encryption errors, and security policy breaches.
    
    This exception provides security context while avoiding exposure of sensitive
    information in logs and error messages.
    """
    
    def __init__(
        self,
        message: str,
        security_violation_type: Optional[str] = None,
        requested_resource: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        security_policy: Optional[str] = None,
        **kwargs
    ):

        """
        Initialise security exception with security context.
        
        Args:
            message: Security error message (sanitized for logging)
            security_violation_type: Type of security violation
            requested_resource: Resource that was being accessed
            user_context: Sanitized user context information
            security_policy: Security policy that was violated
            **kwargs: Additional parameters passed to base exception
        """

        details = kwargs.get('details', {})
        
        if security_violation_type:
            details['security_violation_type'] = security_violation_type
        
        if requested_resource:
            #Sanitising the resource information for security
            details['requested_resource'] = self._sanitize_resource_info(requested_resource)
        
        if user_context:
            #Including only non-sensitive user context
            details['user_context'] = self._sanitize_user_context(user_context)
        
        if security_policy:
            details['security_policy'] = security_policy
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        
        recovery_suggestions.extend([
            "Verify authentication credentials and token validity",
            "Check user permissions and role assignments",
            "Review security policy configuration and access rules",
            "Ensure proper security context and scope for operations",
            "Contact system administrator for access permission issues"
        ])
        
        super().__init__(
            message = message,
            error_code = "SECURITY_ERROR",
            details = details,
            component = "security",
            recovery_suggestions = recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions']}
        )
    
    def _sanitize_resource_info(self, resource: str) -> str:
        
        """Sanitise resource information to prevent sensitive data exposure."""
        
        #Removing potential sensitive information from resource paths
        if len(resource) > 100:
            return resource[:50] + '[...TRUNCATED...]' + resource[-20:]
        
        return resource
    
    def _sanitize_user_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        
        """Sanitise user context to prevent sensitive information exposure."""
        
        sensitive_keys = ['password', 'secret', 'token', 'key', 'credentials']
        sanitized = {}
        
        for key, value in context.items():
            
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            
            elif key in ['user_id', 'service_name', 'scopes', 'roles']:
                sanitized[key] = value
            
        return sanitized

class ServiceUnavailableError(AutoAuditConfigException):
    
    """
    Exception raised when configuration service or dependent services are
    temporarily unavailable or experiencing degraded performance.
    
    This exception provides service availability context and retry guidance
    for transient service failures and maintenance scenarios.
    """
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        health_status: Optional[Dict[str, Any]] = None,
        estimated_recovery_time: Optional[int] = None,
        maintenance_window: Optional[Dict[str, Any]] = None,
        **kwargs
    ):

        """
        Initialise service unavailable exception with availability context.
        
        Args:
            message: Service unavailability message
            service_name: Name of the unavailable service
            health_status: Current health status information
            estimated_recovery_time: Estimated recovery time in seconds
            maintenance_window: Scheduled maintenance window information
            **kwargs: Additional parameters passed to base exception
        """

        details = kwargs.get('details', {})
        
        if service_name:
            details['service_name'] = service_name
        
        if health_status:
            details['health_status'] = health_status
        
        if estimated_recovery_time:
            details['estimated_recovery_time_seconds'] = estimated_recovery_time
        
        if maintenance_window:
            details['maintenance_window'] = maintenance_window
        
        #Setting retry_after from estimated_recovery_time, if not provided
        retry_after = kwargs.get('retry_after', estimated_recovery_time)
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        
        recovery_suggestions.extend([
            "Implement retry logic with exponential backoff",
            "Check service health endpoints for status updates",
            "Use cached configuration data, if available, during outages",
            "Implement circuit breaker patterns for service resilience",
            "Monitor service status and maintenance announcements"
        ])
        
        super().__init__(
            message = message,
            error_code = "SERVICE_UNAVAILABLE",
            details = details,
            retry_after = retry_after,
            component = "service_availability",
            recovery_suggestions = recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions', 'retry_after']}
        )

class ConfigurationVersionConflictError(AutoAuditConfigException):
    
    """
    Exception raised when configuration version conflicts occur during
    concurrent modifications or when attempting to apply outdated changes.
    
    This exception provides version conflict context and resolution strategies
    for maintaining configuration consistency in distributed environments.
    """
    
    def __init__(
        self,
        message: str,
        current_version: Optional[int] = None,
        requested_version: Optional[int] = None,
        parameter_key: Optional[str] = None,
        last_modified_by: Optional[str] = None,
        last_modified_at: Optional[datetime] = None,
        **kwargs
    ):
        
        """
        Initialise version conflict exception with version context.
        
        Args:
            message: Version conflict error message
            current_version: Current configuration version
            requested_version: Version that was requested for modification
            parameter_key: Parameter key involved in the conflict
            last_modified_by: User or service that last modified the configuration
            last_modified_at: Timestamp of last modification
            **kwargs: Additional parameters passed to base exception
        """
        
        details = kwargs.get('details', {})
        
        if current_version is not None:
            details['current_version'] = current_version
        
        if requested_version is not None:
            details['requested_version'] = requested_version
        
        if parameter_key:
            details['parameter_key'] = parameter_key
        
        if last_modified_by:
            details['last_modified_by'] = last_modified_by
        
        if last_modified_at:
            details['last_modified_at'] = last_modified_at.isoformat()
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        
        recovery_suggestions.extend([
            "Refresh configuration data to get the latest version",
            "Implement optimistic locking with version checks",
            "Use configuration merge strategies for concurrent changes",
            "Review change history to understand conflicting modifications",
            "Coordinate configuration changes through change management processes"
        ])
        
        super().__init__(
            message = message,
            error_code = "VERSION_CONFLICT",
            details = details,
            component = "version_control",
            recovery_suggestions = recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions']}
        )

class EncryptionError(AutoAuditConfigException):
    
    """
    Exception raised for encryption and decryption errors including key
    management failures, cryptographic operation errors, and security violations.
    
    This exception provides encryption context while maintaining security
    by avoiding exposure of cryptographic details in logs.
    """
    
    def __init__(
        self,
        message: str,
        encryption_operation: Optional[str] = None,
        key_id: Optional[str] = None,
        algorithm: Optional[str] = None,
        **kwargs
    ):
        
        """
        Initialise encryption exception with cryptographic context.
        
        Args:
            message: Encryption error message (sanitised)
            encryption_operation: Operation that failed (encrypt, decrypt, key_rotation)
            key_id: Identifier of the encryption key involved
            algorithm: Cryptographic algorithm being used
            **kwargs: Additional parameters passed to base exception
        """
        
        details = kwargs.get('details', {})
        
        if encryption_operation:
            details['encryption_operation'] = encryption_operation
        
        if key_id:
            #Only including the key ID; not the actual key material
            details['key_id'] = key_id
        
        if algorithm:
            details['algorithm'] = algorithm
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [])
        
        recovery_suggestions.extend([
            "Verify encryption key availability and permissions",
            "Check key management service connectivity and status",
            "Ensure proper key rotation and lifecycle management",
            "Review encryption algorithm configuration and compatibility",
            "Contact security team for cryptographic key issues"
        ])
        
        super().__init__(
            message = message,
            error_code = "ENCRYPTION_ERROR",
            details = details,
            component = "encryption",
            recovery_suggestions = recovery_suggestions,
            **{k: v for k, v in kwargs.items() if k not in ['details', 'recovery_suggestions']}
        )

#Utility functions for exception handling

def handle_exception_with_context(
    operation: str,
    component: str,
    original_exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> AutoAuditConfigException:
    
    """
    Convert generic exceptions to structured AutoAudit exceptions with comprehensive context.
    
    This function provides centralised exception handling with consistent error context,
    recovery suggestions, and integration with monitoring and alerting systems.
    
    Args:
        operation: Operation that was being performed when the error occurred
        component: System component where the error originated
        original_exception: Original exception that was caught
        context: Additional context information about the operation
        correlation_id: Request correlation identifier for distributed tracing
        
    Returns:
        Structured AutoAudit exception with comprehensive error context
    """

    #Mapping common exception types to the specific AutoAudit exceptions
    exception_mapping = {
        'psycopg2.Error': DatabaseError,
        'asyncpg.PostgresError': DatabaseError,
        'redis.RedisError': CacheError,
        'redis.ConnectionError': CacheError,
        'ConnectionRefusedError': ServiceUnavailableError,
        'TimeoutError': ServiceUnavailableError,
        'ValueError': ValidationError,
        'KeyError': ConfigurationNotFoundException,
        'PermissionError': SecurityError,
        'AuthenticationError': SecurityError,
        'AuthorizationError': SecurityError
    }
    
    #Getting the original exception type name
    original_type = type(original_exception).__name__
    original_module = getattr(type(original_exception), '__module__', '')
    full_type = f"{original_module}.{original_type}" if original_module else original_type
    
    #Selecting the appropriate exception class
    exception_class = AutoAuditConfigException
    
    for exception_pattern, mapped_class in exception_mapping.items():
        
        if exception_pattern in full_type or exception_pattern == original_type:
            exception_class = mapped_class
            break
    
    #Building a comprehensive error message
    error_message = f"{operation} failed: {str(original_exception)}"
    
    #Building the context details
    details = context or {}
    
    details.update({
        'operation': operation,
        'original_exception_type': original_type,
        'original_exception_module': original_module
    })
    
    #Creating a structured exception with full context
    return exception_class(
        message = error_message,
        details = details,
        component = component,
        operation = operation,
        original_exception = original_exception,
        correlation_id = correlation_id
    )

def is_retriable_exception(exception: Exception) -> bool:
    
    """
    Determine if an exception represents a transient failure that can be retried.
    
    Args:
        exception: Exception to evaluate for retry eligibility
        
    Returns:
        Boolean indicating whether the exception is retriable
    """
    
    retriable_exceptions = {
        DatabaseError: ['connection_exception', 'transaction_rollback', 'insufficient_resources'],
        CacheError: ['connection_failure', 'timeout', 'cluster_failover'],
        ServiceUnavailableError: ['*'],  # All service unavailable errors are retriable
    }
    
    #Checking if the exception type is retriable
    exception_type = type(exception)
    
    if exception_type not in retriable_exceptions:
        return False
    
    #Checking the specific error categories for database and cache errors
    if isinstance(exception, (DatabaseError, CacheError)):
        error_category = exception.details.get('error_category', 'unknown')
        allowed_categories = retriable_exceptions[exception_type]
        
        if '*' in allowed_categories:
            return True
        
        return error_category in allowed_categories
    
    #Service unavailable errors are always retriable
    if isinstance(exception, ServiceUnavailableError):
        return True
    
    return False

def get_retry_delay(exception: Exception, attempt_number: int, base_delay: float = 1.0) -> float:
    
    """
    Calculate retry delay using exponential backoff with jitter for transient failures.
    
    Args:
        exception: Exception that triggered the retry
        attempt_number: Current retry attempt number (1-based)
        base_delay: Base delay in seconds for exponential backoff calculation
        
    Returns:
        Retry delay in seconds with exponential backoff and jitter
    """

    import random
    
    #Getting suggested retry delay from exception, if available
    if hasattr(exception, 'retry_after') and exception.retry_after:
        return float(exception.retry_after)
    
    #Calculating the exponential backoff with jitter
    exponential_delay = base_delay * (2 ** (attempt_number - 1))
    
    #Adding jitter to prevent thundering herd effect
    jitter = random.uniform(0.1, 0.5) * exponential_delay
    
    #Capping the maximum delay at 60 seconds
    total_delay = min(exponential_delay + jitter, 60.0)
    
    return total_delay