#!/bin/bash

# Service Status Checker

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 NWU Protocol - Service Status${NC}\n"

echo -e "${YELLOW}Docker Containers:${NC}"
docker-compose ps

echo -e "\n${YELLOW}Service Health Checks:${NC}"

check_service() {
    local name=$1
    local url=$2
    local timeout=2
    
    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is UP${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is DOWN${NC}"
        return 1
    fi
}

check_service "Frontend" "http://localhost:3000"
check_service "Backend API" "http://localhost:8000/health"
check_service "RabbitMQ" "http://localhost:15672"
check_service "IPFS" "http://localhost:5001/api/v0/id"

echo -e "\n${YELLOW}Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo -e "\n${BLUE}💡 Run './logs.sh [service]' to view logs for a specific service${NC}"
