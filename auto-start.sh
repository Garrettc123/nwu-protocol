#!/bin/bash

# NWU Protocol - Complete Auto-Start Script
# This script handles EVERYTHING automatically to prevent any process halts
# Usage: ./auto-start.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}"
cat << "EOF"
    _   ___________       ____            __                  __
   / | / / ____/ / |     / / __ \_________  / /_____  _________  / /
  /  |/ / /   / /| | /| / / / / / ___/ __ \/ __/ __ \/ ___/ __ \/ /
 / /|  / /___/ / | |/ |/ / /_/ / /  / /_/ / /_/ /_/ / /__/ /_/ / /
/_/ |_/\____/_/  |__/|__/\____/_/   \____/\__/\____/\___/\____/_/

           AUTO-START - Complete Automation System
EOF
echo -e "${NC}\n"

# Function to print status
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Step 1: Auto-configuration
print_status "Step 1/7: Running auto-configuration..."
if [ -x ./auto-configure.sh ]; then
    ./auto-configure.sh
else
    print_error "auto-configure.sh not found or not executable"
    exit 1
fi

# Step 2: Pre-flight checks
print_status "Step 2/7: Running pre-flight checks..."
if [ -x ./preflight-check.sh ]; then
    if ! ./preflight-check.sh; then
        print_error "Pre-flight checks failed"
        exit 1
    fi
else
    print_warning "preflight-check.sh not found, skipping checks"
fi

# Step 3: Clean up old containers (if any)
print_status "Step 3/7: Cleaning up old containers..."
if docker-compose ps -q 2>/dev/null | grep -q .; then
    print_status "Found existing containers, stopping them..."
    docker-compose down || true
fi

# Step 4: Pull latest images
print_status "Step 4/7: Pulling latest Docker images..."
docker-compose pull || print_warning "Failed to pull some images, continuing..."

# Step 5: Build custom images
print_status "Step 5/7: Building custom Docker images..."
docker-compose build || print_error "Failed to build images"

# Step 6: Start all services
print_status "Step 6/7: Starting all services..."
docker-compose up -d

# Step 7: Wait for services to be healthy
print_status "Step 7/7: Waiting for services to be healthy..."
RETRY_COUNT=0
MAX_RETRIES=30
SLEEP_TIME=5

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    UNHEALTHY=$(docker-compose ps | grep -c "unhealthy\|starting" || true)

    if [ "$UNHEALTHY" -eq 0 ]; then
        print_status "All services are healthy!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    print_status "Waiting for services... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep $SLEEP_TIME
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_warning "Some services may not be fully healthy yet"
    docker-compose ps
fi

# Step 8: Run database migrations
print_status "Running database migrations..."
if docker ps | grep -q nwu-backend; then
    docker exec nwu-backend alembic upgrade head 2>/dev/null || print_warning "Migrations failed or not needed"
else
    print_warning "Backend container not running, skipping migrations"
fi

# Step 9: Install frontend dependencies (if needed)
print_status "Checking frontend dependencies..."
if [ -d frontend ] && [ ! -d frontend/node_modules ]; then
    print_status "Installing frontend dependencies..."
    cd frontend && npm install --legacy-peer-deps && cd ..
fi

# Step 10: Display service status
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✨ AUTO-START COMPLETE! ✨${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

print_status "Service Status:"
docker-compose ps

echo ""
echo -e "${GREEN}🌐 Access Your Services:${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Frontend:         ${YELLOW}http://localhost:3000${NC}"
echo -e "Backend API:      ${YELLOW}http://localhost:8000${NC}"
echo -e "API Docs:         ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "API Health:       ${YELLOW}http://localhost:8000/health${NC}"
echo -e "RabbitMQ Admin:   ${YELLOW}http://localhost:15672${NC} (guest/guest)"
echo -e "PostgreSQL:       ${YELLOW}localhost:5432${NC} (nwu_user/rocket69!)"
echo -e "MongoDB:          ${YELLOW}localhost:27017${NC} (admin/rocket69!)"
echo -e "Redis:            ${YELLOW}localhost:6379${NC}"
echo -e "IPFS:             ${YELLOW}http://localhost:5001${NC}"
echo -e "${BLUE}================================================${NC}"

echo ""
echo -e "${GREEN}📊 Monitoring & Management:${NC}"
echo -e "  ${YELLOW}./health-monitor.sh${NC}   - Continuous health monitoring"
echo -e "  ${YELLOW}./auto-recovery.sh${NC}    - Auto-recover failed services"
echo -e "  ${YELLOW}./status.sh${NC}           - Check service status"
echo -e "  ${YELLOW}./logs.sh${NC}             - View all logs"
echo -e "  ${YELLOW}make logs-backend${NC}     - View backend logs only"

echo ""
echo -e "${GREEN}🔄 Quick Actions:${NC}"
echo -e "  ${YELLOW}./restart.sh${NC}          - Restart all services"
echo -e "  ${YELLOW}./stop.sh${NC}             - Stop all services"
echo -e "  ${YELLOW}make test${NC}             - Run tests"
echo -e "  ${YELLOW}make migrate${NC}          - Run migrations"

echo ""
echo -e "${GREEN}🎯 Recommended Next Steps:${NC}"
echo -e "  1. Visit ${YELLOW}http://localhost:8000/docs${NC} to explore the API"
echo -e "  2. Check ${YELLOW}http://localhost:8000/health${NC} for system health"
echo -e "  3. Run ${YELLOW}./health-monitor.sh${NC} to monitor services"
echo -e "  4. Review logs with ${YELLOW}./logs.sh${NC} if any issues occur"

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}System is ready for development! 🚀${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Optional: Start health monitor in background
read -p "Start health monitor in background? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    nohup ./health-monitor.sh > health-monitor.log 2>&1 &
    print_status "Health monitor started in background (PID: $!)"
    print_status "View logs: tail -f health-monitor.log"
fi
