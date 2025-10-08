"""
Unit Tests for PluginManager

Author: Senior Lead, AutoAudit
"""

import pytest
import asyncio
from autoaudit_plugin_framework.plugin_manager import PluginManager
from autoaudit_plugin_framework.plugin_interface import IComplianceFrameworkPlugin, PluginContext
from autoaudit_plugin_framework.plugin_metadata import PluginMetadata


class DummyPlugin(IComplianceFrameworkPlugin):
    
    def __init__(self):
        self._metadata = PluginMetadata(
            name = "DummyPlugin",
            version = "1.0.0",
            description = "Dummy plugin for testing",
            author = "Test",
            capabilities = [],
            dependencies = [],
            supported_frameworks = ["CIS"],
            resource_requirements = {},
            security_requirements = {}
        )

        self._initialized = False

    @property
    def metadata(self):
        return self._metadata

    async def initialize(self, context: PluginContext) -> bool:
        self._initialized = True
        return True

    async def validate_configuration(self, config: dict) -> bool:
        return True

    async def execute_assessment(self, data: dict):
        from autoaudit_plugin_framework.plugin_interface import AssessmentResult
        
        return AssessmentResult(
            assessment_id = "test",
            plugin_id = self.metadata.name,
            framework_name = "CIS",
            framework_version = "1.0",
            start_timestamp = None,
            completion_timestamp = None,
            overall_score = 100.0,
            risk_level = "Low",
            findings = [],
            recommendations = []
        )

    async def cleanup(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_plugin_manager_register_initialize_execute_cleanup():
    manager = PluginManager(config = {"plugin_sources": []})
    plugin = DummyPlugin()

    #Registering the plugin
    registered = await manager.register_plugin(plugin)
    assert registered

    #Initialising the plugin
    context = PluginContext(plugin_id = plugin.metadata.name, tenant_id = "tenant1", session_id = "sess1")
    initialized = await manager.initialize_plugin(plugin.metadata.name, context)
    assert initialized

    #Executing the assessment
    result = await manager.execute_plugin_assessment(plugin.metadata.name, data = {})
    assert result is not None
    assert result.overall_score == 100.0

    #Cleaning up the plugin
    cleaned = await manager.cleanup_plugin(plugin.metadata.name)
    assert cleaned
