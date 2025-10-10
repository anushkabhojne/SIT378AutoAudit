#AutoAudit Configuration Management System - Production Dockerfile
#Multi-stage build optimised for security, performance, and minimal attack surface
#Implements enterprise-grade container security practices and runtime optimization

#=============================================================================
#Build Stage - Compilation and Dependency Installation
#=============================================================================

FROM python:3.11.7-slim-bullseye AS builder

#Setting the build-time metadata for container identification and tracking
LABEL stage = builder
LABEL version = "1.0.0"
LABEL description = "AutoAudit Configuration Management System - Build Stage"

#Configuring the build environment variables for optimal Python compilation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.6.1

#Installing the system dependencies required for Python package compilation
#Minimising the attack surface by installing only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    git \
    libffi-dev \
    libpq-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

#Creating a non-root user for build process security
RUN useradd --create-home --shell /bin/bash --uid 1000 builder
USER builder
WORKDIR /home/builder

#Installing Poetry package manager for dependency management
RUN pip install --user poetry==$POETRY_VERSION

#Adding Poetry to PATH for build user
ENV PATH="/home/builder/.local/bin:$PATH"

#Copying the dependency specification files for efficient layer caching
COPY --chown=builder:builder requirements.txt pyproject.toml setup.py ./

#Installing Python dependencies with security optimisations
#Using pip for production to avoid Poetry overhead in final image
RUN python -m pip install --user --no-cache-dir --no-warn-script-location \
    --requirement requirements.txt

#Copying the application source code for final build preparation
COPY --chown=builder:builder config/ ./config/
COPY --chown=builder:builder migrations/ ./migrations/
COPY --chown=builder:builder README.md CHANGELOG.md LICENSE ./

#Compiling Python bytecode for runtime performance optimization
RUN python -m compileall -b config/ migrations/

#=============================================================================
#Runtime Stage - Minimal Production Container
#=============================================================================

FROM python:3.11.7-slim-bullseye AS runtime

#Setting the production metadata for container identification and security scanning
LABEL version = "1.0.0"
LABEL description = "AutoAudit Configuration Management System"
LABEL vendor = "AutoAudit"
LABEL org.opencontainers.image.title = "AutoAudit Configuration Service"
LABEL org.opencontainers.image.description = "Enterprise-grade centralised configuration management"
LABEL org.opencontainers.image.version = "1.0.0"

#Configuring the production runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    PATH="/app/.local/bin:$PATH" \
    USER_ID=1001 \
    GROUP_ID=1001 \
    APP_USER=autoaudit \
    APP_GROUP=autoaudit

#Installing only essential runtime dependencies for minimal attack surface
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dumb-init \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

#Creating the application group and user with specific UID/GID for security
RUN groupadd -g $GROUP_ID $APP_GROUP \
    && useradd -r -u $USER_ID -g $APP_GROUP -d /app -s /sbin/nologin \
       -c "AutoAudit Config Service" $APP_USER

#Creating the application directory structure with proper permissions
RUN mkdir -p /app /var/log/autoaudit /var/run/autoaudit \
    && chown -R $APP_USER:$APP_GROUP /app /var/log/autoaudit /var/run/autoaudit \
    && chmod 755 /app \
    && chmod 755 /var/log/autoaudit \
    && chmod 755 /var/run/autoaudit

#Switching to the application directory and non-root user
WORKDIR /app
USER $APP_USER

#Copying the Python dependencies from builder stage
COPY --from=builder --chown=$APP_USER:$APP_GROUP /home/builder/.local /app/.local

#Copying the application code and compiled bytecode from builder stage
COPY --from=builder --chown=$APP_USER:$APP_GROUP /home/builder/config ./config
COPY --from=builder --chown=$APP_USER:$APP_GROUP /home/builder/migrations ./migrations
COPY --from=builder --chown=$APP_USER:$APP_GROUP /home/builder/README.md ./

#Creating the application configuration and data directories
RUN mkdir -p config/data config/logs config/temp \
    && chmod 755 config/data config/logs config/temp

#Configuring the container health check for orchestration platforms
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

#Exposing the application port (documentation only - actual port binding in runtime)
EXPOSE 8000

#Configuring the container security and resource limits
#Running with dumb-init for proper signal handling and zombie reaping
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

#Default command with production-optimized Gunicorn configuration
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "30", \
     "--keep-alive", "2", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-config", "config/logging.conf", \
     "--preload", \
     "--enable-stdio-inheritance", \
     "config.main:app"]

#=============================================================================
#Development Stage - Extended tooling for development environments
#=============================================================================

FROM runtime AS development

#Switching to to root temporarily for development tool installation
USER root

#Installing the development and debugging tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    git \
    htop \
    nano \
    net-tools \
    procps \
    strace \
    tcpdump \
    telnet \
    vim \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

#Installing the development Python packages
RUN pip install --no-cache-dir \
    debugpy \
    ipdb \
    ipython \
    pytest \
    pytest-asyncio \
    pytest-cov

#Switching back to application user
USER $APP_USER

#Overriding the default command for development with auto-reload
CMD ["uvicorn", \
     "config.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--log-level", "debug"]

#=============================================================================
#Testing Stage - Optimized for CI/CD testing environments
#=============================================================================

FROM builder AS testing

#Installing testing dependencies and tools
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

USER builder

#Installing comprehensive testing dependencies
RUN pip install --user --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    pytest-xdist \
    pytest-html \
    pytest-benchmark \
    coverage \
    bandit \
    safety \
    black \
    isort \
    flake8 \
    mypy

#Copying the test files and configuration
COPY --chown=builder:builder tests/ ./tests/
COPY --chown=builder:builder pytest.ini ./
COPY --chown=builder:builder .coveragerc ./

#Default command runs comprehensive test suite
CMD ["python", "-m", "pytest", \
     "--verbose", \
     "--cov=config", \
     "--cov-report=html", \
     "--cov-report=xml", \
     "--junitxml=reports/junit.xml", \
     "tests/"]