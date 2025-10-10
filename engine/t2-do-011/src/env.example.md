# AutoAudit Container Security Scanning - Environment Configuration

# DEPLOYMENT ENVIRONMENT

# Valid values: development, staging, production, testing
ENVIRONMENT = development

# Service identification
SERVICE_NAME = autoaudit-container-scanner
HOSTNAME = autoaudit-scanner-01

# SCANNER CONFIGURATION

# Trivy scanner binary location
SCANNER_BINARY_PATH = /usr/local/bin/trivy

# Scanner execution timeout (seconds)
SCANNER_TIMEOUT = 300

# Scanning profile (fast, balanced, thorough, compliance)
SCANNING_PROFILE = balanced

# Severity threshold (CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN)
SEVERITY_THRESHOLD = HIGH

# Block deployment on vulnerabilities
BLOCK_ON_CRITICAL = true
BLOCK_ON_HIGH = true

# Parallel scanning configuration
PARALLEL_SCANNING = true
MAX_PARALLEL_SCANS = 5

# Caching configuration
CACHE_ENABLED = true
CACHE_TTL = 86400

# Vulnerability database configuration
VULNERABILITY_DB_PATH = /var/lib/trivy/db
VULNERABILITY_DB_UPDATE_INTERVAL = 3600

# Advanced scanning options
SCAN_LAYERS = true
SCAN_SECRETS = true
SCAN_MISCONFIGURATIONS = true
SCAN_LICENSES = false

# POLICY ENGINE CONFIGURATION (Open Policy Agent)

# OPA server connection
OPA_SERVER_URL = http://localhost:8181
OPA_SERVER_TIMEOUT = 30

# Policy enforcement mode (strict, permissive, audit-only)
ENFORCEMENT_MODE = strict

# Policy bundle path
OPA_POLICY_BUNDLE_PATH = /etc/opa/policies

# Exception management
ALLOW_POLICY_EXCEPTIONS = true
EXCEPTION_APPROVAL_REQUIRED = true
EXCEPTION_EXPIRATION_DAYS = 90

# Compliance framework enablement
ENABLE_CIS_BENCHMARK = true
ENABLE_NIST_CSF = true
ENABLE_ISO27001 = false
ENABLE_ESSENTIAL8 = true
ENABLE_MITRE_ATTACK = true

# GITHUB INTEGRATION

# GitHub authentication token (required for private repositories)
GITHUB_TOKEN = ghp_your_token_here

# GitHub API endpoint
GITHUB_API_URL = https://api.github.com

# Repository information (automatically set by GitHub Actions)
GITHUB_REPOSITORY = hardhat-enterprises/autoaudit
GITHUB_RUN_ID = 
GITHUB_SHA = 
GITHUB_EVENT_PATH = 

# Artifact configuration
ARTIFACT_RETENTION_DAYS = 90
UPLOAD_ARTIFACTS = true
ARTIFACT_COMPRESSION = true

# Check run integration
CREATE_CHECK_RUNS = true
CHECK_RUN_NAME = Container Security Scan

# Notifications
NOTIFY_ON_FAILURE = true
NOTIFY_ON_HIGH_SEVERITY = true

# Webhook URLs for notifications (optional)
NOTIFICATION_TEAMS_WEBHOOK = 
NOTIFICATION_SLACK_WEBHOOK = 

# SECURITY CONFIGURATION

# Encryption settings
ENABLE_ENCRYPTION_AT_REST = true
ENCRYPTION_ALGORITHM = AES-256-GCM
KEY_ROTATION_DAYS = 90

# Network security
ENABLE_TLS = true
TLS_VERSION = 1.3
ENABLE_NETWORK_ISOLATION = true

# Allowed container registries (comma-separated)
ALLOWED_REGISTRIES = docker.io,ghcr.io,gcr.io,public.ecr.aws

# Registry options
INSECURE_REGISTRIES = 
SKIP_TLS_VERIFY = false
REGISTRY_TIMEOUT = 60

# Access control
ENABLE_RBAC = true
REQUIRE_MFA = false
SESSION_TIMEOUT_MINUTES = 480

# Audit logging
ENABLE_AUDIT_LOGGING = true
AUDIT_LOG_RETENTION_DAYS = 365
LOG_SENSITIVE_DATA = false
AUDIT_LOG_DIRECTORY = logs/audit

# Security monitoring
ENABLE_INTRUSION_DETECTION = true
ALERT_ON_SUSPICIOUS_ACTIVITY = true

# MONITORING AND OBSERVABILITY

# Prometheus metrics
ENABLE_METRICS = true
METRICS_PORT = 9090
METRICS_PATH = /metrics

# Grafana integration (optional)
GRAFANA_URL = 
GRAFANA_API_KEY = 

# Alerting configuration
ENABLE_ALERTING = true
ALERT_MANAGER_URL = 
ALERT_SEVERITY_THRESHOLD = HIGH

# Performance monitoring
ENABLE_PERFORMANCE_TRACKING = true
TRACK_SCANNING_DURATION = true
TRACK_RESOURCE_UTILIZATION = true

# Health check configuration
HEALTH_CHECK_INTERVAL = 60
HEALTH_CHECK_TIMEOUT = 10

