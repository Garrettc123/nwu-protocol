#!/bin/bash

################################################################################
# NWU Protocol - API Endpoint Testing Script
# Tests all backend API endpoints to ensure they're working
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED++))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

BASE_URL="http://localhost:8000"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║            NWU Protocol - API Endpoint Testing                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Test root endpoint
log_info "Testing root endpoint..."
if response=$(curl -s -f "$BASE_URL/"); then
    if echo "$response" | jq -e '.status == "operational"' > /dev/null 2>&1; then
        log_success "Root endpoint: API is operational"
    else
        log_fail "Root endpoint: Unexpected response"
    fi
else
    log_fail "Root endpoint: Not accessible"
fi

# Test health endpoint
log_info "Testing health endpoint..."
if response=$(curl -s -f "$BASE_URL/health"); then
    status=$(echo "$response" | jq -r '.status' 2>/dev/null)
    if [ "$status" == "healthy" ]; then
        log_success "Health endpoint: System is healthy"
    else
        log_fail "Health endpoint: System reports degraded ($status)"
    fi
else
    log_fail "Health endpoint: Not accessible"
fi

# Test API info endpoint
log_info "Testing API info endpoint..."
if response=$(curl -s -f "$BASE_URL/api/v1/info"); then
    if echo "$response" | jq -e '.version' > /dev/null 2>&1; then
        log_success "API info endpoint: Working"
    else
        log_fail "API info endpoint: Invalid response"
    fi
else
    log_fail "API info endpoint: Not accessible"
fi

# Test contributions list endpoint
log_info "Testing contributions list endpoint..."
if response=$(curl -s -f "$BASE_URL/api/v1/contributions/"); then
    log_success "Contributions list endpoint: Working"
else
    log_fail "Contributions list endpoint: Failed"
fi

# Test auth connect endpoint (POST)
log_info "Testing auth connect endpoint..."
test_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
if response=$(curl -s -X POST "$BASE_URL/api/v1/auth/connect" \
    -H "Content-Type: application/json" \
    -d "{\"address\": \"$test_address\"}"); then
    if echo "$response" | jq -e '.nonce' > /dev/null 2>&1; then
        log_success "Auth connect endpoint: Working (nonce generated)"
    else
        log_fail "Auth connect endpoint: No nonce returned"
    fi
else
    log_fail "Auth connect endpoint: Failed"
fi

# Test OpenAPI documentation
log_info "Testing OpenAPI documentation..."
if curl -s -f "$BASE_URL/docs" > /dev/null 2>&1; then
    log_success "OpenAPI docs (Swagger UI): Accessible"
else
    log_fail "OpenAPI docs: Not accessible"
fi

if curl -s -f "$BASE_URL/redoc" > /dev/null 2>&1; then
    log_success "ReDoc documentation: Accessible"
else
    log_fail "ReDoc documentation: Not accessible"
fi

# Test OpenAPI JSON
log_info "Testing OpenAPI JSON schema..."
if response=$(curl -s -f "$BASE_URL/openapi.json"); then
    if echo "$response" | jq -e '.openapi' > /dev/null 2>&1; then
        log_success "OpenAPI JSON schema: Valid"
    else
        log_fail "OpenAPI JSON schema: Invalid"
    fi
else
    log_fail "OpenAPI JSON schema: Not accessible"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                      TEST SUMMARY                             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}Passed:${NC} $PASSED"
echo -e "  ${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL API ENDPOINTS ARE WORKING!${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME API ENDPOINTS FAILED${NC}"
    echo ""
    echo "Tips:"
    echo "  - Check if backend is running: docker-compose ps backend"
    echo "  - View backend logs: docker-compose logs backend"
    echo "  - Restart backend: docker-compose restart backend"
    exit 1
fi
