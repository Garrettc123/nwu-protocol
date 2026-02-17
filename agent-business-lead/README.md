# Business Cooperation Lead Agent

> **Autonomous AI-powered business management system that runs your business 24/7**

## What This Does

The Business Cooperation Lead Agent is your autonomous business manager. It:

- 🤖 **Runs continuously** - Operates 24/7, even when you're not around
- 🎯 **Handles everything** - Manages all aspects of your business operations
- 🔧 **Creates agents** - Dynamically spawns specialized agents for specific tasks
- 🧠 **Makes decisions** - Intelligently delegates tasks based on priority and type
- 📊 **Tracks everything** - Monitors all operations and provides status updates

## Quick Start

### 1. Deploy the System

```bash
./deploy.sh
```

This starts the Business Lead Agent along with all other NWU Protocol services.

### 2. Submit a Task

```bash
curl -X POST http://localhost:8000/api/v1/business-tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-001",
    "task_type": "lead_generation",
    "category": "sales",
    "priority": 8,
    "task_data": {
      "target_market": "technology"
    }
  }'
```

### 3. Check Status

```bash
# View all agents
curl http://localhost:8000/api/v1/business-agents/

# View all tasks
curl http://localhost:8000/api/v1/business-tasks/
```

## Architecture

```
Business Cooperation Lead Agent
        ↓
    Agent Factory
        ↓
    ┌───┴────────────────┬──────────────┬─────────────┐
    ↓                    ↓              ↓             ↓
Sales Agent      Marketing Agent   Operations    Finance
                                    Agent         Agent
```

## Agent Types

The system includes 12 specialized agent types:

| Agent Type | Capabilities | Use Cases |
|------------|--------------|-----------|
| **Sales** | Lead generation, client outreach, deal closing | Finding prospects, closing deals |
| **Marketing** | Content creation, campaigns, social media | Marketing automation |
| **Operations** | Process optimization, resource management | Workflow automation |
| **Finance** | Budget management, reporting, forecasting | Financial operations |
| **Customer Service** | Support tickets, issue resolution | Customer support |
| **Research** | Market research, competitive analysis | Business intelligence |
| **Development** | Code development, bug fixing | Software development |
| **QA** | Testing, quality control | Quality assurance |
| **HR** | Recruitment, onboarding, training | Human resources |
| **Legal** | Contract review, compliance | Legal compliance |
| **Strategy** | Strategic planning, goal setting | Business strategy |
| **Project Management** | Task tracking, coordination | Project coordination |

## Configuration

Set these environment variables in your `.env` file or `docker-compose.yml`:

```bash
# Maximum number of concurrent agents
MAX_CONCURRENT_AGENTS=10

# Enable dynamic agent creation
AGENT_CREATION_ENABLED=true

# Enable automatic task delegation
AUTO_DELEGATE=true

# Priority threshold for urgent tasks
PRIORITY_THRESHOLD=7.0
```

## API Endpoints

### Business Agents

- `GET /api/v1/business-agents/` - List all agents
- `GET /api/v1/business-agents/{agent_id}` - Get agent details
- `POST /api/v1/business-agents/` - Create agent manually
- `PUT /api/v1/business-agents/{agent_id}/status` - Update agent status
- `DELETE /api/v1/business-agents/{agent_id}` - Terminate agent

### Business Tasks

- `GET /api/v1/business-tasks/` - List all tasks
- `GET /api/v1/business-tasks/{task_id}` - Get task details
- `POST /api/v1/business-tasks/` - Submit a new task
- `POST /api/v1/business-tasks/results` - Submit task results

## Task Examples

### Sales: Lead Generation

```json
{
  "task_type": "lead_generation",
  "category": "sales",
  "priority": 8,
  "task_data": {
    "target_market": "enterprise",
    "criteria": {"revenue": "10M+"}
  }
}
```

### Marketing: Campaign Launch

```json
{
  "task_type": "campaign_management",
  "category": "marketing",
  "priority": 9,
  "task_data": {
    "campaign_id": "summer-2024",
    "action": "launch"
  }
}
```

### Operations: Process Optimization

```json
{
  "task_type": "process_optimization",
  "category": "operations",
  "priority": 7,
  "task_data": {
    "process_name": "order_fulfillment"
  }
}
```

## Monitoring

### View Logs

```bash
docker logs -f nwu-agent-business-lead
```

### Check System Status

The agent logs operational status every minute:

```
================================================================================
BUSINESS OPERATIONS STATUS
Active Tasks: 3
Completed Tasks: 45
Total Agents: 8
Available Capacity: 2
Tasks Processed: 45
Agents Created: 8
Uptime: 3600s
================================================================================
```

## File Structure

```
agent-business-lead/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration
│   ├── main.py                # Business Lead Agent
│   ├── agent_factory.py       # Agent Factory
│   ├── task_coordinator.py    # Task Coordinator
│   └── agents/                # Specialized Agents
│       ├── sales_agent.py
│       ├── marketing_agent.py
│       ├── operations_agent.py
│       ├── finance_agent.py
│       ├── customer_service_agent.py
│       ├── research_agent.py
│       ├── development_agent.py
│       ├── qa_agent.py
│       ├── hr_agent.py
│       ├── legal_agent.py
│       ├── strategy_agent.py
│       └── pm_agent.py
└── requirements.txt
```

## How It Works

1. **Task Submission**: Tasks are submitted via API or RabbitMQ
2. **Task Analysis**: Business Lead Agent analyzes each task
3. **Agent Selection**: Determines the best agent type for the task
4. **Agent Creation**: Creates a new agent if needed
5. **Task Delegation**: Assigns the task to the selected agent
6. **Execution**: Agent executes the task
7. **Result Reporting**: Results are stored and reported back
8. **Monitoring**: Continuous monitoring of all operations

## Troubleshooting

### Agent Not Starting

Check logs:
```bash
docker logs nwu-agent-business-lead
```

Verify RabbitMQ is running:
```bash
docker ps | grep rabbitmq
```

### Tasks Not Processing

1. Check task queue:
```bash
docker exec nwu-rabbitmq rabbitmqctl list_queues
```

2. Verify task format is correct

3. Check agent capacity is not maxed out

### No Agents Being Created

Ensure `AGENT_CREATION_ENABLED=true` in your configuration.

## Performance

- **Task Throughput**: Handles multiple concurrent tasks
- **Agent Capacity**: Configurable up to 50+ concurrent agents
- **Response Time**: Average task delegation < 100ms
- **Uptime**: Designed for 24/7 operation

## Security

- All API endpoints should be secured with authentication
- Task data is validated before processing
- Agents run in isolated containers
- All operations are logged for audit

## Learn More

- [Complete User Guide](../BUSINESS_AGENT_GUIDE.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [API Reference](../API_REFERENCE.md)
- [Main README](../README.md)

## License

MIT - See [LICENSE](../LICENSE) for details

---

**Your business runs automatically, even while you sleep.** 🚀