# LOGGING CONFIGURATION

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = INFO

# Logging destinations
LOG_TO_FILE = true
LOG_TO_CONSOLE = true

# Log formatting
STRUCTURED_LOGGING = true

# Log directory
LOG_DIRECTORY = logs

# Log file configuration
MAX_LOG_FILE_SIZE = 10485760
LOG_BACKUP_COUNT = 10

# STORAGE AND PERSISTENCE

# Trivy cache directory
TRIVY_CACHE_DIR = /tmp/trivy-cache

# Scan results storage
RESULTS_STORAGE_PATH = /var/lib/autoaudit/results
RESULTS_RETENTION_DAYS = 90

# Report output directory
REPORT_OUTPUT_DIR = /var/lib/autoaudit/reports

# DATABASE CONFIGURATION (for metadata storage)

# Database connection (if using database for results storage)
DATABASE_TYPE = postgresql
DATABASE_HOST = localhost
DATABASE_PORT = 5432
DATABASE_NAME = autoaudit_scanning
DATABASE_USER = autoaudit
DATABASE_PASSWORD = change_this_password
DATABASE_SSL_MODE = require

# Connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_TIMEOUT = 30

# REDIS CONFIGURATION (for caching and queuing)

# Redis connection
REDIS_HOST = localhost
REDIS_PORT = 6379
REDIS_PASSWORD = 
REDIS_DB = 0

# Redis connection pooling
REDIS_POOL_SIZE = 10
REDIS_TIMEOUT = 5

# CLOUD PROVIDER CONFIGURATION

# Cloud provider (aws, azure, gcp, or none)
CLOUD_PROVIDER = none

# AWS Configuration (if using AWS)
AWS_REGION = us-east-1
AWS_ACCESS_KEY_ID = 
AWS_SECRET_ACCESS_KEY = 
AWS_S3_BUCKET_NAME = 

# Azure Configuration (if using Azure)
AZURE_SUBSCRIPTION_ID = 
AZURE_RESOURCE_GROUP = 
AZURE_STORAGE_ACCOUNT = 
AZURE_STORAGE_CONTAINER = 

# GCP Configuration (if using GCP)
GCP_PROJECT_ID = 
GCP_SERVICE_ACCOUNT_KEY_PATH = 
GCP_STORAGE_BUCKET = 

# PERFORMANCE TUNING

# Worker configuration
WORKER_THREADS = 4
WORKER_QUEUE_SIZE = 100

# Memory limits (MB)
MAX_MEMORY_PER_SCAN = 2048
MEMORY_WARNING_THRESHOLD = 1536

# CPU limits
MAX_CPU_PER_SCAN = 2.0
CPU_WARNING_THRESHOLD = 1.5

# COMPLIANCE AND REPORTING

# Report generation
GENERATE_HTML_REPORTS = true
GENERATE_PDF_REPORTS = true
GENERATE_JSON_REPORTS = true
GENERATE_SARIF_REPORTS = true

# Report customisation
REPORT_INCLUDE_EXECUTIVE_SUMMARY = true
REPORT_INCLUDE_REMEDIATION_GUIDANCE = true
REPORT_INCLUDE_COMPLIANCE_MAPPING = true

# DEVELOPMENT AND DEBUGGING

# Debug mode (ONLY for development environments)
DEBUG_MODE = false
VERBOSE_LOGGING = false

# Testing configuration
ENABLE_TEST_MODE = false
MOCK_SCANNER_RESPONSES = false

# Profiling
ENABLE_PROFILING = false
PROFILING_OUTPUT_DIR = profiling

# FEATURE FLAGS

# Feature toggles for gradual rollout
ENABLE_AI_VULNERABILITY_ANALYSIS = false
ENABLE_AUTOMATED_REMEDIATION = false
ENABLE_SBOM_GENERATION = true
ENABLE_LICENSE_COMPLIANCE = false
ENABLE_SUPPLY_CHAIN_VALIDATION = true

# RATE LIMITING AND THROTTLING

# API rate limits
API_RATE_LIMIT_PER_MINUTE = 100
API_RATE_LIMIT_PER_HOUR = 1000

# Scanner rate limits
SCANNER_RATE_LIMIT_PER_MINUTE = 10
SCANNER_RATE_LIMIT_PER_HOUR = 100

# NOTIFICATION CONFIGURATION

# Email notifications (if enabled)
SMTP_HOST = 
SMTP_PORT = 587
SMTP_USERNAME = 
SMTP_PASSWORD = 
SMTP_FROM_ADDRESS = security@autoaudit.com
SMTP_USE_TLS = true

# Notification recipients (comma-separated emails)
NOTIFICATION_RECIPIENTS = security-team@hardhat-enterprises.com

# BACKUP AND DISASTER RECOVERY

# Backup configuration
ENABLE_AUTOMATED_BACKUPS = true
BACKUP_INTERVAL_HOURS = 24
BACKUP_RETENTION_DAYS = 30
BACKUP_STORAGE_PATH = /var/backups/autoaudit

# CUSTOM CONFIGURATION

# Add your custom environment variables below
# CUSTOM_VAR_1 = value1
# CUSTOM_VAR_2 = value2