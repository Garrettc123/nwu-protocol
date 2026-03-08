# 🚀 Quick Start: Halt Process & Progressive Automation

Get started with the comprehensive halt process management and progressive automation system in under 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Backend services running
- PostgreSQL database accessible

## Installation (3 Steps)

### Step 1: Run Database Migration

```bash
cd /home/runner/work/nwu-protocol/nwu-protocol
python scripts/migrate_halt_process.py
```

**What this does:**
- Adds new columns to contributions table
- Creates 4 new tables: engagement_history, process_iterations, workflow_executions, knowledge_threads
- Sets up all necessary indexes
- Initializes default values

**Expected output:**
```
Starting database migration...
============================================================
1. Adding new columns to contributions table...
  ✅ ALTER TABLE contributions ADD COLUMN IF NOT EXISTS engagement_count...
  ✅ ALTER TABLE contributions ADD COLUMN IF NOT EXISTS engagement_score...
  [... more migrations ...]
✅ Database migration completed successfully!
```

### Step 2: Deploy Automation System

```bash
cd automation
./deploy-turnkey-automation.sh
```

**What this does:**
- Creates automation directory structure
- Deploys workflow configurations
- Sets up monitoring scripts
- Creates business automation workflows

**Expected output:**
```
🚀 NWU Protocol - Turnkey Business Automation
================================================
[... deployment progress ...]
✅ Turnkey business automation deployed successfully!
```

### Step 3: Restart Backend

```bash
docker-compose restart backend
# OR
./restart.sh
```

**Verify installation:**
```bash
curl http://localhost:8000/docs
# Should show updated API documentation with halt-process endpoints
```

## Your First Halt Process

### Example 1: Halt and Resume a Contribution

```bash
# 1. Halt a contribution
curl -X POST http://localhost:8000/api/v1/halt-process/contributions/1/halt \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Quality review required",
    "user_id": 1
  }'

# 2. Check halt status
curl http://localhost:8000/api/v1/halt-process/contributions/1/halt-status

# 3. Approve the halt (CORE FEATURE)
curl -X POST http://localhost:8000/api/v1/halt-process/contributions/1/approve-halt \
  -H "Content-Type: application/json" \
  -d '{
    "approval_reason": "Review completed",
    "user_id": 1
  }'

# 4. Resume processing
curl -X POST http://localhost:8000/api/v1/halt-process/contributions/1/resume \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "resume_to_status": "verifying"
  }'
```

### Example 2: Execute Progressive Automation

```bash
# Execute workflow at automation level 3
curl -X POST http://localhost:8000/api/v1/halt-process/contributions/1/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "contribution_verification",
    "max_automation_level": 3
  }'

# Check workflow status
curl http://localhost:8000/api/v1/halt-process/contributions/1/workflow-status

# Advance to higher automation level
curl -X POST http://localhost:8000/api/v1/halt-process/contributions/1/advance-automation?target_level=5
```

### Example 3: Track Engagement

```bash
# Record engagement
curl -X POST http://localhost:8000/api/v1/halt-process/contributions/1/engagement \
  -H "Content-Type: application/json" \
  -d '{
    "engagement_type": "comment",
    "user_id": 1,
    "engagement_data": {"comment": "Great work!"},
    "source": "api"
  }'

# Get engagement analytics
curl http://localhost:8000/api/v1/halt-process/contributions/1/engagement-analytics?days=30

# Get engagement trends
curl http://localhost:8000/api/v1/halt-process/contributions/1/engagement-trends
```

## Available Workflows

The system comes with 4 pre-configured workflows:

1. **contribution_verification** - Automated verification with 5 stages
2. **engagement_iteration** - Engagement tracking and iteration
3. **halt_process_automation** - Halt detection and recovery
4. **progressive_quality_improvement** - Continuous quality enhancement

Each workflow supports 6 automation levels (0-5) with progressive capabilities.

## API Endpoints Reference

### Halt Process Management
- `POST /api/v1/halt-process/contributions/{id}/halt` - Halt contribution
- `POST /api/v1/halt-process/contributions/{id}/pause` - Pause temporarily
- `POST /api/v1/halt-process/contributions/{id}/resume` - Resume processing
- `GET /api/v1/halt-process/contributions/{id}/halt-status` - Get status
- `POST /api/v1/halt-process/contributions/{id}/approve-halt` - **Approve halt** ⭐

### Workflow Automation
- `POST /api/v1/halt-process/contributions/{id}/execute-workflow` - Execute workflow
- `GET /api/v1/halt-process/contributions/{id}/workflow-status` - Get status
- `POST /api/v1/halt-process/contributions/{id}/advance-automation` - Advance level

