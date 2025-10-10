# AutoAudit Centralised Configuration Management System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0+-00a393.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-6.2+-dc382d.svg)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Executive Summary

The AutoAudit Centralised Configuration Management System represents a comprehensive enterprise-grade solution designed to provide unified, secure, and scalable configuration management across the entire AutoAudit microservices ecosystem. This system addresses critical requirements for hierarchical configuration resolution, real-time updates, comprehensive security controls, and operational excellence through advanced monitoring and alerting capabilities.

Built on modern cloud-native technologies including FastAPI, PostgreSQL, Redis, and Kubernetes, the system provides sub-millisecond configuration retrieval performance while maintaining ACID compliance for configuration changes and supporting horizontal scaling to accommodate enterprise-scale deployments with thousands of services and millions of configuration requests per day.

## Architecture Overview

### System Components

The configuration management system implements a sophisticated microservices architecture with the following core components:

- **Configuration Service API**: RESTful FastAPI service providing configuration CRUD operations
- **Database Layer**: PostgreSQL with advanced indexing and replication for configuration persistence
- **Cache Layer**: Redis Cluster providing distributed caching and pub/sub messaging
- **Security Manager**: Comprehensive authentication, authorization, and encryption services
- **Validation Engine**: Schema-based validation with business rule enforcement
- **Notification Manager**: Real-time configuration change notifications
- **Monitoring System**: Prometheus metrics collection with Grafana visualization

### Key Features

- **Hierarchical Configuration Resolution**: Multi-level configuration inheritance (global → namespace → environment → service)
- **Real-time Updates**: Instant configuration propagation through Redis pub/sub channels
- **Enterprise Security**: JWT authentication, role-based access control, and AES-256 encryption
- **High Availability**: Automatic failover, connection pooling, and circuit breaker patterns
- **Comprehensive Monitoring**: Detailed metrics, distributed tracing, and health checking
- **Audit Compliance**: Complete audit trails with change attribution and rollback capabilities

## Technology Stack

### Core Technologies
- **Application Framework**: FastAPI 0.104.0+ with Pydantic validation
- **Database**: PostgreSQL 13+ with asyncpg driver and connection pooling
- **Cache**: Redis 6.2+ with cluster support and persistence
- **Container Runtime**: Docker with multi-stage builds and security scanning
- **Orchestration**: Kubernetes with horizontal pod autoscaling
- **Monitoring**: Prometheus, Grafana, and OpenTelemetry distributed tracing

### Security Components
- **Authentication**: JWT tokens with RS256 signing and Azure AD integration
- **Authorization**: Role-based access control with fine-grained permissions
- **Encryption**: AES-256-GCM for sensitive parameters with HashiCorp Vault key management
- **Transport Security**: TLS 1.3 with certificate automation via Let's Encrypt

### Development Tools
- **Testing**: pytest with comprehensive fixtures and integration testing
- **Code Quality**: Black formatting, flake8 linting, mypy type checking
- **CI/CD**: GitHub Actions with automated testing, security scanning, and deployment
- **Documentation**: Automated OpenAPI documentation with Swagger UI

## Installation and Deployment

### Prerequisites

Before installing the AutoAudit Configuration Management System, ensure the following prerequisites are met:

- Python 3.11+ with pip package manager
- PostgreSQL 13+ database server with appropriate permissions
- Redis 6.2+ server or cluster with persistence enabled
- Docker and Docker Compose for containerized deployment
- Kubernetes cluster for production deployment (optional)
- HashiCorp Vault for encryption key management (optional)

### Local Development Setup

#### 1. Repository Clone and Environment Setup

```bash
# Clone the repository with comprehensive project structure
git clone https://github.com/autoaudit/config-management-system.git
cd config-management-system

# Create isolated Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install comprehensive development dependencies
pip install -r requirements-dev.txt
pip install -e .
```

#### 2. Database Configuration and Migration

```bash
# Create PostgreSQL database and user with appropriate permissions
createdb autoaudit_config
createuser config_service -P  # Enter password when prompted

# Grant comprehensive database permissions
psql -d autoaudit_config -c "GRANT ALL PRIVILEGES ON DATABASE autoaudit_config TO config_service;"

# Execute database schema initialization and migrations
python -m config.database.migrate --init-schema
python -m config.database.migrate --apply-migrations
```

#### 3. Redis Configuration and Optimization

```bash
# Configure Redis for optimal performance
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
echo "save 900 1" >> /etc/redis/redis.conf
echo "appendonly yes" >> /etc/redis/redis.conf

# Restart Redis service with new configuration
systemctl restart redis-server
```

#### 4. Environment Configuration

Create a comprehensive `.env` file with production-ready configuration:

```bash
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=autoaudit_config
DATABASE_USERNAME=config_service
DATABASE_PASSWORD=your_secure_password
DATABASE_POOL_MIN_SIZE=10
DATABASE_POOL_MAX_SIZE=50
DATABASE_POOL_MAX_QUERIES=50000
DATABASE_POOL_MAX_INACTIVE_CONNECTION_LIFETIME=300.0

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_CLUSTER_MODE=false
REDIS_MAX_CONNECTIONS=100
REDIS_HEALTH_CHECK_INTERVAL=30
REDIS_SOCKET_TIMEOUT=5.0
REDIS_SOCKET_CONNECT_TIMEOUT=5.0

# Security Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
AZURE_AD_TENANT_ID=your_azure_tenant_id
AZURE_AD_CLIENT_ID=your_azure_client_id

# HashiCorp Vault Configuration
VAULT_URL=https://vault.example.com:8200
VAULT_TOKEN=your_vault_token
VAULT_MOUNT_POINT=secret

# Application Configuration
CONFIG_CACHE_TTL=300
ENABLE_DETAILED_METRICS=true
ENABLE_STRICT_VALIDATION=true
ALLOWED_HOSTS=localhost,*.autoaudit.com
ALLOWED_ORIGINS=http://localhost:3000,https://admin.autoaudit.com

# Monitoring Configuration
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
PROMETHEUS_REGISTRY_PORT=8001
METRICS_COLLECTION_INTERVAL=15

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=/var/log/config-service/application.log
```

#### 5. Development Server Launch

```bash
# Launch development server with comprehensive configuration
python -m uvicorn config.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

# Alternative: Use the application's built-in development server
python config/main.py
```

### Production Deployment

#### Docker Deployment

```bash
# Build production-optimized Docker image with multi-stage build
docker build -t autoaudit/config-service:1.0.0 .

# Deploy using Docker Compose with comprehensive service stack
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment health and performance
docker-compose logs -f config-service
curl http://localhost:8000/health
```

#### Kubernetes Deployment

```bash
# Apply Kubernetes manifests with comprehensive resource definitions
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Monitor deployment progress and pod health
kubectl get
```