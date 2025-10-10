"""
AutoAudit Configuration Management System - Package Initialisation

This module initialises the AutoAudit Configuration Management System package,
providing version information, package-level exports, and configuration for
enterprise-grade distributed configuration management capabilities.

The package implements comprehensive configuration management functionality including
hierarchical configuration resolution, real-time updates, enterprise security,
and operational excellence through advanced monitoring and observability.

Author: Senior Lead, AutoAudit  
Owner: Backend Team, AutoAudit
"""

import logging
import sys
from typing import Dict, Any, Optional

#Package version and metadata
__version__ = "1.0.0"
__title__ = "AutoAudit Configuration Management System"
__description__ = "Enterprise-grade centralised configuration management system"

#Minimum Python version requirement
MIN_PYTHON_VERSION = (3, 11)

def check_python_version():
    
    """
    Verify Python version compatibility with package requirements.
    
    Raises:
        RuntimeError: If Python version is below minimum requirements
    """
    
    if sys.version_info < MIN_PYTHON_VERSION:
        raise RuntimeError(
            f"AutoAudit Configuration Management System requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ "
            f"but you have Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )

#Performing a version check on the import
check_python_version()

#Configuring package-level logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

#Package-level exports for clean API interface
from .database import DatabaseManager
from .cache import CacheManager  

from .models import (
    ConfigurationParameter,
    ConfigurationRequest,
    ConfigurationResponse,
    ConfigurationAuditLog,
    ValidationResult,
    HealthCheckResult
)

from .exceptions import (
    AutoAuditConfigException,
    DatabaseError,
    CacheError,
    ConfigurationNotFoundException,
    ValidationError,
    SecurityError,
    ServiceUnavailableError
)

#Package metadata dictionary for programmatic access
__package_metadata__ = {
    "name": __title__,
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "author_email": __author_email__,
    "license": __license__,
    "url": __url__,
    "docs_url": __docs_url__,
    "python_requires": f">={MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"
}

#Default configuration constants
DEFAULT_CONFIG = {
    "database": {
        "pool_min_size": 10,
        "pool_max_size": 50,
        "command_timeout": 60.0
    },

    "cache": {
        "default_ttl": 300,
        "max_value_size": 10 * 1024 * 1024,
        "compression_threshold": 1024
    },

    "security": {
        "jwt_algorithm": "RS256",
        "token_expire_minutes": 30
    },

    "monitoring": {
        "metrics_enabled": True,
        "health_check_interval": 30
    }
}

#Export list for clean package interface
__all__ = [
    
    #Version and metadata
    "__version__",
    "__title__", 
    "__description__",
    "__author__",
    "__license__",
    "__package_metadata__",
    
    #Core managers
    "DatabaseManager",
    "CacheManager",
    
    #Data models
    "ConfigurationParameter",
    "ConfigurationRequest", 
    "ConfigurationResponse",
    "ConfigurationAuditLog",
    "ValidationResult",
    "HealthCheckResult",
    
    #Exceptions
    "AutoAuditConfigException",
    "DatabaseError",
    "CacheError", 
    "ConfigurationNotFoundException",
    "ValidationError",
    "SecurityError",
    "ServiceUnavailableError",
    
    #Configuration
    "DEFAULT_CONFIG"
]

def get_version() -> str:
    
    """
    Get the current package version.
    
    Returns:
        Package version string
    """
    
    return __version__

def get_package_info() -> Dict[str, Any]:
    
    """
    Get comprehensive package information and metadata.
    
    Returns:
        Dictionary containing package metadata
    """
    
    return __package_metadata__.copy()

def configure_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    
    """
    Configure package-level logging with enterprise-grade structured logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom logging format string
    """
    
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
            "[%(filename)s:%(lineno)d] [%(funcName)s]"
        )
    
    logging.basicConfig(
        level = getattr(logging, level.upper()),
        format = format_string,
        datefmt = "%Y-%m-%d %H:%M:%S"
    )
    
    #Set specific log levels for dependencies to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)