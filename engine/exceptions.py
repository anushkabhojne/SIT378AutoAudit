"""
Plugin Framework Exceptions Module

Defines specialised exceptions for plugin execution and data access errors.

Author: Senior Lead, AutoAudit
"""

class PluginExecutionError(Exception):
    def __init__(self, message, plugin_id = None, error_code = None, original_exception = None):
        super().__init__(message)
        self.plugin_id = plugin_id
        self.error_code = error_code or "PLUGIN_EXECUTION_ERROR"
        self.original_exception = original_exception