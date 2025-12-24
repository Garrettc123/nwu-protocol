# 🚀 NWU Protocol - Setup & Getting Started Guide

This guide will walk you through setting up the NWU Protocol for local development, testing, and deployment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Component Setup](#component-setup)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows (WSL2)
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 20GB free space

### Required Software

```bash
# Node.js 18+ & npm
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 9.0.0 or higher

# Git
git --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Python 3.9+ (for AI Agents)
python3 --version
```

### Installation

**macOS:**
```bash
# Using Homebrew
brew install node@18 git docker python@3.9
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nodejs npm git python3 python3-pip
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
```

**Windows (WSL2):**
```bash
# In WSL2 terminal
sudo apt update
sudo apt install nodejs npm git python3 python3-pip
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
vim .env
```

### 3. Start Services with Docker

```bash
# Start core services (MongoDB, Redis, RabbitMQ)
docker-compose up -d

# Start with monitoring (includes Grafana, Prometheus)
docker-compose --profile monitoring up -d

# Start with logging (includes Elasticsearch, Kibana)
docker-compose --profile logging up -d
```

### 4. Verify Services

```bash
# Check all containers are running
docker-compose ps

# Test connections
curl http://localhost:27017/  # MongoDB
redis-cli ping               # Redis
curl http://localhost:15672/ # RabbitMQ Management
```

### 5. Install Project Dependencies

```bash
# Backend
cd backend
npm install

# Frontend
cd ../frontend
npm install

# Smart Contracts
cd ../contracts
npm install

# AI Agents
cd ../agents
pip install -r requirements.txt
```

## Component Setup

### Backend Setup

```bash
cd backend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Run migrations (if applicable)
npm run migrate

# Start development server
npm run dev

# Server runs at http://localhost:3000
```

**Available Scripts:**
```bash
npm run dev          # Start with hot reload
npm start            # Start production server
npm test             # Run tests
npm run test:cov     # Run tests with coverage
npm run lint         # ESLint checks
npm run format       # Format code with Prettier
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
cp .env.example .env.local

# Start development server
npm run dev

# Frontend runs at http://localhost:3001
```

**Available Scripts:**
```bash
npm run dev          # Start dev server with hot reload
npm run build        # Build for production
npm start            # Start production server
npm test             # Run tests
npm run lint         # ESLint checks
npm run type-check   # TypeScript type checking
```

### Smart Contracts Setup

```bash
cd contracts

# Install dependencies
npm install

# Compile contracts
npm run compile

# Run tests
npm test

# Check coverage
npm run coverage

# Deploy to local testnet
npm run deploy:local
```

**Available Scripts:**
```bash
npm run compile      # Compile Solidity contracts
npm test             # Run Hardhat tests
npm run coverage     # Generate coverage report
npm run deploy       # Deploy to testnet
npm run verify       # Verify contracts on Etherscan
npm run flatten      # Flatten contract for verification
```

### AI Agents Setup

```bash
cd agents

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run agents
python src/agent_alpha.py
```

**Available Commands:**
```bash
pytest                        # Run tests
pytest --cov=src            # Run with coverage
black src/                    # Format code
flake8 src/                   # Lint code
mypy src/                     # Type checking
```

## Development Workflow

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Edit files
vim path/to/file.js

# Format code
npm run format

# Lint code
npm run lint

# Run tests
npm test
```

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commits format
git commit -m "feat(component): description of change"

# Examples:
# git commit -m "feat(backend): add user authentication"
# git commit -m "fix(frontend): resolve navbar bug"
# git commit -m "docs: update API documentation"
```

### 4. Push and Create PR

```bash
# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
# 1. Go to repository on GitHub
# 2. Click "New Pull Request"
# 3. Select your branch
# 4. Fill in PR template
# 5. Submit PR
```

## Testing

### Run All Tests

```bash
# Backend tests
cd backend && npm test

# Frontend tests
cd frontend && npm test

# Contract tests
cd contracts && npm test

# Agent tests
cd agents && pytest
```

### Run Tests with Coverage

```bash
# Backend
cd backend && npm run test:cov

# Frontend
cd frontend && npm run test:cov

# Contracts
cd contracts && npm run coverage

# Agents
cd agents && pytest --cov=src
```

### Code Quality Checks

```bash
# Backend
cd backend
npm run lint
npm run format:check

# Frontend
cd frontend
npm run lint
npm run type-check

# Contracts
cd contracts
npm run lint

# Agents
cd agents
black --check src/
flake8 src/
mypy src/
```

## Deployment

### Local Testing

```bash
# Build all components
cd backend && npm run build
cd ../frontend && npm run build
cd ../contracts && npm run compile

# Run in containers
docker-compose -f docker-compose.yml up --build
```

### Staging Deployment

```bash
# Trigger deployment workflow
gh workflow run deploy-staging.yml

# Or manually via GitHub Actions
# 1. Go to Actions tab
# 2. Select "Deploy to Staging"
# 3. Click "Run workflow"
```

### Production Deployment

```bash
# Create release
gh release create v1.0.0 --title "Release 1.0.0" --notes "Release notes here"

# Or manually
# 1. Go to Releases
# 2. Click "Create a new release"
# 3. Fill in version and notes
# 4. Publish release
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :3000

# Kill process
kill -9 <PID>

# Or change port in .env
PORT=3001
```

### Docker Container Issues

```bash
# View logs
docker-compose logs mongodb

# Restart service
docker-compose restart mongodb

# Rebuild image
docker-compose up --build mongodb

# Clean everything
docker-compose down -v
```

### MongoDB Connection Errors

```bash
# Check MongoDB is running
mongosh --host localhost:27017 -u admin -p password

# Or check via Docker
docker-compose exec mongodb mongosh -u admin -p password
```

### Out of Memory Errors

```bash
# Increase Docker memory
# macOS/Windows: Docker Desktop -> Preferences -> Resources
# Linux: Edit docker-compose.yml and set memory limits

# Or restart Docker
docker-compose down
docker system prune
docker-compose up -d
```

### Node Module Issues

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Or for all components
for dir in backend frontend contracts; do
  cd $dir
  rm -rf node_modules package-lock.json
  npm install
  cd ..
done
```

### Python Virtual Environment Issues

```bash
# Recreate virtual environment
cd agents
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Search existing [GitHub Issues](https://github.com/Garrettc123/nwu-protocol/issues)
- **Discussions**: Ask in [GitHub Discussions](https://github.com/Garrettc123/nwu-protocol/discussions)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Next Steps

1. ✅ Complete setup
2. 📖 Read architecture documentation in `docs/`
3. 💻 Start with [first contribution](CONTRIBUTING.md)
4. 🚀 Deploy to staging environment
5. 📝 Document your changes

Happy coding! 🎉
