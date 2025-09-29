"""
Plugin Interface Module

Defines the abstract base classes and data models for compliance framework plugins,
including lifecycle methods, assessment execution, and configuration validation.

Author: Senior Lead, AutoAudit
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

class PluginStatus(Enum):
    UNKNOWN = 0
    DISCOVERED = 1
    VALIDATING = 2
    VALIDATED = 3
    REGISTERING = 4
    REGISTERED = 5
    INITIALIZING = 6
    READY = 7
    EXECUTING = 8
    SUSPENDED = 9
    ERROR = 10
    TERMINATING = 11
    TERMINATED = 12
    FAILED = 13

@dataclass
class PluginContext:
    context_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    plugin_id: str = ""
    tenant_id: str = ""
    session_id: str = ""
    creation_time: datetime = field(default_factory = datetime.utcnow)
    expiration_time: datetime = None
    security_level: str = "INTERNAL"
    permissions: Dict[str, bool] = field(default_factory = dict)
    configuration: Dict[str, Any] = field(default_factory = dict)

@dataclass
class AssessmentContext:
    assessment_id: str = field(default_factory = lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    framework_name: str = ""
    framework_version: str = ""
    timestamp: datetime = field(default_factory = datetime.utcnow)
    configuration: Dict[str, Any] = field(default_factory = dict)
    data_sources: List[str] = field(default_factory = list)
    output_formats: List[str] = field(default_factory = lambda: ["json", "html"])


@dataclass
class AssessmentResult:
    assessment_id: str
    plugin_id: str
    framework_name: str
    framework_version: str
    start_timestamp: datetime
    completion_timestamp: datetime
    overall_score: float
    risk_level: str
    findings: List[Dict[str, Any]] = field(default_factory = list)
    recommendations: List[Dict[str, Any]] = field(default_factory = list)


class IComplianceFrameworkPlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> Any:
        pass

    @abstractmethod
    async def initialize(self, context: PluginContext) -> bool:
        pass

    @abstractmethod
    async def validate_configuration(self, config: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def execute_assessment(self, data: Dict[str, Any]) -> AssessmentResult:
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        pass