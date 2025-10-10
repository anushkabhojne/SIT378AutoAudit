"""
AutoAudit Configuration Management System - Data Models

This module defines comprehensive data models and schemas for the AutoAudit Configuration
Management System using Pydantic for validation, serialisation, and API documentation.

The models provide type-safe representations for configuration parameters, audit logs,
service registrations, validation rules, and system metadata with comprehensive
validation rules and serialisation support.

Author: Senior Lead, AutoAudit
Owner: Backend Team, AutoAudit
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Set, Literal
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import UUID4, EmailStr, SecretStr

class ValueType(str, Enum):
    
    """
    Enumeration of supported configuration parameter value types with comprehensive
    type validation and conversion support for enterprise configuration management.
    """

    STRING = "string"
    INTEGER = "integer" 
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    DICT = "dict"
    SECRET = "secret"
    URL = "url"
    EMAIL = "email"
    IP_ADDRESS = "ip_address"
    REGEX = "regex"

class OperationType(str, Enum):
    
    """
    Enumeration of audit log operation types for comprehensive change tracking
    and security monitoring across the configuration management system.
    """

    CREATE = "CREATE"
    READ = "READ" 
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CONFIG_ACCESS = "CONFIG_ACCESS"
    BULK_UPDATE = "BULK_UPDATE"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    SECURITY_EVENT = "SECURITY_EVENT"
    SYSTEM_EVENT = "SYSTEM_EVENT"

class ValidationRuleType(str, Enum):
    
    """
    Enumeration of configuration validation rule types supporting comprehensive
    parameter validation and business rule enforcement.
    """

    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    PATTERN = "pattern"
    RANGE = "range"
    ENUM = "enum"
    CUSTOM = "custom"
    DEPENDENCY = "dependency"
    MUTUAL_EXCLUSION = "mutual_exclusion"

class Environment(str, Enum):
    
    """
    Enumeration of standard deployment environments with priority ordering
    for hierarchical configuration resolution.
    """

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class BaseConfigurationModel(BaseModel):
    
    """
    Base model providing common fields and configuration for all configuration
    management data models with comprehensive metadata and audit support.
    """

    id: Optional[UUID4] = Field(default_factory = uuid.uuid4, description = "Unique identifier")
    created_at: Optional[datetime] = Field(default_factory = lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory = lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(None, max_length = 255)
    metadata: Dict[str, Any] = Field(default_factory = dict)
    
    class Config:
        
        """Pydantic model configuration with comprehensive validation and serialization settings."""
        
        validate_assignment = True
        use_enum_values = True
        allow_population_by_field_name = True
        
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: lambda u: str(u)
        }

class ConfigurationNamespace(BaseConfigurationModel):
    
    """
    Model representing a configuration namespace for organisational structure
    and hierarchical configuration management within the AutoAudit ecosystem.
    """
    
    name: str = Field(..., min_length=1, max_length = 255, regex = r'^[a-zA-Z0-9_-]+$')
    description: Optional[str] = Field(None, max_length = 1000)
    is_active: bool = Field(True)
    priority: int = Field(0, ge=0, le=100)
    
    @validator('name')
    def validate_namespace_name(cls, v):
        
        """Validate namespace name follows organisational naming conventions."""
        
        reserved_names = ['system', 'admin', 'config', 'internal']
        
        if v.lower() in reserved_names:
            raise ValueError(f"Namespace name '{v}' is reserved")
        
        return v.lower()

class ConfigurationEnvironment(BaseConfigurationModel):
    
    """
    Model representing a deployment environment with priority-based configuration
    resolution and production safety controls.
    """
    
    name: Environment = Field(..., description="Environment name")
    description: Optional[str] = Field(None, max_length = 1000)
    priority: int = Field(0, ge = 0, le = 100, description = "Priority for configuration resolution")
    is_production: bool = Field(False, description = "Production environment flag")
    deployment_region: Optional[str] = Field(None, max_length = 100)
    resource_limits: Dict[str, Any] = Field(default_factory = dict)
    
    @validator('priority')
    def validate_priority_for_production(cls, v, values):
        
        """Ensure production environments have appropriate priority settings."""
        
        if values.get('is_production') and v < 90:
            raise ValueError("Production environments must have priority >= 90")
        
        return v

class ServiceRegistration(BaseConfigurationModel):
    
    """
    Model representing a registered service within the AutoAudit ecosystem
    with comprehensive service metadata and health monitoring capabilities.
    """
    
    namespace_id: UUID4 = Field(..., description = "Parent namespace identifier")
    name: str = Field(..., min_length = 1, max_length = 255, regex = r'^[a-zA-Z0-9_-]+$')
    description: Optional[str] = Field(None, max_length = 1000)
    service_type: str = Field("microservice", max_length = 100)
    version: Optional[str] = Field(None, regex = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$')
    health_check_endpoint: Optional[str] = Field(None, max_length = 500)
    api_documentation_url: Optional[str] = Field(None, max_length = 500)
    repository_url: Optional[str] = Field(None, max_length = 500)
    maintainer_team: Optional[str] = Field(None, max_length = 255)
    deployment_strategy: str = Field("rolling", max_length = 50)
    resource_requirements: Dict[str, Any] = Field(default_factory = dict)
    dependencies: List[str] = Field(default_factory = list)
    tags: List[str] = Field(default_factory = list)
    
    @validator('health_check_endpoint')
    def validate_health_check_url(cls, v):
        
        """Validate health check endpoint URL format."""
        
        if v and not (v.startswith('http://') or v.startswith('https://') or v.startswith('/')):
            raise ValueError("Health check endpoint must be a valid URL or path")
        
        return v

class ConfigurationParameter(BaseConfigurationModel):
    
    """
    Model representing a configuration parameter with comprehensive validation,
    encryption support, and hierarchical resolution capabilities.
    """
    
    namespace_id: UUID4 = Field(..., description = "Parent namespace identifier")
    environment_id: Optional[UUID4] = Field(None, description = "Target environment identifier")
    service_id: Optional[UUID4] = Field(None, description = "Target service identifier")
    key: str = Field(..., min_length = 1, max_length = 500, description = "Configuration parameter key")
    value: Optional[str] = Field(None, description = "Configuration parameter value")
    value_type: ValueType = Field(ValueType.STRING, description = "Parameter value type")
    is_sensitive: bool = Field(False, description = "Sensitive parameter flag")
    is_encrypted: bool = Field(False, description = "Encryption status flag")
    encryption_key_id: Optional[str] = Field(None, max_length = 255)
    description: Optional[str] = Field(None, max_length = 1000)
    validation_schema: Optional[Dict[str, Any]] = Field(None)
    tags: List[str] = Field(default_factory = list)
    priority: int = Field(0, ge = 0, le = 100)
    version: int = Field(1, ge = 1)
    effective_date: Optional[datetime] = Field(None)
    expiration_date: Optional[datetime] = Field(None)
    
    @validator('key')
    def validate_parameter_key(cls, v):
        
        """Validate parameter key follows naming conventions."""
        
        import re
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9._-]*$', v):
            raise ValueError("Parameter key must start with letter and contain only alphanumeric, dot, underscore, or hyphen")
        
        return v
    
    @root_validator
    def validate_encryption_consistency(cls, values):
        
        """Ensure encryption settings are consistent."""
        
        is_sensitive = values.get('is_sensitive', False)
        is_encrypted = values.get('is_encrypted', False)
        encryption_key_id = values.get('encryption_key_id')
        
        if is_encrypted and not encryption_key_id:
            raise ValueError("Encrypted parameters must have encryption_key_id")
        
        if encryption_key_id and not is_encrypted:
            raise ValueError("Parameters with encryption_key_id must be marked as encrypted")
        
        if is_encrypted and not is_sensitive:
            
            #Auto-marking the encrypted parameters as sensitive
            values['is_sensitive'] = True
        
        return values
    
    @validator('expiration_date')
    def validate_expiration_after_effective(cls, v, values):
        
        """Ensure expiration date is after effective date."""
        
        effective_date = values.get('effective_date')
        
        if v and effective_date and v <= effective_date:
            raise ValueError("Expiration date must be after effective date")
        
        return v

class ConfigurationValidationRule(BaseConfigurationModel):
    
    """
    Model representing configuration validation rules with comprehensive
    business rule enforcement and custom validation logic support.
    """
    
    namespace_id: UUID4 = Field(..., description = "Parent namespace identifier")
    service_id: Optional[UUID4] = Field(None, description = "Target service identifier")
    parameter_pattern: str = Field(..., min_length = 1, max_length = 500)
    validation_type: ValidationRuleType = Field(..., description = "Type of validation rule")
    validation_config: Dict[str, Any] = Field(..., description = "Validation configuration parameters")
    error_message: Optional[str] = Field(None, max_length = 500)
    is_active: bool = Field(True)
    severity: str = Field("error", regex = r'^(error|warning|info)$')
    
    @validator('validation_config')
    def validate_config_for_type(cls, v, values):
        
        """Validate configuration parameters match the validation type."""
        
        validation_type = values.get('validation_type')
        
        required_fields = {
            ValidationRuleType.MIN_LENGTH: ['min_value'],
            ValidationRuleType.MAX_LENGTH: ['max_value'], 
            ValidationRuleType.RANGE: ['min_value', 'max_value'],
            ValidationRuleType.PATTERN: ['regex'],
            ValidationRuleType.ENUM: ['allowed_values']
        }
        
        if validation_type in required_fields:
            for field in required_fields[validation_type]:
                if field not in v:
                    raise ValueError(f"Validation type {validation_type} requires field: {field}")
        
        return v

class ConfigurationAuditLog(BaseModel):
    
    """
    Model representing audit log entries for comprehensive change tracking,
    security monitoring, and compliance reporting across the configuration system.
    """
    
    id: UUID4 = Field(default_factory=uuid.uuid4)
    parameter_id: Optional[UUID4] = Field(None, description = "Related parameter identifier")
    operation: OperationType = Field(..., description = "Type of operation performed")
    old_value: Optional[str] = Field(None, description = "Previous parameter value")
    new_value: Optional[str] = Field(None, description = "New parameter value")
    changed_by: Optional[str] = Field(None, max_length = 255, description = "User or service that made the change")
    changed_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))
    client_ip: Optional[str] = Field(None, description = "Client IP address")
    user_agent: Optional[str] = Field(None, max_length = 500, description = "Client user agent")
    correlation_id: Optional[UUID4] = Field(None, description = "Request correlation identifier")
    reason: Optional[str] = Field(None, max_length = 1000, description = "Reason for the change")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True
        use_enum_values = True
        
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: lambda u: str(u)
        }

class ConfigurationSnapshot(BaseConfigurationModel):
    
    """
    Model representing configuration snapshots for versioning, rollback capabilities,
    and historical configuration state tracking.
    """

    namespace_id: UUID4 = Field(..., description = "Parent namespace identifier")
    environment_id: Optional[UUID4] = Field(None, description = "Target environment identifier")
    service_id: Optional[UUID4] = Field(None, description = "Target service identifier")
    snapshot_data: Dict[str, Any] = Field(..., description = "Complete configuration snapshot")
    snapshot_hash: str = Field(..., min_length = 64, max_length = 64, description = "SHA-256 hash of snapshot")
    description: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    
    @validator('snapshot_hash')
    def validate_hash_format(cls, v):
        
        """Validate SHA-256 hash format."""
        
        import re
        
        if not re.match(r'^[a-f0-9]{64}$', v):
            raise ValueError("Snapshot hash must be a valid SHA-256 hash (64 hex characters)")
        
        return v

#Request/Response Models for API Operations

class ConfigurationRequest(BaseModel):
    
    """
    Model for configuration retrieval requests with comprehensive filtering
    and customisation options for client applications.
    """
    
    namespace: str = Field(..., min_length=1, max_length=255)
    environment: str = Field(..., min_length=1, max_length=255)
    service_name: str = Field(..., min_length=1, max_length=255)
    include_sensitive: bool = Field(False)
    include_metadata: bool = Field(False)
    format: Literal["json", "yaml", "env"] = Field("json")
    parameter_filter: Optional[List[str]] = Field(None, description = "Specific parameters to retrieve")
    exclude_parameters: Optional[List[str]] = Field(None, description = "Parameters to exclude")

class ConfigurationResponse(BaseModel):
    
    """
    Model for configuration retrieval responses with comprehensive metadata
    and performance tracking information.
    """
    
    namespace: str
    environment: str
    service_name: str
    parameters: Dict[str, Any]
    parameter_count: int = Field(..., ge = 0)
    sensitive_count: int = Field(..., ge = 0)
    cached: bool = Field(False)
    retrieved_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))
    cache_ttl: Optional[int] = Field(None, description = "Cache TTL in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class ConfigurationUpdateRequest(BaseModel):
    
    """
    Model for configuration parameter update requests with comprehensive
    validation and change tracking support.
    """
    
    parameters: Dict[str, Any] = Field(..., min_items = 1)
    reason: Optional[str] = Field(None, max_length = 1000, description = "Reason for the update")
    effective_date: Optional[datetime] = Field(None)
    notify_services: bool = Field(True, description = "Send notifications to affected services")
    validate_only: bool = Field(False, description = "Validate changes without applying")

class ConfigurationBatch(BaseModel):
    
    """
    Model for batch configuration operations with comprehensive validation
    and transaction support for bulk updates.
    """
    
    operations: List[Dict[str, Any]] = Field(..., min_items = 1, max_items = 100)
    transaction_id: UUID4 = Field(default_factory = uuid.uuid4)
    rollback_on_error: bool = Field(True)
    continue_on_error: bool = Field(False)
    reason: Optional[str] = Field(None, max_length = 1000)
    
    @root_validator
    def validate_batch_operations(cls, values):
        
        """Validate batch operation consistency."""
        
        rollback = values.get('rollback_on_error', True)
        continue_on_error = values.get('continue_on_error', False)
        
        if rollback and continue_on_error:
            raise ValueError("Cannot enable both rollback_on_error and continue_on_error")
        
        return values

#Cache and Performance Models

@dataclass
class CacheStatistics:
    
    """
    Dataclass for cache performance statistics with comprehensive metrics
    for monitoring, alerting, and capacity planning purposes.
    """
    
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    expired_keys: int = 0
    memory_usage: int = 0
    connection_count: int = 0
    average_response_time: float = 0.0
    error_count: int = 0
    last_updated: datetime = field(default_factory = lambda: datetime.now(timezone.utc))

@dataclass
class CacheInvalidationEvent:
    
    """
    Dataclass for cache invalidation events with comprehensive event tracking
    for real-time cache management and distributed system coordination.
    """
    
    event_type: str
    keys: List[str]
    pattern: Optional[str] = None
    source: Optional[str] = None
    timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory = dict)

class ValidationResult(BaseModel):
    
    """
    Model for configuration validation results with detailed error reporting
    and remediation guidance for configuration management operations.
    """
    
    is_valid: bool
    errors: List[Dict[str, Any]] = Field(default_factory = list)
    warnings: List[Dict[str, Any]] = Field(default_factory = list)
    validated_parameters: int = Field(..., ge = 0)
    validation_time_ms: float = Field(..., ge = 0)
    schema_version: Optional[str] = Field(None)
    
    def add_error(self, parameter_key: str, message: str, rule_type: str = "unknown"):
        
        """Add validation error with structured information."""
        
        self.errors.append({
            'parameter_key': parameter_key,
            'message': message,
            'rule_type': rule_type,
            'severity': 'error'
        })

        self.is_valid = False
    
    def add_warning(self, parameter_key: str, message: str, rule_type: str = "unknown"):
        
        """Add validation warning with structured information."""
        
        self.warnings.append({
            'parameter_key': parameter_key,
            'message': message,
            'rule_type': rule_type,
            'severity': 'warning'
        })

class HealthCheckResult(BaseModel):
    
    """
    Model for system health check results with comprehensive status information
    and performance metrics for operational monitoring.
    """
    
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))
    version: str = Field("1.0.0")
    components: Dict[str, Dict[str, Any]] = Field(default_factory = dict)
    response_time_ms: Optional[float] = Field(None, ge = 0)
    error_message: Optional[str] = Field(None)
    
    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}

#Security and Authentication Models

class TokenPayload(BaseModel):
    
    """
    Model for JWT token payload with comprehensive authentication and
    authorisation information for secure configuration access.
    """
    
    sub: str = Field(..., description = "Subject (user or service identifier)")
    service_name: Optional[str] = Field(None, max_length = 255)
    user_id: Optional[str] = Field(None, max_length = 255)
    email: Optional[EmailStr] = Field(None)
    scopes: List[str] = Field(default_factory = list, description = "Authorised scopes")
    roles: List[str] = Field(default_factory = list, description = "User or service roles")
    exp: int = Field(..., description = "Token expiration timestamp")
    iat: int = Field(..., description = "Token issued at timestamp")
    iss: str = Field(..., description = "Token issuer")
    
    @validator('scopes')
    def validate_scopes(cls, v):
        
        """Validate scope format and allowed values."""
        
        allowed_prefixes = ['config:', 'admin:', 'read:', 'write:']
        
        for scope in v:
            if not any(scope.startswith(prefix) for prefix in allowed_prefixes):
                raise ValueError(f"Invalid scope format: {scope}")
        
        return v

class EncryptionMetadata(BaseModel):
    
    """
    Model for encryption metadata with comprehensive key management
    and security tracking information.
    """
    
    algorithm: str = Field("AES-256-GCM", max_length = 50)
    key_id: str = Field(..., max_length = 255, description = "Encryption key identifier")
    iv: Optional[str] = Field(None, description = "Initialisation vector")
    created_at: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))
    key_rotation_date: Optional[datetime] = Field(None)
    encryption_context: Dict[str, str] = Field(default_factory = dict)
    
    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}

#Error and Exception Models

class ConfigurationError(BaseModel):
    
    """
    Model for configuration error responses with detailed error information
    and remediation guidance for client applications.
    """
    
    error_code: str = Field(..., max_length = 50)
    error_message: str = Field(..., max_length = 1000)
    error_details: Optional[Dict[str, Any]] = Field(None)
    correlation_id: Optional[str] = Field(None)
    timestamp: datetime = Field(default_factory = lambda: datetime.now(timezone.utc))
    retry_after: Optional[int] = Field(None, ge = 0, description = "Retry delay in seconds")
    documentation_url: Optional[str] = Field(None, max_length = 500)
    
    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}