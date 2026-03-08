#!/bin/bash

# Auto-recovery for failed services
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Auto-Recovery Script${NC}\n"

# Check if services are running
echo "Checking service status..."
UNHEALTHY=$(docker-compose ps | grep -c "unhealthy\|Exit" || true)

if [ "$UNHEALTHY" -gt 0 ]; then
    echo -e "${RED}Found $UNHEALTHY unhealthy services${NC}"
    echo -e "${YELLOW}Attempting recovery...${NC}"

    # Restart unhealthy services
    docker-compose restart

    echo -e "${YELLOW}Waiting for services to stabilize...${NC}"
    sleep 15

    # Check again
    STILL_UNHEALTHY=$(docker-compose ps | grep -c "unhealthy\|Exit" || true)

    if [ "$STILL_UNHEALTHY" -gt 0 ]; then
        echo -e "${RED}❌ Recovery failed. Try: docker-compose down && docker-compose up -d${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ All services recovered successfully${NC}"
    fi
else
    echo -e "${GREEN}✅ All services are healthy${NC}"
fi
