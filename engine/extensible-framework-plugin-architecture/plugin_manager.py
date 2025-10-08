"""
AutoAudit Extensible Framework Plugin Architecture - Core Plugin Implementation

This module provides the foundational classes and interfaces for the plugin architecture,
implementing sophisticated plugin lifecycle management, security boundaries, and 
performance optimisation mechanisms.

Author: Senior Lead, AutoAudit
"""

import asyncio
import logging
import traceback
import json
import hashlib
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Callable, AsyncGenerator, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
import uuid
import weakref

#Importing the cryptographic libraries for security implementation
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

#Importing the validation and serialisation libraries
from marshmallow import Schema, fields, validate, ValidationError
from pydantic import BaseModel, validator, Field
import jsonschema

#Configuring the sophisticated logging with security considerations
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    
    handlers = [
        logging.FileHandler('/var/log/autoaudit/plugin_framework.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

#Type variables for generic implementations
T = TypeVar('T')
P = TypeVar('P', bound='IComplianceFrameworkPlugin')

class PluginStatus(Enum):
    """
    Enumeration defining comprehensive plugin lifecycle states with detailed
    status tracking capabilities for operational monitoring and troubleshooting.
    
    Each status represents a distinct phase in plugin lifecycle management
    enabling precise state tracking and appropriate operational responses.
    """
    UNKNOWN = auto()          #Initial state before discovery
    DISCOVERED = auto()       #Plugin discovered but not validated
    VALIDATING = auto()       #Currently undergoing validation procedures
    VALIDATED = auto()        #Passed validation, ready for registration
    REGISTERING = auto()      #Currently being registered in plugin registry
    REGISTERED = auto()       #Successfully registered, ready for initialisation
    INITIALIZING = auto()     #Currently undergoing initialisation procedures
    READY = auto()           #Fully initialised and ready for execution
    EXECUTING = auto()       #Currently executing assessment operations
    SUSPENDED = auto()       #Temporarily suspended due to errors or maintenance
    ERROR = auto()           #Error state requiring administrative intervention
    TERMINATING = auto()     #Currently undergoing cleanup and termination
    TERMINATED = auto()      #Successfully terminated and resources cleaned up
    FAILED = auto()          #Failed state requiring manual recovery

class PluginCapability(Enum):
    """
    Comprehensive enumeration of plugin capabilities enabling sophisticated
    capability-based plugin selection and workflow orchestration.
    
    Capabilities define specific functional areas plugins can support,
    enabling intelligent plugin composition for complex assessment scenarios.
    """
    RULE_EVALUATION = "rule_evaluation"           #Core compliance rule evaluation
    DATA_TRANSFORMATION = "data_transformation"   #Data format and structure transformation
    REPORT_GENERATION = "report_generation"       #Assessment report generation
    REMEDIATION_GUIDANCE = "remediation_guidance" #Automated remediation recommendations
    RISK_ASSESSMENT = "risk_assessment"          #Risk scoring and analysis
    THREAT_MODELING = "threat_modeling"          #Threat landscape analysis
    AUDIT_LOGGING = "audit_logging"              #Comprehensive audit trail generation
    NOTIFICATION_DISPATCH = "notification_dispatch" #Alert and notification distribution
    DATA_VISUALIZATION = "data_visualization"     #Chart and graph generation
    CUSTOM_ANALYSIS = "custom_analysis"          #Framework-specific analysis capabilities

class SecurityLevel(Enum):
    """
    Security classification levels for plugin execution environments
    determining access controls, resource permissions, and isolation boundaries.
    
    Security levels implement defense-in-depth strategies with graduated
    access controls based on plugin trust levels and organisational policies.
    """
    PUBLIC = 1      #Minimal security requirements, public plugins
    INTERNAL = 2    #Internal organization plugins, moderate security
    RESTRICTED = 3  #Restricted access plugins, enhanced security controls
    CONFIDENTIAL = 4 #Confidential plugins, maximum security boundaries

@dataclass(frozen=True)
class PluginMetadata:
    """
    Immutable metadata container providing comprehensive plugin identification,
    capability declaration, and dependency specification information.
    
    Metadata serves as the authoritative source for plugin characteristics
    enabling automated plugin selection, compatibility verification, and
    operational monitoring throughout the plugin lifecycle.
    """
    #Core identification information
    name: str = field(metadata = {"description": "Unique plugin identifier"})
    version: str = field(metadata = {"description": "Semantic version string"})
    description: str = field(metadata = {"description": "Human-readable plugin description"})
    author: str = field(metadata = {"description": "Plugin author or organization"})
    license: str = field(default = "proprietary", metadata = {"description": "Plugin license type"})
    
    #Functional capability declarations
    capabilities: List[PluginCapability] = field(
        default_factory = list,
        metadata = {"description": "List of supported plugin capabilities"}
    )
    
    #Dependency and compatibility specifications
    dependencies: List[str] = field(
        default_factory = list,
        metadata = {"description": "List of required plugin dependencies"}
    )

    supported_frameworks: List[str] = field(
        default_factory = list,
        metadata = {"description": "List of compatible compliance frameworks"}
    )
    
    #Resource and security requirements
    resource_requirements: Dict[str, Any] = field(
        default_factory = lambda: {
            "cpu_cores": 1,
            "memory_mb": 512,
            "disk_mb": 100,
            "network_bandwidth_mbps": 10
        },
        metadata = {"description": "Resource allocation requirements"}
    )
    security_requirements: Dict[str, Any] = field(
        default_factory = lambda: {
            "security_level": SecurityLevel.INTERNAL,
            "encryption_required": True,
            "audit_logging": True,
            "network_isolation": True
        },
        metadata = {"description": "Security and isolation requirements"}
    )
    
    #Operational metadata
    creation_timestamp: datetime = field(
        default_factory = lambda: datetime.now(timezone.utc),
        metadata = {"description": "Plugin creation timestamp"}
    )

    checksum: Optional[str] = field(
        default = None,
        metadata = {"description": "Plugin integrity verification checksum"}
    )
    
    def __post_init__(self):
        """
        Post-initialisation validation ensuring metadata consistency
        and generating integrity verification checksums for security verification.
        """

        #Validating the semantic version format
        import re
        version_pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        
        if not re.match(version_pattern, self.version):
            raise ValueError(f"Invalid semantic version format: {self.version}")
        
        #Generating the integrity checksum if not provided
        if self.checksum is None:
            metadata_dict = asdict(self)
            metadata_dict.pop('checksum', None)  #Removing the checksum from calculation
            metadata_json = json.dumps(metadata_dict, sort_keys = True, default = str)
            
            object.__setattr__(self, 'checksum', 
                              hashlib.sha256(metadata_json.encode()).hexdigest())

@dataclass
class PluginContext:
    """
    Comprehensive execution context providing plugins with access to system
    services, configuration parameters, and operational resources while
    maintaining security boundaries and audit trail requirements.
    
    Context objects implement sophisticated access control mechanisms ensuring
    plugins receive appropriate system access based on their security level
    and operational requirements.
    """
    #Core identification and session information
    context_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    plugin_id: str = field(metadata = {"description": "Associated plugin identifier"})
    tenant_id: str = field(metadata = {"description": "Tenant isolation identifier"})
    session_id: str = field(metadata = {"description": "Assessment session identifier"})
    
    #Temporal context information
    creation_time: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    expiration_time: Optional[datetime] = field(default = None)
    
    #Security and access control context
    security_level: SecurityLevel = field(default = SecurityLevel.INTERNAL)
    permissions: Dict[str, bool] = field(default_factory = dict)
    encrypted_credentials: Optional[bytes] = field(default = None)
    
    #Configuration and operational parameters
    configuration: Dict[str, Any] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    operational_metadata: Dict[str, Any] = field(default_factory=dict)
    
    #Service provider references (using weak references to prevent circular references)
    _data_provider: Optional[weakref.ReferenceType] = field(default = None, init = False, repr = False)
    _event_bus: Optional[weakref.ReferenceType] = field(default = None, init = False, repr = False)
    _metrics_collector: Optional[weakref.ReferenceType] = field(default = None, init = False, repr = False)
    
    def set_data_provider(self, provider: 'IDataProvider') -> None:
        """Setting the data provider using weak reference to prevent memory leaks."""
        
        self._data_provider = weakref.ref(provider)
    
    def get_data_provider(self) -> Optional['IDataProvider']:
        """Retrieving the data provider instance if available."""
        
        return self._data_provider() if self._data_provider else None
    
    def set_event_bus(self, event_bus: 'IEventBus') -> None:
        """Setting the event bus using weak reference for inter-plugin communication."""
        
        self._event_bus = weakref.ref(event_bus)
    
    def get_event_bus(self) -> Optional['IEventBus']:
        """Retrieving the event bus instance if available."""
        
        return self._event_bus() if self._event_bus else None
    
    def set_metrics_collector(self, collector: 'IMetricsCollector') -> None:
        """Setting the metrics collector for performance and operational monitoring."""
        
        self._metrics_collector = weakref.ref(collector)
    
    def get_metrics_collector(self) -> Optional['IMetricsCollector']:
        """Retrieving the metrics collector instance if available."""
        
        return self._metrics_collector() if self._metrics_collector else None
    
    def is_expired(self) -> bool:
        """Checking if the context has expired based on the expiration time."""
        
        if self.expiration_time is None:
            return False
        
        return datetime.now(timezone.utc) > self.expiration_time
    
    def has_permission(self, permission: str) -> bool:
        
        """Checking if the context has specific permission."""
        return self.permissions.get(permission, False)
    
    def decrypt_credentials(self, encryption_key: bytes) -> Optional[Dict[str, str]]:
        """
        Decrypting the stored credentials using the provided encryption key.
        Implementing secure credential handling with comprehensive error management.
        """

        if not self.encrypted_credentials:
            return None
        
        try:
            f = Fernet(encryption_key)
            decrypted_data = f.decrypt(self.encrypted_credentials)
            return json.loads(decrypted_data.decode())
        
        except Exception as e:
            logger.error(f"Credential decryption failed: {e}")
            return None

@dataclass
class AssessmentContext:
    """
    Comprehensive assessment execution context providing detailed information
    about assessment requirements, data sources, configuration parameters,
    and output specifications for framework plugin execution.
    
    Assessment contexts enable sophisticated assessment orchestration with
    detailed progress tracking, resource management, and result coordination.
    """

    #Core assessment identification
    assessment_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    tenant_id: str = field(metadata = {"description": "Tenant isolation identifier"})
    framework_name: str = field(metadata = {"description": "Target compliance framework"})
    framework_version: str = field(metadata = {"description": "Framework version specification"})
    
    #Temporal context and scheduling
    timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    scheduled_start: Optional[datetime] = field(default = None)
    deadline: Optional[datetime] = field(default = None)
    
    #Configuration and parameters
    configuration: Dict[str, Any] = field(default_factory = dict)
    assessment_scope: Dict[str, Any] = field(default_factory = dict)
    
    #Data source specifications
    data_sources: List[str] = field(default_factory = list)
    data_filters: Dict[str, Any] = field(default_factory = dict)
    
    #Output and reporting specifications
    output_formats: List[str] = field(default_factory = lambda: ["json", "html"])
    report_templates: List[str] = field(default_factory = list)
    notification_targets: List[str] = field(default_factory = list)
    
    #Resource and performance constraints
    execution_timeout: int = field(default = 3600, metadata = {"description": "Execution timeout in seconds"})
    resource_limits: Dict[str, Any] = field(default_factory = dict)
    priority_level: int = field(default = 5, metadata = {"description": "Execution priority (1-10)"})
    
    #Audit and compliance tracking
    requester_identity: Optional[str] = field(default = None)
    authorization_token: Optional[str] = field(default = None)
    audit_requirements: Dict[str, bool] = field(default_factory = dict)

@dataclass
class AssessmentProgress:
    """
    Comprehensive progress tracking for assessment execution providing
    detailed visibility into assessment status, performance metrics,
    and completion estimates for operational monitoring and user experience.
    
    Progress objects enable sophisticated progress reporting with granular
    step tracking, performance analysis, and predictive completion estimates.
    """

    #Core progress identification
    assessment_id: str = field(metadata = {"description": "Associated assessment identifier"})
    plugin_id: str = field(metadata = {"description": "Executing plugin identifier"})
    
    #Progress tracking information
    current_step: str = field(metadata = {"description": "Currently executing step description"})
    current_step_index: int = field(metadata = {"description": "Current step index (0-based)"})
    total_steps: int = field(metadata = {"description": "Total number of assessment steps"})
    completed_steps: int = field(metadata = {"description": "Number of completed steps"})
    
    #Temporal progress information
    start_time: datetime = field(metadata = {"description": "Assessment start timestamp"})
    current_time: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    estimated_completion: Optional[datetime] = field(default = None)
    elapsed_seconds: float = field(init = False)
    
    #Performance and status information
    status_message: str = field(default = "", metadata = {"description": "Detailed status message"})
    progress_percentage: float = field(init = False, metadata = {"description": "Completion percentage"})
    processing_rate: Optional[float] = field(default = None, metadata = {"description": "Items per second"})
    
    #Resource utilisation tracking
    cpu_usage_percentage: Optional[float] = field(default = None)
    memory_usage_mb: Optional[float] = field(default = None)
    network_io_bytes: Optional[int] = field(default = None)
    
    #Error and warning tracking
    warning_count: int = field(default = 0)
    error_count: int = field(default = 0)
    last_error: Optional[str] = field(default = None)
    
    def __post_init__(self):
        """Calculate derived fields and validate progress consistency."""

        #Calculating the elapsed time
        object.__setattr__(self, 'elapsed_seconds', 
                          (self.current_time - self.start_time).total_seconds())
        
        #Calculating the progress percentage
        if self.total_steps > 0:
            object.__setattr__(self, 'progress_percentage', 
                              (self.completed_steps / self.total_steps) * 100)
            
        else:
            object.__setattr__(self, 'progress_percentage', 0.0)
        
        #Validating the progress consistency
        if self.completed_steps > self.total_steps:
            raise ValueError("Completed steps cannot exceed total steps")
        
        if self.current_step_index >= self.total_steps:
            raise ValueError("Current step index must be less than total steps")

@dataclass
class ComplianceFinding:
    """
    Comprehensive compliance finding representation providing detailed
    information about compliance violations, risk assessments, and
    remediation guidance for enterprise compliance reporting.
    
    Findings implement sophisticated classification, risk scoring, and
    remediation tracking enabling comprehensive compliance management.
    """

    #Core finding identification
    finding_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    rule_id: str = field(metadata = {"description": "Associated compliance rule identifier"})
    framework_name: str = field(metadata = {"description": "Source compliance framework"})
    
    #Finding classification and severity
    title: str = field(metadata = {"description": "Human-readable finding title"})
    description: str = field(metadata = {"description": "Detailed finding description"})
    severity: str = field(metadata = {"description": "Finding severity (Critical, High, Medium, Low)"})
    risk_score: float = field(metadata = {"description": "Numerical risk score (0.0-10.0)"})
    
    #Technical details and evidence
    affected_resources: List[str] = field(default_factory=list)
    evidence_data: Dict[str, Any] = field(default_factory=dict)
    technical_details: Dict[str, Any] = field(default_factory=dict)
    
    #Compliance and regulatory context
    compliance_status: str = field(metadata = {"description": "Pass, Fail, Warning, Info"})
    regulatory_impact: List[str] = field(default_factory = list)
    business_impact: str = field(default = "")
    
    #Remediation and response information
    remediation_priority: int = field(default = 5, metadata = {"description": "Remediation priority (1-10)"})
    estimated_remediation_effort: Optional[str] = field(default = None)
    remediation_deadline: Optional[datetime] = field(default = None)
    
    #Audit and tracking information
    discovery_timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    last_verified: Optional[datetime] = field(default = None)
    false_positive_likelihood: float = field(default = 0.0, metadata = {"description": "False positive probability (0.0-1.0)"})
    
    def __post_init__(self):
        """Validate finding data consistency and apply business rules."""

        #Validating the severity levels
        valid_severities = ["Critical", "High", "Medium", "Low", "Info"]
        
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}. Must be one of {valid_severities}")
        
        #Validating the compliance status
        valid_statuses = ["Pass", "Fail", "Warning", "Info", "Not_Applicable"]
        
        if self.compliance_status not in valid_statuses:
            raise ValueError(f"Invalid compliance status: {self.compliance_status}")
        
        #Validating the risk score range
        if not 0.0 <= self.risk_score <= 10.0:
            raise ValueError("Risk score must be between 0.0 and 10.0")
        
        #Validating the priority range
        if not 1 <= self.remediation_priority <= 10:
            raise ValueError("Remediation priority must be between 1 and 10")

@dataclass
class RemediationRecommendation:
    """
    Comprehensive remediation recommendation providing detailed guidance
    for addressing compliance violations with implementation procedures,
    risk mitigation strategies, and success verification criteria.
    
    Recommendations implement sophisticated guidance frameworks enabling
    automated remediation workflows and comprehensive tracking capabilities.
    """
    #Core recommendation identification
    recommendation_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    finding_id: str = field(metadata={"description": "Associated compliance finding"})
    
    #Recommendation content and guidance
    title: str = field(metadata = {"description": "Recommendation title"})
    description: str = field(metadata = {"description": "Detailed recommendation description"})
    implementation_steps: List[str] = field(default_factory = list)
    
    #Risk and impact assessment
    risk_reduction: float = field(metadata = {"description": "Risk reduction percentage (0.0-100.0)"})
    implementation_complexity: str = field(metadata = {"description": "Low, Medium, High, Critical"})
    estimated_effort_hours: Optional[float] = field(default = None)
    
    #Implementation guidance and automation
    automation_available: bool = field(default = False)
    automation_script: Optional[str] = field(default = None)
    verification_procedures: List[str] = field(default_factory = list)
    rollback_procedures: List[str] = field(default_factory = list)
    
    #Dependencies and prerequisites
    prerequisites: List[str] = field(default_factory = list)
    affected_systems: List[str] = field(default_factory = list)
    business_approval_required: bool = field(default = False)
    
    #Tracking and monitoring
    creation_timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    implementation_deadline: Optional[datetime] = field(default = None)
    success_criteria: List[str] = field(default_factory = list)

@dataclass
class AssessmentResult:
    """
    Comprehensive assessment result container providing detailed assessment
    outcomes, performance metrics, and operational information for compliance
    reporting and decision-making processes.
    
    Results implement sophisticated aggregation, analysis, and reporting
    capabilities enabling comprehensive compliance posture assessment.
    """
    #Core result identification
    assessment_id: str = field(metadata = {"description": "Unique assessment identifier"})
    plugin_id: str = field(metadata = {"description": "Executing plugin identifier"})
    framework_name: str = field(metadata = {"description": "Assessed compliance framework"})
    framework_version: str = field(metadata = {"description": "Framework version used"})
    
    #Temporal execution information
    start_timestamp: datetime = field(metadata = {"description": "Assessment start time"})
    completion_timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    execution_duration_seconds: float = field(init = False)
    
    #Assessment outcomes and scoring
    overall_score: float = field(metadata = {"description": "Overall compliance score (0.0-100.0)"})
    risk_level: str = field(metadata = {"description": "Overall risk level assessment"})
    compliance_percentage: float = field(metadata = {"description": "Percentage of controls passed"})
    
    #Detailed findings and recommendations
    findings: List[ComplianceFinding] = field(default_factory = list)
    recommendations: List[RemediationRecommendation] = field(default_factory = list)
    
    #Performance and operational metrics
    performance_metrics: Dict[str, float] = field(default_factory = dict)
    resource_consumption: Dict[str, float] = field(default_factory = dict)
    data_points_analyzed: int = field(default = 0)
    
    #Metadata and context information
    metadata: Dict[str, Any] = field(default_factory = dict)
    execution_context: Dict[str, Any] = field(default_factory = dict)
    
    #Quality and reliability indicators
    confidence_score: float = field(default = 1.0, metadata = {"description": "Result confidence (0.0-1.0)"})
    data_completeness: float = field(default = 1.0, metadata = {"description": "Data completeness percentage"})
    assessment_quality_score: float = field(default = 1.0, metadata = {"description": "Assessment quality indicator"})
    
    def __post_init__(self):
        """Calculate derived metrics and validate result consistency."""
        
        #Calculating the execution duration
        object.__setattr__(self, 'execution_duration_seconds',
                          (self.completion_timestamp - self.start_timestamp).total_seconds())
        
        #Validating the score ranges
        if not 0.0 <= self.overall_score <= 100.0:
            raise ValueError("Overall score must be between 0.0 and 100.0")
        
        #Calculating the compliance percentage from findings if not provided
        if self.compliance_percentage == 0.0 and self.findings:
            passed_findings = sum(1 for f in self.findings if f.compliance_status == "Pass")
            
            object.__setattr__(self, 'compliance_percentage', 
                              (passed_findings / len(self.findings)) * 100)

class PluginExecutionError(Exception):
    """
    Specialised exception class for plugin execution errors providing
    comprehensive error context, troubleshooting guidance, and recovery
    information for operational support and debugging procedures.
    
    Error objects implement sophisticated error categorization enabling
    automated error handling, escalation procedures, and resolution tracking.
    """
    
    def __init__(
        self, 
        message: str, 
        plugin_id: str = None,
        error_code: str = None,
        error_category: str = None,
        recovery_suggestions: List[str] = None,
        technical_details: Dict[str, Any] = None,
        original_exception: Exception = None
    ):
        
        """
        Initialise plugin execution error with comprehensive context information
        enabling detailed error analysis and automated recovery procedures.
        """
        super().__init__(message)
        
        self.message = message
        self.plugin_id = plugin_id
        self.error_code = error_code or "PLUGIN_EXECUTION_ERROR"
        self.error_category = error_category or "EXECUTION"
        self.recovery_suggestions = recovery_suggestions or []
        self.technical_details = technical_details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now(timezone.utc)
        self.error_id = str(uuid.uuid4())
        
        #Generating the comprehensive error context for troubleshooting
        self.error_context = {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "plugin_id": self.plugin_id,
            "error_code": self.error_code,
            "error_category": self.error_category,
            "message": self.message,
            "technical_details": self.technical_details,
            "stack_trace": traceback.format_exc() if original_exception else None,
            "recovery_suggestions": self.recovery_suggestions
        }
        
        #Logging the error for operational monitoring
        logger.error(f"Plugin execution error: {self.error_context}")

class IComplianceFrameworkPlugin(ABC):
    """
    Abstract base class defining the comprehensive interface contract for
    compliance framework plugins, establishing standardised integration
    patterns while enabling framework-specific implementation flexibility.
    
    This interface serves as the foundational contract ensuring consistent
    plugin behaviour across diverse compliance framework implementations
    while providing sophisticated lifecycle management and execution capabilities.
    """
    
    def __init__(self):
        """
        Initialise plugin base implementation with sophisticated state
        management, performance monitoring, and operational tracking capabilities.
        """

        self._status = PluginStatus.UNKNOWN
        self._context: Optional[PluginContext] = None
        self._initialization_time: Optional[datetime] = None
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0
        self._last_error: Optional[Exception] = None
        
        #Performance monitoring initialisation
        self._performance_metrics = {
            "initialization_time_seconds": 0.0,
            "average_execution_time_seconds": 0.0,
            "total_executions": 0,
            "success_rate": 1.0,
            "resource_efficiency_score": 1.0
        }
        
        #Security and audit tracking
        self._security_events = []
        self._audit_trail = []
        
        logger.info(f"Plugin {self.__class__.__name__} initialised with base capabilities")
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        Return comprehensive plugin metadata including identification,
        capabilities, dependencies, and operational requirements.
        
        Metadata serves as the authoritative source for plugin characteristics
        enabling automated plugin selection and operational management.
        """

        pass
    
    @abstractmethod
    async def initialize(self, context: PluginContext) -> bool:
        """
        Initialise plugin with provided execution context implementing
        sophisticated initialisation procedures including dependency resolution,
        configuration validation, and resource allocation.
        
        Initialisation must be idempotent, supporting multiple initialisation
        calls without adverse effects or resource leaks.
        
        Args:
            context: Plugin execution context with configuration and resources
            
        Returns:
            bool: True if initialisation successful, False otherwise
            
        Raises:
            PluginExecutionError: If initialisation fails with detailed error context
        """
        pass
    
    @abstractmethod
    async def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration parameters ensuring compliance with
        plugin requirements and system constraints while providing detailed
        validation feedback for troubleshooting and configuration management.
        
        Validation must be comprehensive, checking parameter types, value ranges,
        dependency compatibility, and security policy compliance.
        
        Args:
            config: Configuration dictionary with plugin-specific parameters
            
        Returns:
            bool: True if configuration valid, False otherwise
            
        Raises:
            ValidationError: If configuration validation fails with specific details
        """

        pass
    
    @abstractmethod
    async def execute_assessment(self, data: Dict[str, Any]) -> AssessmentResult:
        """
        Execute compliance assessment with provided data implementing
        framework-specific assessment logic while maintaining standardised
        result formats and comprehensive progress reporting.
        
        Assessment execution must be resilient, implementing comprehensive
        error handling, resource management, and progress tracking capabilities.
        
        Args:
            data: Assessment data including Microsoft 365 configurations
            
        Returns:
            AssessmentResult: Comprehensive assessment results and findings
            
        Raises:
            PluginExecutionError: If assessment execution fails
        """

        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleanup plugin resources implementing comprehensive resource
        deallocation, temporary data removal, and graceful shutdown procedures.
        
        Cleanup must be robust, ensuring resource release even under
        error conditions while maintaining audit trail integrity.
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """

        pass
    
    #Base implementation methods providing common functionality
    
    async def get_status(self) -> PluginStatus:
        """Return current plugin operational status."""
        
        return self._status
    
    async def get_performance_metrics(self) -> Dict[str, float]:
        """Return comprehensive performance metrics for monitoring."""
        
        return self._performance_metrics.copy()
    
    async def get_execution_history(self) -> List[Dict[str, Any]]:
        """Return execution history for analysis and troubleshooting."""
        
        return self._audit_trail.copy()
    
    def _update_status(self, new_status: PluginStatus) -> None:
        """Update plugin status with audit trail generation."""
        
        old_status = self._status
        self._status = new_status
        
        #Generating the audit trail entry
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "status_change",
            "old_status": old_status.name,
            "new_status": new_status.name,
            "context_id": self._context.context_id if self._context else None
        }

        self._audit_trail.append(audit_entry)
        
        logger.info(f"Plugin {self.metadata.name} status changed: {old_status.name} -> {new_status.name}")
    
    def _record_execution_metrics(self, execution_time: float, success: bool) -> None:
        """Record execution metrics for performance monitoring."""
        
        self._execution_count += 1
        self._total_execution_time += execution_time
        
        if not success:
            self._error_count += 1
        
        #Updating the performance metrics
        self._performance_metrics.update({
            "average_execution_time_seconds": self._total_execution_time / self._execution_count,
            "total_executions": self._execution_count,
            "success_rate": (self._execution_count - self._error_count) / self._execution_count,
            "last_execution_time_seconds": execution_time
        })
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check returning detailed status information
        for operational monitoring and troubleshooting procedures.
        """

        return {
            "plugin_id": self.metadata.name,
            "status": self._status.name,
            "health": "healthy" if self._status == PluginStatus.READY else "degraded",
            "uptime_seconds": (datetime.now(timezone.utc) - self._initialization_time).total_seconds() if self._initialization_time else 0,
            "execution_count": self._execution_count,
            "error_count": self._error_count,
            "last_error": str(self._last_error) if self._last_error else None,
            "performance_metrics": self._performance_metrics,
            "resource_usage": await self._get_resource_usage()
        }
    
    async def _get_resource_usage(self) -> Dict[str, float]:
        """Retrieve current resource usage metrics for monitoring."""
        
        #Implementation would integrate with system monitoring tools
        #This is a placeholder for actual resource monitoring integration
        
        return {
            "cpu_percentage": 0.0,
            "memory_mb": 0.0,
            "network_io_bytes": 0.0,
            "disk_io_bytes": 0.0
        }

class IDataProvider(ABC):
    """
    Abstract interface for data access capabilities providing standardised
    mechanisms for framework plugins to access Microsoft 365 configuration
    data while maintaining security boundaries and performance optimisation.
    
    Data providers implement sophisticated access control, caching strategies,
    and performance monitoring ensuring efficient data utilisation across
    multiple plugin instances and assessment scenarios.
    """
    
    @abstractmethod
    async def query_data(self, query: 'DataQuery') -> 'DataResult':
        """
        Execute data query with specified parameters implementing comprehensive
        data access control, performance optimization, and audit trail generation.
        
        Query execution must implement sophisticated caching strategies,
        access control validation, and performance monitoring ensuring
        optimal data access patterns while maintaining security compliance.
        
        Args:
            query: Data query specification with parameters and constraints
            
        Returns:
            DataResult: Query results with metadata and performance information
            
        Raises:
            DataAccessError: If query execution fails or access denied
        """

        pass
    
    @abstractmethod
    async def validate_query(self, query: 'DataQuery') -> bool:
        """
        Validate data query parameters and access permissions ensuring
        query compliance with security policies and system constraints.
        
        Args:
            query: Data query specification for validation
            
        Returns:
            bool: True if query valid and authorized, False otherwise
        """

        pass
    
    @abstractmethod
    async def get_data_schema(self, data_source: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive data source schema information enabling
        dynamic query construction and validation capabilities.
        
        Args:
            data_source: Data source identifier
            
        Returns:
            Dict containing schema information and metadata
        """

        pass

class IEventBus(ABC):
    """
    Abstract interface for event-driven inter-plugin communication providing
    sophisticated message routing, transformation, and delivery capabilities
    enabling complex plugin coordination and workflow orchestration.
    
    Event bus implementations support multiple communication patterns including
    point-to-point messaging, publish-subscribe, and broadcast distribution
    with comprehensive delivery guarantees and audit trail generation.
    """
    
    @abstractmethod
    async def publish_event(self, event: 'PluginEvent') -> bool:
        """
        Publish event to event bus for distribution to interested subscribers
        implementing sophisticated routing, transformation, and delivery mechanisms.
        
        Args:
            event: Event object with payload and routing information
            
        Returns:
            bool: True if event published successfully, False otherwise
        """

        pass
    
    @abstractmethod
    async def subscribe_to_events(
        self, 
        event_types: List[str], 
        callback: Callable[['PluginEvent'], None]
    ) -> str:
        """
        Subscribe to specific event types with callback function for
        asynchronous event processing and plugin coordination.
        
        Args:
            event_types: List of event types to subscribe to
            callback: Callback function for event processing
            
        Returns:
            str: Subscription identifier for management and cancellation
        """
        
        pass
    
    @abstractmethod
    async def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """
        Unsubscribe from event notifications using subscription identifier
        ensuring proper cleanup and resource deallocation.
        
        Args:
            subscription_id: Subscription identifier from subscribe operation
            
        Returns:
            bool: True if unsubscription successful, False otherwise
        """
        
        pass

class IMetricsCollector(ABC):
    """
    Abstract interface for metrics collection and performance monitoring
    providing comprehensive operational visibility into plugin execution,
    resource utilisation, and system performance characteristics.
    
    Metrics collectors implement sophisticated data aggregation, analysis,
    and reporting capabilities enabling operational excellence and
    continuous improvement initiatives.
    """
    
    @abstractmethod
    async def record_metric(
        self, 
        metric_name: str, 
        value: Union[int, float], 
        tags: Dict[str, str] = None
    ) -> None:
        """
        Record individual metric value with optional tags for
        dimensional analysis and filtering capabilities.
        
        Args:
            metric_name: Metric identifier for aggregation and analysis
            value: Metric value (numeric)
            tags: Optional dimensional tags for filtering and grouping
        """
        
        pass
    
    @abstractmethod
    async def record_execution_time(
        self, 
        operation: str, 
        duration_seconds: float,
        plugin_id: str = None
    ) -> None:
        """
        Record operation execution time for performance analysis
        and optimisation opportunity identification.
        
        Args:
            operation: Operation identifier
            duration_seconds: Execution duration in seconds
            plugin_id: Optional plugin identifier for attribution
        """
        
        pass
    
    @abstractmethod
    async def get_metrics_summary(
        self, 
        time_range: Dict[str, datetime] = None
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive metrics summary for specified time range
        enabling performance analysis and operational reporting.
        
        Args:
            time_range: Optional time range specification for filtering
            
        Returns:
            Dict containing aggregated metrics and analysis
        """
        
        pass

@dataclass
class DataQuery:
    """
    Comprehensive data query specification providing detailed query
    parameters, filtering criteria, performance constraints, and
    security requirements for data access operations.
    
    Query objects enable sophisticated data access patterns with
    comprehensive access control, caching optimisation, and
    performance monitoring capabilities.
    """
    #Core query identification
    query_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    requester_id: str = field(metadata = {"description": "Plugin or user making the query"})
    
    #Data source and targeting
    data_source: str = field(metadata = {"description": "Target data source identifier"})
    query_type: str = field(metadata = {"description": "Query operation type"})
    query_parameters: Dict[str, Any] = field(default_factory = dict)
    
    #Filtering and selection criteria
    filtering_criteria: Dict[str, Any] = field(default_factory = dict)
    sorting_criteria: List[Dict[str, str]] = field(default_factory = list)
    pagination: Optional[Dict[str, Any]] = field(default = None)
    
    #Performance and caching configuration
    caching_policy: str = field(default = "default", metadata = {"description": "Caching behaviour specification"})
    timeout_seconds: int = field(default = 30, metadata = {"description": "Query timeout limit"})
    priority_level: int = field(default = 5, metadata = {"description": "Query priority (1-10)"})
    
    #Security and access control
    access_token: Optional[str] = field(default = None)
    permission_scope: List[str] = field(default_factory = list)
    
    #Audit and tracking information
    creation_timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = field(default = None)

@dataclass
class DataResult:
    """
    Comprehensive data query result container providing query outcomes,
    performance metrics, cache status information, and operational metadata
    enabling sophisticated data access analysis and optimisation.
    
    Result objects implement detailed performance tracking enabling
    comprehensive data access pattern analysis and optimisation opportunities.
    """

    #Core result identification
    query_id: str = field(metadata = {"description": "Associated query identifier"})
    result_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    
    #Temporal result information
    timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    execution_start: datetime = field(metadata = {"description": "Query execution start time"})
    execution_duration_seconds: float = field(metadata = {"description": "Total execution time"})
    
    #Query result data and metadata
    data: Union[Dict, List, Any] = field(metadata = {"description": "Query result data"})
    record_count: int = field(metadata = {"description": "Number of records returned"})
    data_size_bytes: int = field(metadata = {"description": "Result data size in bytes"})
    
    #Performance and caching information
    cache_status: str = field(metadata = {"description": "Cache hit/miss/refresh status"})
    query_performance: Dict[str, float] = field(default_factory = dict)
    
    #Quality and reliability indicators
    data_quality_score: float = field(default = 1.0, metadata = {"description": "Data quality assessment"})
    completeness_percentage: float = field(default = 100.0, metadata = {"description": "Data completeness"})
    
    #Metadata and context
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

@dataclass
class PluginEvent:
    """
    Comprehensive event object for inter-plugin communication providing
    detailed event information, routing specifications, and payload data
    enabling sophisticated event-driven plugin coordination.
    
    Events implement comprehensive routing, transformation, and delivery
    tracking enabling reliable communication patterns across plugin boundaries.
    """

    #Core event identification
    event_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    event_type: str = field(metadata = {"description": "Event type classification"})
    event_source: str = field(metadata = {"description": "Event source plugin identifier"})
    
    #Temporal event information
    timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    expiration_time: Optional[datetime] = field(default = None)
    
    #Event payload and context
    payload: Dict[str, Any] = field(default_factory = dict)
    correlation_id: Optional[str] = field(default = None)
    
    #Routing and delivery configuration
    target_plugins: List[str] = field(default_factory = list)
    broadcast: bool = field(default = False)
    delivery_guarantee: str = field(default = "at_least_once")
    
    #Priority and processing configuration
    priority: int = field(default = 5, metadata = {"description": "Event priority (1-10)"})
    processing_requirements: Dict[str, Any] = field(default_factory = dict)
    
    #Security and access control
    security_classification: str = field(default = "internal")
    access_requirements: List[str] = field(default_factory = list)

class PluginManager:
    """
    Comprehensive plugin management system implementing sophisticated
    plugin lifecycle management, dependency resolution, security enforcement,
    and operational monitoring capabilities for enterprise-scale deployments.
    
    Plugin managers coordinate all aspects of plugin operations including
    discovery, registration, validation, activation, execution coordination,
    and cleanup procedures while maintaining comprehensive audit trails
    and performance monitoring.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialise plugin manager with comprehensive configuration management,
        security policy enforcement, and operational monitoring capabilities.
        
        Args:
            config: Optional configuration dictionary for manager customization
        """

        self.config = config or {}
        
        #Core plugin management data structures
        self._registered_plugins: Dict[str, IComplianceFrameworkPlugin] = {}
        self._plugin_metadata: Dict[str, PluginMetadata] = {}
        
        self._plugin_contexts: Dict[str, PluginContext] = {}
                #Dependency graph for plugins: plugin name -> list of dependent plugin names
        
        self._dependency_graph: Dict[str, List[str]] = {}

        #Plugin status tracking: plugin name -> PluginStatus
        self._plugin_statuses: Dict[str, PluginStatus] = {}

        #Plugin execution locks to prevent concurrent conflicting operations
        self._plugin_locks: Dict[str, asyncio.Lock] = {}

        #Event loop for async operations
        self._loop = asyncio.get_event_loop()

        #Logger instance
        self._logger = logging.getLogger(self.__class__.__name__)

        #Plugin registry source locations (filesystem paths, remote URLs, etc.)
        self._plugin_sources: List[str] = self.config.get("plugin_sources", [])

        #Plugin validation policies and security scanners
        self._validation_policies = self.config.get("validation_policies", {})

        #Plugin execution resource limits (can be overridden per plugin)
        self._default_resource_limits = self.config.get("default_resource_limits", {
            "cpu_cores": 1,
            "memory_mb": 512,
            "disk_mb": 100,
            "network_bandwidth_mbps": 10
        })

        #Audit trail storage (in-memory for now, extendable to persistent storage)
        self._audit_trail: List[Dict[str, Any]] = []

        self._logger.info("PluginManager initialized with configuration: %s", self.config)

    async def discover_plugins(self) -> List[PluginMetadata]:
        """
        Discover plugins from configured sources.

        This method scans configured plugin sources (e.g., filesystem directories,
        remote repositories) to identify available plugins. It loads plugin metadata
        and prepares them for registration.

        Returns:
            List[PluginMetadata]: List of discovered plugin metadata objects.
        """
        
        discovered_plugins = []
        self._logger.info("Starting plugin discovery from sources: %s", self._plugin_sources)

        for source in self._plugin_sources:
            
            #For filesystem source, scan directory for plugin manifests
            if source.startswith("file://"):
                path = Path(source[7:])
                
                if not path.exists() or not path.is_dir():
                    self._logger.warning("Plugin source path does not exist or is not a directory: %s", path)
                    continue
                
                for plugin_dir in path.iterdir():
                    
                    if plugin_dir.is_dir():
                        manifest_path = plugin_dir / "plugin_metadata.json"
                        
                        if manifest_path.exists():
                            try:
                                with open(manifest_path, "r", encoding="utf-8") as f:
                                    metadata_json = json.load(f)
                                
                                metadata = PluginMetadata(**metadata_json)
                                discovered_plugins.append(metadata)
                                self._logger.info("Discovered plugin: %s version %s", metadata.name, metadata.version)
                            
                            except Exception as e:
                                self._logger.error("Failed to load plugin metadata from %s: %s", manifest_path, e)
            else:
                #Placeholder for remote repository or other source types
                self._logger.warning("Unsupported plugin source type: %s", source)

        self._logger.info("Plugin discovery completed: %d plugins found", len(discovered_plugins))
        return discovered_plugins

    async def register_plugin(self, plugin: IComplianceFrameworkPlugin) -> bool:
        """
        Register a plugin with the manager after validation.

        This method performs multi-stage validation including schema compliance,
        security scanning, dependency resolution, and compatibility checks.
        Upon successful validation, the plugin is added to the registry and
        prepared for activation.

        Args:
            plugin (IComplianceFrameworkPlugin): Plugin instance to register.

        Returns:
            bool: True if registration successful, False otherwise.
        """
        plugin_name = plugin.metadata.name
        self._logger.info("Registering plugin: %s", plugin_name)

        if plugin_name in self._registered_plugins:
            self._logger.warning("Plugin %s is already registered", plugin_name)
            return False

        #Validating the plugin metadata and configuration
        try:
            valid = await plugin.validate_configuration(plugin.metadata.resource_requirements)
            if not valid:
                self._logger.error("Plugin %s failed configuration validation", plugin_name)
                return False
            
        except Exception as e:
            self._logger.error("Exception during configuration validation for plugin %s: %s", plugin_name, e)
            return False

        #Dependency resolution
        dependencies = plugin.metadata.dependencies
        for dep in dependencies:
            
            if dep not in self._registered_plugins:
                self._logger.error("Plugin %s dependency %s is not registered", plugin_name, dep)
                return False

        #Checking for circular dependencies
        if self._detect_circular_dependency(plugin_name, dependencies):
            self._logger.error("Circular dependency detected for plugin %s", plugin_name)
            return False

        #Registering the plugin metadata and instance
        self._registered_plugins[plugin_name] = plugin
        self._plugin_metadata[plugin_name] = plugin.metadata
        self._dependency_graph[plugin_name] = dependencies
        self._plugin_statuses[plugin_name] = PluginStatus.REGISTERED
        self._plugin_locks[plugin_name] = asyncio.Lock()

        #Audit trail entry
        self._audit_trail.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "plugin_registered",
            "plugin_name": plugin_name,
            "metadata": asdict(plugin.metadata)
        })

        self._logger.info("Plugin %s registered successfully", plugin_name)
        return True

    def _detect_circular_dependency(self, plugin_name: str, dependencies: List[str]) -> bool:
        """
        Detect circular dependencies in the plugin dependency graph.

        Args:
            plugin_name (str): Name of the plugin being registered.
            dependencies (List[str]): List of plugin dependencies.

        Returns:
            bool: True if circular dependency detected, False otherwise.
        """
        
        visited = set()
        stack = set()

        def visit(node: str) -> bool:
            if node in stack:
                return True  #Circular dependency detected
            
            if node in visited:
                return False
            
            visited.add(node)
            stack.add(node)
            
            for dep in self._dependency_graph.get(node, []):
                if visit(dep):
                    return True
            
            stack.remove(node)
            return False

        #Temporarily adding the new plugin dependencies for detection
        self._dependency_graph[plugin_name] = dependencies
        has_cycle = visit(plugin_name)
        
        if has_cycle:
            #Removing the temporary addition if cycle detected
            self._dependency_graph.pop(plugin_name, None)
        
        return has_cycle

    async def initialize_plugin(self, plugin_name: str, context: PluginContext) -> bool:
        """
        Initialise a registered plugin with the provided execution context.

        Args:
            plugin_name (str): Name of the plugin to initialize.
            context (PluginContext): Execution context for the plugin.

        Returns:
            bool: True if initialization successful, False otherwise.
        """
        
        if plugin_name not in self._registered_plugins:
            self._logger.error("Plugin %s is not registered", plugin_name)
            return False

        plugin = self._registered_plugins[plugin_name]
        lock = self._plugin_locks[plugin_name]

        async with lock:
            try:
                self._plugin_statuses[plugin_name] = PluginStatus.INITIALIZING
                self._logger.info("Initialising plugin %s", plugin_name)
                success = await plugin.initialize(context)
                
                if success:
                    self._plugin_statuses[plugin_name] = PluginStatus.READY
                    self._logger.info("Plugin %s initialized successfully", plugin_name)
                    return True
                
                else:
                    self._plugin_statuses[plugin_name] = PluginStatus.ERROR
                    self._logger.error("Plugin %s failed to initialize", plugin_name)
                    return False
            
            except Exception as e:
                self._plugin_statuses[plugin_name] = PluginStatus.ERROR
                self._logger.error("Exception during plugin %s initialization: %s", plugin_name, e)
                return False

    async def execute_plugin_assessment(self, plugin_name: str, data: Dict[str, Any]) -> AssessmentResult:
        """
        Execute the compliance assessment using the specified plugin.

        Args:
            plugin_name (str): Name of the plugin to execute.
            data (Dict[str, Any]): Assessment data input.

        Returns:
            AssessmentResult: Result of the compliance assessment.

        Raises:
            PluginExecutionError: If execution fails or plugin is not ready.
        """
        
        if plugin_name not in self._registered_plugins:
            raise PluginExecutionError(f"Plugin {plugin_name} is not registered", plugin_id = plugin_name)

        plugin = self._registered_plugins[plugin_name]
        status = self._plugin_statuses.get(plugin_name, PluginStatus.UNKNOWN)
        if status != PluginStatus.READY:
            raise PluginExecutionError(f"Plugin {plugin_name} is not ready for execution (status: {status.name})", plugin_id = plugin_name)

        lock = self._plugin_locks[plugin_name]
        
        async with lock:
            self._plugin_statuses[plugin_name] = PluginStatus.EXECUTING
            start_time = time.perf_counter()
            
            try:
                self._logger.info("Executing assessment with plugin %s", plugin_name)
                result = await plugin.execute_assessment(data)
                execution_time = time.perf_counter() - start_time
                plugin._record_execution_metrics(execution_time, success = True)
                self._plugin_statuses[plugin_name] = PluginStatus.READY

                #Audit trail entry
                self._audit_trail.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "plugin_assessment_executed",
                    "plugin_name": plugin_name,
                    "execution_time_seconds": execution_time,
                    "result_summary": {
                        "overall_score": result.overall_score,
                        "risk_level": result.risk_level,
                        "findings_count": len(result.findings)
                    }
                })

                self._logger.info("Plugin %s assessment executed successfully in %.3f seconds", plugin_name, execution_time)
                return result
            
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                plugin._record_execution_metrics(execution_time, success = False)
                self._plugin_statuses[plugin_name] = PluginStatus.ERROR
                self._logger.error("Plugin %s assessment execution failed: %s", plugin_name, e)
                raise PluginExecutionError(f"Execution failed for plugin {plugin_name}: {e}", plugin_id = plugin_name, original_exception = e)

    async def cleanup_plugin(self, plugin_name: str) -> bool:
        """
        Cleanup resources used by the specified plugin.

        Args:
            plugin_name (str): Name of the plugin to cleanup.

        Returns:
            bool: True if cleanup successful, False otherwise.
        """

        if plugin_name not in self._registered_plugins:
            self._logger.warning("Plugin %s is not registered, skipping cleanup", plugin_name)
            return False

        plugin = self._registered_plugins[plugin_name]
        lock = self._plugin_locks[plugin_name]

        async with lock:
            self._plugin_statuses[plugin_name] = PluginStatus.TERMINATING
            try:
                self._logger.info("Cleaning up plugin %s", plugin_name)
                success = await plugin.cleanup()

                if success:
                    self._plugin_statuses[plugin_name] = PluginStatus.TERMINATED
                    self._logger.info("Plugin %s cleaned up successfully", plugin_name)
                    return True
                
                else:
                    self._plugin_statuses[plugin_name] = PluginStatus.ERROR
                    self._logger.error("Plugin %s cleanup failed", plugin_name)
                    return False
                
            except Exception as e:
                self._plugin_statuses[plugin_name] = PluginStatus.ERROR
                self._logger.error("Exception during plugin %s cleanup: %s", plugin_name, e)
                return False

    async def get_plugin_status(self, plugin_name: str) -> PluginStatus:
        """
        Retrieve the current status of a plugin.

        Args:
            plugin_name (str): Name of the plugin.

        Returns:
            PluginStatus: Current status of the plugin.
        """
        
        return self._plugin_statuses.get(plugin_name, PluginStatus.UNKNOWN)

    async def list_registered_plugins(self) -> List[PluginMetadata]:
        """
        List metadata of all registered plugins.

        Returns:
            List[PluginMetadata]: List of registered plugin metadata.
        """
        
        return list(self._plugin_metadata.values())

    async def get_audit_trail(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail entries, optionally filtered by timestamp.

        Args:
            since (Optional[datetime]): Filter entries after this timestamp.

        Returns:
            List[Dict[str, Any]]: List of audit trail entries.
        """
        
        if since is None:
            return self._audit_trail.copy()
        
        else:
            return [entry for entry in self._audit_trail if datetime.fromisoformat(entry["timestamp"]) > since]

    async def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of all registered plugins.

        Returns:
            Dict[str, Any]: Health status report including plugin statuses and metrics.
        """
        
        health_report = {}
        
        for plugin_name, plugin in self._registered_plugins.items():
            try:
                status = self._plugin_statuses.get(plugin_name, PluginStatus.UNKNOWN)
                health = await plugin.health_check()
                
                health_report[plugin_name] = {
                    "status": status.name,
                    "health": health.get("health", "unknown"),
                    "uptime_seconds": health.get("uptime_seconds", 0),
                    "execution_count": health.get("execution_count", 0),
                    "error_count": health.get("error_count", 0),
                    "performance_metrics": health.get("performance_metrics", {})
                }
            
            except Exception as e:
                self._logger.error("Health check failed for plugin %s: %s", plugin_name, e)
                
                health_report[plugin_name] = {
                    "status": "ERROR",
                    "health": "unhealthy",
                    "error": str(e)
                }
        return health_report
