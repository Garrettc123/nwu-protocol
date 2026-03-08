#!/bin/bash

# NWU Protocol - Comprehensive Troubleshooting Script
# Automatically diagnose and fix common issues
# Usage: ./troubleshoot.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════╗
║          NWU Protocol Troubleshooting Tool             ║
║      Automatic diagnosis and repair system             ║
╚════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

ISSUES_FOUND=0
FIXES_APPLIED=0

# Function to log issues
log_issue() {
    echo -e "${RED}❌ ISSUE: $1${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
}

log_fix() {
    echo -e "${GREEN}✅ FIXED: $1${NC}"
    FIXES_APPLIED=$((FIXES_APPLIED + 1))
}

log_check() {
    echo -e "${GREEN}✅ OK: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

# Check 1: Environment Files
echo -e "${YELLOW}[1/10] Checking environment files...${NC}"
if [ ! -f .env ]; then
    log_issue ".env file missing"
    echo "Running auto-configure..."
    ./auto-configure.sh
    log_fix "Created .env file"
else
    log_check ".env file exists"
fi

if [ ! -f frontend/.env.local ]; then
    log_warning "frontend/.env.local missing"
    if [ -f auto-configure.sh ]; then
        ./auto-configure.sh
        log_fix "Created frontend/.env.local"
    fi
else
    log_check "frontend/.env.local exists"
fi

# Check 2: Docker Status
echo -e "\n${YELLOW}[2/10] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    log_issue "Docker daemon not running"
    echo "Please start Docker and run this script again"
    exit 1
else
    log_check "Docker is running"
fi

if ! docker-compose version > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    log_issue "Docker Compose not available"
    echo "Please install Docker Compose"
    exit 1
else
    log_check "Docker Compose is available"
fi

# Check 3: Port Conflicts
echo -e "\n${YELLOW}[3/10] Checking for port conflicts...${NC}"
PORTS=(3000 5432 6379 8000 5672 15672 27017 5001 8080)
PORT_NAMES=("Frontend" "PostgreSQL" "Redis" "Backend" "RabbitMQ" "RabbitMQ-Admin" "MongoDB" "IPFS-API" "IPFS-Gateway")
CONFLICTS=0

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}

    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        # Check if it's one of our containers
        if docker ps --format "{{.Ports}}" | grep -q "$PORT"; then
            log_check "Port $PORT ($NAME) - used by NWU container"
        else
            log_warning "Port $PORT ($NAME) in use by another process"
            CONFLICTS=$((CONFLICTS + 1))
        fi
    else
        log_check "Port $PORT ($NAME) available"
    fi
done

if [ $CONFLICTS -gt 0 ]; then
    log_warning "$CONFLICTS port(s) in use by non-NWU processes"
    echo "To fix: Stop the conflicting processes or run: docker-compose down"
fi

# Check 4: Disk Space
echo -e "\n${YELLOW}[4/10] Checking disk space...${NC}"
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "${AVAILABLE%.*}" -lt 5 ]; then
    log_issue "Low disk space: ${AVAILABLE}GB available"
    echo "Free up disk space or run: docker system prune -a"
else
    log_check "Sufficient disk space: ${AVAILABLE}GB"
fi

# Check 5: Container Status
echo -e "\n${YELLOW}[5/10] Checking container status...${NC}"
if docker-compose ps -q 2>/dev/null | grep -q .; then
    UNHEALTHY=$(docker-compose ps | grep -c "unhealthy\|Exit" || true)
    RUNNING=$(docker-compose ps | grep -c "Up" || true)

    if [ "$UNHEALTHY" -gt 0 ]; then
        log_issue "$UNHEALTHY unhealthy container(s)"
        echo "Running auto-recovery..."
        ./auto-recovery.sh
        log_fix "Attempted to recover services"
    elif [ "$RUNNING" -gt 0 ]; then
        log_check "$RUNNING container(s) running"
    else
        log_warning "No containers running"
        echo "Start with: ./auto-start.sh"
    fi
else
    log_warning "No containers found"
    echo "Start with: ./auto-start.sh"
fi

# Check 6: Database Connectivity
echo -e "\n${YELLOW}[6/10] Checking database connectivity...${NC}"
if docker ps | grep -q nwu-postgres; then
    if docker exec nwu-postgres pg_isready -U nwu_user > /dev/null 2>&1; then
        log_check "PostgreSQL is ready"
    else
        log_issue "PostgreSQL not responding"
        echo "Restarting PostgreSQL..."
        docker-compose restart postgres
        log_fix "PostgreSQL restarted"
    fi
