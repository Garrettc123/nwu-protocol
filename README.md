# NWU Protocol

[![CI/CD Pipeline](https://github.com/Garrettc123/nwu-protocol/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Garrettc123/nwu-protocol/actions)
[![Quality & Security Checks](https://github.com/Garrettc123/nwu-protocol/actions/workflows/quality-checks.yml/badge.svg)](https://github.com/Garrettc123/nwu-protocol/actions)
[![Microsoft Defender for DevOps](https://github.com/Garrettc123/nwu-protocol/actions/workflows/defender-for-devops.yml/badge.svg)](https://github.com/Garrettc123/nwu-protocol/actions)
[![codecov](https://codecov.io/gh/Garrettc123/nwu-protocol/branch/main/graph/badge.svg)](https://codecov.io/gh/Garrettc123/nwu-protocol)

## 🎯 Stability & Excellence Initiative

**NWU Protocol operates under a zero-tolerance stability mandate.** We maintain world-class engineering standards with strict governance, comprehensive testing, and security-first practices.

📋 **[Read our Stability Mandate](STABILITY_MANDATE.md)** | 🏛️ **[Governance Framework](GOVERNANCE.md)** | ✅ **[Definition of Done](DEFINITION_OF_DONE.md)**

---

## 🚀 Perfect One-Command Deployment

```bash
./deploy.sh
```

**That's it!** The deployment script automatically handles everything:

- ✅ Builds all Docker images
- ✅ Starts 7 infrastructure services
- ✅ Runs database migrations
- ✅ Performs health checks
- ✅ Displays all service URLs

**Alternative with Make:**

```bash
make deploy
```

See [DEPLOY_NOW.md](DEPLOY_NOW.md) for the complete quick-start guide.

## Overview

Decentralized Intelligence & Verified Truth Protocol - Safeguarding humanity through AI-powered verification and blockchain immutability.

A complete, production-ready platform for submitting code, datasets, and documents that are verified by AI agents and rewarded with blockchain tokens.

**NEW: Multi-Agent Orchestration System** - Full-scale "god bots" that dynamically spawn and manage specialized agents. Master agents can create verifier, analyzer, coordinator, and specialist agents on-demand with auto-scaling, health monitoring, and hierarchical structures. See [AGENT_ORCHESTRATION.md](AGENT_ORCHESTRATION.md) for complete documentation.

## ✨ Features

### 🚀 Backend API (FastAPI)

- ✅ Contribution submission and management
- ✅ User registration and stats tracking
- ✅ IPFS integration for decentralized file storage
- ✅ RabbitMQ message queue for async processing
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ RESTful API with automatic OpenAPI documentation
- ✅ **Payment integration with Stripe for subscriptions**
- ✅ **API key management and rate limiting**
- ✅ **Three-tier subscription system (Free, Pro, Enterprise)**

### 🤖 Agent-Alpha (AI Verification)

- ✅ Automated quality verification using OpenAI GPT-4
- ✅ Code quality, originality, and security analysis
- ✅ Dataset and document verification
- ✅ Consensus-based scoring system
- ✅ RabbitMQ consumer for async task processing

### 🌐 Multi-Agent Orchestration System (NEW!)

- ✅ **Dynamic Agent Spawning** - Create agents on-demand based on workload
- ✅ **Hierarchical Structure** - Master "god bot" agents spawn and manage children
- ✅ **Auto-scaling** - Automatically scale agents up/down based on utilization (80%/20% thresholds)
- ✅ **Self-healing** - Failed agents automatically detected and recovered
- ✅ **5 Agent Types** - Master, Verifier, Analyzer, Coordinator, Specialist
- ✅ **Load Balancing** - Intelligent task routing to appropriate agents
- ✅ **Health Monitoring** - Continuous heartbeat monitoring with 60s timeout
- ✅ **REST API** - Full control via `/api/v1/agents/*` endpoints
- ✅ **CLI Tool** - Manage agents from command line with `agent_cli.py`
- ✅ **Metrics Tracking** - Task completion, failures, duration, uptime per agent

**Quick Start:**

```bash
# The orchestrator auto-initializes with the backend
python -m backend.app.main

# Use the CLI
python agent_cli.py status
python agent_cli.py spawn verifier
python agent_cli.py list

# Or run the full demo
python examples/agent_orchestration_demo.py
```

See [AGENT_ORCHESTRATION.md](AGENT_ORCHESTRATION.md) for complete documentation and [AGENT_QUICKSTART.md](AGENT_QUICKSTART.md) for quick start guide.

### 🎨 Frontend (Next.js 14)

- ✅ Modern, responsive UI with Tailwind CSS
- ✅ File upload with drag-and-drop support
- ✅ Real-time contribution status tracking
- ✅ Browse all contributions
- ✅ Integration with backend API

### 🔗 Smart Contracts (Solidity)

- ✅ ERC-20 NWU Token with minting and burning
- ✅ Verification Registry for on-chain results
- ✅ Reward Distribution with quality-based calculations
- ✅ OpenZeppelin security standards

### 💳 Payment System (Stripe)

- ✅ Three-tier subscription system (Free, Pro, Enterprise)
- ✅ Secure API key generation and management
- ✅ Rate limiting per subscription tier
- ✅ Payment processing and billing
- ✅ Usage metering foundation
- ✅ Webhook integration for real-time updates

**Pricing:**

- **Free**: $0/month - 100 API requests/day
- **Pro**: $99/month - 10,000 API requests/day + advanced features
- **Enterprise**: $999/month - 100,000 API requests/day + premium support

See [PAYMENT_INTEGRATION.md](PAYMENT_INTEGRATION.md) for complete documentation.

## 🔧 CI/CD & Automation

The project includes comprehensive GitHub Actions workflows for continuous integration, security scanning, and automated maintenance:

### Security & Quality

- **Microsoft Defender for DevOps** (`defender-for-devops.yml`) - Advanced security scanning with SARIF reporting
- **Quality & Security Checks** (`quality-checks.yml`) - Code quality, linting, and security audits across all components
- **CI/CD Pipeline** (`ci.yml`) - Comprehensive CI pipeline for Node.js, backend tests, and smart contract validation

### Automated Maintenance

- **Codex Auto-Fix** (`codex-autofix.yml`) - Automatically fixes CI failures using AI-powered analysis
- **Continuous Code Healing** (`continuous-healing.yml`) - Proactive code health monitoring and auto-repair
- **Auto-Complete Code Pipeline** (`auto-complete-repair.yml`) - AI-assisted code completion and repair
- **Auto PR Workflow** (`auto-pr.yml`) - Automated pull request creation and management

### Deployment & Release

- **Deploy to Production** (`deploy.yml`) - Production deployment pipeline
- **Failover Deployment System** (`failover-deployment.yml`) - Multi-region failover and disaster recovery
- **Self-Healing Deployment** (`autofix-deploy.yml`) - Node.js-focused deployment with auto-recovery
- **Automated Release** (`release.yml`) - Automated version management and release notes generation

### Project Management

- **Universal CI/CD** (`ci-cd.yml`) - Auto-detecting pipeline for Python, Node.js, and Docker environments
- **FastAPI Entrypoint Verification** (`fastapi-check.yml`) - Validates FastAPI backend configuration
- **Project Initialization Helper** (`project-init.yml`) - Automated project setup and configuration

All workflows are configured with appropriate permissions and security best practices.

## 🎯 Quick Start (3 Simple Steps)

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend)
- OpenAI API key (optional, for AI verification)

### Step 1: Clone and Configure

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Step 2: Perfect Deployment

```bash
./deploy.sh
```

Or use Make:

```bash
make deploy
```

### Step 3: Access Your System

The deployment script will display all URLs automatically:

- **Backend API** - http://localhost:8000
- **API Documentation** - http://localhost:8000/docs
- **Frontend** - http://localhost:3000 (run `make frontend` in another terminal)
- **RabbitMQ Management** - http://localhost:15672 (guest/guest)

## 📦 What's Included

This deployment automatically starts:

- **Backend API** - http://localhost:8000
- **Agent-Alpha** - Background AI verification service
- **PostgreSQL** - Database on port 5432
- **MongoDB** - NoSQL database on port 27017
- **Redis** - Cache on port 6379
- **RabbitMQ** - Message queue on port 5672 (Management UI: http://localhost:15672)
- **IPFS** - Decentralized storage on port 8080

## 💡 Useful Commands

### Standard Commands

```bash
make help          # Show all available commands
make status        # Check service status
make logs          # View all logs
make health        # Check system health
make validate      # Run comprehensive backend validation
make test-api      # Test all API endpoints
make test-all      # Full system validation
make frontend      # Start frontend dev server
make clean         # Clean up everything
```

### 🤖 Automation Commands (New!)

```bash
./scripts/setup-automation.sh   # Install all automation (run once)
./configure.sh                  # Interactive environment setup
./test-all.sh                   # Smart test runner with caching
./test-all.sh --no-cache        # Force run all tests
./test-all.sh api health        # Run specific test categories
```

**See [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) for complete automation documentation.**

## 🔍 Backend Verification

All backend services (invisible components) are automatically validated:

```bash
# Run comprehensive backend validation
make validate

# Test all API endpoints
make test-api

# Full validation (infrastructure + API)
make test-all
```

See [BACKEND_VERIFICATION.md](BACKEND_VERIFICATION.md) for complete details on what gets tested.

## 📖 Documentation

### Getting Started

- **[Quick Start Guide](DEPLOY_NOW.md)** - Get running in minutes
- **[Automation Guide](AUTOMATION_GUIDE.md)** - Eliminate repetitive tasks ⚡ **NEW!**
- **[Onboarding Guide](ONBOARDING.md)** - New to the project? Start here
- **[Deployment Guide](DEPLOYMENT.md)** - Comprehensive deployment documentation
- **[API Reference](API_REFERENCE.md)** - Complete API documentation

### Governance & Standards

- **[Governance Framework](GOVERNANCE.md)** - Decision-making, roles, and accountability
- **[Stability Mandate](STABILITY_MANDATE.md)** - Our commitment to excellence
- **[Definition of Done](DEFINITION_OF_DONE.md)** - Completion criteria for all work
- **[Coding Standards](CODING_STANDARDS.md)** - Code style and quality guidelines
- **[Build Standards](BUILD_STANDARDS.md)** - CI/CD and deployment requirements
- **[Metrics Dashboard](METRICS_DASHBOARD.md)** - KPIs and performance tracking
- **[Stability Audit Checklist](STABILITY_AUDIT_CHECKLIST.md)** - Quarterly audit process

### Contributing

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute effectively
- **[Security Policy](SECURITY.md)** - Security practices and reporting
- **[Code of Conduct](CODE_OF_CONDUCT.md)** - Community guidelines

### Additional Resources

- **[Architecture](ARCHITECTURE.md)** - System architecture and design
- **[Implementation Status](IMPLEMENTATION_COMPLETE.md)** - Implementation checklist

## 🔍 Service Details

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **IPFS Gateway**: http://localhost:8080

### 4. Run Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## Architecture

### System Components

```
┌─────────────────────────────────────────────┐
│              Frontend (Next.js)             │
│     File Upload, Dashboard, Contributions   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│           Backend API (FastAPI)             │
│  Contributions, Users, Verifications        │
└─────┬─────────────────────┬─────────────────┘
      │                     │
      ▼                     ▼
┌──────────┐        ┌──────────────┐
│   IPFS   │        │   RabbitMQ   │
│ Storage  │        │ Message Queue│
└──────────┘        └──────┬───────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Agent-Alpha   │
                  │ AI Verification│
                  └────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  PostgreSQL    │
                  │   Database     │
                  └────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │Smart Contracts │
                  │   (Ethereum)   │
                  └────────────────┘
```

## API Endpoints

### Contributions

- `POST /api/v1/contributions/` - Upload a new contribution
- `GET /api/v1/contributions/` - List all contributions
- `GET /api/v1/contributions/{id}` - Get contribution details
- `GET /api/v1/contributions/{id}/status` - Get verification status
- `GET /api/v1/contributions/{id}/file` - Download file

### Users

- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{address}` - Get user by address
- `GET /api/v1/users/{address}/contributions` - Get user contributions
- `GET /api/v1/users/{address}/rewards` - Get user rewards
- `GET /api/v1/users/{address}/stats` - Get user statistics

### Verifications

- `POST /api/v1/verifications/` - Submit verification (agents only)
- `GET /api/v1/verifications/contribution/{id}` - Get contribution verifications

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL, MongoDB, Redis
- **Storage**: IPFS
- **Message Queue**: RabbitMQ
- **AI/ML**: OpenAI GPT-4, LangChain
- **Blockchain**: Solidity, Hardhat, OpenZeppelin
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **DevOps**: Docker, Docker Compose

## Project Structure

```
nwu-protocol/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── models.py    # Database models
│   │   ├── schemas.py   # Pydantic schemas
│   │   ├── services/    # IPFS, RabbitMQ services
│   │   └── main.py      # FastAPI app
│   └── requirements.txt
├── agent-alpha/          # AI verification agent
│   ├── app/
│   │   ├── verifier.py  # AI verification logic
│   │   └── main.py      # RabbitMQ consumer
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── app/            # App router pages
│   └── package.json
├── contracts/          # Smart contracts
│   ├── contracts/     # Solidity files
│   ├── scripts/       # Deployment scripts
│   └── hardhat.config.js
└── docker-compose.yml  # Docker orchestration
```

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Agent Development

```bash
cd agent-alpha
pip install -r requirements.txt
python -m app.main
```

### Smart Contracts

```bash
cd contracts
npm install
npx hardhat compile
npx hardhat test
npx hardhat node  # Start local blockchain
npx hardhat run scripts/deploy.js --network localhost
```

## 🏛️ Governance & Quality

NWU Protocol follows a comprehensive governance model to ensure stability and excellence:

- **Tiger Team**: Elite cross-functional squad with authority to enforce standards
- **Code Owners**: All changes require approval from designated code owners
- **Quality Gates**: Automated checks enforce coding standards, testing, and security
- **Metrics-Driven**: KPIs tracked bi-weekly with transparent dashboards
- **Quarterly Audits**: Regular stability audits to prevent regression

See [Governance Framework](GOVERNANCE.md) for complete details.

## 📊 Our Standards

- ✅ **80%+ Test Coverage** across all components
- ✅ **Zero Critical Vulnerabilities** in production
- ✅ **95%+ Deployment Success Rate**
- ✅ **< 24h Lead Time** from commit to production
- ✅ **99.9% System Uptime** target
- ✅ **100% Code Review** requirement
- ✅ **Comprehensive Security Scanning** in CI/CD
- ✅ **Signed and Traceable Builds**

View real-time metrics in our [Metrics Dashboard](METRICS_DASHBOARD.md).

## Testing

```bash
# Backend tests
cd backend
pytest

# Smart contract tests
cd contracts
npx hardhat test
```

## Deployment

See [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) for detailed deployment instructions.

## Documentation

- [Architecture](ARCHITECTURE.md) - System architecture and design
- [Master Control](MASTER_CONTROL.md) - Complete system status and commands
- [Quickstart](QUICKSTART.md) - Quick setup guide
- [Contributing](CONTRIBUTING.md) - How to contribute

## Project Status

- ✅ Backend API (Complete)
- ✅ Agent-Alpha AI Verification (Complete)
- ✅ Frontend UI (Complete)
- ✅ Smart Contracts (Complete)
- ✅ Docker Infrastructure (Complete)
- ✅ Database Models (Complete)
- ✅ IPFS Integration (Complete)
- ✅ RabbitMQ Messaging (Complete)
- 🔄 Additional testing and documentation
- 📋 [Project Roadmap](https://github.com/Garrettc123/nwu-protocol/issues/1)

## License

MIT
