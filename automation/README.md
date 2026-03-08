# Halt Process Management and Progressive Automation

## Overview

This directory contains the comprehensive halt process management system with engagement iteration and progressive automation capabilities for the NWU Protocol.

## Features

### 1. Halt Process Management
- **Halt/Pause/Resume Operations**: Complete control over contribution processing lifecycles
- **Engagement Tracking**: Track all user interactions and engagement patterns
- **Approval Workflows**: Approve halt processes through engagement and iteration
- **Status Monitoring**: Real-time halt status and history tracking

### 2. Progressive Automation (6 Levels)
- **Level 0**: Manual processing only
- **Level 1**: Basic automated validation
- **Level 2**: Automated quality checks
- **Level 3**: Intelligent routing and prioritization
- **Level 4**: Predictive analysis and recommendations
- **Level 5**: Fully autonomous decision-making

### 3. Engagement Iteration System
- **Engagement Analytics**: Track engagement patterns and trends
- **Iteration History**: Complete history of process iterations
- **Health Monitoring**: Assess contribution health based on engagement
- **User Engagement**: Summary and analytics for user interactions

### 4. Turnkey Business Automation
- **Workflow Registry**: Centralized workflow configuration
- **Automated Monitoring**: Continuous workflow health checks
- **Business Workflows**: Pre-configured business process automation
- **Integration Ready**: Prepared for Perplexity knowledge integration

## Directory Structure

```
automation/
├── deploy-turnkey-automation.sh    # Main deployment script
├── configs/                         # Configuration files
│   └── workflow_registry.json      # Workflow definitions
├── scripts/                         # Automation scripts
│   ├── monitor_workflows.sh        # Workflow monitoring
│   └── integrate_perplexity.sh     # Knowledge integration
└── workflows/                       # Workflow implementations
    └── business_automation.py      # Business automation logic
```

## Quick Start

### Deploy Automation System

```bash
cd automation
./deploy-turnkey-automation.sh
```

This will:
1. Check system prerequisites
2. Create necessary directories
3. Deploy workflow configurations
4. Setup monitoring scripts
5. Deploy automation integration
6. Create business workflow automation

### Monitor Workflows

```bash
./automation/scripts/monitor_workflows.sh
```

Continuously monitors workflow execution and system health.

## API Endpoints

### Halt Process Management

```bash
# Halt a contribution
POST /api/v1/halt-process/contributions/{id}/halt
{
  "reason": "Quality issues detected",
  "user_id": 123,
  "halt_data": {"details": "..."}
}

# Pause a contribution
POST /api/v1/halt-process/contributions/{id}/pause
{
  "reason": "Waiting for additional review",
  "user_id": 123
}

# Resume a contribution
POST /api/v1/halt-process/contributions/{id}/resume
{
  "user_id": 123,
  "resume_to_status": "verifying"
}

# Get halt status
GET /api/v1/halt-process/contributions/{id}/halt-status

# Approve halt engagement (core requirement)
POST /api/v1/halt-process/contributions/{id}/approve-halt
{
  "approval_reason": "Manual review completed",
  "user_id": 123
}
```

### Workflow Automation

```bash
# Execute workflow
POST /api/v1/halt-process/contributions/{id}/execute-workflow
{
  "workflow_name": "contribution_verification",
  "max_automation_level": 3,
  "workflow_data": {}
}

# Get workflow status
GET /api/v1/halt-process/contributions/{id}/workflow-status

# Advance automation level
POST /api/v1/halt-process/contributions/{id}/advance-automation?target_level=4
```

### Engagement Tracking

```bash
# Record engagement
POST /api/v1/halt-process/contributions/{id}/engagement
{
  "engagement_type": "view",
  "user_id": 123,
  "engagement_data": {},
  "source": "api"
}

# Get engagement analytics
GET /api/v1/halt-process/contributions/{id}/engagement-analytics?days=30

# Get iteration history
GET /api/v1/halt-process/contributions/{id}/iteration-history?limit=20

# Get engagement trends
GET /api/v1/halt-process/contributions/{id}/engagement-trends

# Get user engagement summary
GET /api/v1/halt-process/users/{id}/engagement-summary?days=30
```

## Database Schema

### New Tables

#### engagement_history
Tracks all engagement events for contributions.

#### process_iterations
Records contribution iteration history and status changes.

#### workflow_executions
Tracks progressive automation workflow executions.

#### knowledge_threads
Manages knowledge threads for Perplexity integration (future).

### Extended Columns

**Contribution Table**:
- `engagement_count`: Total engagement interactions
- `engagement_score`: Calculated engagement metric
- `iteration_count`: Number of revision iterations
- `halt_reason`: Reason for halting
- `halt_status`: Current halt state (active, halted, paused, resumed)
- `process_stage`: Current progressive automation stage
- `automation_level`: Progressive automation capability level (0-5)
- `halted_at`: Timestamp when halted
- `resumed_at`: Timestamp when resumed

## Workflows

