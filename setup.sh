#!/bin/bash

# NWU Protocol - One-Command Setup Script
# Usage: ./setup.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
███╗   ██╗██╗    ██╗██╗   ██╗    ██████╗ ██████╗  ██████╗ ████████╗ ██████╗  ██████╗ ██████╗ ██╗     
████╗  ██║██║    ██║██║   ██║    ██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗██╔════╝██╔═══██╗██║     
██╔██╗ ██║██║ █╗ ██║██║   ██║    ██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║     
██║╚██╗██║██║███╗██║██║   ██║    ██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║     
██║ ╚████║╚███╔███╔╝╚██████╔╝    ██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╗╚██████╔╝███████╗
╚═╝  ╚═══╝ ╚══╝╚══╝  ╚═════╝     ╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 NWU Protocol - Automated Setup${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ Docker not found. Install from: https://docs.docker.com/get-docker/${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}❌ Docker Compose not found. Install from: https://docs.docker.com/compose/install/${NC}"; exit 1; }

echo -e "${GREEN}✅ Docker installed${NC}"
echo -e "${GREEN}✅ Docker Compose installed${NC}\n"

# Setup environment file
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cp .env.example .env
    
    echo -e "${YELLOW}🔑 Enter your OpenAI API Key (or press Enter to skip):${NC}"
    read -r OPENAI_KEY
    
    if [ -n "$OPENAI_KEY" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/your-openai-api-key-here/$OPENAI_KEY/" .env
        else
            sed -i "s/your-openai-api-key-here/$OPENAI_KEY/" .env
        fi
        echo -e "${GREEN}✅ API key configured${NC}"
    else
        echo -e "${YELLOW}⚠️  You can add your API key later in .env file${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

echo ""

# Pull latest images
echo -e "${YELLOW}📦 Pulling Docker images...${NC}"
docker-compose pull

echo ""

# Start services
echo -e "${YELLOW}🚀 Starting all services...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo -e "${YELLOW}🏥 Checking service health...${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}✨ Setup Complete! ✨${NC}\n"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}🌐 Access Your Services:${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Frontend:         ${YELLOW}http://localhost:3000${NC}"
echo -e "Backend API:      ${YELLOW}http://localhost:8000${NC}"
echo -e "API Docs:         ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "RabbitMQ:         ${YELLOW}http://localhost:15672${NC} (guest/guest)"
echo -e "PostgreSQL:       ${YELLOW}localhost:5432${NC}"
echo -e "Redis:            ${YELLOW}localhost:6379${NC}"
echo -e "IPFS:             ${YELLOW}http://localhost:5001${NC}"
echo -e "${BLUE}================================================${NC}\n"

echo -e "${GREEN}📚 Quick Commands:${NC}"
echo -e "  ${YELLOW}./status.sh${NC}     - Check all service status"
echo -e "  ${YELLOW}./logs.sh${NC}       - View service logs"
echo -e "  ${YELLOW}./stop.sh${NC}       - Stop all services"
echo -e "  ${YELLOW}./restart.sh${NC}    - Restart all services"
echo -e "  ${YELLOW}./clean.sh${NC}      - Clean and reset everything\n"

echo -e "${GREEN}🎯 Next Steps:${NC}"
echo -e "  1. Visit ${YELLOW}http://localhost:3000${NC} to see the frontend"
echo -e "  2. Check ${YELLOW}http://localhost:8000/docs${NC} for API documentation"
echo -e "  3. Run ${YELLOW}./status.sh${NC} to monitor service health\n"

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Need help? Check QUICKSTART.md or run: ./help.sh${NC}"
echo -e "${BLUE}================================================${NC}\n"
