"""
Microsoft Graph Data Provider

Implements data access to Microsoft 365 configuration and security data via Microsoft Graph API.

Author: Senior Lead, AutoAudit
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from aiohttp import ClientSession, ClientResponseError
from .interfaces import IDataProvider
from .cache import CacheManager

class MicrosoftGraphProvider(IDataProvider):
    
    def __init__(self, token: str, cache: Optional[CacheManager] = None):
        self._token = token
        self._cache = cache
        self._logger = logging.getLogger(self.__class__.__name__)
        self._base_url = "https://graph.microsoft.com/v1.0"

    async def _get(self, endpoint: str) -> Dict[str, Any]:
        
        headers = {
            "Authorisation": f"Bearer {self._token}",
            "Accept": "application/json"
        }
        
        url = f"{self._base_url}/{endpoint}"
        
        if self._cache:
            cached = await self._cache.get(url)
        
            if cached:
                self._logger.debug(f"Cache hit for {url}")
                return cached

        async with ClientSession() as session:
            
            try:
            
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
            
                    if self._cache:
                        await self._cache.set(url, data)
            
                    return data
            
            except ClientResponseError as e:
                self._logger.error(f"Microsoft Graph API error: {e.status} {e.message}")
                raise
            
            except Exception as e:
                self._logger.error(f"Unexpected error fetching {url}: {e}")
                raise

    async def get_tenant_details(self) -> Dict[str, Any]:
        return await self._get("organization")

    async def get_security_compliance_settings(self) -> Dict[str, Any]:
        return await self._get("security/compliance")

    async def get_audit_logs(self, filter_query: Optional[str] = None) -> Dict[str, Any]:
        endpoint = "auditLogs/signIns"
        
        if filter_query:
            endpoint += f"?$filter={filter_query}"
        
        return await self._get(endpoint)
