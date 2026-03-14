# Multi-Agent Orchestration System

## Overview

The NWU Protocol now includes a full-scale multi-agent orchestration system that can dynamically spawn and manage specialized agents. This "god bot" architecture allows for:

- **Dynamic Agent Spawning**: Create agents on-demand based on workload
- **Hierarchical Structure**: Master agents that spawn and manage child agents
- **Auto-scaling**: Automatically scale agents up or down based on utilization
- **Task Distribution**: Intelligent routing of tasks to appropriate agents
- **Health Monitoring**: Automatic detection and recovery of failed agents
- **Multi-level Coordination**: Agents can coordinate with each other

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
│  (Master Controller - Spawns and manages all agents)        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├──► Master Agent (God Bot)
                   │    └──► Can spawn other agents
                   │         ├──► Verifier Agents (2-10)
                   │         ├──► Analyzer Agents (1-5)
                   │         ├──► Coordinator Agents (1-3)
                   │         └──► Specialist Agents (as needed)
                   │
                   └──► Auto-Scaler
                        └──► Monitors load and scales agents
```

## Agent Types

### 1. Master Agent (God Bot)
- **Role**: Top-level orchestrator
- **Capabilities**:
  - Spawns and manages all other agents
  - Orchestrates complex workflows
  - Delegates tasks to specialized agents
  - Coordinates multi-agent operations
- **Can Spawn**: Yes (unlimited)
- **Spawned By**: Orchestrator on initialization

### 2. Verifier Agent
- **Role**: Verifies contributions (code, datasets, documents)
- **Capabilities**:
  - AI-powered verification using GPT-4
  - Quality, security, and originality assessment
  - Integration with IPFS for file retrieval
- **Can Spawn**: No
- **Spawned By**: Master Agent or Orchestrator

### 3. Analyzer Agent
- **Role**: Analyzes patterns and generates insights
- **Capabilities**:
  - Trend analysis
  - Pattern detection
  - Insight generation
- **Can Spawn**: No
- **Spawned By**: Master Agent or Orchestrator

### 4. Coordinator Agent
- **Role**: Coordinates multiple agents and aggregates results
- **Capabilities**:
  - Multi-agent coordination
  - Result aggregation
  - Workflow management
- **Can Spawn**: Yes (up to 10 child agents)
- **Spawned By**: Master Agent or Orchestrator

### 5. Specialist Agent
- **Role**: Handles domain-specific tasks
- **Capabilities**: Configurable based on specific needs
- **Can Spawn**: No
- **Spawned By**: Any coordinator or master agent

## API Endpoints

### Initialize Orchestrator
```http
POST /api/v1/agents/initialize
```

Initializes the orchestrator and spawns the master agent.

**Response:**
```json
{
  "success": true,
  "message": "Orchestrator initialized successfully",
  "master_agent_id": "master-abc12345"
}
```

### Spawn an Agent
```http
POST /api/v1/agents/spawn
Content-Type: application/json

{
  "agent_type": "verifier",
  "parent_agent_id": "master-abc12345",
  "config": {
    "name": "Verifier-3",
    "max_concurrent_tasks": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "agent_id": "verifier-def67890",
  "message": "Agent verifier-def67890 spawned successfully"
}
```

### Submit a Task
```http
POST /api/v1/agents/tasks
Content-Type: application/json

{
  "task_type": "verify_code",
  "task_data": {
    "contribution_id": 123,
    "ipfs_hash": "QmXXX...",
    "file_type": "code"
  },
  "preferred_agent_type": "verifier"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Task submitted successfully"
}
```

### Get Agent Status
```http
GET /api/v1/agents/agents/{agent_id}
```

**Response:**
```json
{
  "agent_id": "verifier-def67890",
  "agent_type": "verifier",
  "status": "active",
  "metrics": {
    "tasks_completed": 42,
    "tasks_failed": 2,
    "average_duration": 3.5,
    "error_count": 2
  },
  "current_tasks": 2,
  "child_agents": 0,
  "uptime": 3600.5
}
```

### Get All Agents
```http
GET /api/v1/agents/agents
```

Returns status for all active agents.

### Get Orchestrator Status
```http
GET /api/v1/agents/status
```

**Response:**
```json
{
  "running": true,
  "total_agents": 7,
  "agents_by_type": {
    "master": 1,
    "verifier": 3,
    "analyzer": 1,
    "coordinator": 1,
    "specialist": 1
  },
  "auto_scaling_enabled": true,
  "master_agent_id": "master-abc12345"
}
```

### Stop an Agent
```http
DELETE /api/v1/agents/agents/{agent_id}?graceful=true
```

### Shutdown Orchestrator
```http
POST /api/v1/agents/shutdown
```

Gracefully shuts down all agents and the orchestrator.

### Configure Auto-scaling
```http
PUT /api/v1/agents/config/auto-scaling?enabled=true
```

### Configure Max Agents
```http
PUT /api/v1/agents/config/max-agents?max_agents_per_type=10
```

## Features

### 1. Auto-scaling
The orchestrator automatically scales agents based on utilization:
- **Scale Up**: When utilization > 80%, spawn new agents
- **Scale Down**: When utilization < 20% and > 1 agent, stop idle agents
- **Checks**: Every 30 seconds

### 2. Health Monitoring
Continuous health monitoring with automatic recovery:
- **Heartbeat**: Every 10 seconds
- **Timeout**: 60 seconds
- **Recovery**: Failed agents are automatically replaced

### 3. Load Balancing
Tasks are distributed to agents based on:
- Agent capabilities
- Current load
- Task requirements
- Agent health

### 4. Hierarchical Structure
Agents can form hierarchical relationships:
- Master agents spawn and manage child agents
- Coordinators can spawn specialist agents
- Parent-child relationships tracked

## Usage Examples

### Example 1: Initialize the System
```bash
curl -X POST http://localhost:8000/api/v1/agents/initialize
```

### Example 2: Spawn Additional Verifier
```bash
curl -X POST http://localhost:8000/api/v1/agents/spawn \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "verifier",
    "config": {"name": "Verifier-Extra"}
  }'
