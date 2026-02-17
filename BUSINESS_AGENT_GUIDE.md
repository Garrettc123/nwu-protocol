# Business Cooperation Agent System

## Overview

The **Business Cooperation Lead Agent** is an autonomous AI system designed to manage business operations continuously, even when you're not around. It creates specialized agents for specific tasks, delegates work intelligently, and ensures your business runs smoothly 24/7.

## 🚀 Key Features

### 1. **Autonomous Operation**
- Runs continuously without human intervention
- Makes intelligent decisions based on task priority and business rules
- Self-manages resources and agents

### 2. **Dynamic Agent Creation**
The system can create specialized agents for various business functions:
- **Sales Agent**: Lead generation, client outreach, deal closing
- **Marketing Agent**: Content creation, campaign management, social media
- **Operations Agent**: Process optimization, resource management, workflow automation
- **Finance Agent**: Budget management, financial reporting, forecasting
- **Customer Service Agent**: Ticket management, issue resolution, support
- **Research Agent**: Market research, competitive analysis, trend analysis
- **Development Agent**: Code development, bug fixing, feature implementation
- **QA Agent**: Testing, quality control, bug detection
- **HR Agent**: Recruitment, onboarding, performance reviews
- **Legal Agent**: Contract review, compliance checks, legal research
- **Strategy Agent**: Strategic planning, goal setting, performance analysis
- **Project Management Agent**: Project planning, task tracking, team coordination

### 3. **Intelligent Task Delegation**
- Automatically determines the best agent for each task
- Creates new agents when needed
- Balances load across available agents
- Prioritizes tasks based on urgency

### 4. **Complete Business Coverage**
The system handles everything from sales to operations to finance, ensuring all aspects of your business are managed.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│     Business Cooperation Lead Agent             │
│  - Autonomous Decision Making                   │
│  - Task Analysis & Delegation                   │
│  - Agent Lifecycle Management                   │
└───────────────┬─────────────────────────────────┘
                │
        ┌───────┴────────┐
        │  Agent Factory │
        └───────┬────────┘
                │
    ┌───────────┴─────────────┬──────────────┐
    │                         │              │
┌───▼───┐              ┌──────▼────┐   ┌────▼─────┐
│ Sales │              │Marketing  │   │Operations│
│ Agent │              │  Agent    │   │  Agent   │
└───────┘              └───────────┘   └──────────┘
    │                         │              │
    └──────────┬──────────────┴──────┬───────┘
               │                     │
          ┌────▼────┐          ┌─────▼─────┐
          │Customer │          │  Finance  │
          │ Service │          │   Agent   │
          └─────────┘          └───────────┘
```

## 📦 Installation & Setup

### 1. Start the System

The Business Lead Agent is included in the standard deployment:

```bash
./deploy.sh
```

Or using Docker Compose directly:

```bash
docker-compose up -d
```

### 2. Configuration

Environment variables (set in `.env` or docker-compose.yml):

```bash
# Backend Configuration
BACKEND_URL=http://backend:8000
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672

# OpenAI (optional, for AI-powered decision making)
OPENAI_API_KEY=your_api_key_here

# Agent Configuration
MAX_CONCURRENT_AGENTS=10        # Maximum number of agents
AGENT_CREATION_ENABLED=true     # Allow dynamic agent creation
AUTO_DELEGATE=true              # Automatically delegate tasks
PRIORITY_THRESHOLD=7.0          # Priority threshold for urgent tasks
```

### 3. Verify Installation

Check that the business lead agent is running:

```bash
docker ps | grep business-lead
```

Check logs:

```bash
docker logs nwu-agent-business-lead
```

## 🎯 Usage

### Creating Tasks via API

Submit tasks to the Business Lead Agent:

```bash
curl -X POST http://localhost:8000/api/v1/business-tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-001",
    "task_type": "lead_generation",
    "category": "sales",
    "priority": 8,
    "task_data": {
      "target_market": "technology",
      "criteria": {
        "company_size": "50-200",
        "industry": "SaaS"
      }
    }
  }'
