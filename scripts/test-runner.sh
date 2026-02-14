#!/bin/bash

################################################################################
# NWU Protocol - Unified Test Runner
# Smart test orchestration with caching and parallel execution
################################################################################

set -e

# Source service registry
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/service-registry.sh"

# Test results
PASSED=0
FAILED=0
SKIPPED=0
START_TIME=$(date +%s)

# Cache directory for test results
CACHE_DIR="/tmp/nwu-test-cache"
mkdir -p "$CACHE_DIR"

# Parse command line arguments
SKIP_CACHE=false
PARALLEL=true
VERBOSE=false
CATEGORIES=()

print_usage() {
    echo "Usage: $0 [OPTIONS] [CATEGORIES...]"
    echo ""
    echo "Smart test runner with caching and parallel execution"
    echo ""
    echo "Options:"
    echo "  --no-cache       Skip cache and run all tests"
    echo "  --sequential     Run tests sequentially (default: parallel)"
    echo "  --verbose        Show detailed output"
    echo "  --help           Show this help message"
    echo ""
    echo "Categories (if none specified, runs all):"
    echo "  infrastructure   Test Docker services (PostgreSQL, MongoDB, Redis, etc.)"
    echo "  api              Test backend API endpoints"
    echo "  health           Test service health checks"
    echo "  integration      Test service integrations"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run all tests with caching"
    echo "  $0 --no-cache               # Force run all tests"
    echo "  $0 api health               # Run only API and health tests"
    echo "  $0 --verbose infrastructure # Run infrastructure tests with details"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            SKIP_CACHE=true
            shift
            ;;
        --sequential)
            PARALLEL=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        infrastructure|api|health|integration)
            CATEGORIES+=("$1")
            shift
            ;;
        *)
            log_warning "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# If no categories specified, run all
