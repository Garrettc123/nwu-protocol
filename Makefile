.PHONY: help deploy start stop restart logs status clean test build

# Default target
help:
	@echo "NWU Protocol - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "  make deploy     - Perfect one-command deployment"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View all logs"
	@echo "  make status     - Show service status"
	@echo "  make health     - Check system health"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make test       - Run all tests"
	@echo "  make build      - Build Docker images"
	@echo "  make frontend   - Start frontend dev server"
	@echo "  make migrate    - Run database migrations"
	@echo "  make contracts  - Deploy smart contracts"
	@echo ""

# Perfect deployment
deploy:
	@echo "🚀 Starting perfect deployment..."
	@./deploy.sh

# Start services
start:
	@echo "Starting NWU Protocol services..."
	@docker-compose up -d
	@echo "✅ Services started"
	@make status

# Stop services
stop:
	@echo "Stopping NWU Protocol services..."
	@docker-compose down
	@echo "✅ Services stopped"

# Restart services
restart:
	@echo "Restarting NWU Protocol services..."
	@docker-compose restart
	@echo "✅ Services restarted"

# View logs
logs:
	@docker-compose logs -f

# View logs for specific service
logs-backend:
	@docker-compose logs -f backend

logs-agent:
	@docker-compose logs -f agent-alpha

logs-postgres:
	@docker-compose logs -f postgres

# Check status
status:
	@echo "Service Status:"
	@docker-compose ps

# Health check
health:
	@echo "Checking system health..."
	@curl -s http://localhost:8000/health | jq . || echo "Backend not responding"

# Clean up
clean:
	@echo "⚠️  This will remove all containers and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker system prune -f; \
		echo "✅ Cleanup complete"; \
	fi

# Run tests
test:
	@echo "Running backend tests..."
	@cd backend && pytest
	@echo "Running contract tests..."
	@cd contracts && npx hardhat test

# Build images
build:
	@echo "Building Docker images..."
	@docker-compose build
	@echo "✅ Images built"

# Frontend
frontend:
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

# Run migrations
migrate:
	@echo "Running database migrations..."
	@docker exec nwu-backend alembic upgrade head
	@echo "✅ Migrations complete"

# Deploy contracts
contracts:
	@echo "Compiling and deploying smart contracts..."
	@cd contracts && npx hardhat compile
	@cd contracts && npx hardhat run scripts/deploy.js --network localhost
	@echo "✅ Contracts deployed"

# Production deployment
deploy-prod:
	@echo "🚀 Starting production deployment..."
	@cp .env.production.example .env
	@echo "⚠️  Please edit .env with production credentials"
	@read -p "Press Enter after editing .env..."
	@docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production deployment complete"

# Backup databases
backup:
	@echo "Creating database backups..."
	@mkdir -p backups
	@docker exec nwu-postgres pg_dump -U nwu_user nwu_db > backups/postgres_$$(date +%Y%m%d_%H%M%S).sql
	@docker exec nwu-mongodb mongodump --out backups/mongodb_$$(date +%Y%m%d_%H%M%S)
	@echo "✅ Backups created in ./backups/"

# Monitor services
monitor:
	@watch -n 2 docker-compose ps

# Enter backend container
shell-backend:
	@docker exec -it nwu-backend /bin/bash

# Enter database
shell-postgres:
	@docker exec -it nwu-postgres psql -U nwu_user -d nwu_db

shell-mongodb:
	@docker exec -it nwu-mongodb mongosh -u admin -p rocket69!

# Quick dev setup
dev-setup:
	@echo "Setting up development environment..."
	@cp .env.example .env
	@cd frontend && cp .env.local.example .env.local
	@cd frontend && npm install
	@cd contracts && npm install
	@echo "✅ Development environment ready"
	@echo "Edit .env and frontend/.env.local with your settings"
