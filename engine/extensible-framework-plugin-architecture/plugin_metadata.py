"""
Plugin Metadata Module

Defines the PluginMetadata dataclass representing immutable plugin identification,
capabilities, dependencies, and resource/security requirements.

Author: Senior Lead, AutoAudit
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timezone
import re

class SecurityLevel(Enum):
    PUBLIC = 1
    INTERNAL = 2
    RESTRICTED = 3
    CONFIDENTIAL = 4

@dataclass(frozen=True)
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    license: str = "proprietary"
    capabilities: List[str] = field(default_factory = list)
    dependencies: List[str] = field(default_factory = list)
    supported_frameworks: List[str] = field(default_factory = list)
   
    resource_requirements: Dict[str, Any] = field(default_factory = lambda: {
        "cpu_cores": 1,
        "memory_mb": 512,
        "disk_mb": 100,
        "network_bandwidth_mbps": 10
    })

    security_requirements: Dict[str, Any] = field(default_factory = lambda: {
        "security_level": SecurityLevel.INTERNAL.name,
        "encryption_required": True,
        "audit_logging": True,
        "network_isolation": True
    })

    creation_timestamp: datetime = field(default_factory = lambda: datetime.now(timezone.utc))
    checksum: Optional[str] = None

    def __post_init__(self):
        
        #Validating the semantic version format
        version_pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z-.]+)?(?:\+[0-9A-Za-z-.]+)?$'
        
        if not re.match(version_pattern, self.version):
            raise ValueError(f"Invalid semantic version format: {self.version}")

        #Generating checksum if not provided
        if self.checksum is None:
            metadata_dict = asdict(self)
            metadata_dict.pop('checksum', None)
            metadata_json = json.dumps(metadata_dict, sort_keys=True, default=str)
            
            object.__setattr__(self, 'checksum',
                              hashlib.sha256(metadata_json.encode('utf-8')).hexdigest())
