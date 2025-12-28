#!/bin/bash

# Restart All Services

BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Restarting all services...${NC}\n"

if [ -n "$1" ]; then
    echo -e "${BLUE}Restarting: $1${NC}"
    docker-compose restart "$1"
else
    docker-compose restart
fi

echo -e "\n${GREEN}✅ Services restarted${NC}"
echo -e "${BLUE}💡 Run './status.sh' to check health${NC}\n"
