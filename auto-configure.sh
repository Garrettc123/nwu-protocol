#!/bin/bash

# NWU Protocol - Automatic Configuration Script
# This script automatically configures everything to prevent any halting issues
# Usage: ./auto-configure.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 NWU Protocol - Auto Configuration${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Function to generate random secure key
generate_secret_key() {
    openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1
}

# Function to check and install dependencies
check_dependencies() {
    echo -e "${YELLOW}📋 Checking system dependencies...${NC}"

    MISSING_DEPS=""

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not found${NC}"
        MISSING_DEPS="docker $MISSING_DEPS"
    else
        echo -e "${GREEN}✅ Docker installed${NC}"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker Compose not found${NC}"
        MISSING_DEPS="docker-compose $MISSING_DEPS"
    else
        echo -e "${GREEN}✅ Docker Compose installed${NC}"
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}⚠️  Node.js not found${NC}"
        MISSING_DEPS="node $MISSING_DEPS"
    else
        echo -e "${GREEN}✅ Node.js installed ($(node --version))${NC}"
    fi

    # Check Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        echo -e "${YELLOW}⚠️  Python not found${NC}"
        MISSING_DEPS="python3 $MISSING_DEPS"
    else
        PYTHON_CMD=$(command -v python3 || command -v python)
        echo -e "${GREEN}✅ Python installed ($($PYTHON_CMD --version))${NC}"
    fi

    if [ -n "$MISSING_DEPS" ]; then
        echo -e "\n${RED}❌ Missing dependencies: $MISSING_DEPS${NC}"
        echo -e "${YELLOW}Please install missing dependencies and run again${NC}"
        echo -e "${YELLOW}Continuing with available tools...${NC}\n"
    fi
}

# Configure main environment file
configure_main_env() {
    echo -e "\n${YELLOW}📝 Configuring main .env file...${NC}"

    if [ -f .env ]; then
        echo -e "${GREEN}✅ .env file already exists, backing up...${NC}"
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi

    # Copy example to .env
    cp .env.example .env

    # Generate secure JWT secret
    JWT_SECRET=$(generate_secret_key)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-secret-key-change-in-production/$JWT_SECRET/" .env
    else
        sed -i "s/your-secret-key-change-in-production/$JWT_SECRET/" .env
    fi

    echo -e "${GREEN}✅ Main .env configured with secure defaults${NC}"
}

# Configure frontend environment
configure_frontend_env() {
    echo -e "\n${YELLOW}📝 Configuring frontend .env.local...${NC}"

    if [ ! -d frontend ]; then
        echo -e "${YELLOW}⚠️  Frontend directory not found, skipping${NC}"
        return
    fi

    if [ -f frontend/.env.local ]; then
        echo -e "${GREEN}✅ frontend/.env.local already exists, backing up...${NC}"
        cp frontend/.env.local frontend/.env.local.backup.$(date +%Y%m%d_%H%M%S)
    fi

    # Create frontend .env.local
    cat > frontend/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CHAIN_ID=11155111
NEXT_PUBLIC_NETWORK_NAME=Sepolia
EOF

    echo -e "${GREEN}✅ Frontend environment configured${NC}"
}

# Configure backend environment
configure_backend_env() {
    echo -e "\n${YELLOW}📝 Configuring backend environment...${NC}"

    if [ ! -d backend ]; then
        echo -e "${YELLOW}⚠️  Backend directory not found, skipping${NC}"
        return
    fi

    # Ensure backend .env exists (for local development)
    if [ ! -f backend/.env ]; then
        cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://nwu_user:rocket69!@localhost:5432/nwu_db
REDIS_URL=redis://localhost:6379
MONGODB_URI=mongodb://admin:rocket69!@localhost:27017/nwu_db?authSource=admin
RABBITMQ_URL=amqp://guest:guest@localhost:5672
IPFS_HOST=localhost
IPFS_PORT=5001
EOF
        echo -e "${GREEN}✅ Backend .env created${NC}"
    else
        echo -e "${GREEN}✅ Backend .env already exists${NC}"
    fi
}

# Setup .gitignore to prevent sensitive files
configure_gitignore() {
    echo -e "\n${YELLOW}📝 Ensuring .gitignore is configured...${NC}"

    # Add sensitive files to .gitignore if not already there
    GITIGNORE_ADDITIONS=".env
.env.local
.env.*.local
*.backup.*
.vscode/settings.json
.idea/
*.log
__pycache__/
*.pyc
node_modules/
.DS_Store
.pytest_cache/
.coverage
coverage.xml
*.db
*.sqlite"

    if [ -f .gitignore ]; then
        # Check if .env is already in .gitignore
        if ! grep -q "^\.env$" .gitignore; then
            echo "$GITIGNORE_ADDITIONS" >> .gitignore
            echo -e "${GREEN}✅ Updated .gitignore${NC}"
        else
            echo -e "${GREEN}✅ .gitignore already configured${NC}"
        fi
    else
        echo "$GITIGNORE_ADDITIONS" > .gitignore
        echo -e "${GREEN}✅ Created .gitignore${NC}"
    fi
}

# Create startup readiness checks
create_preflight_check() {
    echo -e "\n${YELLOW}📝 Creating pre-flight check script...${NC}"

    cat > preflight-check.sh << 'PREFLIGHT_EOF'
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
PREFLIGHT_EOF

    chmod +x preflight-check.sh
    echo -e "${GREEN}✅ Pre-flight check script created${NC}"
}

# Create health monitoring script
create_health_monitor() {
    echo -e "\n${YELLOW}📝 Creating health monitoring script...${NC}"

    cat > health-monitor.sh << 'HEALTH_EOF'
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
HEALTH_EOF

    chmod +x health-monitor.sh
    echo -e "${GREEN}✅ Health monitor script created${NC}"
}

# Create auto-recovery script
create_auto_recovery() {
    echo -e "\n${YELLOW}📝 Creating auto-recovery script...${NC}"

    cat > auto-recovery.sh << 'RECOVERY_EOF'
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
RECOVERY_EOF

    chmod +x auto-recovery.sh
    echo -e "${GREEN}✅ Auto-recovery script created${NC}"
}

# Main execution
main() {
    check_dependencies
    configure_main_env
    configure_frontend_env
    configure_backend_env
    configure_gitignore
    create_preflight_check
    create_health_monitor
    create_auto_recovery

    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${GREEN}✨ Auto-Configuration Complete! ✨${NC}\n"
    echo -e "${GREEN}Created Files:${NC}"
    echo -e "  ✅ .env (main configuration)"
    echo -e "  ✅ frontend/.env.local (frontend config)"
    echo -e "  ✅ backend/.env (backend config)"
    echo -e "  ✅ preflight-check.sh (startup checks)"
    echo -e "  ✅ health-monitor.sh (continuous monitoring)"
    echo -e "  ✅ auto-recovery.sh (automatic recovery)"
    echo -e "\n${GREEN}Next Steps:${NC}"
    echo -e "  1. Run ${YELLOW}./preflight-check.sh${NC} to verify system readiness"
    echo -e "  2. Run ${YELLOW}make deploy${NC} or ${YELLOW}./setup.sh${NC} to start services"
    echo -e "  3. Run ${YELLOW}./health-monitor.sh${NC} to monitor system health"
    echo -e "  4. Use ${YELLOW}./auto-recovery.sh${NC} if services fail"
    echo -e "\n${BLUE}================================================${NC}\n"
}

main
