"""
Configuration Schema

Defines the JSON schema for configuration validation.

Author: Senior Lead, AutoAudit
"""

CONFIG_SCHEMA = {
    "type": "object",
    
    "properties": {
        "logging": {
            "type": "object",
    
            "properties": {
                "level": {"type": "string"},
                "file": {"type": "string"}
            },
    
            "required": ["level"]
        },
    
        "security": {
            "type": "object",
    
            "properties": {
                "encryption_key": {"type": "string"},
                "credential_store_path": {"type": "string"}
            },
    
            "required": ["encryption_key"]
        },
    
        "orchestration": {
            "type": "object",
    
            "properties": {
                "kubeconfig_path": {"type": "string"}
            }
        }
    },
    
    "required": ["logging", "security"]
}