```

### Creating Tasks via RabbitMQ

Send tasks directly to the `business.tasks` queue:

```python
import pika
import json

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()

# Declare queue
channel.queue_declare(queue='business.tasks', durable=True)

# Create task
task = {
    "task_id": "task-002",
    "task_type": "campaign_management",
    "category": "marketing",
    "priority": 7,
    "data": {
        "campaign_id": "summer-2024",
        "action": "launch"
    }
}

# Send task
channel.basic_publish(
    exchange='',
    routing_key='business.tasks',
    body=json.dumps(task),
    properties=pika.BasicProperties(delivery_mode=2)
)

connection.close()
```

## 📊 Monitoring & Management

### View All Agents

```bash
curl http://localhost:8000/api/v1/business-agents/
```

### View Specific Agent

```bash
curl http://localhost:8000/api/v1/business-agents/agent-id-here
```

### View Agent Tasks

```bash
curl http://localhost:8000/api/v1/business-agents/agent-id-here/tasks
```

### View All Business Tasks

```bash
curl http://localhost:8000/api/v1/business-tasks/
```

### Filter by Status

```bash
# Get pending tasks
curl http://localhost:8000/api/v1/business-tasks/?status=pending

# Get completed tasks
curl http://localhost:8000/api/v1/business-tasks/?status=completed
```

## 🔧 Agent Types & Capabilities

### Sales Agent
- **Capabilities**: lead_generation, client_outreach, deal_closing, relationship_management
- **Use Cases**: Generating leads, contacting prospects, closing deals, managing client relationships

### Marketing Agent
- **Capabilities**: content_creation, campaign_management, social_media, analytics
- **Use Cases**: Creating marketing content, managing campaigns, social media management, performance analytics

### Operations Agent
- **Capabilities**: process_optimization, resource_management, workflow_automation, monitoring
- **Use Cases**: Optimizing business processes, managing resources, automating workflows, monitoring operations

### Finance Agent
- **Capabilities**: budget_management, financial_reporting, forecasting, invoice_processing
- **Use Cases**: Managing budgets, generating financial reports, creating forecasts, processing invoices

### Customer Service Agent
- **Capabilities**: ticket_management, customer_support, issue_resolution, feedback_collection
- **Use Cases**: Managing support tickets, providing customer support, resolving issues, collecting feedback

### Research Agent
- **Capabilities**: market_research, competitive_analysis, trend_analysis, data_collection
- **Use Cases**: Conducting market research, analyzing competition, identifying trends, collecting data

## 💡 Task Examples

### Sales Tasks

```json
{
  "task_type": "lead_generation",
  "category": "sales",
  "data": {
    "target_market": "enterprise",
    "criteria": {"revenue": "10M+"}
  }
}
```

### Marketing Tasks

```json
{
  "task_type": "content_creation",
  "category": "marketing",
  "data": {
    "content_type": "blog_post",
    "topic": "AI in business"
  }
}
```

### Operations Tasks

```json
{
  "task_type": "process_optimization",
  "category": "operations",
  "data": {
    "process_name": "order_fulfillment"
  }
}
```

## 🔄 Task Lifecycle

1. **Submission**: Task is submitted via API or message queue
2. **Analysis**: Business Lead Agent analyzes the task
3. **Agent Selection**: Determines best agent type for the task
4. **Agent Creation**: Creates new agent if needed
5. **Delegation**: Assigns task to appropriate agent
6. **Execution**: Agent executes the task
7. **Completion**: Result is stored and reported back
8. **Monitoring**: Continuous monitoring of agent health

## 🎛️ Advanced Configuration

### Custom Agent Types

You can extend the system by creating custom agent types. Add new agent classes in:

```
agent-business-lead/app/agents/your_custom_agent.py
```

### Task Priority Levels

- **CRITICAL (10)**: Highest priority, immediate execution
- **HIGH (7)**: High priority, execute soon
- **MEDIUM (5)**: Normal priority (default)
- **LOW (3)**: Low priority, execute when resources available
- **MINIMAL (1)**: Lowest priority, execute when idle

### Agent Limits

Control resource usage:

```bash
MAX_CONCURRENT_AGENTS=20  # Allow up to 20 concurrent agents
AGENT_CREATION_ENABLED=false  # Disable dynamic agent creation
```

## 🚨 Troubleshooting

### Agent Not Starting

Check logs:
```bash
docker logs nwu-agent-business-lead
```

Common issues:
- RabbitMQ not running
- Backend not accessible
- Database connection issues

### Tasks Not Being Processed

1. Check RabbitMQ queue:
```bash
docker exec nwu-rabbitmq rabbitmqctl list_queues
```

2. Verify task format matches expected schema

3. Check agent status via API

### Agent Creation Failing

Verify:
- `AGENT_CREATION_ENABLED=true`
- Not at max agent capacity
- Sufficient system resources

## 📈 Performance Metrics

The Business Lead Agent tracks:
- **Tasks Processed**: Total number of tasks completed
- **Agents Created**: Number of specialized agents created
- **Decisions Made**: Intelligent decisions made by the lead agent
- **Uptime**: System uptime in seconds
- **Agent Utilization**: Percentage of agents actively working

Access metrics via logs or implement custom monitoring dashboard.

## 🔐 Security Considerations

1. **API Access**: Secure API endpoints with authentication
2. **Task Validation**: Validate all incoming tasks
3. **Agent Isolation**: Agents run in isolated containers
4. **Data Protection**: Sensitive data is encrypted
5. **Audit Logging**: All actions are logged

## 🌟 Best Practices

1. **Task Prioritization**: Use appropriate priority levels
2. **Agent Capacity**: Monitor and adjust MAX_CONCURRENT_AGENTS
3. **Task Batching**: Submit related tasks together
4. **Error Handling**: Implement retry logic for failed tasks
5. **Monitoring**: Regularly check agent health and performance

## 📝 API Reference

### Business Agents

- `GET /api/v1/business-agents/` - List all agents
- `GET /api/v1/business-agents/{agent_id}` - Get agent details
- `POST /api/v1/business-agents/` - Create agent
- `PUT /api/v1/business-agents/{agent_id}/status` - Update agent status
- `DELETE /api/v1/business-agents/{agent_id}` - Terminate agent
- `GET /api/v1/business-agents/{agent_id}/tasks` - Get agent tasks

### Business Tasks

- `GET /api/v1/business-tasks/` - List all tasks
- `GET /api/v1/business-tasks/{task_id}` - Get task details
- `POST /api/v1/business-tasks/` - Create task
- `POST /api/v1/business-tasks/results` - Submit task result

## 🎓 Examples & Use Cases

### Scenario 1: Automated Lead Generation

```python
# Submit lead generation task
task = {
    "task_id": f"lead-gen-{datetime.now().timestamp()}",
    "task_type": "lead_generation",
    "category": "sales",
    "priority": 8,
    "task_data": {
        "target_market": "fintech",
        "criteria": {
            "company_size": "100-500",
            "location": "North America"
        }
    }
}
```

### Scenario 2: Marketing Campaign Launch

```python
# Launch marketing campaign
task = {
    "task_id": "campaign-q4-2024",
    "task_type": "campaign_management",
    "category": "marketing",
    "priority": 9,
    "task_data": {
        "campaign_id": "q4-promo",
        "action": "launch",
        "budget": 50000
    }
}
```

### Scenario 3: Process Optimization

```python
# Optimize business process
task = {
    "task_id": "optimize-fulfillment",
    "task_type": "process_optimization",
    "category": "operations",
    "priority": 7,
    "task_data": {
        "process_name": "order_fulfillment",
        "current_metrics": {
            "avg_time": 48,
            "error_rate": 5
        }
    }
}
```

## 🆘 Support

For issues, questions, or feature requests:

1. Check the logs: `docker logs nwu-agent-business-lead`
2. Review this documentation
3. Check the main project README
4. Open an issue on GitHub

## 📚 Additional Resources

- [Main Project README](../README.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [API Reference](../API_REFERENCE.md)
- [Deployment Guide](../DEPLOYMENT.md)

---

**The Business Cooperation Lead Agent ensures your business never stops, even when you're not around.**
