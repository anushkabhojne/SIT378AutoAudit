"""
Data Provider Interfaces

Defines abstract base classes for data providers.

Author: Senior Lead, AutoAudit
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class IDataProvider(ABC):
    @abstractmethod
    async def get_tenant_details(self) -> Dict[str, Any]:
        """
        Retrieve Microsoft 365 tenant details.
        """
        
        pass

    @abstractmethod
    async def get_security_compliance_settings(self) -> Dict[str, Any]:
        """
        Retrieve security and compliance settings.
        """
        
        pass

    @abstractmethod
    async def get_audit_logs(self, filter_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve audit logs with optional filtering.
        """
        
        pass
