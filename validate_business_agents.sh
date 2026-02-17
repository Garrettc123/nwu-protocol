#!/bin/bash
# Validation script for Business Cooperation Agent System

echo "================================================================================"
echo "BUSINESS COOPERATION AGENT SYSTEM - VALIDATION"
echo "================================================================================"
echo ""

ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
        return 0
    else
        echo "✗ MISSING: $1"
        ((ERRORS++))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1/"
        return 0
    else
        echo "✗ MISSING: $1/"
        ((ERRORS++))
        return 1
    fi
}

echo "Checking Agent Structure..."
echo "---"

# Check main agent directory
check_dir "agent-business-lead"
check_dir "agent-business-lead/app"
check_dir "agent-business-lead/app/agents"

# Check main files
check_file "agent-business-lead/app/__init__.py"
check_file "agent-business-lead/app/config.py"
check_file "agent-business-lead/app/main.py"
check_file "agent-business-lead/app/agent_factory.py"
check_file "agent-business-lead/app/task_coordinator.py"
check_file "agent-business-lead/requirements.txt"

echo ""
echo "Checking Specialized Agents..."
echo "---"

# Check specialized agents
check_file "agent-business-lead/app/agents/__init__.py"
check_file "agent-business-lead/app/agents/sales_agent.py"
check_file "agent-business-lead/app/agents/marketing_agent.py"
check_file "agent-business-lead/app/agents/operations_agent.py"
check_file "agent-business-lead/app/agents/finance_agent.py"
check_file "agent-business-lead/app/agents/customer_service_agent.py"
check_file "agent-business-lead/app/agents/research_agent.py"
check_file "agent-business-lead/app/agents/development_agent.py"
check_file "agent-business-lead/app/agents/qa_agent.py"
check_file "agent-business-lead/app/agents/hr_agent.py"
check_file "agent-business-lead/app/agents/legal_agent.py"
check_file "agent-business-lead/app/agents/strategy_agent.py"
check_file "agent-business-lead/app/agents/pm_agent.py"

echo ""
echo "Checking Backend Integration..."
echo "---"

check_file "backend/app/api/business_agents.py"
check_file "backend/app/models.py"
check_file "backend/app/schemas.py"

echo ""
echo "Checking Configuration..."
echo "---"

check_file "Dockerfile.business-lead"
check_file "docker-compose.yml"

# Check if business-lead is in docker-compose
if grep -q "agent-business-lead:" docker-compose.yml; then
    echo "✓ docker-compose.yml includes business-lead service"
else
    echo "✗ docker-compose.yml missing business-lead service"
    ((ERRORS++))
fi

echo ""
echo "Checking Documentation..."
echo "---"

check_file "BUSINESS_AGENT_GUIDE.md"

echo ""
echo "Checking File Contents..."
echo "---"

# Check for key classes and functions
if grep -q "class BusinessCooperationLeadAgent" agent-business-lead/app/main.py; then
    echo "✓ BusinessCooperationLeadAgent class defined"
else
    echo "✗ Missing BusinessCooperationLeadAgent class"
    ((ERRORS++))
fi

if grep -q "class AgentFactory" agent-business-lead/app/agent_factory.py; then
    echo "✓ AgentFactory class defined"
else
    echo "✗ Missing AgentFactory class"
    ((ERRORS++))
fi

if grep -q "class TaskCoordinator" agent-business-lead/app/task_coordinator.py; then
    echo "✓ TaskCoordinator class defined"
else
    echo "✗ Missing TaskCoordinator class"
    ((ERRORS++))
fi

# Check for agent types
AGENT_COUNT=$(grep -c "class.*Agent(SpecializedAgent)" agent-business-lead/app/agents/*.py)
if [ "$AGENT_COUNT" -ge 12 ]; then
    echo "✓ Found $AGENT_COUNT specialized agent types"
else
    echo "⚠ Only found $AGENT_COUNT specialized agent types (expected 12)"
    ((WARNINGS++))
fi

# Check database models
if grep -q "class BusinessAgent(Base)" backend/app/models.py; then
    echo "✓ BusinessAgent database model defined"
else
    echo "✗ Missing BusinessAgent database model"
    ((ERRORS++))
fi

if grep -q "class BusinessTask(Base)" backend/app/models.py; then
    echo "✓ BusinessTask database model defined"
else
    echo "✗ Missing BusinessTask database model"
    ((ERRORS++))
fi

# Check API endpoints
if grep -q "router = APIRouter.*business-agents" backend/app/api/business_agents.py; then
    echo "✓ Business agents API router defined"
else
    echo "✗ Missing business agents API router"
    ((ERRORS++))
fi

if grep -q "task_router = APIRouter.*business-tasks" backend/app/api/business_agents.py; then
    echo "✓ Business tasks API router defined"
else
    echo "✗ Missing business tasks API router"
    ((ERRORS++))
fi

echo ""
echo "================================================================================"
echo "VALIDATION SUMMARY"
echo "================================================================================"

if [ $ERRORS -eq 0 ]; then
    echo "✓ All validation checks passed!"
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠ $WARNINGS warnings (non-critical)"
    fi
    echo ""
    echo "The Business Cooperation Agent System is ready to use!"
    echo "See BUSINESS_AGENT_GUIDE.md for usage instructions."
    exit 0
else
    echo "✗ $ERRORS errors found"
    if [ $WARNINGS -gt 0 ]; then
        echo "⚠ $WARNINGS warnings"
    fi
    echo ""
    echo "Please fix the errors above before deploying."
    exit 1
fi
