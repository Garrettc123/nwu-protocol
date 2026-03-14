#!/bin/bash

# Continuous health monitoring
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🏥 Health Monitor - Press Ctrl+C to exit${NC}\n"

check_service() {
    SERVICE=$1
    URL=$2

    if curl -s -f "$URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $SERVICE is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ $SERVICE is not responding${NC}"
        return 1
    fi
}

while true; do
    clear
    echo -e "${GREEN}🏥 NWU Protocol Health Monitor${NC}"
    echo -e "${GREEN}================================${NC}\n"
    echo "Timestamp: $(date)"
    echo ""

    # Check Docker services
    echo -e "${YELLOW}Docker Services:${NC}"
    docker-compose ps 2>/dev/null || echo "Docker Compose not available"
    echo ""

    # Check HTTP endpoints
    echo -e "${YELLOW}HTTP Endpoints:${NC}"
    check_service "Backend API" "http://localhost:8000/health" || true
    check_service "Backend Docs" "http://localhost:8000/docs" || true
    check_service "RabbitMQ Admin" "http://localhost:15672" || true

    # Check database connections
    echo ""
    echo -e "${YELLOW}Database Connections:${NC}"
    if docker exec nwu-postgres pg_isready -U nwu_user > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
    else
        echo -e "${RED}❌ PostgreSQL not responding${NC}"
    fi

    if docker exec nwu-redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is ready${NC}"
    else
        echo -e "${RED}❌ Redis not responding${NC}"
    fi

    echo ""
    echo "Refreshing in 5 seconds... (Ctrl+C to exit)"
    sleep 5
done