```

### Example 3: Submit Verification Task
```bash
curl -X POST http://localhost:8000/api/v1/agents/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "verify_code",
    "task_data": {
      "contribution_id": 123,
      "ipfs_hash": "QmXXX",
      "file_type": "code"
    },
    "preferred_agent_type": "verifier"
  }'
```

### Example 4: Check System Status
```bash
curl http://localhost:8000/api/v1/agents/status
```

### Example 5: Monitor Specific Agent
```bash
curl http://localhost:8000/api/v1/agents/agents/verifier-abc123
```

## Integration with Existing System

The orchestrator integrates seamlessly with the existing NWU Protocol infrastructure:

1. **RabbitMQ**: Tasks can be submitted through the orchestrator or traditional queues
2. **Database**: Agent metrics and status can be persisted
3. **IPFS**: Verifier agents access IPFS for file retrieval
4. **WebSocket**: Real-time updates for agent status changes

## Configuration

### Environment Variables
```env
# Agent Orchestrator Configuration
AGENT_AUTO_SCALING=true
AGENT_MAX_PER_TYPE=10
AGENT_HEALTH_CHECK_INTERVAL=30
AGENT_TASK_TIMEOUT=300
```

### Orchestrator Settings
```python
orchestrator.auto_scale_enabled = True
orchestrator.max_agents_per_type = 10
orchestrator.health_check_interval = 30  # seconds
orchestrator.task_timeout = 300  # seconds
```

## Monitoring and Metrics

Each agent tracks:
- **Tasks Completed**: Total successful tasks
- **Tasks Failed**: Total failed tasks
- **Average Duration**: Mean task execution time
- **Error Count**: Total errors encountered
- **Uptime**: Time since agent creation
- **Current Load**: Number of active tasks

## Best Practices

1. **Initialize on Startup**: Initialize the orchestrator when the backend starts
2. **Monitor Health**: Regularly check orchestrator status
3. **Enable Auto-scaling**: Let the system handle agent scaling
4. **Set Reasonable Limits**: Configure max_agents_per_type based on resources
5. **Use Appropriate Types**: Choose the right agent type for each task
6. **Graceful Shutdown**: Always use graceful shutdown to avoid data loss

## Troubleshooting

### Orchestrator Not Starting
- Check that RabbitMQ and Redis are running
- Verify database connection
- Check logs for initialization errors

### Agents Not Spawning
- Check max_agents_per_type limit
- Verify sufficient system resources
- Check for initialization failures in logs

### Tasks Not Being Processed
- Verify orchestrator is running
- Check that appropriate agent types are available
- Monitor agent health and status

### High Error Rate
- Check agent logs for specific errors
- Verify external service connectivity (IPFS, OpenAI)
- Monitor system resources

## Future Enhancements

1. **Persistent Agent State**: Save and restore agent state across restarts
2. **Advanced Load Balancing**: ML-based task routing
3. **Cross-node Coordination**: Distributed agent orchestration
4. **Custom Agent Types**: Plugin system for custom agent implementations
5. **Performance Analytics**: Advanced metrics and reporting
6. **Resource Quotas**: Per-agent resource limits and quotas

## Conclusion

The multi-agent orchestration system provides a robust, scalable foundation for dynamic agent management in the NWU Protocol. The "god bot" architecture enables sophisticated task distribution and processing while maintaining system health and efficiency.
