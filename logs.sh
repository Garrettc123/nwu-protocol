#!/bin/bash

# Log Viewer Script

BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${BLUE}📋 Showing logs for all services...${NC}\n"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"
    docker-compose logs -f --tail=50
else
    echo -e "${BLUE}📋 Showing logs for: $1${NC}\n"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"
    docker-compose logs -f --tail=100 "$1"
fi
