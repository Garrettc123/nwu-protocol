# Business Cooperation Lead Agent — Guide

The **Business Cooperation Lead Agent** is an autonomous business manager that
orchestrates 12 specialised agent types, delegates work via a priority-based task
queue, and integrates with both RabbitMQ (async messaging) and the NWU Protocol
REST API (persistent state).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [12 Specialised Agent Types](#12-specialised-agent-types)
3. [Environment Variables](#environment-variables)
4. [Running with Docker Compose](#running-with-docker-compose)
5. [REST API Reference — Business Agents](#rest-api-reference--business-agents)
6. [REST API Reference — Business Tasks](#rest-api-reference--business-tasks)
7. [RabbitMQ Integration](#rabbitmq-integration)
8. [Priority Queue Levels](#priority-queue-levels)
9. [Validation Script](#validation-script)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  BusinessLeadAgent (main.py)                │
│  ┌─────────────────┐      ┌──────────────────────────────┐  │
│  │  AgentFactory   │      │      TaskCoordinator         │  │
│  │  (agent_factory │◄─────│  (task_coordinator.py)       │  │
│  │   .py)          │      │  Priority queue  1-10 levels │  │
│  │  12 agent types │      │  Concurrent execution        │  │
│  │  Lifecycle mgmt │      │  Load balancing              │  │
│  └─────────────────┘      └──────────────────────────────┘  │
│           ▲                          ▲                       │
│           │                          │                       │
│  ┌────────┴──────────┐   ┌───────────┴──────────────────┐   │
│  │   RabbitMQ        │   │   NWU Backend REST API       │   │
│  │   (task queue)    │   │   /api/v1/business-agents/   │   │
│  │   (result queue)  │   │   /api/v1/business-tasks/    │   │
│  └───────────────────┘   └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key files**:

| File                                          | Purpose                                         |
| --------------------------------------------- | ----------------------------------------------- |
| `agent-business-lead/app/main.py`             | Entry point; RabbitMQ consumer; orchestrator    |
| `agent-business-lead/app/agent_factory.py`    | Creates & manages the 12 agent types            |
| `agent-business-lead/app/task_coordinator.py` | Priority queue, load balancer, execution engine |
| `backend/app/api/business_agents.py`          | REST endpoints for agents & tasks               |
| `backend/app/models.py`                       | `BusinessAgent` and `BusinessTask` DB models    |
| `Dockerfile.business-lead`                    | Container image for the lead agent              |

---

## 12 Specialised Agent Types

| #   | Type               | `agent_type` value   | Domain responsibilities                                              |
| --- | ------------------ | -------------------- | -------------------------------------------------------------------- |
| 1   | Sales              | `sales`              | Lead qualification, pipeline management, deal tracking, forecasting  |
| 2   | Marketing          | `marketing`          | Campaign creation, content strategy, brand analysis, SEO             |
| 3   | Operations         | `operations`         | Process optimisation, resource allocation, logistics, KPI tracking   |
| 4   | Finance            | `finance`            | Budget analysis, forecasting, expense approval, reporting            |
| 5   | Customer Service   | `customer_service`   | Ticket resolution, escalation, feedback analysis, SLA tracking       |
| 6   | Research           | `research`           | Market analysis, competitive intelligence, trend detection           |
| 7   | Development        | `development`        | Feature planning, code review, technical debt, architecture          |
| 8   | QA                 | `qa`                 | Test planning, bug triage, quality metrics, regression testing       |
| 9   | HR                 | `hr`                 | Recruitment, onboarding, performance reviews, policy management      |
| 10  | Legal              | `legal`              | Contract review, compliance checks, risk assessment, IP management   |
| 11  | Strategy           | `strategy`           | OKR planning, partnership evaluation, growth analysis, roadmapping   |
| 12  | Project Management | `project_management` | Sprint planning, risk tracking, stakeholder updates, dependency mgmt |

---

## Environment Variables

Configure the `business-lead` Docker service via these environment variables:

| Variable                 | Default                            | Description                                                |
| ------------------------ | ---------------------------------- | ---------------------------------------------------------- |
| `RABBITMQ_URL`           | `amqp://guest:guest@rabbitmq:5672` | RabbitMQ AMQP connection URL                               |
| `BACKEND_URL`            | `http://backend:8000`              | NWU Protocol backend base URL                              |
| `MAX_CONCURRENT_AGENTS`  | `20`                               | Maximum simultaneous agent instances                       |
| `AGENT_CREATION_ENABLED` | `true`                             | Allow dynamic agent creation at runtime                    |
| `AUTO_DELEGATE`          | `true`                             | Automatically dispatch queued tasks to agents              |
| `MAX_CONCURRENT_TASKS`   | `10`                               | Maximum tasks executing concurrently                       |
| `LOG_LEVEL`              | `INFO`                             | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Running with Docker Compose

```bash
# Start all services including business-lead
docker compose up -d business-lead

# Override env vars at runtime
MAX_CONCURRENT_AGENTS=50 AUTO_DELEGATE=true docker compose up -d business-lead

# View logs
docker compose logs -f business-lead
```

---

## REST API Reference — Business Agents

Base URL: `/api/v1/business-agents`

### Create an agent

```
POST /api/v1/business-agents/
```

**Request body** (JSON):

```json
{
  "agent_type": "sales",
  "name": "Sales Lead Agent",
  "description": "Handles inbound lead qualification",
  "capabilities": ["lead_qualification", "pipeline_management"],
  "config": { "max_daily_leads": 100 }
}
```

**Response** `201 Created`:

```json
{
  "id": 1,
  "agent_id": "business-sales-a3f7b2c1",
  "agent_type": "sales",
  "status": "idle",
  "name": "Sales Lead Agent",
  "description": "Handles inbound lead qualification",
  "capabilities": ["lead_qualification", "pipeline_management"],
  "config": { "max_daily_leads": 100 },
  "tasks_completed": 0,
  "tasks_failed": 0,
  "last_active_at": null,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00",
  "terminated_at": null
}
```

### List agents

```
GET /api/v1/business-agents/?agent_type=sales&status=idle&skip=0&limit=50
```

Query parameters:

| Param        | Type   | Description                                                   |
| ------------ | ------ | ------------------------------------------------------------- |
| `agent_type` | string | Filter by one of the 12 agent types                           |
| `status`     | string | Filter by `idle`, `active`, `busy`, `paused`, or `terminated` |
| `skip`       | int    | Pagination offset (default 0)                                 |
| `limit`      | int    | Page size (default 50, max 200)                               |

### Get a single agent

```
GET /api/v1/business-agents/{agent_id}
```

### Update an agent

```
PATCH /api/v1/business-agents/{agent_id}
```

**Request body** (all fields optional):

```json
{
  "name": "Renamed Agent",
  "status": "paused",
  "capabilities": ["lead_qualification"],
  "config": {}
}
```

### Terminate an agent

```
DELETE /api/v1/business-agents/{agent_id}
```

Soft-deletes the agent by setting its status to `terminated`. Returns `204 No Content`.

---

## REST API Reference — Business Tasks

Base URL: `/api/v1/business-tasks`

### Create a task

```
POST /api/v1/business-tasks/
```

**Request body** (JSON):

```json
{
  "title": "Qualify inbound lead from Acme Corp",
  "description": "Lead submitted via web form",
  "task_type": "qualify_lead",
  "required_agent_type": "sales",
  "priority": 2,
  "task_data": {
    "lead_id": "lead-9f2a",
    "company": "Acme Corp",
    "lead_score": 78
  },
  "max_retries": 3
}
```

**Priority values**: `1` (critical) → `10` (idle)

**Response** `201 Created`:

```json
{
  "id": 42,
  "task_id": "task-8b3c1a2d...",
  "title": "Qualify inbound lead from Acme Corp",
  "task_type": "qualify_lead",
  "required_agent_type": "sales",
  "agent_id": null,
  "status": "queued",
  "priority": 2,
  "task_data": { "lead_id": "lead-9f2a", "company": "Acme Corp", "lead_score": 78 },
  "result_data": null,
  "error_message": null,
  "retry_count": 0,
  "max_retries": 3,
  "scheduled_at": null,
  "started_at": null,
  "completed_at": null,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

### List tasks

```
GET /api/v1/business-tasks/?status=queued&required_agent_type=sales&priority=2&skip=0&limit=50
```

Results are ordered by **priority ascending** (highest first), then by `created_at`.

### Get a single task

```
GET /api/v1/business-tasks/{task_id}
```

### Update a task

```
PATCH /api/v1/business-tasks/{task_id}
```

**Request body** (all fields optional):

```json
{
  "status": "completed",
  "result_data": { "score": 92, "next_step": "schedule_demo" }
}
```

### Cancel a task

```
DELETE /api/v1/business-tasks/{task_id}
```

Cancels a `queued` or `in_progress` task. Returns `204 No Content`.

### Delegate a task to an agent

```
POST /api/v1/business-tasks/{task_id}/delegate
```

**Request body** (JSON):

```json
{ "agent_id": "business-sales-a3f7b2c1" }
```

---

## RabbitMQ Integration

The lead agent consumes from queue **`business_tasks`** and publishes results to **`business_results`**.

### Task message format

```json
{
  "task_type": "qualify_lead",
  "title": "Qualify lead from Acme Corp",
  "task_data": {
    "lead_id": "lead-9f2a",
    "lead_score": 78
  },
  "priority": 2,
  "required_agent_type": "sales"
}
```

All fields except `task_type` are optional. When `required_agent_type` is omitted the
agent type is inferred from keywords in `task_type`.

### Result message format

```json
{
  "task_id": "task-8b3c1a2d...",
  "result": {
    "action": "qualify_lead",
    "result": "lead_qualified",
    "score": 78,
    "next_step": "schedule_demo"
  }
}
```

---

## Priority Queue Levels

| Level | Constant                | Meaning                              |
| ----- | ----------------------- | ------------------------------------ |
| 1     | `PRIORITY_CRITICAL`     | Immediate action required            |
| 2     | `PRIORITY_HIGH`         | Urgent business impact               |
| 3     | `PRIORITY_ELEVATED`     | Time-sensitive                       |
| 4     | `PRIORITY_ABOVE_NORMAL` | Important but not urgent             |
| 5     | `PRIORITY_NORMAL`       | Default priority                     |
| 6     | `PRIORITY_BELOW_NORMAL` | Can wait                             |
| 7     | `PRIORITY_LOW`          | Low business impact                  |
| 8     | `PRIORITY_BACKGROUND`   | Batch / overnight processing         |
| 9     | `PRIORITY_DEFERRED`     | Deferred until capacity available    |
| 10    | `PRIORITY_IDLE`         | Lowest; run only when queue is empty |

---

## Validation Script

Run `./validate_business_agents.sh` to verify the complete system is operational:

```bash
chmod +x validate_business_agents.sh
./validate_business_agents.sh
```

The script checks:

- Backend health endpoint
- Agent API endpoints (list, create, get, update, terminate)
- Task API endpoints (list, create, get, update, delegate, cancel)
- All 12 agent types can be created and retrieved
