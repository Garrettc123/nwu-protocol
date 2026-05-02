# CLAUDE.md — NWU Protocol

Comprehensive guide for AI assistants working in this repository.

---

## Project Overview

**NWU Protocol** (Neural Workflow Unification) is a decentralized AI agent coordination and contribution-verification platform. Contributors submit work (code, datasets, documents), AI agents verify quality and originality, and verified contributors earn NWU tokens via smart contracts.

**Stack at a glance:**
- Backend: Python / FastAPI + SQLAlchemy (PostgreSQL) + MongoDB + Redis + RabbitMQ
- Frontend: Next.js 16 / React 19 / TailwindCSS / ethers.js v6
- AI Agents: Python async (aio-pika), OpenAI GPT-4 via LangChain
- Smart Contracts: Solidity / Hardhat / OpenZeppelin (Ethereum)
- Infrastructure: Docker Compose (dev) / Kubernetes (prod)

---

## Repository Layout

```
nwu-protocol/
├── backend/                  # Primary FastAPI application (production backend)
│   ├── app/
│   │   ├── main.py           # FastAPI app, lifespan startup/shutdown
│   │   ├── config.py         # Pydantic Settings from env vars
│   │   ├── database.py       # SQLAlchemy engine + get_db() dependency
│   │   ├── models.py         # All ORM models (User, Contribution, Verification…)
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── api/              # Route handlers (one file per domain)
│   │   │   ├── contributions.py
│   │   │   ├── users.py
│   │   │   ├── verifications.py
│   │   │   ├── auth.py
│   │   │   ├── payments.py
│   │   │   ├── referrals.py
│   │   │   ├── agents.py
│   │   │   ├── business_agents.py
│   │   │   ├── halt_process.py
│   │   │   ├── admin.py
│   │   │   └── websocket.py
│   │   ├── services/         # Business logic (rabbitmq, redis, ipfs, orchestrator…)
│   │   └── utils/
│   ├── alembic/              # Database migrations
│   ├── tests/                # pytest tests (conftest uses SQLite in-memory)
│   └── requirements.txt
│
├── agent-alpha/              # AI verification agent (RabbitMQ consumer)
│   └── app/
│       ├── main.py           # AgentAlpha class, IPFS + RabbitMQ consumer
│       ├── verifier.py       # GPT-4 code/dataset/document analysis
│       └── config.py
│
├── agent-business-lead/      # Business cooperation lead agent
│   └── app/
│       ├── main.py           # BusinessLeadAgent, task routing
│       ├── agent_factory.py  # Creates/manages 12 typed business agents
│       └── task_coordinator.py
│
├── nwu_protocol/             # Standalone Python library (pip-installable)
│   ├── api/                  # contributions, payments, users, verifications
│   ├── core/
│   ├── models/               # Pydantic domain models
│   └── services/             # ContributionManager, VerificationEngine, etc.
│
├── frontend/                 # Next.js 16 App Router frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   ├── hooks/
│   └── lib/
│
├── contracts/                # Solidity smart contracts + Hardhat
│   ├── contracts/
│   │   ├── NWUToken.sol      # ERC-20 token
│   │   ├── VerificationRegistry.sol
│   │   └── RewardDistribution.sol
│   ├── test/
│   └── scripts/
│
├── tests/                    # Top-level Python tests for nwu_protocol library
├── .github/workflows/        # GitHub Actions CI/CD
├── docker-compose.yml        # Dev environment (7 services)
├── docker-compose.prod.yml   # Production compose
├── Makefile                  # Common dev commands
└── pyproject.toml            # Python package config + tool settings
```

---

## Architecture

### Data Flow

```
User → Frontend → REST API (FastAPI)
                      ↓
                  PostgreSQL (state) + MongoDB (documents)
                      ↓
                  RabbitMQ → agent-alpha (AI verification)
                                  ↓ (via IPFS retrieval + GPT-4)
                  Backend ← verification result
                      ↓
                  Reward calculation → Ethereum smart contract
                      ↓
                  WebSocket → Frontend (real-time notification)
```

