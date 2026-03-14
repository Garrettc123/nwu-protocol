#!/bin/bash

################################################################################
# NWU Protocol - Service Registry
# Central source of truth for all services and their configurations
# This file is sourced by other scripts to maintain DRY principle
################################################################################

# Service definitions
declare -A SERVICES
SERVICES[postgres]="PostgreSQL Database"
SERVICES[mongodb]="MongoDB Database"
SERVICES[redis]="Redis Cache"
SERVICES[rabbitmq]="RabbitMQ Message Queue"
SERVICES[ipfs]="IPFS Storage"
SERVICES[backend]="Backend API (FastAPI)"
SERVICES[agent-alpha]="Agent-Alpha AI Verification"

# Service health check URLs
declare -A HEALTH_URLS
HEALTH_URLS[postgres]="psql"  # Special: requires psql command
HEALTH_URLS[mongodb]="mongosh"  # Special: requires mongosh command
HEALTH_URLS[redis]="redis-cli"  # Special: requires redis-cli command
HEALTH_URLS[rabbitmq]="http://localhost:15672"
HEALTH_URLS[ipfs]="http://localhost:8080/api/v0/version"
HEALTH_URLS[backend]="http://localhost:8000/health"
HEALTH_URLS[agent-alpha]="container"  # Special: check container status

# Service ports
declare -A SERVICE_PORTS
SERVICE_PORTS[postgres]="5432"
SERVICE_PORTS[mongodb]="27017"
SERVICE_PORTS[redis]="6379"
SERVICE_PORTS[rabbitmq]="5672"
SERVICE_PORTS[ipfs]="8080"
SERVICE_PORTS[backend]="8000"
SERVICE_PORTS[agent-alpha]="N/A"

# Service Docker container names
declare -A CONTAINER_NAMES
CONTAINER_NAMES[postgres]="nwu-postgres"
CONTAINER_NAMES[mongodb]="nwu-mongodb"
CONTAINER_NAMES[redis]="nwu-redis"
CONTAINER_NAMES[rabbitmq]="nwu-rabbitmq"
CONTAINER_NAMES[ipfs]="nwu-ipfs"
CONTAINER_NAMES[backend]="nwu-backend"
CONTAINER_NAMES[agent-alpha]="nwu-agent-alpha"

# Service startup order (for dependencies)
SERVICE_ORDER=(
    "postgres"
    "mongodb"
    "redis"
    "rabbitmq"
    "ipfs"
    "backend"
    "agent-alpha"
)

# Health check timeouts (in seconds)
declare -A HEALTH_TIMEOUTS
HEALTH_TIMEOUTS[postgres]=30
HEALTH_TIMEOUTS[mongodb]=30
HEALTH_TIMEOUTS[redis]=10
HEALTH_TIMEOUTS[rabbitmq]=30
HEALTH_TIMEOUTS[ipfs]=20
HEALTH_TIMEOUTS[backend]=30
HEALTH_TIMEOUTS[agent-alpha]=10

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_fail() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

# Check if a service container is running
is_service_running() {
    local service=$1
    local container="${CONTAINER_NAMES[$service]}"
    
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        return 0
    else
        return 1
    fi
}

# Check if a service is healthy
check_service_health() {
    local service=$1
    local url="${HEALTH_URLS[$service]}"
    local timeout="${HEALTH_TIMEOUTS[$service]:-10}"
    
    case "$url" in
        psql)
            docker exec "${CONTAINER_NAMES[$service]}" pg_isready -U nwu_user -d nwu_db > /dev/null 2>&1
            return $?
            ;;
        mongosh)
            docker exec "${CONTAINER_NAMES[$service]}" mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1
            return $?
            ;;
        redis-cli)
            docker exec "${CONTAINER_NAMES[$service]}" redis-cli ping > /dev/null 2>&1
            return $?
            ;;
        container)
            is_service_running "$service"
            return $?
            ;;
        *)
            curl -s --max-time "$timeout" "$url" > /dev/null 2>&1
            return $?
            ;;
    esac
}

# Wait for a service to become healthy
wait_for_service() {
    local service=$1
    local max_wait="${2:-60}"
    local elapsed=0
    
    log_info "Waiting for ${SERVICES[$service]} to become healthy..."
    
    while [ $elapsed -lt $max_wait ]; do
        if check_service_health "$service"; then
            log_success "${SERVICES[$service]} is healthy"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    log_fail "${SERVICES[$service]} failed to become healthy after ${max_wait}s"
    return 1
}

# Get all service names
get_all_services() {
    echo "${!SERVICES[@]}"
}

# Get service description
get_service_description() {
    local service=$1
    echo "${SERVICES[$service]}"
}

# Export functions for use in other scripts
export -f log_info log_success log_fail log_warning
export -f is_service_running check_service_health wait_for_service
export -f get_all_services get_service_description
