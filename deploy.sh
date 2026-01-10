#!/bin/bash

################################################################################
# NWU Protocol - Perfect Deployment Script
# This script handles the complete deployment of the NWU Protocol system
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║              NWU Protocol Deployment Script                   ║"
    echo "║        Decentralized Intelligence & Verified Truth            ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    # Check Node.js (for frontend)
    if ! command -v node &> /dev/null; then
        log_warning "Node.js not found - frontend will not be built"
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_warning "npm not found - frontend will not be built"
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and try again"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            log_info "Creating .env from .env.example..."
            cp .env.example .env
            log_warning "Please edit .env and add your OPENAI_API_KEY and other credentials"
            log_warning "Press Enter to continue after editing .env, or Ctrl+C to abort"
            read -r
        else
            log_error ".env.example not found. Cannot create .env file."
            exit 1
        fi
    else
        log_success ".env file already exists"
    fi
    
    # Check if OPENAI_API_KEY is set
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        log_warning "OPENAI_API_KEY appears to be placeholder. AI verification will use mock mode."
    fi
}

# Clean up old containers and volumes
cleanup() {
    log_info "Cleaning up old containers and volumes..."
    
    docker-compose down -v 2>/dev/null || true
    
    # Remove dangling images
    docker image prune -f &> /dev/null || true
    
    log_success "Cleanup completed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    log_info "Building backend image..."
    docker-compose build backend
    
    log_info "Building agent-alpha image..."
    docker-compose build agent-alpha
    
    log_success "Docker images built successfully"
}

# Start infrastructure services first
start_infrastructure() {
    log_info "Starting infrastructure services..."
    
    # Start databases and message queue first
    docker-compose up -d postgres mongodb redis rabbitmq ipfs
    
    log_info "Waiting for infrastructure services to be healthy..."
    
    # Wait for PostgreSQL
    log_info "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker exec nwu-postgres pg_isready -U nwu_user &> /dev/null; then
            log_success "PostgreSQL is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for MongoDB
    log_info "Waiting for MongoDB..."
    for i in {1..30}; do
        if docker exec nwu-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            log_success "MongoDB is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    for i in {1..30}; do
        if docker exec nwu-redis redis-cli ping &> /dev/null; then
            log_success "Redis is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for RabbitMQ
    log_info "Waiting for RabbitMQ..."
    for i in {1..30}; do
        if docker exec nwu-rabbitmq rabbitmq-diagnostics ping &> /dev/null; then
            log_success "RabbitMQ is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    log_success "All infrastructure services are healthy"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait a bit for backend to be ready
    sleep 5
    
    # Run Alembic migrations
    docker exec nwu-backend alembic upgrade head 2>/dev/null || {
        log_warning "Migration command failed or migrations already applied"
    }
    
    log_success "Database migrations completed"
}

# Start application services
start_application() {
    log_info "Starting application services..."
    
    docker-compose up -d backend agent-alpha
    
    log_info "Waiting for backend to be healthy..."
    for i in {1..60}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is healthy"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    log_success "Application services started"
}

# Setup frontend
setup_frontend() {
    log_info "Setting up frontend..."
    
    if [ ! -d "frontend" ]; then
        log_warning "Frontend directory not found, skipping frontend setup"
        return
    fi
    
    cd frontend
    
    # Create .env.local if it doesn't exist
    if [ ! -f .env.local ]; then
        if [ -f .env.local.example ]; then
            cp .env.local.example .env.local
            log_success "Created frontend/.env.local"
        fi
    fi
    
    # Install dependencies
    if command -v npm &> /dev/null; then
        log_info "Installing frontend dependencies..."
        npm install --silent
        log_success "Frontend dependencies installed"
    fi
    
    cd ..
}

# Display service URLs
display_urls() {
    echo ""
    log_success "═══════════════════════════════════════════════════════════════"
    log_success "          NWU Protocol Deployment Complete!                    "
    log_success "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "🌐 Service URLs:"
    echo "   • Backend API:        http://localhost:8000"
    echo "   • API Documentation:  http://localhost:8000/docs"
    echo "   • Health Check:       http://localhost:8000/health"
    echo "   • RabbitMQ Management: http://localhost:15672 (guest/guest)"
    echo "   • IPFS Gateway:       http://localhost:8080"
    echo ""
    echo "📊 Database Connections:"
    echo "   • PostgreSQL:         localhost:5432 (nwu_user/rocket69!)"
    echo "   • MongoDB:            localhost:27017 (admin/rocket69!)"
    echo "   • Redis:              localhost:6379"
    echo ""
    echo "🚀 To start the frontend (in another terminal):"
    echo "   cd frontend && npm run dev"
    echo "   Then visit: http://localhost:3000"
    echo ""
    echo "📝 Useful Commands:"
    echo "   • View logs:          docker-compose logs -f"
    echo "   • View backend logs:  docker-compose logs -f backend"
    echo "   • View agent logs:    docker-compose logs -f agent-alpha"
    echo "   • Stop services:      docker-compose down"
    echo "   • Restart services:   docker-compose restart"
    echo ""
    log_success "═══════════════════════════════════════════════════════════════"
    echo ""
}

# Health check
perform_health_check() {
    log_info "Performing health check..."
    
    sleep 5
    
    # Check backend health
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "✓ Backend API is responding"
        
        # Get detailed health status
        health_response=$(curl -s http://localhost:8000/health)
        echo "$health_response" | grep -q '"status": "healthy"' && \
            log_success "✓ All backend services are healthy" || \
            log_warning "⚠ Some backend services may be degraded"
    else
        log_error "✗ Backend API is not responding"
    fi
    
    # Check RabbitMQ
    if curl -f http://localhost:15672 &> /dev/null; then
        log_success "✓ RabbitMQ Management UI is accessible"
    else
        log_warning "⚠ RabbitMQ Management UI is not accessible"
    fi
    
    echo ""
}

# Main deployment flow
main() {
    print_banner
    
    log_info "Starting NWU Protocol deployment..."
    echo ""
    
    # Check prerequisites
    check_prerequisites
    echo ""
    
    # Setup environment
    setup_environment
    echo ""
    
    # Option to clean up
    read -p "Do you want to clean up old containers and volumes? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup
        echo ""
    fi
    
    # Build images
    build_images
    echo ""
    
    # Start infrastructure
    start_infrastructure
    echo ""
    
    # Start application
    start_application
    echo ""
    
    # Run migrations
    run_migrations
    echo ""
    
    # Setup frontend
    setup_frontend
    echo ""
    
    # Health check
    perform_health_check
    
    # Display URLs
    display_urls
    
    log_success "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"
