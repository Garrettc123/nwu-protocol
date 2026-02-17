#!/bin/bash

################################################################################
# NWU Protocol - Deployment Verification Script
# Verifies that all deployment components are working correctly
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0
WARNINGS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARNINGS++))
}

# Print banner
print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║        NWU Protocol Deployment Verification Script            ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
}

# Check Docker installation
check_docker() {
    log_info "Checking Docker installation..."

    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        log_success "Docker installed: $DOCKER_VERSION"
    else
        log_error "Docker not installed"
        return 1
    fi

    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version 2>&1 | head -1 | awk '{print $4}')
        log_success "Docker Compose installed: $COMPOSE_VERSION"
    else
        log_error "Docker Compose not installed"
        return 1
    fi
}

# Verify Docker Compose files
check_compose_files() {
    log_info "Verifying Docker Compose files..."

    # Check docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        if docker compose -f docker-compose.yml config --quiet 2>/dev/null; then
            log_success "docker-compose.yml is valid"
        else
            log_error "docker-compose.yml has syntax errors"
        fi
    else
        log_error "docker-compose.yml not found"
    fi

    # Check docker-compose.prod.yml
    if [ -f "docker-compose.prod.yml" ]; then
        if docker compose -f docker-compose.prod.yml config --quiet 2>/dev/null; then
            log_success "docker-compose.prod.yml is valid"
        else
            log_warning "docker-compose.prod.yml has syntax errors (may need .env file)"
        fi
    else
        log_error "docker-compose.prod.yml not found"
    fi
}

# Check Dockerfiles
check_dockerfiles() {
    log_info "Checking Dockerfiles..."

    if [ -f "Dockerfile.backend" ]; then
        log_success "Dockerfile.backend exists"
    else
        log_error "Dockerfile.backend not found"
    fi

    if [ -f "Dockerfile.agent" ]; then
        log_success "Dockerfile.agent exists"
    else
        log_error "Dockerfile.agent not found"
    fi
}

# Check deployment scripts
check_scripts() {
    log_info "Checking deployment scripts..."

    if [ -f "deploy.sh" ] && [ -x "deploy.sh" ]; then
        log_success "deploy.sh exists and is executable"
    elif [ -f "deploy.sh" ]; then
        log_warning "deploy.sh exists but is not executable (run: chmod +x deploy.sh)"
    else
        log_error "deploy.sh not found"
    fi

    if [ -f "Makefile" ]; then
        log_success "Makefile exists"

        # Check for key Makefile targets
        if grep -q "^deploy:" Makefile; then
            log_success "Makefile has 'deploy' target"
        else
            log_warning "Makefile missing 'deploy' target"
        fi
    else
        log_error "Makefile not found"
    fi
}

# Check environment files
check_env_files() {
    log_info "Checking environment files..."

    if [ -f ".env.example" ]; then
        log_success ".env.example exists"
    else
        log_error ".env.example not found"
    fi

    if [ -f ".env.production.example" ]; then
        log_success ".env.production.example exists"
    else
        log_warning ".env.production.example not found"
    fi

    if [ -f ".env" ]; then
        log_success ".env file exists"

        # Check for critical variables
        if grep -q "OPENAI_API_KEY" .env; then
            if grep -q "OPENAI_API_KEY=sk-" .env; then
                log_success "OPENAI_API_KEY is configured"
            else
                log_warning "OPENAI_API_KEY may need to be set"
            fi
        else
            log_warning "OPENAI_API_KEY not found in .env"
        fi
    else
        log_warning ".env file not found (will use defaults)"
    fi
}

# Check application structure
check_app_structure() {
    log_info "Checking application structure..."

    # Backend
    if [ -d "backend" ]; then
        log_success "backend directory exists"

        if [ -f "backend/app/main.py" ]; then
            log_success "backend/app/main.py exists"
        else
            log_error "backend/app/main.py not found"
        fi

        if [ -f "backend/requirements.txt" ]; then
            log_success "backend/requirements.txt exists"
        else
            log_error "backend/requirements.txt not found"
        fi
    else
        log_error "backend directory not found"
    fi

    # Agent
    if [ -d "agent-alpha" ]; then
        log_success "agent-alpha directory exists"

        if [ -f "agent-alpha/app/main.py" ]; then
            log_success "agent-alpha/app/main.py exists"
        else
            log_error "agent-alpha/app/main.py not found"
        fi

        if [ -f "agent-alpha/requirements.txt" ]; then
            log_success "agent-alpha/requirements.txt exists"
        else
            log_error "agent-alpha/requirements.txt not found"
        fi
    else
        log_error "agent-alpha directory not found"
    fi

    # Frontend
    if [ -d "frontend" ]; then
        log_success "frontend directory exists"

        if [ -f "frontend/package.json" ]; then
            log_success "frontend/package.json exists"
        else
            log_warning "frontend/package.json not found"
        fi
    else
        log_warning "frontend directory not found"
    fi
}

# Check GitHub Actions workflows
check_github_actions() {
    log_info "Checking GitHub Actions workflows..."

    if [ -d ".github/workflows" ]; then
        log_success ".github/workflows directory exists"

        if [ -f ".github/workflows/deploy.yml" ]; then
            log_success "deploy.yml workflow exists"
        else
            log_warning "deploy.yml workflow not found"
        fi

        if [ -f ".github/workflows/ci-cd.yml" ]; then
            log_success "ci-cd.yml workflow exists"
        else
            log_warning "ci-cd.yml workflow not found"
        fi
    else
        log_warning ".github/workflows directory not found"
    fi
}

# Check documentation
check_documentation() {
    log_info "Checking deployment documentation..."

    local docs=(
        "README.md"
        "DEPLOYMENT.md"
        "DEPLOY_NOW.md"
        "PRODUCTION_DEPLOYMENT.md"
    )

    for doc in "${docs[@]}"; do
        if [ -f "$doc" ]; then
            log_success "$doc exists"
        else
            log_warning "$doc not found"
        fi
    done
}

# Test running services (if deployed)
check_running_services() {
    log_info "Checking running services..."

    # Check if Docker Compose is running
    if docker compose ps 2>/dev/null | grep -q "Up"; then
        log_success "Docker Compose services are running"

        # Check backend health
        if curl -f -s http://localhost:8000/health &> /dev/null; then
            log_success "Backend health check passed"
        else
            log_warning "Backend not responding (may not be deployed)"
        fi

        # Check RabbitMQ
        if curl -f -s http://localhost:15672 &> /dev/null; then
            log_success "RabbitMQ Management UI accessible"
        else
            log_warning "RabbitMQ not accessible"
        fi
    else
        log_info "No services currently running (deployment not started)"
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "                    Verification Summary                       "
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ Deployment verification completed successfully!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Review any warnings above"
        echo "  2. Configure .env file if not already done"
        echo "  3. Run: ./deploy.sh or make deploy"
        echo ""
        return 0
    else
        echo -e "${RED}✗ Deployment verification failed with $FAILED error(s)${NC}"
        echo ""
        echo "Please fix the errors above before deploying."
        echo ""
        return 1
    fi
}

# Main verification flow
main() {
    print_banner

    log_info "Starting deployment verification..."
    echo ""

    check_docker
    echo ""

    check_compose_files
    echo ""

    check_dockerfiles
    echo ""

    check_scripts
    echo ""

    check_env_files
    echo ""

    check_app_structure
    echo ""

    check_github_actions
    echo ""

    check_documentation
    echo ""

    check_running_services
    echo ""

    print_summary
}

# Run main function
main "$@"
