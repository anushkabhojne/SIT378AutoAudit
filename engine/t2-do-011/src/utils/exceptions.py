"""
Custom Exception Hierarchy for AutoAudit Container Security Scanning

This module defines comprehensive exception classes for error handling, categorisation,
and recovery strategy implementation across the scanning infrastructure.

Author: Senior Lead, AutoAudit
"""

from typing import Optional, Dict, Any


class AutoAuditScanningError(Exception):
    """
    Base exception class for all AutoAudit scanning errors.
    
    This provides common error handling infrastructure including error codes,
    context preservation, and recovery strategy hints.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ):
        
        """
        Initialising the base scanning error.
        
        Args:
            message: Human-readable error description
            error_code: Machine-readable error code for categorisation
            context: Additional context information for debugging
            recoverable: Whether error condition is recoverable with retry
        """

        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.recoverable = recoverable
    
    def to_dict(self) -> Dict[str, Any]:
        """Converting the exception to dictionary for logging and serialisation."""
        
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'recoverable': self.recoverable
        }


#Scanner-related exceptions
class ScannerError(AutoAuditScanningError):
    """Base class for scanner-specific errors."""
    
    pass


class ScannerNotFoundError(ScannerError):
    """Raised when scanner binary cannot be found or is not executable."""
    
    def __init__(self, message: str):
        
        super().__init__(
            message = message,
            error_code = 'SCANNER_NOT_FOUND',
            recoverable = False
        )


class ScannerExecutionError(ScannerError):
    """Raised when scanner execution fails with non-zero exit code."""
    
    def __init__(self, message: str, return_code: Optional[int] = None):
        context = {'return_code': return_code} if return_code else {}
        
        super().__init__(
            message = message,
            error_code = 'SCANNER_EXECUTION_FAILED',
            context = context,
            recoverable = True
        )


class ScannerTimeoutError(ScannerError):
    """Raised when the scanner execution exceeds a timeout threshold."""
    
    def __init__(self, message: str, timeout_seconds: Optional[int] = None):
        context = {'timeout_seconds': timeout_seconds} if timeout_seconds else {}
        
        super().__init__(
            message = message,
            error_code = 'SCANNER_TIMEOUT',
            context = context,
            recoverable = True
        )


class InvalidImageError(ScannerError):
    """Raised when the container image is invalid or cannot be accessed."""
    
    def __init__(self, message: str, image: Optional[str] = None):
        context = {'image': image} if image else {}
        
        super().__init__(
            message = message,
            error_code = 'INVALID_IMAGE',
            context = context,
            recoverable = False
        )


class DatabaseUpdateError(ScannerError):
    """Raised when the vulnerability database update fails."""
    
    def __init__(self, message: str):
        
        super().__init__(
            message = message,
            error_code = 'DATABASE_UPDATE_FAILED',
            recoverable = True
        )


#Policy-related exceptions
class PolicyError(AutoAuditScanningError):
    """Base class for policy evaluation errors."""
    pass


class PolicyEvaluationError(PolicyError):
    """Raised when the policy evaluation fails."""
    
    def __init__(self, message: str, policy_name: Optional[str] = None):
        context = {'policy_name': policy_name} if policy_name else {}
        
        super().__init__(
            message = message,
            error_code = 'POLICY_EVALUATION_FAILED',
            context = context,
            recoverable = True
        )


class PolicyLoadError(PolicyError):
    """Raised when the policy loading or parsing fails."""
    
    def __init__(self, message: str, policy_path: Optional[str] = None):
        context = {'policy_path': policy_path} if policy_path else {}
        
        super().__init__(
            message = message,
            error_code = 'POLICY_LOAD_FAILED',
            context = context,
            recoverable = False
        )


class PolicyViolationError(PolicyError):
    """Raised when the scan results violate security policies."""
    
    def __init__(
        self, 
        message: str, 
        violations: Optional[list] = None,
        severity: str = 'HIGH'
    ):
        
        context = {
            'violations': violations or [],
            'severity': severity
        }

        super().__init__(
            message = message,
            error_code = 'POLICY_VIOLATION',
            context = context,
            recoverable = False
        )


class PolicyConnectionError(PolicyError):
    """Raised when the connection to the OPA server fails."""
    
    def __init__(self, message: str, server_url: Optional[str] = None):
        context = {'server_url': server_url} if server_url else {}
        
        super().__init__(
            message = message,
            error_code = 'POLICY_CONNECTION_FAILED',
            context = context,
            recoverable = True
        )


#Configuration-related exceptions
class ConfigurationError(AutoAuditScanningError):
    """Base class for configuration errors."""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when the configuration validation fails."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None):
        context = {'validation_errors': validation_errors or []}
        
        super().__init__(
            message = message,
            error_code = 'INVALID_CONFIGURATION',
            context = context,
            recoverable = False
        )


class MissingConfigurationError(ConfigurationError):
    """Raised when the required configuration is missing."""
    
    def __init__(self, message: str, missing_keys: Optional[list] = None):
        context = {'missing_keys': missing_keys or []}
        
        super().__init__(
            message = message,
            error_code = 'MISSING_CONFIGURATION',
            context = context,
            recoverable = False
        )


#Report generation exceptions
class ReportError(AutoAuditScanningError):
    """Base class for report generation errors."""
    pass


class ReportGenerationError(ReportError):
    """Raised when the report generation fails."""
    
    def __init__(self, message: str, format: Optional[str] = None):
        context = {'format': format} if format else {}
        super().__init__(
        
            message = message,
            error_code = 'REPORT_GENERATION_FAILED',
            context = context,
            recoverable = True
        )


class ReportTemplateError(ReportError):
    """Raised when the report template is invalid or missing."""
    
    def __init__(self, message: str, template_path: Optional[str] = None):
        context = {'template_path': template_path} if template_path else {}
        
        super().__init__(
            message = message,
            error_code = 'REPORT_TEMPLATE_ERROR',
            context = context,
            recoverable = False
        )


#Storage and persistence exceptions
class StorageError(AutoAuditScanningError):
    """Base class for storage-related errors."""
    pass


class ResultStorageError(StorageError):
    """Raised when storing scan results fails."""
    
    def __init__(self, message: str, storage_path: Optional[str] = None):
        context = {'storage_path': storage_path} if storage_path else {}
        
        super().__init__(
            message = message,
            error_code = 'RESULT_STORAGE_FAILED',
            context = context,
            recoverable = True
        )


class CacheError(StorageError):
    """Raised when the cache operations fail."""
    
    def __init__(self, message: str, cache_key: Optional[str] = None):
        context = {'cache_key': cache_key} if cache_key else {}
        super().__init__(
            message = message,
            error_code = 'CACHE_ERROR',
            context = context,
            recoverable = True
        )


#Integration exceptions
class IntegrationError(AutoAuditScanningError):
    """Base class for external integration errors."""
    pass


class GitHubIntegrationError(IntegrationError):
    """Raised when GitHub integration fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        context = {'operation': operation} if operation else {}
        
        super().__init__(
            message = message,
            error_code = 'GITHUB_INTEGRATION_FAILED',
            context = context,
            recoverable = True
        )


