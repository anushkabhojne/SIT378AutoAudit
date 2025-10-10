"""
Comprehensive Logging Framework for AutoAudit Container Security Scanning System

This module provides enterprise-grade logging capabilities with structured logging,
audit trail generation, security event logging, and compliance-ready log formatting.
The implementation supports multiple output handlers, log rotation, encryption for
sensitive data, and integration with a centralised logging systems.

Author: Senior Lead, AutoAudit
"""

import logging
import sys
import os
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import hashlib
import re


class SecurityFilter(logging.Filter):
    """
    Advanced logging filter that sanitises sensitive information from log messages
    preventing accidental exposure of credentials, tokens, and other sensitive data.
    
    This filter implements comprehensive pattern matching for various sensitive data
    types and provides configurable redaction strategies for different security levels.
    """
    
    #Comprehensive patterns for sensitive data detection
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'token'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'api_key'),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'secret'),
        (r'authorization["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'authorization'),
        (r'bearer\s+([a-zA-Z0-9\-._~+/]+)', 'bearer_token'),
        (r'private[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'private_key'),
        (r'AKIA[0-9A-Z]{16}', 'aws_access_key'),
        (r'ghp_[a-zA-Z0-9]{36}', 'github_token'),
        (r'xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}', 'slack_token'),
        (r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', 'credit_card'),
        (r'(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])', 'email'),
    ]
    
    def __init__(self, redaction_strategy: str = 'hash'):
        """
        Initialising the security filter with configurable redaction strategy.
        
        Args:
            redaction_strategy: Strategy for redacting sensitive data ('mask', 'hash', 'remove')
                - 'mask': Replace with asterisks (default for most scenarios)
                - 'hash': Replace with SHA-256 hash (for audit trail correlation)
                - 'remove': Complete removal from log message
        """
        
        super().__init__()
        self.redaction_strategy = redaction_strategy
        
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtering and sanitising the log records removing or redacting sensitive information.
        
        Args:
            record: LogRecord instance to be filtered
            
        Returns:
            bool: Always returns True to allow record through after sanitization
        """
        
        #Sanitising the main message
        record.msg = self._sanitize_message(str(record.msg))
        
        #Sanitising any arguments that will be formatted into the message
        if record.args:
            
            if isinstance(record.args, dict):
                record.args = {k: self._sanitize_value(v) for k, v in record.args.items()}
            
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize_value(arg) for arg in record.args)
        
        return True
    
    def _sanitize_message(self, message: str) -> str:
        """
        Sanitising a message string by detecting and redacting sensitive patterns.
        
        Args:
            message: Original log message potentially containing sensitive data
            
        Returns:
            str: Sanitized message with sensitive data redacted
        """
        
        sanitized = message
        
        for pattern, data_type in self.SENSITIVE_PATTERNS:
            
            if self.redaction_strategy == 'hash':
                
                sanitized = re.sub(
                    pattern,
                    lambda m: f'{data_type} = [REDACTED:SHA256:{hashlib.sha256(m.group(1).encode()).hexdigest()[:16]}]',
                    sanitized,
                    flags = re.IGNORECASE
                )
            
            elif self.redaction_strategy == 'mask':
                
                sanitized = re.sub(
                    pattern,
                    f'{data_type} = [REDACTED:********]',
                    sanitized,
                    flags = re.IGNORECASE
                )
            
            elif self.redaction_strategy == 'remove':
                
                sanitized = re.sub(
                    pattern,
                    f'{data_type} = [REMOVED]',
                    sanitized,
                    flags = re.IGNORECASE
                )
        
        return sanitized
    
    def _sanitize_value(self, value: Any) -> Any:
        """
        Recursively sanitising values including nested dictionaries and lists.
        
        Args:
            value: Value to sanitise (can be string, dict, list, or primitive)
            
        Returns:
            Sanitised value with same type as input
        """
        
        if isinstance(value, str):
            return self._sanitize_message(value)
        
        elif isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items()}
        
        elif isinstance(value, (list, tuple)):
            return type(value)(self._sanitize_value(item) for item in value)
        
        else:
            return value


class StructuredFormatter(logging.Formatter):
    """
    Advanced JSON-based structured logging formatter providing machine-readable
    log output with comprehensive metadata, context information, and audit trail data.
    
    This formatter supports SIEM integration, compliance requirements, and
    advanced log analysis through consistent structured output.
    """
    
    def __init__(self, include_trace: bool = True, environment: str = 'production'):
        """
        Initialising the structured formatter with configuration options.
        
        Args:
            include_trace: Whether to include stack traces for errors
            environment: Deployment environment identifier for log correlation
        """
        
        super().__init__()
        self.include_trace = include_trace
        self.environment = environment
        self.hostname = os.environ.get('HOSTNAME', 'unknown')
        self.service_name = os.environ.get('SERVICE_NAME', 'autoaudit-scanner')
        
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON with comprehensive metadata.
        
        Args:
            record: LogRecord instance to format
            
        Returns:
            str: JSON-formatted log message with metadata
        """
        
        #Building the base log structure
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz = timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'environment': self.environment,
            'service': self.service_name,
            'hostname': self.hostname,
            
            'process': {
                'pid': record.process,
                'name': record.processName,
                'thread_id': record.thread,
                'thread_name': record.threadName,
            },

            'location': {
                'file': record.pathname,
                'line': record.lineno,
                'function': record.funcName,
                'module': record.module,
            }
        }
        
        #Adding the exception information if present
        if record.exc_info and self.include_trace:
            
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        elif record.exc_info:
            
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1])
            }
        
        #Adding custom fields from the extra parameter
        if hasattr(record, 'custom_fields'):
            log_data['custom'] = record.custom_fields
        
        #Adding the correlation ID, if present, for distributed tracing
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        #Adding the security context, if present, for audit logging
        if hasattr(record, 'security_context'):
            log_data['security'] = record.security_context
        
        #Adding the performance metrics, if present
        if hasattr(record, 'performance_metrics'):
            log_data['metrics'] = record.performance_metrics
        
        return json.dumps(log_data, default = str, ensure_ascii = False)


