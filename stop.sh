#!/bin/bash

# Stop All Services

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping all NWU Protocol services...${NC}\n"

docker-compose down

echo -e "\n${GREEN}✅ All services stopped${NC}"
echo -e "${BLUE}💡 Data is preserved. Run './setup.sh' to restart${NC}\n"