### Key Services (docker-compose)

| Container | Port | Purpose |
|-----------|------|---------|
| `nwu-backend` | 8000 | FastAPI application |
| `nwu-agent-alpha` | — | AI verification consumer |
| `nwu-business-lead` | — | Business task orchestrator |
| `nwu-postgres` | 5432 | Primary relational DB |
| `nwu-mongodb` | 27017 | Document storage |
| `nwu-redis` | 6379 | Cache + sessions |
| `nwu-rabbitmq` | 5672/15672 | Message bus |
| `nwu-ipfs` | 5001/8080 | Decentralized file storage |

### RabbitMQ Queues

- `contributions.new` — new submissions from backend
- `verifications.pending` — consumed by agent-alpha
- `verifications.complete` — results back to backend
- `rewards.pending` / `rewards.distributed` — token payout pipeline
- `business_tasks` / `business_results` — business lead agent queues

### Business Agent Types (12 types)

`sales`, `marketing`, `operations`, `finance`, `customer_service`, `research`, `development`, `qa`, `hr`, `legal`, `strategy`, `project_management`

---

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (frontend and contracts)
- Python 3.10+ (backend and agents)

### Quick Start

```bash
# 1. Copy env and fill in secrets
cp .env.example .env

# 2. Start all services
make start          # or: docker-compose up -d

# 3. Run migrations
make migrate        # alembic upgrade head inside backend container

# 4. Frontend dev server
make frontend       # cd frontend && npm run dev

# 5. Check health
make health         # curl http://localhost:8000/health
```

### Development-Only Setup (no Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Smart contracts
cd contracts
npm install
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```

---

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `MONGO_URL` | MongoDB connection string |
| `REDIS_URL` | Redis connection string |
| `RABBITMQ_URL` | RabbitMQ AMQP URL |
| `JWT_SECRET_KEY` | JWT signing key (auto-generated if absent; set explicitly for prod) |
| `OPENAI_API_KEY` | Required for agent-alpha AI verification |
| `STRIPE_API_KEY` | Stripe payments integration |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook validation |
| `ETH_RPC_URL` | Ethereum RPC endpoint |
| `CONTRACT_ADDRESS` | Deployed NWU contract address |
| `ADMIN_ADDRESSES` | Comma-separated Ethereum addresses with admin access |

Agent-specific env (docker-compose sets these automatically):
- `BACKEND_URL`, `MAX_CONCURRENT_AGENTS`, `AGENT_CREATION_ENABLED`, `AUTO_DELEGATE`

---

## Running Tests

### Backend (pytest)

```bash
cd backend
pytest                        # all tests
pytest tests/test_api.py      # specific file
pytest --cov=app --cov-report=html  # with coverage
```

Tests use SQLite in-memory via `conftest.py` — no running Postgres needed.

### Top-level library tests

```bash
pytest tests/                 # nwu_protocol library tests
```

### Smart contracts (Hardhat)

```bash
cd contracts
npx hardhat compile
npx hardhat test
```

### Full system validation

```bash
make test-all    # validate-backend.sh + test-api-endpoints.sh
make test        # backend pytest + contract tests
```

---

## Makefile Commands

```
make start          Start all Docker services
make stop           Stop all services
make restart        Restart all services
make logs           Tail all container logs
make status         Show docker-compose ps
make health         Hit /health endpoint
make validate       Run validate-backend.sh
make test-api       Run test-api-endpoints.sh
make test-all       Full system validation
make clean          Remove containers + volumes (prompts for confirmation)
make test           pytest + hardhat test
make build          Build Docker images
make frontend       Start Next.js dev server
make migrate        alembic upgrade head
make contracts      Compile + deploy contracts to localhost
make deploy-prod    Production deploy with docker-compose.prod.yml
make backup         Dump Postgres + MongoDB to ./backups/
make pr-list        List open PRs
make pr-merge PR=N  Merge a specific PR
make pr-auto        Auto-merge all ready PRs
```

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info |
| GET | `/health` | Service health check (DB, IPFS, RabbitMQ, Redis) |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |
| POST | `/api/v1/contributions/` | Upload new contribution |
| GET | `/api/v1/contributions/{id}` | Get contribution details |
| GET | `/api/v1/users/{address}` | Get user by Ethereum address |
| POST | `/api/v1/auth/connect` | Web3 wallet auth |
| POST | `/api/v1/verifications/` | Submit verification result (agent use) |
| POST | `/api/v1/payments/` | Payment endpoints |
| POST | `/api/v1/business-tasks/` | Create business task |
| PATCH | `/api/v1/business-tasks/{id}` | Update task status |
| POST | `/api/v1/halt-process/{id}` | Halt a contribution's process |
| WS | `/ws` | WebSocket for real-time updates |

---

## Database Models (PostgreSQL via SQLAlchemy)

Key models in `backend/app/models.py`:

- **User** — Ethereum address, reputation score, subscription, referral tracking
- **Contribution** — IPFS hash, file type, status, quality score, halt/resume fields
- **Verification** — Per-agent vote scores (quality, originality, security, documentation)
- **Reward** — Token distribution record with tx hash
- **Subscription** / **Payment** / **UsageRecord** / **APIKey** — Stripe billing
- **Referral** / **ReferralCode** / **ReferralEvent** — Affiliate programme
- **EngagementHistory** / **ProcessIteration** / **WorkflowExecution** — Audit trails
- **BusinessAgent** / **BusinessTask** — Business cooperation lead system
- **KnowledgeThread** — Perplexity integration context

Contribution status values: `pending`, `verifying`, `verified`, `rejected`, `halted`, `paused`, `resumed`

---

## Coding Standards

### Python

- Follow PEP 8 and Google Python Style Guide
- `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- Type hints on all function signatures
- Google-style docstrings for public methods
- Format with **Black** (`line-length = 100` per `pyproject.toml`)
- Sort imports with **isort** (`profile = "black"`)
- Lint with **Flake8**, type-check with **MyPy**
- Specific exception handling — no bare `except`
- Use `async/await` throughout; never block the event loop

