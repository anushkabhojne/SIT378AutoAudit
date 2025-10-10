"""
Comprehensive Configuration Management System for AutoAudit Container Security Scanning

This module provides centralised configuration management with environment variable
support, validation, type conversion, and secure credential handling. The implementation
supports multiple configuration sources with precedence hierarchy and runtime reconfiguration.

Author: Senior Lead, AutoAudit
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import re


class Environment(Enum):
    
    """Deployment environment enumeration for configuration profiles."""
    
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ScanningProfile(Enum):
    
    """Scanning profile enumeration defining performance and thoroughness balance."""
    
    FAST = "fast"  #Optimised for speed, basic vulnerability detection
    BALANCED = "balanced"  #Standard scanning with comprehensive coverage
    THOROUGH = "thorough"  #Exhaustive scanning including all databases
    COMPLIANCE = "compliance"  #Focused on regulatory compliance requirements


@dataclass
class ScannerConfiguration:
    """
    Configuration dataclass for vulnerability scanner settings.
    
    This class encapsulates all scanner-related configuration including
    timeouts, severity thresholds, scanning profiles, and database sources.
    """
    
    #Scanner execution settings
    scanner_binary_path: str = "/usr/local/bin/trivy"
    scanner_version: str = "0.48.0"
    scanner_timeout: int = 300  #seconds (5 minutes)
    scanning_profile: ScanningProfile = ScanningProfile.BALANCED
    
    # Vulnerability database configuration
    vulnerability_db_path: str = "/var/lib/trivy/db"
    vulnerability_db_update_interval: int = 3600  # seconds (1 hour)
    
    vulnerability_db_sources: List[str] = field(default_factory = lambda: [
        "nvd",  #National Vulnerability Database
        "ghsa",  #GitHub Security Advisories
        "redhat",  #Red Hat Security Data
        "debian",  #Debian Security Tracker
        "alpine",  #Alpine Linux Security
        "oracle",  #Oracle Linux Security
        "photon",  #VMware Photon OS Security
        "amazon"  #Amazon Linux Security Center
    ])
    
    #Severity threshold configuration
    severity_threshold: str = "HIGH"  #Minimum severity to report (CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN)
    block_on_critical: bool = True  #Block deployment on Critical vulnerabilities
    block_on_high: bool = True  #Block deployment on High vulnerabilities
    
    #Performance optimisation settings
    parallel_scanning: bool = True
    max_parallel_scans: int = 5
    cache_enabled: bool = True
    cache_ttl: int = 86400  #seconds (24 hours)
    
    #Output configuration
    output_formats: List[str] = field(default_factory = lambda: ["json", "sarif", "html"])
    include_suppressed: bool = False  #Including the suppressed vulnerabilities in reports
    
    #Advanced scanning options
    scan_layers: bool = True  #Scanning the individual image layers
    scan_secrets: bool = True  #Scanning for exposed secrets
    scan_misconfigurations: bool = True  #Scanning for security misconfigurations
    scan_licenses: bool = False  #Scannin for license compliance
    
    #Network and registry settings
    insecure_registries: List[str] = field(default_factory = list)
    registry_timeout: int = 60  #seconds
    skip_tls_verify: bool = False
    
    def validate(self) -> List[str]:
        """
        Validating the configuration parameters and return list of validation errors.
        
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """

        errors = []
        
        if self.scanner_timeout < 30:
            errors.append("Scanner timeout must be at least 30 seconds")
        
        if self.max_parallel_scans < 1 or self.max_parallel_scans > 20:
            errors.append("Max parallel scans must be between 1 and 20")
        
        if self.severity_threshold not in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
            errors.append(f"Invalid severity threshold: {self.severity_threshold}")
        
        if not Path(self.scanner_binary_path).exists():
            errors.append(f"Scanner binary not found at: {self.scanner_binary_path}")
        
        return errors


@dataclass
class PolicyConfiguration:
    """
    Configuration dataclass for Open Policy Agent policy enforcement settings.
    
    This class manages policy evaluation settings, exception handling, and
    compliance framework alignment configurations.
    """
    
    #OPA server configuration
    opa_server_url: str = "http://localhost:8181"
    opa_server_timeout: int = 30  #seconds
    opa_policy_bundle_path: str = "/etc/opa/policies"
    
    #Policy enforcement settings
    enforcement_mode: str = "strict"  #strict, permissive, audit-only
    policy_version: str = "1.0.0"
    
    #Exception management
    allow_policy_exceptions: bool = True
    exception_approval_required: bool = True
    exception_expiration_days: int = 90
    
    #Compliance framework mappings
    enable_cis_benchmark: bool = True
    enable_nist_csf: bool = True
    enable_iso27001: bool = False
    enable_essential8: bool = True
    enable_mitre_attack: bool = True
    
    #Policy evaluation settings
    fail_on_policy_error: bool = True
    continue_on_warning: bool = True
    
    #Audit and reporting
    log_policy_decisions: bool = True
    generate_policy_report: bool = True
    
    def validate(self) -> List[str]:
        """
        Validating the policy configuration parameters.
        
        Returns:
            List[str]: List of validation error messages
        """
        
        errors = []
        
        if self.enforcement_mode not in ["strict", "permissive", "audit-only"]:
            errors.append(f"Invalid enforcement mode: {self.enforcement_mode}")
        
        if self.opa_server_timeout < 5:
            errors.append("OPA server timeout must be at least 5 seconds")
        
        if self.exception_expiration_days < 1:
            errors.append("Exception expiration days must be positive")
        
        return errors


@dataclass
class GitHubConfiguration:
    """
    Configuration dataclass for GitHub Actions integration settings.
    
    This class manages GitHub-specific configuration including authentication,
    artifact management, and workflow integration parameters.
    """
    
    #GitHub authentication
    github_token: Optional[str] = None
    github_api_url: str = "https://api.github.com"
    
    #Repository information
    repository: Optional[str] = None  #Format: owner/repo
    workflow_run_id: Optional[str] = None
    pull_request_number: Optional[int] = None
    commit_sha: Optional[str] = None
    
    #Artifact management
    artifact_retention_days: int = 90
    upload_artifacts: bool = True
    artifact_compression: bool = True
    
    #Check run integration
    create_check_runs: bool = True
    check_run_name: str = "Container Security Scan"
    
    #Notification settings
    notify_on_failure: bool = True
    notify_on_high_severity: bool = True
    notification_teams_webhook: Optional[str] = None
    notification_slack_webhook: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Validating the GitHub configuration parameters."""
        
        errors = []
        
        if self.artifact_retention_days < 1 or self.artifact_retention_days > 400:
            errors.append("Artifact retention days must be between 1 and 400")
        
        if self.repository and not re.match(r'^[\w\-\.]+/[\w\-\.]+, self.repository):
            errors.append(f"Invalid repository format: {self.repository}")
        
        return errors


@dataclass
class SecurityConfiguration:
    """
    Configuration dataclass for security and encryption settings.
    
    This class manages security-related configuration including encryption,
    access control, network security, and audit logging parameters.
    """
    
    #Encryption settings
    enable_encryption_at_rest: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    
    #Network security
    enable_tls: bool = True
    tls_version: str = "1.3"
    enable_network_isolation: bool = True
    
    allowed_registries: List[str] = field(default_factory = lambda: [
        "docker.io",
        "ghcr.io",
        "gcr.io",
        "public.ecr.aws"
    ])
    
    #Access control
    enable_rbac: bool = True
    require_mfa: bool = False
    session_timeout_minutes: int = 480  #8 hours
    
    #Audit logging
    enable_audit_logging: bool = True
    audit_log_retention_days: int = 365
    log_sensitive_data: bool = False
    
    #Security monitoring
    enable_intrusion_detection: bool = True
    alert_on_suspicious_activity: bool = True
    
    def validate(self) -> List[str]:
        """Validating the security configuration parameters."""
        
        errors = []
        
        if self.encryption_algorithm not in ["AES-256-GCM", "AES-256-CBC", "ChaCha20-Poly1305"]:
            errors.append(f"Unsupported encryption algorithm: {self.encryption_algorithm}")
        
        if self.tls_version not in ["1.2", "1.3"]:
            errors.append(f"TLS version must be 1.2 or 1.3: {self.tls_version}")
        
        if self.session_timeout_minutes < 15:
            errors.append("Session timeout must be at least 15 minutes")
        
        return errors


@dataclass
class MonitoringConfiguration:
    """
    Configuration dataclass for monitoring and observability settings.
    
    This class manages monitoring infrastructure configuration including
    metrics collection, alerting, and observability platform integration.
    """
    
    #Prometheus metrics
    enable_metrics: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    
    #Grafana integration
    grafana_url: Optional[str] = None
    grafana_api_key: Optional[str] = None
    
    #Alerting configuration
    enable_alerting: bool = True
    alert_manager_url: Optional[str] = None
    alert_severity_threshold: str = "HIGH"
    
    #Performance monitoring
    enable_performance_tracking: bool = True
    track_scanning_duration: bool = True
    track_resource_utilization: bool = True
    
    #Health check configuration
    health_check_interval: int = 60  #seconds
    health_check_timeout: int = 10  #seconds
    
    def validate(self) -> List[str]:
        """Validating the monitoring configuration parameters."""
        
        errors = []
        
        if self.metrics_port < 1024 or self.metrics_port > 65535:
            errors.append("Metrics port must be between 1024 and 65535")
        
        if self.health_check_interval < 10:
            errors.append("Health check interval must be at least 10 seconds")
        
        return errors


class ConfigurationManager:
    """
    Comprehensive configuration management system with multi-source support.
    
    This class implements hierarchical configuration loading from environment
    variables, configuration files, and programmatic overrides with validation
    and type conversion.
    """
    
    def __init__(self, environment: Optional[Environment] = None, config_file: Optional[Path] = None):
        """
        Initialising the configuration manager with environment and optional config file.
        
        Args:
            environment: Deployment environment (defaults to DEVELOPMENT)
            config_file: Optional path to YAML/JSON configuration file
        """
        
        self.environment = environment or self._detect_environment()
        self.config_file = config_file
        
        #Initialising the configuration dataclasses
        self.scanner = ScannerConfiguration()
        self.policy = PolicyConfiguration()
        self.github = GitHubConfiguration()
        self.security = SecurityConfiguration()
        self.monitoring = MonitoringConfiguration()
        
        #Loading the configuration from all sources
        self._load_configuration()
        
        #Validating all configurations
        self._validate_all()
    
    def _detect_environment(self) -> Environment:
        """
        Detecting the deployment environment from the environment variables.
        
        Returns:
            Environment: Detected environment enumeration value
        """
        
        env_name = os.environ.get('ENVIRONMENT', 'development').lower()
        
        try:
            return Environment(env_name)
        
        except ValueError:
            return Environment.DEVELOPMENT
    
    def _load_configuration(self) -> None:
        """Loading the configuration from all sources in precedence order."""
        
        #1. Loading from config file, if provided
        if self.config_file and self.config_file.exists():
            self._load_from_file(self.config_file)
        
        #2. Loading from environment-specific config file
        env_config_file = Path(f"config/{self.environment.value}.yaml")
        
        if env_config_file.exists():
            self._load_from_file(env_config_file)
        
        #3. Overriding with the environment variables (highest precedence)
        self._load_from_environment()
    
    def _load_from_file(self, config_path: Path) -> None:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            config_path: Path to configuration file
        """
        
        with open(config_path, 'r') as f:
            
            if config_path.suffix in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            
            elif config_path.suffix == '.json':
                config_data = json.load(f)
            
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        #Updating the configuration dataclasses with file data
        if 'scanner' in config_data:
            self._update_dataclass(self.scanner, config_data['scanner'])
        
        if 'policy' in config_data:
            self._update_dataclass(self.policy, config_data['policy'])
        
        if 'github' in config_data:
            self._update_dataclass(self.github, config_data['github'])
        
        if 'security' in config_data:
            self._update_dataclass(self.security, config_data['security'])
        
        if 'monitoring' in config_data:
            self._update_dataclass(self.monitoring, config_data['monitoring'])
    
    def _load_from_environment(self) -> None:
        """Loading the configuration from environment variables."""
        
        #Scanner configuration from the environment
        self.scanner.scanner_binary_path = os.environ.get('SCANNER_BINARY_PATH', self.scanner.scanner_binary_path)
        self.scanner.scanner_timeout = int(os.environ.get('SCANNER_TIMEOUT', self.scanner.scanner_timeout))
        self.scanner.severity_threshold = os.environ.get('SEVERITY_THRESHOLD', self.scanner.severity_threshold)
        self.scanner.block_on_critical = os.environ.get('BLOCK_ON_CRITICAL', str(self.scanner.block_on_critical)).lower() == 'true'
        self.scanner.block_on_high = os.environ.get('BLOCK_ON_HIGH', str(self.scanner.block_on_high)).lower() == 'true'
        
        #Policy configuration from the environment
        self.policy.opa_server_url = os.environ.get('OPA_SERVER_URL', self.policy.opa_server_url)
        self.policy.enforcement_mode = os.environ.get('ENFORCEMENT_MODE', self.policy.enforcement_mode)
        
        #GitHub configuration from the environment
        self.github.github_token = os.environ.get('GITHUB_TOKEN')
        self.github.repository = os.environ.get('GITHUB_REPOSITORY')
        self.github.workflow_run_id = os.environ.get('GITHUB_RUN_ID')
        self.github.commit_sha = os.environ.get('GITHUB_SHA')
        
        if os.environ.get('GITHUB_EVENT_PATH'):
            self._load_github_event_data(os.environ['GITHUB_EVENT_PATH'])
        
        #Security configuration from the environment
        self.security.enable_encryption_at_rest = os.environ.get('ENABLE_ENCRYPTION', str(self.security.enable_encryption_at_rest)).lower() == 'true'
        self.security.enable_audit_logging = os.environ.get('ENABLE_AUDIT_LOGGING', str(self.security.enable_audit_logging)).lower() == 'true'
        
        #Monitoring configuration from the environment
        self.monitoring.enable_metrics = os.environ.get('ENABLE_METRICS', str(self.monitoring.enable_metrics)).lower() == 'true'
        self.monitoring.metrics_port = int(os.environ.get('METRICS_PORT', self.monitoring.metrics_port))
    
    def _load_github_event_data(self, event_path: str) -> None:
        """
        Loading the GitHub event data for pull request context.
        
        Args:
            event_path: Path to GitHub event JSON file
        """
        
        try:
            with open(event_path, 'r') as f:
                event_data = json.load(f)
            
            if 'pull_request' in event_data:
                self.github.pull_request_number = event_data['pull_request']['number']
        
        #Event data not available or malformed
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass  
    
    def _update_dataclass(self, dataclass_instance: Any, update_dict: Dict[str, Any]) -> None:
        """
        Updating the dataclass instance fields from dictionary.
        
        Args:
            dataclass_instance: Dataclass instance to update
            update_dict: Dictionary containing field updates
        """

        for key, value in update_dict.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)
    
    def _validate_all(self) -> None:
        """Validating all the configuration components and raising on errors."""
        
        all_errors = []
        
        all_errors.extend([f"Scanner: {e}" for e in self.scanner.validate()])
        all_errors.extend([f"Policy: {e}" for e in self.policy.validate()])
        all_errors.extend([f"GitHub: {e}" for e in self.github.validate()])
        all_errors.extend([f"Security: {e}" for e in self.security.validate()])
        all_errors.extend([f"Monitoring: {e}" for e in self.monitoring.validate()])
        
        if all_errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(all_errors))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converting all the configuration to dictionary format.
        
        Returns:
            Dict[str, Any]: Complete configuration dictionary
        """
        return {
            'environment': self.environment.value,
            'scanner': asdict(self.scanner),
            'policy': asdict(self.policy),
            'github': asdict(self.github),
            'security': asdict(self.security),
            'monitoring': asdict(self.monitoring)
        }
    
    def save_to_file(self, output_path: Path, format: str = 'yaml') -> None:
        """
        Saving the current configuration to a file.
        
        Args:
            output_path: Path for output configuration file
            format: Output format ('yaml' or 'json')
        """

        config_dict = self.to_dict()
        
        with open(output_path, 'w') as f:
            
            if format == 'yaml':
                yaml.dump(config_dict, f, default_flow_style = False, sort_keys = False)
            
            elif format == 'json':
                json.dump(config_dict, f, indent = 2)
            
            else:
                raise ValueError(f"Unsupported format: {format}")


#Global configuration instance
_config: Optional[ConfigurationManager] = None


def get_config() -> ConfigurationManager:
    """
    Getting or creating a global configuration instance.
    
    Returns:
        ConfigurationManager: Global configuration manager instance
    """
    
    global _config
    
    if _config is None:
        _config = ConfigurationManager()
    
    return _config


def reload_config(config_file: Optional[Path] = None) -> ConfigurationManager:
    """
    Reloading the global configuration from sources.
    
    Args:
        config_file: Optional new configuration file path
        
    Returns:
        ConfigurationManager: Reloaded configuration instance
    """
    
    global _config
    _config = ConfigurationManager(config_file = config_file)
    return _config