### 1. Contribution Verification Workflow
Progressive automated verification with 5 stages:
1. Initial validation (Level 1)
2. Quality analysis (Level 2)
3. Intelligent routing (Level 3)
4. Predictive scoring (Level 4)
5. Autonomous approval (Level 5)

### 2. Engagement Iteration Workflow
Automated engagement tracking and iteration:
1. Engagement tracking (Level 1)
2. Pattern analysis (Level 2)
3. Adaptive response (Level 3)
4. Predictive engagement (Level 4)
5. Autonomous iteration (Level 5)

### 3. Halt Process Automation Workflow
Automated halt detection and recovery:
1. Halt detection (Level 1)
2. Automated analysis (Level 2)
3. Intelligent recovery (Level 3)
4. Predictive prevention (Level 4)
5. Self-healing (Level 5)

### 4. Progressive Quality Improvement Workflow
Continuous quality enhancement:
1. Baseline assessment (Level 1)
2. Improvement planning (Level 2)
3. Automated refinement (Level 3)
4. Quality validation (Level 4)
5. Continuous optimization (Level 5)

## Integration

### Perplexity Knowledge Integration (Prepared)
Infrastructure ready for Perplexity API integration:
- Knowledge thread management
- Context-aware analysis
- Multi-turn conversation tracking
- External knowledge enrichment

See `scripts/integrate_perplexity.sh` for configuration.

## Monitoring

### Health Status Levels
- **healthy**: High engagement and active iteration
- **moderate**: Moderate engagement activity
- **low_activity**: Low engagement but active
- **inactive**: No recent engagement
- **halted**: Process halted by user/system

### Metrics Tracked
- Engagement velocity (engagements/day)
- Iteration frequency
- Automation level progression
- Workflow execution success rate
- Halt/resume cycles

## Usage Examples

### Example 1: Halt and Approve Process

```python
# Halt a contribution
response = requests.post(
    "http://localhost:8000/api/v1/halt-process/contributions/123/halt",
    json={
        "reason": "Requires manual review",
        "user_id": 456
    }
)

# Approve the halt engagement
response = requests.post(
    "http://localhost:8000/api/v1/halt-process/contributions/123/approve-halt",
    json={
        "approval_reason": "Review completed, quality improved",
        "user_id": 456
    }
)

# Resume processing
response = requests.post(
    "http://localhost:8000/api/v1/halt-process/contributions/123/resume",
    json={
        "user_id": 456,
        "resume_to_status": "verifying"
    }
)
```

### Example 2: Progressive Automation

```python
# Start with basic automation
response = requests.post(
    "http://localhost:8000/api/v1/halt-process/contributions/123/execute-workflow",
    json={
        "workflow_name": "contribution_verification",
        "max_automation_level": 2
    }
)

# Advance to higher automation level
response = requests.post(
    "http://localhost:8000/api/v1/halt-process/contributions/123/advance-automation?target_level=4"
)
```

### Example 3: Engagement Tracking

```python
# Track user engagement
response = requests.post(
    "http://localhost:8000/api/v1/halt-process/contributions/123/engagement",
    json={
        "engagement_type": "view",
        "user_id": 456,
        "source": "web"
    }
)

# Get analytics
response = requests.get(
    "http://localhost:8000/api/v1/halt-process/contributions/123/engagement-analytics?days=30"
)
```

## Configuration

### Environment Variables

```bash
# Automation settings
AUTOMATION_ENABLED=true
MAX_AUTOMATION_LEVEL=5
WORKFLOW_MONITORING_INTERVAL=300

# Perplexity integration (future)
PERPLEXITY_API_KEY=your_api_key_here
THREAD_TIMEOUT=3600
MAX_CONTEXT_LENGTH=8192
```

## Troubleshooting

### Issue: Workflows not executing
**Solution**: Check backend service status and logs

```bash
docker-compose logs backend
curl http://localhost:8000/health
```

### Issue: Halt operations failing
**Solution**: Verify contribution exists and status

```bash
curl http://localhost:8000/api/v1/halt-process/contributions/{id}/halt-status
```

### Issue: Engagement not tracking
**Solution**: Check database connectivity and service status

```bash
docker-compose ps
docker-compose logs postgres
```

## Development

### Running Tests
```bash
# Test halt process service
pytest backend/tests/test_halt_process_service.py

# Test workflow engine
pytest backend/tests/test_workflow_engine.py

# Test engagement service
pytest backend/tests/test_engagement_service.py
```

### Adding New Workflows
1. Define workflow in `configs/workflow_registry.json`
2. Implement stages in workflow engine
3. Register workflow in `ProgressiveAutomationEngine`
4. Add API endpoint in `halt_process.py`
5. Update documentation

## Support

For questions or issues:
1. Check logs in `logs/automation/`
2. Review API documentation at http://localhost:8000/docs
3. Consult main README.md for general setup
4. Create GitHub issue for bugs or feature requests

## License

MIT License - See main repository LICENSE file
