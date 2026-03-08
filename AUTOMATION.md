# 🚀 NWU Protocol - Complete Automation Guide

## Overview

This repository is now fully configured with comprehensive automation to prevent any process halts. Everything can be started and managed automatically with zero manual configuration required.

## 🎯 Quick Start (One Command)

```bash
./auto-start.sh
```

This single command will:
1. ✅ Auto-configure all environment files
2. ✅ Run pre-flight system checks
3. ✅ Clean up old containers
4. ✅ Pull and build all images
5. ✅ Start all services with health checks
6. ✅ Run database migrations
7. ✅ Display complete service status

## 📋 Available Automation Scripts

### Core Automation

| Script | Purpose | Usage |
|--------|---------|-------|
| `auto-configure.sh` | Automatically configures all environment files and creates monitoring scripts | `./auto-configure.sh` |
| `auto-start.sh` | Complete automated startup (recommended) | `./auto-start.sh` |
| `auto-recovery.sh` | Automatically recovers failed services | `./auto-recovery.sh` |
| `preflight-check.sh` | Verify system readiness before starting | `./preflight-check.sh` |
| `health-monitor.sh` | Continuous health monitoring (live dashboard) | `./health-monitor.sh` |

### Management Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` | Interactive setup wizard |
| `deploy.sh` | Production deployment |
| `status.sh` | Show service status |
| `logs.sh` | View all service logs |
| `restart.sh` | Restart all services |
| `stop.sh` | Stop all services |

## 🔧 Configuration Files (Auto-Generated)

All configuration files are automatically created by `auto-configure.sh`:

- `.env` - Main environment configuration (with secure JWT secret)
- `frontend/.env.local` - Frontend configuration
- `backend/.env` - Backend local development configuration

**No manual editing required!** The auto-configure script generates secure defaults.

## 🏥 Health & Monitoring

### Continuous Monitoring
```bash
./health-monitor.sh
```
Provides real-time dashboard showing:
- Docker service status
- HTTP endpoint health
- Database connectivity
- Auto-refreshes every 5 seconds

### Health Checks
All services include health checks:
- PostgreSQL: `pg_isready` check
- Redis: `redis-cli ping`
- MongoDB: `mongosh ping`
- RabbitMQ: `rabbitmq-diagnostics ping`
- Backend API: `/health` endpoint

### Auto-Recovery
```bash
./auto-recovery.sh
```
Automatically detects and restarts unhealthy services.

## 🚦 Pre-Flight Checks

Before starting, `preflight-check.sh` verifies:
1. ✅ Environment files exist
2. ✅ Docker daemon is running
3. ✅ Required ports are available (3000, 5432, 6379, 8000, etc.)
4. ✅ Sufficient disk space (>5GB)

## 🎮 Service Access

Once started, access services at:

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Documentation | http://localhost:8000/docs | - |
| API Health | http://localhost:8000/health | - |
| RabbitMQ Admin | http://localhost:15672 | guest/guest |
| PostgreSQL | localhost:5432 | nwu_user/rocket69! |
| MongoDB | localhost:27017 | admin/rocket69! |
| Redis | localhost:6379 | - |
| IPFS | http://localhost:5001 | - |

## 🔄 Common Operations

### Complete Reset
```bash
./stop.sh
./clean.sh  # Will prompt for confirmation
./auto-start.sh
```

### View Logs
```bash
# All services
./logs.sh

# Specific service
make logs-backend
make logs-agent
```

### Run Migrations
```bash
make migrate
# Or manually:
docker exec nwu-backend alembic upgrade head
```

### Run Tests
```bash
make test           # Run all tests
make test-api       # Test API endpoints
./validate-backend.sh  # Comprehensive validation
```

## 🐳 Docker Compose Commands

For advanced users:

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart backend

# Rebuild images
docker-compose build
```

## 🔐 Security Notes

- Default passwords are provided for development only
- For production, use `deploy-prod` target and update credentials
- JWT secrets are auto-generated with secure random values
- Sensitive files are automatically added to `.gitignore`

## 🆘 Troubleshooting

### Services Won't Start

1. Run pre-flight checks:
   ```bash
   ./preflight-check.sh
   ```

2. Check if ports are in use:
   ```bash
   lsof -i :8000  # Backend port
   lsof -i :3000  # Frontend port
   ```

3. Check Docker daemon:
   ```bash
   docker info
   ```

4. Try auto-recovery:
   ```bash
   ./auto-recovery.sh
   ```

### Service Unhealthy

```bash
# Check logs
./logs.sh

# Try recovery
./auto-recovery.sh

# Full restart
./restart.sh
```

### Database Connection Issues

```bash
# Check database containers
docker-compose ps postgres mongodb redis

# Access database shell
make shell-postgres
make shell-mongodb
```

## 📊 Makefile Targets

Quick reference for `make` commands:

```bash
make help           # Show all available commands
make deploy         # Perfect one-command deployment
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make logs           # View all logs
make status         # Show service status
make health         # Check system health
make validate       # Run comprehensive validation
make test-api       # Test API endpoints
make clean          # Clean up containers and volumes
make build          # Build Docker images
make frontend       # Start frontend dev server
make migrate        # Run database migrations
```

## 🎯 Development Workflow

1. **First Time Setup:**
   ```bash
   ./auto-start.sh
   ```

2. **Daily Development:**
   ```bash
   ./status.sh        # Check if services are running
   ./logs.sh          # Monitor logs if needed
   make frontend      # Start frontend dev server
   ```

3. **After Changes:**
   ```bash
   docker-compose build [service]
   ./restart.sh
   ```

4. **Before Committing:**
   ```bash
   make test          # Run all tests
   make validate      # Validate backend
   ```

## 🚀 Production Deployment

```bash
# Use the automated production deployment
make deploy-prod

# Or manually:
cp .env.production.example .env
# Edit .env with production credentials
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 Environment Variables

Key variables (auto-configured):

- `DATABASE_URL` - PostgreSQL connection
- `MONGODB_URI` - MongoDB connection
- `REDIS_URL` - Redis connection
- `RABBITMQ_URL` - RabbitMQ connection
- `IPFS_HOST` / `IPFS_PORT` - IPFS configuration
- `JWT_SECRET_KEY` - Auto-generated secure secret
- `OPENAI_API_KEY` - Optional, for AI features
- `STRIPE_API_KEY` - Optional, for payments

## 🎓 Additional Resources

- **API Documentation**: http://localhost:8000/docs (after starting)
- **Project README**: [README.md](README.md)
- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)

## ✨ Key Features

- **Zero Configuration**: Everything auto-configured with secure defaults
- **Health Monitoring**: Continuous health checks and auto-recovery
- **Pre-Flight Checks**: Verify system readiness before starting
- **Smart Logging**: Comprehensive logging with easy access
- **Auto-Recovery**: Automatic service recovery on failures
- **One-Command Start**: Single command to start everything
- **Development Ready**: Optimized for local development
- **Production Ready**: Includes production deployment scripts

---

**Need Help?** Run `./help.sh` or `make help` for available commands.