### TypeScript / JavaScript

- Airbnb style guide base
- `camelCase` vars/functions, `PascalCase` classes/components, `UPPER_SNAKE_CASE` constants
- No `any` types; use `unknown` when truly unknown
- `strict: true` in tsconfig
- Format with **Prettier**, lint with **ESLint**
- Always `async/await`; use `Promise.all()` for concurrent ops
- Explicit error handling — never silent failures

### Solidity

- Solidity style guide; OpenZeppelin contracts for standard patterns
- Checks-Effects-Interactions pattern for all state-mutating functions
- Emit events for all state changes
- `UPPER_SNAKE_CASE` constants, `camelCase` functions, `PascalCase` contracts/events
- Test coverage ≥ 95%; mandatory security audit before mainnet

### General

- Minimum 80% test coverage overall; 100% on critical paths
- No hardcoded secrets — always use environment variables
- Parameterized queries only (no string-concatenated SQL)
- Validate all user inputs at API boundaries

---

## Commit Convention

Follows **Conventional Commits** (see `.conventional-commits.json`):

```
feat: add referral programme endpoint
fix: prevent duplicate verification submissions
docs: update API reference for halt-process
refactor: extract reward calculation to service layer
test: add coverage for business agent factory
chore: bump stripe sdk to 7.9.0
security: rotate JWT secret handling
```

Types and their changelog sections: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `security`.

---

## CI/CD

Workflows live in `.github/workflows/`. The primary pipeline is `ci.yml`:

1. **lint-and-security** — ESLint, Prettier check, `npm audit`
2. **test-backend** — backend npm/pytest tests
3. **test-frontend** — frontend build + tests
4. **test-contracts** — `hardhat compile` + `hardhat test`
5. **test-ai-agents** — Python agent tests
6. **ci-complete** — summary gate

