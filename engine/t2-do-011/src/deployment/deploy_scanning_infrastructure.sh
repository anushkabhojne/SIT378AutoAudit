#!/bin/bash

#AutoAudit Container Security Scanning Infrastructure Deployment Script
#This comprehensive deployment script handles the complete infrastructure
#provisioning, configuration deployment, validation, and health checking
#for the AutoAudit container security scanning system.
#Author: Senior Lead, AutoAudit

#Exiting on error, undefined variable, or pipe failure
set -euo pipefail  

#Script configuration
readonly SCRIPT_NAME = "$(basename "$0")"
readonly SCRIPT_DIR = "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT = "$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly TIMESTAMP = "$(date +%Y%m%d_%H%M%S)"

#Color codes for output
readonly RED = '\033[0;31m'
readonly GREEN = '\033[0;32m'
readonly YELLOW = '\033[1;33m'
readonly BLUE = '\033[0;34m'
readonly NC = '\033[0m' #No Color

#Logging configuration
readonly LOG_DIR = "${PROJECT_ROOT}/logs/deployment"
readonly LOG_FILE = "${LOG_DIR}/deployment_${TIMESTAMP}.log"

#Default configuration
ENVIRONMENT = "${ENVIRONMENT:-development}"
DRY_RUN = "${DRY_RUN:-false}"
SKIP_VALIDATION = "${SKIP_VALIDATION:-false}"
SKIP_HEALTH_CHECK = "${SKIP_HEALTH_CHECK:-false}"
TERRAFORM_AUTO_APPROVE = "${TERRAFORM_AUTO_APPROVE:-false}"

#Logging Functions

#Initialising the logging directory
init_logging() {
    mkdir -p "${LOG_DIR}"
    
    log_info "==================================================================="
    log_info "AutoAudit Container Security Scanning Infrastructure Deployment"
    log_info "==================================================================="
    log_info "Timestamp: ${TIMESTAMP}"
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Log File: ${LOG_FILE}"
    log_info "==================================================================="
}

#Log message with timestamp
log_message() {
    local level = "$1"
    shift
    local message = "$*"
    local timestamp = "$(date '+%Y-%m-%d %H:%M:%S')"
    
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

#Log informational message
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${LOG_FILE}"
}

#Log success message
log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "${LOG_FILE}"
}

#Log warning message
log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "${LOG_FILE}"
}

#Log error message
log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${LOG_FILE}" >&2
}

#Log fatal error and exit
log_fatal() {
    log_error "$*"
    log_error "Deployment failed. Check logs at: ${LOG_FILE}"
    exit 1
}

#Utility Functions

#Checking if the command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

#Validating the required dependencies
validate_dependencies() {
    log_info "Validating required dependencies..."
    
    local missing_deps = ()
    
    #Required commands
    local required_commands = (
        "terraform"
        "docker"
        "python3"
        "git"
        "curl"
        "jq"
    )
    
    for cmd in "${required_commands[@]}"; do
        
        if ! command_exists "${cmd}"; then
            missing_deps+=("${cmd}")
        
        fi
    
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_fatal "Missing required dependencies: ${missing_deps[*]}"
    
    fi
    
    #Verifying the Terraform version
    local tf_version = $(terraform version -json | jq -r '.terraform_version')
    log_info "Terraform version: ${tf_version}"
    
    #Verifying the Docker version
    local docker_version = $(docker version --format '{{.Server.Version}}')
    log_info "Docker version: ${docker_version}"
    
    #Verifying the Python version
    local python_version = $(python3 --version | cut -d' ' -f2)
    log_info "Python version: ${python_version}"
    
    log_success "All required dependencies validated successfully"
}

#Parsing the command line arguments
parse_arguments() {
    
    while [[ $#-gt 0 ]]; do
        
        case $1 in
            
            -e|--environment)
                ENVIRONMENT = "$2"
                shift 2
                ;;
            
            --dry-run)
                DRY_RUN = "true"
                shift
                ;;
            
            --skip-validation)
                SKIP_VALIDATION = "true"
                shift
                ;;
            
            --skip-health-check)
                SKIP_HEALTH_CHECK = "true"
                shift
                ;;
            
            --auto-approve)
                TERRAFORM_AUTO_APPROVE = "true"
                shift
                ;;
            
            -h|--help)
                print_usage
                exit 0
                ;;
            
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        
        esac
    
    done
    
    #Validating the environment value
    if [[ ! "${ENVIRONMENT}" =~ ^(development|staging|production|testing)$ ]]; then
        log_fatal "Invalid environment: ${ENVIRONMENT}. Must be one of: development, staging, production, testing"
    
    fi
}

