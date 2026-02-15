#!/bin/bash

# Clean and Reset Everything

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}⚠️  WARNING: This will DELETE all data!${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "  - All Docker containers"
echo -e "  - All Docker volumes (databases, IPFS data, etc.)"
echo -e "  - All Docker images"
echo -e "  - Your .env file\n"

read -p "Are you sure? Type 'DELETE' to confirm: " confirm

if [ "$confirm" != "DELETE" ]; then
    echo -e "${GREEN}✅ Cancelled. No changes made.${NC}"
    exit 0
fi

echo -e "\n${YELLOW}🧹 Cleaning up...${NC}\n"

# Stop and remove containers
echo -e "${BLUE}Stopping containers...${NC}"
docker-compose down

# Remove volumes
echo -e "${BLUE}Removing volumes...${NC}"
docker-compose down -v

# Remove images
echo -e "${BLUE}Removing images...${NC}"
docker-compose down --rmi all

# Remove .env file
if [ -f .env ]; then
    echo -e "${BLUE}Removing .env file...${NC}"
    rm .env
fi

echo -e "\n${GREEN}✨ Cleanup complete!${NC}"
echo -e "${BLUE}💡 Run './setup.sh' to start fresh${NC}\n"