Triggers: push/PR to `main` or `develop`, plus a daily cron at 06:41 UTC.

Auto-merge workflows (`auto-merge.yml`, `auto-merge-copilot.yml`) can merge Dependabot and Copilot PRs automatically when checks pass.

---

## Smart Contracts

Location: `contracts/`

| Contract | Purpose |
|----------|---------|
| `NWUToken.sol` | ERC-20 token (1B initial supply) |
| `VerificationRegistry.sol` | On-chain verification records |
| `RewardDistribution.sol` | Token payout to contributors |
| `NWUProtocol.sol` | Core protocol logic |
| `NWUGovernance.sol` | DAO governance |
| `NWUDataToken.sol` | Data contribution token |

```bash
# Compile
cd contracts && npx hardhat compile

# Test
npx hardhat test

# Deploy to local node
npx hardhat node               # terminal 1
npx hardhat run scripts/deploy.js --network localhost  # terminal 2

# Deploy to Sepolia testnet
npx hardhat run scripts/deploy.js --network sepolia
```

---

## Agent Architecture

### agent-alpha (Verification Agent)

- Consumes from `verifications.pending` queue
- Fetches file content from IPFS
- Runs GPT-4 analysis across four criteria: code quality (40%), originality (30%), security (20%), documentation (10%)
- Posts `POST /api/v1/verifications/` with scores + reasoning

### agent-business-lead (Business Cooperation Lead)

- Consumes from `business_tasks` queue
- Infers required agent type from task keywords (12 types)
- Uses `AgentFactory` to create/reuse typed agents
- Delegates via `TaskCoordinator` with configurable concurrency
- Persists tasks + results to backend REST API
- Publishes results to `business_results` queue

### orchestrator (in-process)

- Lives inside backend (`backend/app/services/agent_orchestrator.py`)
- Initialized on app startup; shut down gracefully on exit

---

## Subscription / Payment System

Three tiers managed via Stripe:

| Tier | Rate Limit |
|------|-----------|
| Free | 100 req/day |
| Pro | 10,000 req/day |
| Enterprise | 100,000 req/day |

Key models: `Subscription`, `Payment`, `UsageRecord`, `APIKey`.
Webhook endpoint handles Stripe events for subscription lifecycle.

---

## Referral / Affiliate Programme

- Users receive a `ReferralCode` (10-char alphanumeric)
- On referee signup: `ReferralEvent` (type `signup`) + reputation bonuses (referrer +10, referee +5)
- On referee subscription: `ReferralEvent` (type `subscription`) + NWU token reward
- After 10 conversions: `User.is_affiliate = True`, unlocking revenue-share (10%)
- Constants in `models.py`: `NWU_REWARD_PER_REFERRAL = 50.0`, `SUBSCRIPTION_REWARD_PERCENT = 5.0`

---

## Common Pitfalls

1. **JWT secret auto-generation** — `config.py` generates a random `JWT_SECRET_KEY` if unset. Sessions won't survive restarts. Always set `JWT_SECRET_KEY` explicitly in production.
2. **Dual databases** — PostgreSQL is the primary ORM target. MongoDB is also connected (for document storage). Don't conflate the two.
3. **CORS** — `main.py` restricts origins to `localhost:3000` and `localhost:8000`. Update `allow_origins` for production deployment.
4. **Database migrations** — Use Alembic (`make migrate`). Do not use `Base.metadata.create_all()` in production; it won't apply incremental changes.
5. **Agent queue names** — agent-alpha listens on `verifications.pending`. Ensure the backend publishes to exactly that queue name.
6. **IPFS connection** — agent-alpha will proceed with empty content if IPFS is unreachable; verifications will silently fail. Check IPFS container health first.
7. **Test isolation** — backend tests use SQLite; some features (e.g., PostgreSQL-specific types) may behave differently. Run full integration tests against the Docker stack for production confidence.