class RegistryConnectionError(IntegrationError):
    """Raised when the container registry connection fails."""
    
    def __init__(self, message: str, registry: Optional[str] = None):
        context = {'registry': registry} if registry else {}
        
        super().__init__(
            message = message,
            error_code = 'REGISTRY_CONNECTION_FAILED',
            context = context,
            recoverable = True
        )


class MetricsCollectionError(IntegrationError):
    """Raised when the metrics collection fails."""
    
    def __init__(self, message: str):
        
        super().__init__(
            message = message,
            error_code = 'METRICS_COLLECTION_FAILED',
            recoverable = True
        )


#Orchestration exceptions
class OrchestrationError(AutoAuditScanningError):
    """Base class for orchestration workflow errors."""
    pass


class WorkflowExecutionError(OrchestrationError):
    """Raised when the scanning workflow execution fails."""
    
    def __init__(self, message: str, step: Optional[str] = None):
        context = {'failed_step': step} if step else {}
        
        super().__init__(
            message = message,
            error_code = 'WORKFLOW_EXECUTION_FAILED',
            context = context,
            recoverable = True
        )


class ParallelExecutionError(OrchestrationError):
    """Raised when parallel scan execution fails."""
    
    def __init__(self, message: str, failed_scans: Optional[list] = None):
        context = {'failed_scans': failed_scans or []}
        
        super().__init__(
            message = message,
            error_code = 'PARALLEL_EXECUTION_FAILED',
            context = context,
            recoverable = True
        )


#Validation exceptions
class ValidationError(AutoAuditScanningError):
    """Base class for validation errors."""
    pass


class InputValidationError(ValidationError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        context = {'field': field} if field else {}
        
        super().__init__(
            message = message,
            error_code = 'INPUT_VALIDATION_FAILED',
            context = context,
            recoverable = False
        )


class ResultValidationError(ValidationError):
    """Raised when scan result validation fails."""
    
    def __init__(self, message: str, validation_failures: Optional[list] = None):
        context = {'validation_failures': validation_failures or []}
        
        super().__init__(
            message = message,
            error_code = 'RESULT_VALIDATION_FAILED',
            context = context,
            recoverable = False
        )


#Authentication and authorisation exceptions
class AuthenticationError(AutoAuditScanningError):
    """Base class for authentication errors."""
    pass


class CredentialError(AuthenticationError):
    """Raised when the credentials are invalid or missing."""
    
    def __init__(self, message: str, credential_type: Optional[str] = None):
        context = {'credential_type': credential_type} if credential_type else {}
        
        super().__init__(
            message = message,
            error_code = 'CREDENTIAL_ERROR',
            context = context,
            recoverable = False
        )


class AuthorizationError(AuthenticationError):
    """Raised when the authorisation check fails."""
    
    def __init__(self, message: str, required_permission: Optional[str] = None):
        context = {'required_permission': required_permission} if required_permission else {}
        
        super().__init__(
            message = message,
            error_code = 'AUTHORIZATION_FAILED',
            context = context,
            recoverable = False
        )


#Resource exceptions
class ResourceError(AutoAuditScanningError):
    """Base class for resource-related errors."""
    pass


class ResourceExhaustedError(ResourceError):
    """Raised when the system resources are exhausted."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None):
        context = {'resource_type': resource_type} if resource_type else {}
        
        super().__init__(
            message = message,
            error_code = 'RESOURCE_EXHAUSTED',
            context = context,
            recoverable = True
        )


class ResourceNotFoundError(ResourceError):
    """Raised when the required resource is not found."""
    
    def __init__(self, message: str, resource_path: Optional[str] = None):
        context = {'resource_path': resource_path} if resource_path else {}
        
        super().__init__(
            message = message,
            error_code = 'RESOURCE_NOT_FOUND',
            context = context,
            recoverable = False
        )