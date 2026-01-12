#!/bin/bash

################################################################################
# NWU Protocol - Backend Services Validation Script
# Ensures all invisible/backend components are working correctly
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0
WARNINGS=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[⚠ WARN]${NC} $1"
    ((WARNINGS++))
}

print_header() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║          NWU Protocol Backend Validation Suite                ║"
    echo "║         Testing All Invisible/Backend Components              ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
}

# Test 1: Docker containers running
test_containers() {
    log_info "Testing Docker containers..."
    
    local containers=(
        "nwu-postgres"
        "nwu-mongodb"
        "nwu-redis"
        "nwu-rabbitmq"
        "nwu-ipfs"
        "nwu-backend"
        "nwu-agent-alpha"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            if [ "$(docker inspect -f '{{.State.Running}}' ${container})" == "true" ]; then
                log_success "Container ${container} is running"
            else
                log_fail "Container ${container} exists but is not running"
            fi
        else
            log_fail "Container ${container} not found"
        fi
    done
}

# Test 2: PostgreSQL database
test_postgres() {
    log_info "Testing PostgreSQL database..."
    
    if docker exec nwu-postgres pg_isready -U nwu_user > /dev/null 2>&1; then
        log_success "PostgreSQL is accepting connections"
        
        # Test database exists
        if docker exec nwu-postgres psql -U nwu_user -lqt | cut -d \| -f 1 | grep -qw nwu_db; then
            log_success "Database 'nwu_db' exists"
        else
            log_fail "Database 'nwu_db' not found"
        fi
        
        # Test tables exist
        local table_count=$(docker exec nwu-postgres psql -U nwu_user -d nwu_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)
        if [ "$table_count" -gt 0 ]; then
            log_success "PostgreSQL has $table_count tables"
        else
            log_warning "PostgreSQL has no tables (migrations may not have run)"
        fi
    else
        log_fail "PostgreSQL is not accepting connections"
    fi
}

# Test 3: MongoDB
test_mongodb() {
    log_info "Testing MongoDB..."
    
    if docker exec nwu-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        log_success "MongoDB is accepting connections"
        
        # Test authentication
        if docker exec nwu-mongodb mongosh -u admin -p rocket69! --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            log_success "MongoDB authentication working"
        else
            log_warning "MongoDB authentication may have issues"
        fi
    else
        log_fail "MongoDB is not accepting connections"
    fi
}

# Test 4: Redis
test_redis() {
    log_info "Testing Redis..."
    
    if docker exec nwu-redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is responding to ping"
        
        # Test write/read
        if docker exec nwu-redis redis-cli SET test_key "test_value" > /dev/null 2>&1; then
            local value=$(docker exec nwu-redis redis-cli GET test_key 2>/dev/null)
            if [ "$value" == "test_value" ]; then
                log_success "Redis read/write operations working"
                docker exec nwu-redis redis-cli DEL test_key > /dev/null 2>&1
            else
                log_fail "Redis read operation failed"
            fi
        else
            log_fail "Redis write operation failed"
        fi
    else
        log_fail "Redis is not responding"
    fi
}

# Test 5: RabbitMQ
test_rabbitmq() {
    log_info "Testing RabbitMQ..."
    
    if docker exec nwu-rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
        log_success "RabbitMQ is running"
        
        # Test management API
        if curl -s -f -u guest:guest http://localhost:15672/api/overview > /dev/null 2>&1; then
            log_success "RabbitMQ Management API is accessible"
            
            # Check queues
            local queue_count=$(curl -s -u guest:guest http://localhost:15672/api/queues | jq '. | length' 2>/dev/null || echo "0")
            if [ "$queue_count" -gt 0 ]; then
                log_success "RabbitMQ has $queue_count queue(s)"
            else
                log_warning "RabbitMQ has no queues yet"
            fi
        else
            log_warning "RabbitMQ Management API not accessible"
        fi
    else
        log_fail "RabbitMQ is not running"
    fi
}

# Test 6: IPFS
test_ipfs() {
    log_info "Testing IPFS..."
    
    if curl -s -f http://localhost:5001/api/v0/id > /dev/null 2>&1; then
        log_success "IPFS API is accessible"
        
        # Test adding and retrieving data
        local test_hash=$(echo "test_content" | curl -s -F "file=@-" http://localhost:5001/api/v0/add | jq -r '.Hash' 2>/dev/null)
        if [ -n "$test_hash" ] && [ "$test_hash" != "null" ]; then
            log_success "IPFS add operation successful (hash: $test_hash)"
            
            # Try to retrieve
            if curl -s -f "http://localhost:5001/api/v0/cat?arg=$test_hash" > /dev/null 2>&1; then
                log_success "IPFS cat operation successful"
            else
                log_warning "IPFS cat operation failed"
            fi
        else
            log_warning "IPFS add operation returned no hash"
        fi
    else
        log_fail "IPFS API is not accessible"
    fi
}

# Test 7: Backend API
test_backend_api() {
    log_info "Testing Backend API..."
    
    # Test health endpoint
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend health endpoint is accessible"
        
        # Parse health response
        local health_response=$(curl -s http://localhost:8000/health)
        local status=$(echo "$health_response" | jq -r '.status' 2>/dev/null)
        
        if [ "$status" == "healthy" ]; then
            log_success "Backend reports healthy status"
        else
            log_warning "Backend reports degraded status"
        fi
        
        # Check individual service health
        local db_health=$(echo "$health_response" | jq -r '.checks.database' 2>/dev/null)
        local ipfs_health=$(echo "$health_response" | jq -r '.checks.ipfs' 2>/dev/null)
        local rabbitmq_health=$(echo "$health_response" | jq -r '.checks.rabbitmq' 2>/dev/null)
        local redis_health=$(echo "$health_response" | jq -r '.checks.redis' 2>/dev/null)
        
        [ "$db_health" == "true" ] && log_success "Backend: Database connection OK" || log_fail "Backend: Database connection FAILED"
        [ "$ipfs_health" == "true" ] && log_success "Backend: IPFS connection OK" || log_fail "Backend: IPFS connection FAILED"
        [ "$rabbitmq_health" == "true" ] && log_success "Backend: RabbitMQ connection OK" || log_fail "Backend: RabbitMQ connection FAILED"
        [ "$redis_health" == "true" ] && log_success "Backend: Redis connection OK" || log_fail "Backend: Redis connection FAILED"
    else
        log_fail "Backend health endpoint is not accessible"
        return
    fi
    
    # Test API documentation
    if curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
        log_success "API documentation (Swagger) is accessible"
    else
        log_warning "API documentation not accessible"
    fi
    
    # Test root endpoint
    if curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
        log_success "Backend root endpoint is accessible"
    else
        log_fail "Backend root endpoint failed"
    fi
    
    # Test API endpoints
    if curl -s -f http://localhost:8000/api/v1/contributions/ > /dev/null 2>&1; then
        log_success "Contributions API endpoint is accessible"
    else
        log_warning "Contributions API endpoint not accessible"
    fi
}

# Test 8: Agent-Alpha
test_agent() {
    log_info "Testing Agent-Alpha..."
    
    if docker ps --format '{{.Names}}' | grep -q "^nwu-agent-alpha$"; then
        log_success "Agent-Alpha container is running"
        
        # Check logs for successful startup
        local logs=$(docker logs nwu-agent-alpha 2>&1 | tail -20)
        
        if echo "$logs" | grep -q "Starting Agent-Alpha"; then
            log_success "Agent-Alpha started successfully"
        else
            log_warning "Agent-Alpha startup message not found in logs"
        fi
        
        if echo "$logs" | grep -q "Connected to RabbitMQ"; then
            log_success "Agent-Alpha connected to RabbitMQ"
        else
            log_warning "Agent-Alpha RabbitMQ connection not confirmed"
        fi
        
        if echo "$logs" | grep -q "Connected to IPFS"; then
            log_success "Agent-Alpha connected to IPFS"
        elif echo "$logs" | grep -q "Failed to connect to IPFS"; then
            log_warning "Agent-Alpha failed to connect to IPFS"
        fi
    else
        log_fail "Agent-Alpha container is not running"
    fi
}

# Test 9: Database migrations
test_migrations() {
    log_info "Testing database migrations..."
    
    if docker exec nwu-backend alembic current 2>&1 | grep -q "head"; then
        log_success "Database migrations are at HEAD"
    elif docker exec nwu-backend alembic current 2>&1 | grep -q "[0-9a-f]"; then
        log_warning "Database migrations exist but may not be at HEAD"
    else
        log_warning "Cannot determine migration status"
    fi
}

# Test 10: Environment configuration
test_environment() {
    log_info "Testing environment configuration..."
    
    if [ -f .env ]; then
        log_success ".env file exists"
        
        # Check for critical variables
        if grep -q "OPENAI_API_KEY" .env; then
            if grep -q "OPENAI_API_KEY=sk-" .env; then
                log_warning "OPENAI_API_KEY appears to be placeholder (AI verification will use mock mode)"
            else
                log_success "OPENAI_API_KEY is configured"
            fi
        else
            log_warning "OPENAI_API_KEY not found in .env"
        fi
    else
        log_fail ".env file not found"
    fi
    
    if [ -f .env.example ]; then
        log_success ".env.example exists"
    else
        log_warning ".env.example not found"
    fi
}

# Test 11: Network connectivity
test_network() {
    log_info "Testing Docker network connectivity..."
    
    # Test backend can reach postgres
    if docker exec nwu-backend nc -z postgres 5432 2>/dev/null; then
        log_success "Backend can reach PostgreSQL"
    else
        log_fail "Backend cannot reach PostgreSQL"
    fi
    
    # Test backend can reach redis
    if docker exec nwu-backend nc -z redis 6379 2>/dev/null; then
        log_success "Backend can reach Redis"
    else
        log_fail "Backend cannot reach Redis"
    fi
    
    # Test backend can reach rabbitmq
    if docker exec nwu-backend nc -z rabbitmq 5672 2>/dev/null; then
        log_success "Backend can reach RabbitMQ"
    else
        log_fail "Backend cannot reach RabbitMQ"
    fi
    
    # Test agent can reach backend
    if docker exec nwu-agent-alpha nc -z backend 8000 2>/dev/null; then
        log_success "Agent can reach Backend"
    else
        log_fail "Agent cannot reach Backend"
    fi
}

# Summary
print_summary() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                     VALIDATION SUMMARY                        ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "  ${GREEN}Tests Passed:${NC}    $PASSED"
    echo -e "  ${RED}Tests Failed:${NC}    $FAILED"
    echo -e "  ${YELLOW}Warnings:${NC}        $WARNINGS"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ ALL BACKEND SERVICES ARE WORKING CORRECTLY!${NC}"
        echo ""
        echo "Your NWU Protocol backend is fully operational and ready for use."
        exit 0
    else
        echo -e "${RED}✗ SOME BACKEND SERVICES HAVE ISSUES${NC}"
        echo ""
        echo "Please review the failed tests above and check:"
        echo "  1. All containers are running: docker-compose ps"
        echo "  2. View logs: docker-compose logs [service-name]"
        echo "  3. Restart services: docker-compose restart"
        exit 1
    fi
}

# Main execution
main() {
    print_header
    
    log_info "Starting comprehensive backend validation..."
    echo ""
    
    test_containers
    echo ""
    
    test_postgres
    echo ""
    
    test_mongodb
    echo ""
    
    test_redis
    echo ""
    
    test_rabbitmq
    echo ""
    
    test_ipfs
    echo ""
    
    test_backend_api
    echo ""
    
    test_agent
    echo ""
    
    test_migrations
    echo ""
    
    test_environment
    echo ""
    
    test_network
    echo ""
    
    print_summary
}

# Run main
main "$@"