### Engagement Tracking
- `POST /api/v1/halt-process/contributions/{id}/engagement` - Record engagement
- `GET /api/v1/halt-process/contributions/{id}/engagement-analytics` - Get analytics
- `GET /api/v1/halt-process/contributions/{id}/iteration-history` - Get history
- `GET /api/v1/halt-process/contributions/{id}/engagement-trends` - Get trends
- `GET /api/v1/halt-process/users/{id}/engagement-summary` - User summary

## Monitoring

### Start Continuous Monitoring
```bash
./automation/scripts/monitor_workflows.sh
```

### Check Logs
```bash
tail -f logs/automation/turnkey_automation_*.log
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Understanding Automation Levels

| Level | Name | Description |
|-------|------|-------------|
| 0 | Manual | Manual processing only |
| 1 | Basic | Basic automated validation |
| 2 | Quality | Automated quality checks |
| 3 | Intelligent | Intelligent routing and prioritization |
| 4 | Predictive | Predictive analysis and recommendations |
| 5 | Autonomous | Fully autonomous decision-making |

Contributions start at level 0 and can progressively advance through levels as they demonstrate quality and engagement.

## Engagement Types

The system tracks these engagement types (with scoring weights):

- **view** (0.5) - Simple view of contribution
- **comment** (2.0) - User comment or feedback
- **share** (3.0) - Sharing contribution
- **iterate** (5.0) - Process iteration/revision
- **halt** (1.0) - Halt operation
- **resume** (2.5) - Resume operation
- **halt_approval** (4.0) - Halt approval (important!)
- **automation** (1.5) - Automated process
- **automation_advance** (3.0) - Automation level increase

## Troubleshooting

### Backend not responding
```bash
docker-compose ps
docker-compose restart backend
docker-compose logs backend
```

### Migration issues
```bash
# Check database connection
docker-compose exec postgres psql -U nwu_user -d nwu_db -c "\dt"

# Re-run migration
python scripts/migrate_halt_process.py
```

### API endpoints missing
```bash
# Verify router is registered
grep "halt_process_router" backend/app/main.py

# Restart backend
docker-compose restart backend
```

## Next Steps

1. **Explore API** - Visit http://localhost:8000/docs for interactive API documentation
2. **Read Full Guide** - See `HALT_PROCESS_IMPLEMENTATION.md` for detailed documentation
3. **Automation Guide** - See `automation/README.md` for automation details
4. **Integration** - Integrate halt process into your existing workflows

## Key Features Implemented

✅ **Halt Process by Engaging and Iteration** (Core Requirement)
- Complete halt/pause/resume operations
- Engagement tracking throughout halt lifecycle
- Approval workflow with `approve_halt_engagement()` endpoint

✅ **Progressive Automation** (6 Levels)
- Unprecedented harmoniously integrated automation
- Smooth progression from manual to autonomous
- 4 pre-configured business workflows

✅ **Engagement Iteration Tracking**
- Comprehensive engagement analytics
- Trend analysis and health monitoring
- User engagement summaries

✅ **Turnkey Business Automation**
- One-command deployment
- Automated monitoring
- Integration-ready architecture

## Support

- **API Documentation**: http://localhost:8000/docs
- **Implementation Guide**: `HALT_PROCESS_IMPLEMENTATION.md`
- **Automation Guide**: `automation/README.md`
- **Validation Script**: `./scripts/validate-halt-process.sh`

## Example Python Integration

```python
import requests

class HaltProcessClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = f"{base_url}/api/v1/halt-process"

    def halt_contribution(self, contribution_id, reason, user_id=None):
        """Halt a contribution."""
        response = requests.post(
            f"{self.base_url}/contributions/{contribution_id}/halt",
            json={"reason": reason, "user_id": user_id}
        )
        return response.json()

    def approve_halt(self, contribution_id, approval_reason, user_id=None):
        """Approve halt engagement (CORE FEATURE)."""
        response = requests.post(
            f"{self.base_url}/contributions/{contribution_id}/approve-halt",
            json={"approval_reason": approval_reason, "user_id": user_id}
        )
        return response.json()

    def resume_contribution(self, contribution_id, user_id=None):
        """Resume a halted contribution."""
        response = requests.post(
            f"{self.base_url}/contributions/{contribution_id}/resume",
            json={"user_id": user_id}
        )
        return response.json()

# Usage
client = HaltProcessClient()
result = client.halt_contribution(1, "Quality review required", user_id=1)
print(result)
```

---

**Ready to start?** Run the 3 installation steps above and begin using halt process management! 🚀
