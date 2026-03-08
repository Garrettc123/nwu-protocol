#!/bin/bash
# Validation script for halt process and automation features

set -e

echo "=========================================================="
echo "🧪 Halt Process & Automation Validation"
echo "=========================================================="
echo ""

# Configuration
BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1/halt-process"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Logging functions
log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
    TESTS_RUN=$((TESTS_RUN + 1))
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Check if backend is running
check_backend() {
    log_info "Checking if backend is running..."

    if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        log_success "Backend is running"
        return 0
    else
        log_failure "Backend is not running at $BASE_URL"
        echo ""
        echo "Please start the backend first:"
        echo "  ./auto-start.sh"
        echo ""
        exit 1
    fi
}

# Test API endpoint availability
test_api_endpoints() {
    log_info "Testing API endpoint availability..."
    echo ""

    # Check OpenAPI docs
    log_test "OpenAPI documentation accessible"
    if curl -s "$BASE_URL/docs" | grep -q "swagger"; then
        log_success "OpenAPI docs are accessible"
    else
        log_failure "OpenAPI docs are not accessible"
    fi

    # Check if halt-process endpoints are registered
    log_test "Halt process endpoints registered"
    if curl -s "$BASE_URL/openapi.json" | grep -q "halt-process"; then
        log_success "Halt process endpoints are registered"
    else
        log_failure "Halt process endpoints are not registered"
    fi
}

# Test database schema
test_database_schema() {
    log_info "Testing database schema..."
    echo ""

    log_test "Checking if migration script exists"
    if [ -f "scripts/migrate_halt_process.py" ]; then
        log_success "Migration script exists"
    else
        log_failure "Migration script not found"
    fi

    log_info "To run migration: python scripts/migrate_halt_process.py"
}

# Test service files
test_service_files() {
    log_info "Testing service implementation files..."
    echo ""

    local services=(
        "backend/app/services/halt_process_service.py"
        "backend/app/services/workflow_engine.py"
        "backend/app/services/engagement_service.py"
        "backend/app/api/halt_process.py"
    )

    for service in "${services[@]}"; do
        log_test "Checking $service"
        if [ -f "$service" ]; then
            log_success "$service exists"
        else
            log_failure "$service not found"
        fi
    done
}

# Test automation scripts
test_automation_scripts() {
    log_info "Testing automation deployment..."
    echo ""

    log_test "Checking automation directory"
    if [ -d "automation" ]; then
        log_success "Automation directory exists"
    else
        log_failure "Automation directory not found"
    fi

    log_test "Checking deployment script"
    if [ -f "automation/deploy-turnkey-automation.sh" ] && [ -x "automation/deploy-turnkey-automation.sh" ]; then
        log_success "Deployment script exists and is executable"
    else
        log_failure "Deployment script not found or not executable"
    fi

    log_test "Checking automation README"
    if [ -f "automation/README.md" ]; then
        log_success "Automation README exists"
    else
        log_failure "Automation README not found"
    fi
}

# Test documentation
test_documentation() {
    log_info "Testing documentation..."
    echo ""

    log_test "Checking implementation guide"
    if [ -f "HALT_PROCESS_IMPLEMENTATION.md" ]; then
        log_success "Implementation guide exists"
    else
        log_failure "Implementation guide not found"
    fi
}

# Test model changes
test_model_changes() {
    log_info "Testing model changes..."
    echo ""

    log_test "Checking Contribution model extensions"
    if grep -q "halt_status" backend/app/models.py && \
       grep -q "engagement_count" backend/app/models.py && \
       grep -q "automation_level" backend/app/models.py; then
        log_success "Contribution model has new fields"
    else
        log_failure "Contribution model missing expected fields"
    fi

    log_test "Checking ContributionStatus enum"
    if grep -q "HALTED" nwu_protocol/models/contribution.py && \
       grep -q "PAUSED" nwu_protocol/models/contribution.py && \
       grep -q "RESUMED" nwu_protocol/models/contribution.py; then
        log_success "ContributionStatus enum has new states"
    else
        log_failure "ContributionStatus enum missing expected states"
    fi

    log_test "Checking new model classes"
    if grep -q "class EngagementHistory" backend/app/models.py && \
       grep -q "class ProcessIteration" backend/app/models.py && \
       grep -q "class WorkflowExecution" backend/app/models.py && \
       grep -q "class KnowledgeThread" backend/app/models.py; then
        log_success "New model classes defined"
    else
        log_failure "New model classes not found"
    fi
}

# Test API integration
test_api_integration() {
    log_info "Testing API integration..."
    echo ""

    log_test "Checking main.py router registration"
    if grep -q "halt_process_router" backend/app/main.py; then
        log_success "Halt process router is registered"
    else
        log_failure "Halt process router not registered in main.py"
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================================="
    echo "📊 Validation Summary"
    echo "=========================================================="
    echo ""
    echo "Tests Run:    $TESTS_RUN"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All validation tests passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Run database migration: python scripts/migrate_halt_process.py"
        echo "  2. Restart backend: docker-compose restart backend"
        echo "  3. Deploy automation: ./automation/deploy-turnkey-automation.sh"
        echo "  4. Test API endpoints: curl $BASE_URL/docs"
        echo ""
        return 0
    else
        echo -e "${RED}❌ Some validation tests failed${NC}"
        echo ""
        echo "Please review the failures above and fix any issues."
        echo ""
        return 1
    fi
}

# Main execution
main() {
    echo "Starting validation..."
    echo ""

    check_backend
    echo ""

    test_api_endpoints
    echo ""

    test_database_schema
    echo ""

    test_service_files
    echo ""

    test_automation_scripts
    echo ""

    test_documentation
    echo ""

    test_model_changes
    echo ""

    test_api_integration
    echo ""

    print_summary
}

# Run main function
main

exit $?