#Printing the usage information
print_usage() {
    cat << EOF

Usage: ${SCRIPT_NAME} [OPTIONS]

Deploy AutoAudit container security scanning infrastructure.

OPTIONS:
    -e, --environment ENV     Deployment environment (development|staging|production|testing)
                              Default: development
    
    --dry-run                 Perform dry-run without making changes
    --skip-validation         Skip pre-deployment validation
    --skip-health-check       Skip post-deployment health checks
    --auto-approve            Auto-approve Terraform changes without prompting
    -h, --help                Display this help message

EXAMPLES:
    #Deploy to development environment
    ${SCRIPT_NAME} --environment development
    
    #Deploy to production with auto-approve
    ${SCRIPT_NAME} --environment production --auto-approve
    
    #Dry-run deployment to staging
    ${SCRIPT_NAME} --environment staging --dry-run

EOF
}

#Pre-Deployment Validation

validate_environment_config() {
    log_info "Validating environment configuration for: ${ENVIRONMENT}"
    
    local config_file = "${PROJECT_ROOT}/config/${ENVIRONMENT}.yaml"
    
    if [ ! -f "${config_file}" ]; then
        log_fatal "Configuration file not found: ${config_file}"
    fi
    
    log_info "Configuration file found: ${config_file}"
    
    #Validate YAML syntax
    if command_exists python3; then
        python3 -c "import yaml; yaml.safe_load(open('${config_file}'))" 2>/dev/null
        
        if [ $? -ne 0 ]; then
            log_fatal "Invalid YAML syntax in configuration file: ${config_file}"
        
        fi
        log_success "Configuration file syntax validated"
    fi
}

validate_terraform_configuration() {
    log_info "Validating Terraform configuration..."
    
    local terraform_dir = "${PROJECT_ROOT}/infrastructure/terraform"
    
    cd "${terraform_dir}" || log_fatal "Failed to change to Terraform directory"
    
    #Initialising Terraform
    log_info "Initialising Terraform..."
    terraform init -upgrade 2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Terraform initialisation failed"
    
    fi
    
    #Validating the Terraform configuration
    log_info "Validating Terraform syntax..."
    terraform validate 2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Terraform validation failed"
    
    fi
    
    log_success "Terraform configuration validated successfully"
    
    cd "${PROJECT_ROOT}" || exit 1
}

validate_docker_registry_access() {
    log_info "Validating Docker registry access..."
    
    #Checking if the Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_fatal "Docker daemon is not running or not accessible"
    
    fi
    
    #Testing the registry access, if the credentials are available
    if [ -n "${DOCKER_REGISTRY_USERNAME:-}" ] && [ -n "${DOCKER_REGISTRY_PASSWORD:-}" ]; then
        log_info "Testing Docker registry authentication..."
        
        echo "${DOCKER_REGISTRY_PASSWORD}" | docker login "${DOCKER_REGISTRY:-docker.io}" \
            -u "${DOCKER_REGISTRY_USERNAME}" --password-stdin 2>&1 | tee -a "${LOG_FILE}"
        
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            log_warning "Docker registry authentication failed"
        
        else
            log_success "Docker registry authentication successful"
        
        fi
    fi
}

validate_scanner_installation() {
    log_info "Validating Trivy scanner installation..."
    
    local scanner_path = "${SCANNER_BINARY_PATH:-/usr/local/bin/trivy}"
    
    if [ ! -x "${scanner_path}" ]; then
        log_warning "Trivy scanner not found at ${scanner_path}, attempting installation..."
        install_trivy_scanner
    
    else
        local trivy_version = $(${scanner_path} --version 2>&1 | head -n1)
        log_success "Trivy scanner found: ${trivy_version}"
    
    fi
}

install_trivy_scanner() {
    log_info "Installing the Trivy scanner..."
    
    local install_script = "/tmp/trivy-install.sh"
    
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
        -o "${install_script}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Failed to download Trivy installation script"
    
    fi
    
    chmod +x "${install_script}"
    sh "${install_script}" -b /usr/local/bin 2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Trivy installation failed"
    
    fi
    
    rm -f "${install_script}"
    log_success "Trivy scanner installed successfully"
}

#Infrastructure Deployment

