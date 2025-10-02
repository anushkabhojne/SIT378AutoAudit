# AutoAudit Extensible Framework Plugin Architecture

## Overview

This repository contains the core interfaces and example implementations for the AutoAudit Extensible Framework Plugin Architecture. This architecture enables the AutoAudit platform to dynamically load, execute, and manage compliance framework plugins, supporting multiple compliance standards in a scalable, secure, and maintainable manner.

## Plugin Development Guide

### Core Concepts

- **Plugin Interface:** Plugins must implement the `IComplianceFrameworkPlugin` interface, providing lifecycle methods such as `initialize`, `validate_configuration`, `execute_assessment`, and `cleanup`.
- **Assessment Execution:** Plugins implement `IAssessmentExecutor` to support asynchronous, streaming assessment execution with progress reporting.
- **Metadata:** Each plugin must provide Metadata describing its capabilities, dependencies, supported frameworks, and resource/security requirements.

### Development Steps

1. **Implement Interfaces:** Create a new class implementing `IComplianceFrameworkPlugin` and `IAssessmentExecutor`.
2. **Define Metadata:** Provide detailed plugin metadata for discovery and management.
3. **Initialize Plugin:** Implement asynchronous initialization logic.
4. **Validate Configuration:** Ensure plugin configuration parameters are validated before execution.
5. **Execute Assessment:** Implement assessment logic supporting streaming progress updates.
6. **Cleanup:** Release resources on plugin shutdown.

### Example

See `example_plugin.py` for a minimal working example.

### Testing

- Write unit tests for your plugin logic.
- Validate configuration and error handling.
- Test integration with the AutoAudit core system.

### Packaging and Deployment

- Package your plugin as a Docker container following the containerization guidelines.
- Ensure your container image passes security scans (e.g., Trivy).
- Register your plugin with the Plugin Registry Service.

## Architectural Decisions

Refer to the `docs/adr` directory for Architectural Decision Records explaining key design choices.

## Support

For questions or contributions, contact the Compliance Framework Engine Team.

**Author:** Senior Lead, AutoAudit