if [ ${#CATEGORIES[@]} -eq 0 ]; then
    CATEGORIES=("infrastructure" "health" "api" "integration")
fi

print_header() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║          NWU Protocol - Unified Test Runner                   ║"
    echo "║              Smart Testing with Caching                       ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
}

# Check if test should be skipped based on cache
should_skip_test() {
    local test_name=$1
    local cache_file="$CACHE_DIR/${test_name}.cache"
    
    if [ "$SKIP_CACHE" = true ]; then
        return 1  # Don't skip
    fi
    
    if [ ! -f "$cache_file" ]; then
        return 1  # Don't skip (no cache)
    fi
    
    # Check if cache is less than 5 minutes old
    local cache_time=$(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null)
    local current_time=$(date +%s)
    local age=$((current_time - cache_time))
    
    if [ $age -lt 300 ]; then
        local result=$(cat "$cache_file")
        if [ "$result" = "PASS" ]; then
            return 0  # Skip test
        fi
    fi
    
    return 1  # Don't skip
}

# Cache test result
cache_test_result() {
    local test_name=$1
    local result=$2
    echo "$result" > "$CACHE_DIR/${test_name}.cache"
}

# Test infrastructure services
test_infrastructure() {
    log_info "Testing Infrastructure Services..."
    
    local tests=(
        "docker:Docker is installed and running"
        "docker-compose:Docker Compose is available"
    )
    
    # Check Docker
    if should_skip_test "docker"; then
        log_success "Docker check (cached)"
        ((SKIPPED++))
    else
        if docker info > /dev/null 2>&1; then
            log_success "Docker is installed and running"
            cache_test_result "docker" "PASS"
            ((PASSED++))
        else
            log_fail "Docker is not running"
            cache_test_result "docker" "FAIL"
            ((FAILED++))
        fi
    fi
    
    # Check Docker Compose
    if should_skip_test "docker-compose"; then
        log_success "Docker Compose check (cached)"
        ((SKIPPED++))
    else
        if docker-compose --version > /dev/null 2>&1; then
            log_success "Docker Compose is available"
            cache_test_result "docker-compose" "PASS"
            ((PASSED++))
        else
            log_fail "Docker Compose is not installed"
            cache_test_result "docker-compose" "FAIL"
            ((FAILED++))
        fi
    fi
    
    # Test each service in parallel if enabled
    if [ "$PARALLEL" = true ]; then
        log_info "Running service checks in parallel..."
        local pids=()
        
        for service in "${SERVICE_ORDER[@]}"; do
            (
                test_name="service-${service}"
                if should_skip_test "$test_name"; then
                    log_success "${SERVICES[$service]} (cached)"
                else
                    if is_service_running "$service"; then
                        log_success "${SERVICES[$service]} is running"
                        cache_test_result "$test_name" "PASS"
                    else
                        log_fail "${SERVICES[$service]} is not running"
                        cache_test_result "$test_name" "FAIL"
                        exit 1
                    fi
                fi
            ) &
            pids+=($!)
        done
        
        # Wait for all parallel checks
        for pid in "${pids[@]}"; do
            if wait "$pid"; then
                ((PASSED++))
            else
                ((FAILED++))
            fi
        done
    else
        # Sequential service checks
        for service in "${SERVICE_ORDER[@]}"; do
            test_name="service-${service}"
            if should_skip_test "$test_name"; then
                log_success "${SERVICES[$service]} (cached)"
                ((SKIPPED++))
            else
                if is_service_running "$service"; then
                    log_success "${SERVICES[$service]} is running"
                    cache_test_result "$test_name" "PASS"
                    ((PASSED++))
                else
                    log_fail "${SERVICES[$service]} is not running"
                    cache_test_result "$test_name" "FAIL"
                    ((FAILED++))
                fi
            fi
        done
    fi
}

# Test service health
test_health() {
    log_info "Testing Service Health..."
    
    for service in "${SERVICE_ORDER[@]}"; do
        test_name="health-${service}"
        
        if should_skip_test "$test_name"; then
            log_success "${SERVICES[$service]} health (cached)"
            ((SKIPPED++))
        else
            if check_service_health "$service"; then
                log_success "${SERVICES[$service]} is healthy"
                cache_test_result "$test_name" "PASS"
                ((PASSED++))
            else
                log_fail "${SERVICES[$service]} health check failed"
                cache_test_result "$test_name" "FAIL"
                ((FAILED++))
            fi
        fi
    done
}

# Test API endpoints
test_api() {
    log_info "Testing API Endpoints..."
    
    BASE_URL="http://localhost:8000"
    
    # Test root endpoint
    test_name="api-root"
    if should_skip_test "$test_name"; then
        log_success "API root endpoint (cached)"
        ((SKIPPED++))
    else
        if response=$(curl -s -f "$BASE_URL/" 2>/dev/null); then
            if echo "$response" | jq -e '.status == "operational"' > /dev/null 2>&1; then
                log_success "API root endpoint is operational"
                cache_test_result "$test_name" "PASS"
                ((PASSED++))
            else
                log_fail "API root endpoint returned unexpected response"
                cache_test_result "$test_name" "FAIL"
                ((FAILED++))
            fi
        else
            log_fail "API root endpoint is not responding"
            cache_test_result "$test_name" "FAIL"
            ((FAILED++))
        fi
    fi
    
    # Test health endpoint
    test_name="api-health"
    if should_skip_test "$test_name"; then
        log_success "API health endpoint (cached)"
        ((SKIPPED++))
    else
        if response=$(curl -s -f "$BASE_URL/health" 2>/dev/null); then
            if echo "$response" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
                log_success "API health endpoint is healthy"
                cache_test_result "$test_name" "PASS"
                ((PASSED++))
            else
                log_fail "API health endpoint is not healthy"
                cache_test_result "$test_name" "FAIL"
                ((FAILED++))
            fi
        else
            log_fail "API health endpoint is not responding"
            cache_test_result "$test_name" "FAIL"
            ((FAILED++))
        fi
    fi
    
    # Test docs endpoint
    test_name="api-docs"
    if should_skip_test "$test_name"; then
        log_success "API documentation (cached)"
        ((SKIPPED++))
    else
        if curl -s -f "$BASE_URL/docs" > /dev/null 2>&1; then
            log_success "API documentation is accessible"
            cache_test_result "$test_name" "PASS"
            ((PASSED++))
        else
            log_fail "API documentation is not accessible"
            cache_test_result "$test_name" "FAIL"
            ((FAILED++))
        fi
    fi
}

# Test service integrations
test_integration() {
    log_info "Testing Service Integrations..."
    
    # Test database connectivity from backend
    test_name="integration-backend-postgres"
    if should_skip_test "$test_name"; then
        log_success "Backend → PostgreSQL (cached)"
        ((SKIPPED++))
    else
        if docker exec nwu-backend python -c "from app.database import engine; engine.connect()" 2>/dev/null; then
            log_success "Backend → PostgreSQL connection works"
            cache_test_result "$test_name" "PASS"
            ((PASSED++))
        else
            log_fail "Backend → PostgreSQL connection failed"
            cache_test_result "$test_name" "FAIL"
            ((FAILED++))
        fi
    fi
    
    # Test RabbitMQ connectivity
    test_name="integration-rabbitmq"
    if should_skip_test "$test_name"; then
        log_success "RabbitMQ queues (cached)"
        ((SKIPPED++))
    else
        if docker exec nwu-rabbitmq rabbitmqctl list_queues > /dev/null 2>&1; then
            log_success "RabbitMQ queues are accessible"
            cache_test_result "$test_name" "PASS"
            ((PASSED++))
        else
            log_fail "RabbitMQ queues are not accessible"
            cache_test_result "$test_name" "FAIL"
            ((FAILED++))
        fi
    fi
}

# Print summary
print_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                       Test Summary                            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}Passed:${NC}  $PASSED"
    echo -e "${RED}Failed:${NC}  $FAILED"
    echo -e "${CYAN}Skipped:${NC} $SKIPPED (cached)"
    echo -e "${BLUE}Time:${NC}    ${duration}s"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo ""
        echo "Tips:"
        echo "  - Run with --no-cache to force re-run all tests"
        echo "  - Run with --verbose for detailed output"
        echo "  - Check service logs: docker-compose logs [service-name]"
        return 1
    fi
}

# Main execution
main() {
    print_header
    
    log_info "Test configuration:"
    log_info "  Cache: $([ "$SKIP_CACHE" = true ] && echo "disabled" || echo "enabled")"
    log_info "  Parallel: $([ "$PARALLEL" = true ] && echo "yes" || echo "no")"
    log_info "  Categories: ${CATEGORIES[*]}"
    echo ""
    
    for category in "${CATEGORIES[@]}"; do
        case "$category" in
            infrastructure)
                test_infrastructure
                ;;
            health)
                test_health
                ;;
            api)
                test_api
                ;;
            integration)
                test_integration
                ;;
        esac
        echo ""
    done
    
    print_summary
}

# Run main function
main
exit $?