deploy_infrastructure() {
    log_info "Deploying infrastructure for ${ENVIRONMENT} environment..."
    
    local terraform_dir = "${PROJECT_ROOT}/infrastructure/terraform"
    local tfvars_file = "${terraform_dir}/environments/${ENVIRONMENT}.tfvars"
    
    if [ ! -f "${tfvars_file}" ]; then
        log_fatal "Terraform variables file not found: ${tfvars_file}"
    
    fi
    
    cd "${terraform_dir}" || log_fatal "Failed to change to Terraform directory"
    
    #Generating the Terraform plan
    log_info "Generating Terraform execution plan..."
    
    terraform plan \
        -var-file = "${tfvars_file}" \
        -out = "${ENVIRONMENT}.tfplan" \
        2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Terraform plan generation failed"
    
    fi
    
    log_success "Terraform plan generated successfully"
    
    #Applying Terraform plan (if not dry-run)
    if [ "${DRY_RUN}" = "true" ]; then
        log_info "Dry-run mode: Skipping Terraform apply"
    
    else
        log_info "Applying Terraform plan..."
        
        local tf_apply_args = ("-input = false" "${ENVIRONMENT}.tfplan")
        
        if [ "${TERRAFORM_AUTO_APPROVE}" = "true" ]; then
            terraform apply "${tf_apply_args[@]}" 2>&1 | tee -a "${LOG_FILE}"
        
        else
            log_warning "Review the plan above and confirm to proceed with deployment"
            terraform apply "${tf_apply_args[@]}" 2>&1 | tee -a "${LOG_FILE}"
        
        fi
        
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            log_fatal "Terraform apply failed"
        
        fi
        
        log_success "Infrastructure deployed successfully"
    fi
    
    #Saving the Terraform outputs
    log_info "Saving Terraform outputs..."
    terraform output -json > "${PROJECT_ROOT}/terraform-outputs-${ENVIRONMENT}.json"
    
    cd "${PROJECT_ROOT}" || exit 1
}

#Application Deployment

deploy_application() {
    log_info "Deploying application components..."
    
    #Building the scanner container image
    build_scanner_image
    
    #Deploying the scanner services
    deploy_scanner_services
    
    #Configuring the scanning policies
    configure_policies
    
    log_success "Application components deployed successfully"
}

build_scanner_image() {
    log_info "Building scanner container image..."
    
    local image_tag = "autoaudit-scanner:${ENVIRONMENT}-${TIMESTAMP}"
    
    if [ "${DRY_RUN}" = "true" ]; then
        log_info "Dry-run mode: Skipping image build"
        return

    fi
    
    docker build \
        -t "${image_tag}" \
        -f "${PROJECT_ROOT}/Dockerfile" \
        --build-arg ENVIRONMENT = "${ENVIRONMENT}" \
        --build-arg BUILD_DATE = "${TIMESTAMP}" \
        "${PROJECT_ROOT}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Docker image build failed"

    fi
    
    #Tagging as latest for environment
    docker tag "${image_tag}" "autoaudit-scanner:${ENVIRONMENT}-latest"
    
    log_success "Scanner image built successfully: ${image_tag}"
}

deploy_scanner_services() {
    log_info "Deploying scanner services..."
    
    if [ "${DRY_RUN}" = "true" ]; then
        log_info "Dry-run mode: Skipping service deployment"
        return

    fi
    
    #Deploying using docker-compose for development and testing
    if [[ "${ENVIRONMENT}" =~ ^(development|testing)$ ]]; then
        deploy_with_docker_compose

    else
        #Deploying to Kubernetes for staging and production
        deploy_to_kubernetes
    fi
}

deploy_with_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    local compose_file = "${PROJECT_ROOT}/docker-compose.${ENVIRONMENT}.yml"
    
    if [ ! -f "${compose_file}" ]; then
        log_warning "Environment-specific compose file not found, using default"
        compose_file = "${PROJECT_ROOT}/docker-compose.yml"
    
    fi
    
    docker-compose -f "${compose_file}" up -d 2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Docker Compose deployment failed"
    
    fi
    
    log_success "Services deployed with Docker Compose"
}

deploy_to_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    local k8s_manifests = "${PROJECT_ROOT}/infrastructure/kubernetes/${ENVIRONMENT}"
    
    if [ ! -d "${k8s_manifests}" ]; then
        log_fatal "Kubernetes manifests not found: ${k8s_manifests}"
    
    fi
    
    kubectl apply -f "${k8s_manifests}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_fatal "Kubernetes deployment failed"
    
    fi
    
    log_success "Services deployed to Kubernetes"
}

configure_policies() {
    log_info "Configuring security policies..."
    
    if [ "${DRY_RUN}" = "true" ]; then
        log_info "Dry-run mode: Skipping policy configuration"
        return
    
    fi
    
    local policy_dir = "${PROJECT_ROOT}/policies"
    
    #Validating the policy syntax
    log_info "Validating policy syntax..."
    
    find "${policy_dir}" -name "*.rego" -type f | while read -r policy_file; do
        log_info "Validating: ${policy_file}"
        opa fmt -d "${policy_file}" >/dev/null 2>&1
        
        if [ $? -ne 0 ]; then
            log_error "Policy validation failed: ${policy_file}"
        
        fi

    done
    
    log_success "Policy configuration completed"
}

