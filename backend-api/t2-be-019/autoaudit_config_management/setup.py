"""
AutoAudit Configuration Management System - Package Setup Configuration

This setup.py file defines the package configuration for the AutoAudit Configuration
Management System, providing comprehensive metadata, dependency management, and
distribution settings for enterprise deployment and development environments.

The configuration supports both development installation and production packaging
with appropriate entry points and optional dependencies for different deployment
scenarios including Docker containers and Kubernetes clusters.

Author: Senior Lead, AutoAudit
Owner: Backend Team, AutoAudit
"""

from setuptools import setup, find_packages
import os
import re


def get_version():
    
    """Extract version number from the package __init__.py file."""
    
    version_file = os.path.join(os.path.dirname(__file__), 'config', '__init__.py')
    
    with open(version_file, 'r', encoding='utf-8') as f:
        version_content = f.read()
    
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_content, re.M)
    
    if version_match:
        return version_match.group(1)
    
    raise RuntimeError("Unable to find version string in config/__init__.py")


def get_long_description():
    
    """Read the comprehensive project description from README.md."""
    
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_requirements(filename):
    
    """Parse requirements from requirements files with comprehensive error handling."""
    
    requirements_path = os.path.join(os.path.dirname(__file__), filename)
    requirements = []
    
    if os.path.exists(requirements_path):
        
        with open(requirements_path, 'r', encoding='utf-8') as f:
            
            for line in f:
                line = line.strip()
                
                #Skipping comments, empty lines, and -r includes
                if line and not line.startswith('#') and not line.startswith('-r'):
                    requirements.append(line)
    
    return requirements


#Defining the package metadata with comprehensive information
PACKAGE_NAME = "autoaudit-config-management"
PACKAGE_VERSION = get_version()
PACKAGE_DESCRIPTION = "Enterprise-grade centralised configuration management system for AutoAudit microservices ecosystem"
PACKAGE_LONG_DESCRIPTION = get_long_description()
PACKAGE_AUTHOR = "AutoAudit Development Team"

#Defining the supported Python versions and platforms
PYTHON_REQUIRES = ">=3.11"
SUPPORTED_PLATFORMS = ["Linux", "Darwin", "Windows"]

#Defining the package classifiers for PyPI publication
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Systems Administration",
    "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    "Topic :: Database :: Database Engines/Servers",
    "Topic :: Security :: Cryptography",
    "Framework :: FastAPI",
    "Framework :: AsyncIO",
    "Environment :: Web Environment",
    "Natural Language :: English",
]

#Defining the optional dependencies for different deployment scenarios

EXTRAS_REQUIRE = {
    "dev": get_requirements("requirements-dev.txt"),
    "production": [
        "gunicorn>=21.2.0",
        "gevent>=23.9.1",
        "setproctitle>=1.3.3",
    ],

    "monitoring": [
        "prometheus-client>=0.19.0",
        "opentelemetry-api>=1.21.0",
        "opentelemetry-sdk>=1.21.0",
        "grafana-api>=1.0.3",
    ],

    "security": [
        "cryptography>=41.0.8",
        "hvac>=2.0.0",
        "azure-keyvault-secrets>=4.7.0",
    ],

    "testing": [
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "testcontainers>=3.7.1",
    ],

    "docs": [
        "sphinx>=7.2.6",
        "sphinx-rtd-theme>=1.3.0",
        "mkdocs-material>=9.4.8",
    ],
}

#Adding the 'all' option that includes all optional dependencies
EXTRAS_REQUIRE["all"] = list(set(
    dep for deps in EXTRAS_REQUIRE.values() for dep in deps
))

#Defining the console entry points for the command-line tools
ENTRY_POINTS = {
    "console_scripts": [
        "autoaudit-config=config.cli:main",
        "autoaudit-config-server=config.main:run_server",
        "autoaudit-config-migrate=config.database.migrate:main",
        "autoaudit-config-admin=config.admin.cli:main",
    ],
}

#Defining the package data to include non-Python files
PACKAGE_DATA = {
    "config": [
        "migrations/versions/*.sql",
        "schemas/*.json",
        "templates/*.html",
        "static/css/*.css",
        "static/js/*.js",
    ],
}

#Defining the additional data files for system-wide configuration
DATA_FILES = [
    ("etc/autoaudit", ["config/autoaudit.conf.example"]),
    ("var/log/autoaudit", []),
]

setup(
    
    #Basic package information
    name = PACKAGE_NAME,
    version = PACKAGE_VERSION,
    description = PACKAGE_DESCRIPTION,
    long_description = PACKAGE_LONG_DESCRIPTION,
    long_description_content_type = "text/markdown",
    
    #Python version and platform requirements
    python_requires = PYTHON_REQUIRES,
    platforms = SUPPORTED_PLATFORMS,
    
    #Package discovery and structure
    packages = find_packages(exclude=["tests*", "docs*", "scripts*"]),
    package_data = PACKAGE_DATA,
    data_files = DATA_FILES,
    include_package_data = True,
    zip_safe = False,
    
    #Dependencies and requirements
    install_requires = get_requirements("requirements.txt"),
    extras_require = EXTRAS_REQUIRE,
    
    #Entry points for command-line tools
    entry_points=ENTRY_POINTS,
    
    #Additional configuration for development and testing
    test_suite = "tests",
    tests_require = EXTRAS_REQUIRE.get("testing", []),
    
    #Package configuration options
    options = {
        "bdist_wheel": {
            "universal": False,  #The package is not universal (Python 3.11+ only)
        },

        "egg_info": {
            "tag_build": "",
            "tag_date": False,
        },
    },
)