else
    log_warning "PostgreSQL container not running"
fi

if docker ps | grep -q nwu-redis; then
    if docker exec nwu-redis redis-cli ping > /dev/null 2>&1; then
        log_check "Redis is ready"
    else
        log_issue "Redis not responding"
        echo "Restarting Redis..."
        docker-compose restart redis
        log_fix "Redis restarted"
    fi
else
    log_warning "Redis container not running"
fi

# Check 7: Backend API
echo -e "\n${YELLOW}[7/10] Checking backend API...${NC}"
if docker ps | grep -q nwu-backend; then
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_check "Backend API is healthy"
    else
        log_issue "Backend API not responding"
        echo "Checking backend logs..."
        docker-compose logs --tail=20 backend
        echo "Restarting backend..."
        docker-compose restart backend
        sleep 10
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_fix "Backend API recovered"
        else
            log_issue "Backend API still not responding - check logs"
        fi
    fi
else
    log_warning "Backend container not running"
fi

# Check 8: Dependencies
echo -e "\n${YELLOW}[8/10] Checking dependencies...${NC}"
if [ -d frontend ] && [ ! -d frontend/node_modules ]; then
    log_issue "Frontend dependencies not installed"
    echo "Installing frontend dependencies..."
    cd frontend && npm install --legacy-peer-deps && cd ..
    log_fix "Frontend dependencies installed"
else
    log_check "Frontend dependencies installed"
fi

if [ -d backend ] && [ ! -d backend/.pytest_cache ]; then
    log_warning "Backend Python environment might need setup"
else
    log_check "Backend environment appears configured"
fi

# Check 9: Docker Images
echo -e "\n${YELLOW}[9/10] Checking Docker images...${NC}"
if docker images | grep -q nwu; then
    log_check "NWU Docker images exist"
else
    log_warning "NWU Docker images not found"
    echo "Build with: docker-compose build"
fi

# Check 10: File Permissions
echo -e "\n${YELLOW}[10/10] Checking file permissions...${NC}"
SCRIPTS=(auto-configure.sh auto-start.sh auto-recovery.sh preflight-check.sh health-monitor.sh)
PERMISSION_ISSUES=0

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ ! -x "$script" ]; then
            log_issue "$script is not executable"
            chmod +x "$script"
            log_fix "Made $script executable"
        else
            log_check "$script is executable"
        fi
    fi
done

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  TROUBLESHOOTING SUMMARY                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✨ No issues found! System is healthy. ✨${NC}"
else
    echo -e "${YELLOW}Issues found: $ISSUES_FOUND${NC}"
    echo -e "${GREEN}Fixes applied: $FIXES_APPLIED${NC}"

    if [ $FIXES_APPLIED -lt $ISSUES_FOUND ]; then
        echo -e "\n${RED}Some issues require manual intervention:${NC}"
        echo -e "1. Check Docker logs: ${YELLOW}docker-compose logs${NC}"
        echo -e "2. Restart services: ${YELLOW}./restart.sh${NC}"
        echo -e "3. Full reset: ${YELLOW}./stop.sh && ./clean.sh && ./auto-start.sh${NC}"
        echo -e "4. Check documentation: ${YELLOW}AUTOMATION.md${NC}"
    else
        echo -e "\n${GREEN}All issues have been automatically fixed!${NC}"
        echo -e "Run ${YELLOW}./auto-start.sh${NC} to start the system"
    fi
fi

# Recommendations
echo -e "\n${YELLOW}📋 Recommended Actions:${NC}"
if ! docker-compose ps -q 2>/dev/null | grep -q .; then
    echo -e "  1. Start system: ${YELLOW}./auto-start.sh${NC}"
elif [ $ISSUES_FOUND -gt 0 ]; then
    echo -e "  1. Restart services: ${YELLOW}./restart.sh${NC}"
    echo -e "  2. Monitor health: ${YELLOW}./health-monitor.sh${NC}"
else
    echo -e "  1. Monitor health: ${YELLOW}./health-monitor.sh${NC}"
    echo -e "  2. View API docs: ${YELLOW}http://localhost:8000/docs${NC}"
fi

echo -e "\n${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"