#Post-Deployment Validation

run_health_checks() {
    log_info "Running post-deployment health checks..."
    
    if [ "${SKIP_HEALTH_CHECK}" = "true" ]; then
        log_warning "Skipping health checks as requested"
        return
    fi
    
    #Waiting for the services to be ready
    log_info "Waiting for services to become ready..."
    sleep 10
    
    #Checking the scanner service health
    check_scanner_health
    
    #Checking the policy service health
    check_policy_service_health
    
    #Checking the database's connectivity
    check_database_connectivity
    
    #Running smoke tests
    run_smoke_tests
    
    log_success "All health checks passed"
}

check_scanner_health() {
    log_info "Checking scanner service health..."
    
    local max_attempts = 30
    local attempt = 0
    local health_endpoint = "${SCANNER_HEALTH_ENDPOINT:-http://localhost:8080/health}"
    
    while [ ${attempt} -lt ${max_attempts} ]; do
        if curl -sf "${health_endpoint}" >/dev/null 2>&1; then
            log_success "Scanner service is healthy"
            return 0
        
        fi
        
        attempt = $((attempt + 1))
        log_info "Waiting for scanner service... (${attempt}/${max_attempts})"
        sleep 2
    
    done
    
    log_fatal "Scanner service health check failed after ${max_attempts} attempts"
}

check_policy_service_health() {
    log_info "Checking policy service health..."
    
    local opa_endpoint = "${OPA_SERVER_URL:-http://localhost:8181}/health"
    
    if curl -sf "${opa_endpoint}" >/dev/null 2>&1; then
        log_success "Policy service is healthy"
    
    else
        log_warning "Policy service health check failed"
    
    fi
}

check_database_connectivity() {
    log_info "Checking database connectivity..."
    
    if [ -z "${DATABASE_HOST:-}" ]; then
        log_info "No database configured, skipping connectivity check"
        return
    
    fi
    
    #Testing the database connection
    if command_exists psql; then
        PGPASSWORD = "${DATABASE_PASSWORD}" psql \
            -h "${DATABASE_HOST}" \
            -p "${DATABASE_PORT:-5432}" \
            -U "${DATABASE_USER}" \
            -d "${DATABASE_NAME}" \
            -c "SELECT 1" >/dev/null 2>&1
        
        
        if [ $? -eq 0 ]; then
            log_success "Database connectivity verified"
        
        else
            log_warning "Database connectivity check failed"
        
        fi
    
    fi
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    local test_script = "${PROJECT_ROOT}/scripts/smoke-tests.sh"
    
    if [ -x "${test_script}" ]; then
        "${test_script}" 2>&1 | tee -a "${LOG_FILE}"
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log_success "Smoke tests passed"
        
        else
            log_warning "Some smoke tests failed"
        
        fi

    else
        log_info "Smoke test script not found, skipping"
    
    fi
}

#Deployment Summary

print_deployment_summary() {
    log_info "==================================================================="
    log_info "Deployment Summary"
    log_info "==================================================================="
    log_info "Environment:         ${ENVIRONMENT}"
    log_info "Deployment Time:     ${TIMESTAMP}"
    log_info "Dry Run:             ${DRY_RUN}"
    log_info "Log File:            ${LOG_FILE}"
    log_info "==================================================================="
    
    if [ "${DRY_RUN}" = "false" ]; then
        log_success "Deployment completed successfully!"
        log_info "Next steps:"
        log_info "  1. Review deployment logs: ${LOG_FILE}"
        log_info "  2. Verify services: ./scripts/verify-deployment.sh"
        log_info "  3. Run integration tests: ./scripts/run-tests.sh"
    
    else
        log_info "Dry-run completed. Review the plan and run without --dry-run to deploy."
    
    fi
    
    log_info "==================================================================="
}

#Main Execution

main() {
    #Initialising the logging
    init_logging
    
    #Parsing the command line arguments
    parse_arguments "$@"
    
    #Validating the dependencies
    validate_dependencies
    
    #Pre-deployment validation
    if [ "${SKIP_VALIDATION}" = "false" ]; then
        validate_environment_config
        validate_terraform_configuration
        validate_docker_registry_access
        validate_scanner_installation
    
    else
        log_warning "Skipping pre-deployment validation as requested"
    
    fi
    
    #Deploying infrastructure
    deploy_infrastructure
    
    #Deploying application
    deploy_application
    
    #Post-deployment validation
    run_health_checks
    
    #Printing the deployment summary
    print_deployment_summary
    
    exit 0
}

#Executing the main function with all arguments
main "$@"