# Agent Orchestration System - Quick Start

## Overview

This is the **full-scale multi-agent orchestration system** for NWU Protocol - a "god bot" architecture where agents can dynamically spawn and manage other agents.

## Key Features

✅ **Dynamic Agent Spawning** - Create agents on-demand
✅ **Hierarchical Structure** - Master agents spawn and manage children
✅ **Auto-scaling** - Automatically scale based on load
✅ **Self-healing** - Failed agents are automatically recovered
✅ **Load Balancing** - Intelligent task distribution
✅ **Multi-agent Coordination** - Agents work together

## Quick Start

### 1. Start the Backend

```bash
# The orchestrator initializes automatically when the backend starts
cd backend
python -m app.main
```

### 2. Initialize the Orchestrator (Optional)

The orchestrator auto-initializes, but you can reinitialize if needed:

```bash
curl -X POST http://localhost:8000/api/v1/agents/initialize
```

### 3. Check Status

```bash
curl http://localhost:8000/api/v1/agents/status
```

### 4. Run the Demo

```bash
python examples/agent_orchestration_demo.py
```

## Agent Types

| Type | Role | Can Spawn | Description |
|------|------|-----------|-------------|
| **Master** | God Bot | ✅ Yes | Top-level orchestrator, manages everything |
| **Verifier** | Verification | ❌ No | AI-powered contribution verification |
| **Analyzer** | Analysis | ❌ No | Pattern detection and insights |
| **Coordinator** | Coordination | ✅ Yes | Multi-agent task coordination |
| **Specialist** | Custom | ❌ No | Domain-specific tasks |

## API Examples

### Spawn an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/spawn \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "verifier",
    "config": {"name": "Verifier-1"}
  }'
```

### Submit a Task

```bash
curl -X POST http://localhost:8000/api/v1/agents/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "verify_code",
    "task_data": {
      "contribution_id": 123,
      "ipfs_hash": "QmXXX",
      "file_type": "code"
    }
  }'
```

### List All Agents

```bash
curl http://localhost:8000/api/v1/agents/agents
```

### Get Agent Status

```bash
curl http://localhost:8000/api/v1/agents/agents/{agent_id}
```

## Architecture

```
┌──────────────────────────────────────┐
│      Agent Orchestrator              │
│      (Master Controller)             │
└────────────┬─────────────────────────┘
             │
             ├─► Master Agent (God Bot)
             │   ├─► Spawns Verifiers
             │   ├─► Spawns Analyzers
             │   ├─► Spawns Coordinators
             │   └─► Spawns Specialists
             │
             ├─► Auto-Scaler
             │   └─► Scales agents up/down
             │
             ├─► Health Monitor
             │   └─► Recovers failed agents
             │
             └─► Task Router
                 └─► Distributes tasks
```

## Configuration

### Environment Variables

```env
# Agent Orchestrator
AGENT_AUTO_SCALING=true
AGENT_MAX_PER_TYPE=10
AGENT_HEALTH_CHECK_INTERVAL=30
```

### Runtime Configuration

```bash
# Enable auto-scaling
curl -X PUT "http://localhost:8000/api/v1/agents/config/auto-scaling?enabled=true"

# Set max agents per type
curl -X PUT "http://localhost:8000/api/v1/agents/config/max-agents?max_agents_per_type=15"
```

## Monitoring

### View Dashboard

Open the API docs to see all endpoints:
```
http://localhost:8000/docs
```

### Real-time Metrics

Each agent tracks:
- Tasks completed/failed
- Average execution time
- Error count
- Current load
- Uptime

### Health Checks

Agents send heartbeats every 10 seconds. If an agent fails to respond for 60 seconds, it's automatically recovered.

## Auto-scaling

The orchestrator automatically scales agents:

- **Scale Up**: When utilization > 80%
- **Scale Down**: When utilization < 20% (keeping at least 1)
- **Check Interval**: Every 30 seconds

## Advanced Usage

### Hierarchical Spawning

Master and Coordinator agents can spawn children:

```python
# A coordinator spawns specialist agents
{
  "task_type": "coordinate",
  "task_data": {
    "tasks": [
      {"type": "specialized", "agent_type": "specialist"},
      {"type": "specialized", "agent_type": "specialist"}
    ]
  }
}
```

### Complex Workflows

```python
# Master orchestrates multi-step workflow
{
  "task_type": "orchestrate",
  "task_data": {
    "workflow_id": "complex-analysis",
    "steps": [
      {"type": "verification", "name": "Verify Data"},
      {"type": "analysis", "name": "Analyze Results"},
      {"type": "coordination", "name": "Aggregate Findings"}
    ]
  }
}
```

## Files

### Core Implementation

- `backend/app/services/agent_orchestrator.py` - Main orchestrator
- `backend/app/services/base_agent.py` - Base agent classes
- `backend/app/api/agents.py` - API endpoints

### Documentation

- `AGENT_ORCHESTRATION.md` - Complete documentation
- `examples/agent_orchestration_demo.py` - Full demonstration

## Troubleshooting

### Orchestrator not starting?

```bash
# Check logs
tail -f backend/logs/app.log

# Verify services are running
docker ps
```

### Agents not spawning?

- Check max_agents_per_type limit
- Verify sufficient memory
- Check orchestrator status

### Tasks not processing?

- Ensure appropriate agent types are active
- Check agent health status
- Verify task type matches agent capabilities

## Next Steps

1. ✅ Initialize the orchestrator
2. ✅ Run the demo script
3. ✅ Spawn agents for your use case
4. ✅ Submit tasks
5. ✅ Monitor performance
6. ✅ Configure auto-scaling

## Learn More

- Full Documentation: `AGENT_ORCHESTRATION.md`
- API Reference: http://localhost:8000/docs
- Example Usage: `examples/agent_orchestration_demo.py`

## Support

For issues or questions:
- Check the logs: `backend/logs/`
- Review documentation: `AGENT_ORCHESTRATION.md`
- Open an issue on GitHub

---

**"Full God Bots" - Agents that create more agents to run everything correctly! 🤖🚀**