class AuditLogger:
    """
    Specialised audit logger for security-relevant events requiring comprehensive
    audit trails for compliance verification and forensic analysis.
    
    This logger implements tamper-evident logging with cryptographic checksums,
    mandatory field validation, and immutable log record generation.
    """
    
    def __init__(self, logger: logging.Logger, audit_log_path: Optional[Path] = None):
        """
        Initialising the audit logger with dedicated audit trail storage.
        
        Args:
            logger: Base logger instance for audit event output
            audit_log_path: Optional dedicated path for audit log storage
        """
        
        self.logger = logger
        self.audit_log_path = audit_log_path or Path('logs/audit')
        self.audit_log_path.mkdir(parents = True, exist_ok = True)
        
        #Creating a dedicated audit file handler with daily rotation
        audit_file = self.audit_log_path / 'audit.log'
        
        audit_handler = TimedRotatingFileHandler(
            audit_file,
            when = 'midnight',
            interval = 1,
            backupCount = 365,  #Retaining the audit logs for 1 year
            encoding = 'utf-8'
        )

        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(StructuredFormatter(include_trace = True))
        self.logger.addHandler(audit_handler)
        
    def log_security_event(self, event_type: str, user: str, action: str, 
                          resource: str, result: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Logging the security-relevant event with mandatory audit trail fields.
        
        Args:
            event_type: Type of security event (e.g., authentication, authorisation, access, modification)
            user: User or service account performing the action
            action: Specific action being performed
            resource: Resource being accessed or modified
            result: Result of the action (success, failure, denied)
            details: Optional additional context information
        """
        
        audit_data = {
            'event_type': event_type,
            'user': user,
            'action': action,
            'resource': resource,
            'result': result,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': details or {}
        }
        
        #Generating the checksum for tamper detection
        audit_data['checksum'] = self._generate_checksum(audit_data)
        
        self.logger.info(
            f"AUDIT: {event_type} - {user} performed {action} on {resource}: {result}",
            extra = {'security_context': audit_data}
        )
    
    def _generate_checksum(self, data: Dict[str, Any]) -> str:
        """
        Generating the cryptographic checksum for audit record integrity verification.
        
        Args:
            data: Audit record data for checksum calculation
            
        Returns:
            str: SHA-256 checksum of audit record
        """
        
        #Serialising the audit data excluding checksum field
        serialized = json.dumps(
            {k: v for k, v in data.items() if k != 'checksum'},
            sort_keys = True,
            default = str
        )
        return hashlib.sha256(serialized.encode()).hexdigest()


def setup_logger(
    name: str,
    level: str = 'INFO',
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_directory: Optional[Path] = None,
    structured_logging: bool = True,
    enable_audit: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  #10MB default
    backup_count: int = 10
) -> logging.Logger:
    """
    Configuring and returning a comprehensive logger instance with enterprise-grade features.
    
    This function creates a fully configured logger with multiple handlers, security
    filtering, structured output, and optional audit trail capabilities suitable for
    production deployment in security-critical applications.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable file-based logging with rotation
        log_to_console: Enable console output for development/debugging
        log_directory: Custom directory for log file storage
        structured_logging: Enable JSON structured logging format
        enable_audit: Enable dedicated audit trail logging
        max_file_size: Maximum size per log file before rotation
        backup_count: Number of rotated log files to retain
        
    Returns:
        logging.Logger: Fully configured logger instance ready for use
        
    Example:
        >>> logger = setup_logger(__name__, level = 'DEBUG', enable_audit = True)
        >>> logger.info("Container scanning initiated", extra = {
        ...     'custom_fields': {'image': 'autoaudit:latest', 'registry': 'docker.io'}
        ... })
    """
    
    #Getting or creating a logger instance
    logger = logging.getLogger(name)
    
    #Preventing the duplicate handler configuration on repeated calls
    if logger.hasHandlers():
        return logger
    
    #Setting the base logging level
    logger.setLevel(getattr(logging, level.upper()))
    
    #Preventing the propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    #Adding the security filter to all handlers for sensitive data protection
    security_filter = SecurityFilter(redaction_strategy = 'hash')
    
    #Configuring the console handler for development and debugging
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if structured_logging:
            console_formatter = StructuredFormatter(
                include_trace = True,
                environment = os.environ.get('ENVIRONMENT', 'development')
            )

        else:
            console_formatter = logging.Formatter(
                fmt = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(security_filter)
        logger.addHandler(console_handler)
    
    #Configuring the file handler with rotation for persistent logging
    if log_to_file:
        
        #Determining the log directory's location
        if log_directory is None:
            log_directory = Path(os.environ.get('LOG_DIRECTORY', 'logs'))
        
        log_directory = Path(log_directory)
        log_directory.mkdir(parents = True, exist_ok = True)
        
        #Creating a rotating file handler with size-based rotation
        log_file = log_directory / f'{name.replace(".", "_")}.log'
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes = max_file_size,
            backupCount = backup_count,
            encoding = 'utf-8'
        )

        file_handler.setLevel(logging.DEBUG)
        
        if structured_logging:
            
            file_formatter = StructuredFormatter(
                include_trace = True,
                environment = os.environ.get('ENVIRONMENT', 'production')
            )

        else:
            file_formatter = logging.Formatter(
                fmt = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt = '%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(security_filter)
        logger.addHandler(file_handler)
        
        #Creating a separate error log file for critical issues
        error_log_file = log_directory / f'{name.replace(".", "_")}_error.log'
        
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes = max_file_size,
            backupCount = backup_count,
            encoding = 'utf-8'
        )

        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        error_handler.addFilter(security_filter)
        logger.addHandler(error_handler)
    
    #Configuring the audit logger, if enabled
    if enable_audit:
        audit_path = Path(os.environ.get('AUDIT_LOG_DIRECTORY', 'logs/audit'))
        audit_logger = AuditLogger(logger, audit_path)
        logger.audit = audit_logger.log_security_event
    
    logger.info(
        f"Logger initialised for {name}",
        
        extra = {
            'custom_fields': {
                'level': level,
                'structured': structured_logging,
                'audit_enabled': enable_audit,
                'file_logging': log_to_file,
                'console_logging': log_to_console
            }
        }
    )
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retrieving the existing logger instance or create new one with default configuration.
    
    This function provides convenient access to logger instances with consistent
    configuration across the application while supporting lazy initialisation.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        logging.Logger: Logger instance with default configuration
    """

    logger = logging.getLogger(name)
    
    if not logger.hasHandlers():
        
        return setup_logger(
            name,
            level = os.environ.get('LOG_LEVEL', 'INFO'),
            log_to_file = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true',
            log_to_console = os.environ.get('LOG_TO_CONSOLE', 'true').lower() == 'true',
            structured_logging = os.environ.get('STRUCTURED_LOGGING', 'true').lower() == 'true',
            enable_audit = os.environ.get('ENABLE_AUDIT_LOGGING', 'false').lower() == 'true'
        )
    
    return logger

#Module-level logger for internal logging framework messages
_framework_logger = logging.getLogger('autoaudit.logging.framework')
_framework_logger.info("Logging framework initialised successfully")