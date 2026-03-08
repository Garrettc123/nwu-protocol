#!/bin/bash

# Pre-flight system checks
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔍 Running pre-flight checks...${NC}\n"

# Check environment files
echo "1. Checking environment files..."
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file missing! Run ./auto-configure.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✅ .env exists${NC}"

# Check Docker daemon
echo "2. Checking Docker daemon..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon not running! Start Docker first${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check port availability
echo "3. Checking port availability..."
PORTS=(3000 5432 6379 8000 5672 15672 27017 5001)
PORT_NAMES=("Frontend" "PostgreSQL" "Redis" "Backend API" "RabbitMQ" "RabbitMQ Admin" "MongoDB" "IPFS")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo -e "${YELLOW}⚠️  Port $PORT ($NAME) is already in use${NC}"
    else
        echo -e "${GREEN}✅ Port $PORT ($NAME) available${NC}"
    fi
done

# Check disk space
echo "4. Checking disk space..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "${AVAILABLE_SPACE%.*}" -lt 5 ]; then
    echo -e "${YELLOW}⚠️  Low disk space: ${AVAILABLE_SPACE}GB available${NC}"
else
    echo -e "${GREEN}✅ Sufficient disk space: ${AVAILABLE_SPACE}GB available${NC}"
fi

echo -e "\n${GREEN}✅ All pre-flight checks passed!${NC}"
