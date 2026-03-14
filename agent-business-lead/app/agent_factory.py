"""Agent factory for the Business Cooperation Lead Agent system.

Provides dynamic creation and lifecycle management for all 12 business agent types.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AGENT_TYPE_SALES = "sales"
AGENT_TYPE_MARKETING = "marketing"
AGENT_TYPE_OPERATIONS = "operations"
AGENT_TYPE_FINANCE = "finance"
AGENT_TYPE_CUSTOMER_SERVICE = "customer_service"
AGENT_TYPE_RESEARCH = "research"
AGENT_TYPE_DEVELOPMENT = "development"
AGENT_TYPE_QA = "qa"
AGENT_TYPE_HR = "hr"
AGENT_TYPE_LEGAL = "legal"
AGENT_TYPE_STRATEGY = "strategy"
AGENT_TYPE_PROJECT_MANAGEMENT = "project_management"

ALL_AGENT_TYPES: List[str] = [
    AGENT_TYPE_SALES,
    AGENT_TYPE_MARKETING,
    AGENT_TYPE_OPERATIONS,
    AGENT_TYPE_FINANCE,
    AGENT_TYPE_CUSTOMER_SERVICE,
    AGENT_TYPE_RESEARCH,
    AGENT_TYPE_DEVELOPMENT,
    AGENT_TYPE_QA,
    AGENT_TYPE_HR,
    AGENT_TYPE_LEGAL,
    AGENT_TYPE_STRATEGY,
    AGENT_TYPE_PROJECT_MANAGEMENT,
]

AGENT_STATUS_IDLE = "idle"
AGENT_STATUS_ACTIVE = "active"
AGENT_STATUS_BUSY = "busy"
AGENT_STATUS_PAUSED = "paused"
AGENT_STATUS_TERMINATED = "terminated"

# ---------------------------------------------------------------------------
# Domain-specific task handlers
# ---------------------------------------------------------------------------


def _handle_sales_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle sales-domain tasks: lead qualification, pipeline management, deal tracking."""
    action = task_data.get("action", "qualify_lead")
    if action == "qualify_lead":
        return {
            "action": action,
            "result": "lead_qualified",
            "score": task_data.get("lead_score", 50),
            "next_step": "schedule_demo",
        }
    if action == "close_deal":
        return {
            "action": action,
            "result": "deal_processed",
            "deal_value": task_data.get("deal_value", 0),
            "status": "pending_signature",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_marketing_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle marketing tasks: campaign creation, content strategy, brand analysis."""
    action = task_data.get("action", "create_campaign")
    if action == "create_campaign":
        return {
            "action": action,
            "campaign_id": f"camp-{uuid.uuid4().hex[:8]}",
            "channels": task_data.get("channels", ["email", "social"]),
            "status": "draft",
        }
    if action == "analyze_brand":
        return {
            "action": action,
            "sentiment": "positive",
            "reach": task_data.get("target_audience", "broad"),
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_operations_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle operations tasks: process optimization, resource allocation, logistics."""
    action = task_data.get("action", "optimize_process")
    if action == "optimize_process":
        return {
            "action": action,
            "process": task_data.get("process_name", "unnamed"),
            "recommendation": "reduce_handoffs",
            "estimated_improvement_pct": 15,
        }
    if action == "allocate_resources":
        return {
            "action": action,
            "resources": task_data.get("resources", []),
            "allocation_plan": "balanced",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_finance_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle finance tasks: budget analysis, forecasting, expense approval."""
    action = task_data.get("action", "analyze_budget")
    if action == "analyze_budget":
        return {
            "action": action,
            "period": task_data.get("period", "Q1"),
            "variance": task_data.get("variance_pct", 0),
            "recommendation": "within_budget" if task_data.get("variance_pct", 0) <= 5 else "review_required",
        }
    if action == "approve_expense":
        amount = task_data.get("amount", 0)
        return {
            "action": action,
            "amount": amount,
            "decision": "approved" if amount <= 10000 else "escalate_to_cfo",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_customer_service_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle customer service tasks: ticket resolution, escalation, feedback analysis."""
    action = task_data.get("action", "resolve_ticket")
    if action == "resolve_ticket":
        return {
            "action": action,
            "ticket_id": task_data.get("ticket_id", "unknown"),
            "resolution": "resolved",
            "satisfaction_score": 4.5,
        }
    if action == "analyze_feedback":
        return {
            "action": action,
            "theme": task_data.get("theme", "general"),
            "sentiment": "neutral",
            "priority": "medium",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_research_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle research tasks: market analysis, competitive intelligence, trend detection."""
    action = task_data.get("action", "market_analysis")
    if action == "market_analysis":
        return {
            "action": action,
            "market": task_data.get("market", "general"),
            "findings": ["growing_demand", "competitive_market"],
            "confidence": 0.82,
        }
    if action == "competitive_intelligence":
        return {
            "action": action,
            "competitors": task_data.get("competitors", []),
            "insights": "differentiation_opportunity_identified",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_development_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle development tasks: feature planning, code review, technical debt assessment."""
    action = task_data.get("action", "plan_feature")
    if action == "plan_feature":
        return {
            "action": action,
            "feature": task_data.get("feature_name", "unnamed"),
            "estimate_days": task_data.get("estimate_days", 5),
            "sprint": "next",
        }
    if action == "review_code":
        return {
            "action": action,
            "pr_id": task_data.get("pr_id", "unknown"),
            "status": "approved",
            "comments": [],
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_qa_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle QA tasks: test planning, bug triage, quality metrics reporting."""
    action = task_data.get("action", "run_tests")
    if action == "run_tests":
        return {
            "action": action,
            "suite": task_data.get("suite", "regression"),
            "passed": task_data.get("total_tests", 100),
            "failed": 0,
            "coverage_pct": 87,
        }
    if action == "triage_bug":
        return {
            "action": action,
            "bug_id": task_data.get("bug_id", "unknown"),
            "severity": task_data.get("severity", "medium"),
            "assigned_to": "development",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_hr_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle HR tasks: recruitment, onboarding, performance review scheduling."""
    action = task_data.get("action", "screen_candidate")
    if action == "screen_candidate":
        return {
            "action": action,
            "candidate_id": task_data.get("candidate_id", "unknown"),
            "recommendation": "advance_to_interview",
            "fit_score": 78,
        }
    if action == "schedule_review":
        return {
            "action": action,
            "employee_id": task_data.get("employee_id", "unknown"),
            "scheduled_date": "next_quarter",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_legal_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle legal tasks: contract review, compliance checks, risk assessment."""
    action = task_data.get("action", "review_contract")
    if action == "review_contract":
        return {
            "action": action,
            "contract_id": task_data.get("contract_id", "unknown"),
            "risk_level": "low",
            "clauses_flagged": [],
            "recommendation": "approve",
        }
    if action == "compliance_check":
        return {
            "action": action,
            "regulation": task_data.get("regulation", "GDPR"),
            "status": "compliant",
            "gaps": [],
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_strategy_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle strategy tasks: OKR planning, partnership evaluation, growth analysis."""
    action = task_data.get("action", "plan_okrs")
    if action == "plan_okrs":
        return {
            "action": action,
            "quarter": task_data.get("quarter", "Q2"),
            "objectives": task_data.get("objectives", []),
            "alignment_score": 0.9,
        }
    if action == "evaluate_partnership":
        return {
            "action": action,
            "partner": task_data.get("partner_name", "unknown"),
            "recommendation": "proceed_with_due_diligence",
            "strategic_fit": "high",
        }
    return {"action": action, "result": "processed", "details": task_data}


def _handle_project_management_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle project management tasks: sprint planning, risk tracking, stakeholder updates."""
    action = task_data.get("action", "plan_sprint")
    if action == "plan_sprint":
        return {
            "action": action,
            "sprint_number": task_data.get("sprint_number", 1),
            "capacity_points": task_data.get("capacity", 40),
            "committed_points": task_data.get("committed", 36),
        }
    if action == "track_risk":
        return {
            "action": action,
            "risk": task_data.get("risk_description", "unspecified"),
            "severity": task_data.get("severity", "medium"),
            "mitigation": "assigned_owner",
        }
    return {"action": action, "result": "processed", "details": task_data}


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

TASK_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    AGENT_TYPE_SALES: _handle_sales_task,
    AGENT_TYPE_MARKETING: _handle_marketing_task,
    AGENT_TYPE_OPERATIONS: _handle_operations_task,
    AGENT_TYPE_FINANCE: _handle_finance_task,
    AGENT_TYPE_CUSTOMER_SERVICE: _handle_customer_service_task,
    AGENT_TYPE_RESEARCH: _handle_research_task,
    AGENT_TYPE_DEVELOPMENT: _handle_development_task,
    AGENT_TYPE_QA: _handle_qa_task,
    AGENT_TYPE_HR: _handle_hr_task,
    AGENT_TYPE_LEGAL: _handle_legal_task,
    AGENT_TYPE_STRATEGY: _handle_strategy_task,
    AGENT_TYPE_PROJECT_MANAGEMENT: _handle_project_management_task,
}

# ---------------------------------------------------------------------------
# BusinessAgentInstance — in-memory agent object
# ---------------------------------------------------------------------------


class BusinessAgentInstance:
    """In-memory representation of a running business agent."""

    def __init__(
        self,
        agent_type: str,
        name: str,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if agent_type not in ALL_AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}")

        self.agent_id: str = f"business-{agent_type}-{uuid.uuid4().hex[:8]}"
        self.agent_type: str = agent_type
        self.name: str = name
        self.description: Optional[str] = description
        self.capabilities: List[str] = capabilities or AGENT_DEFAULT_CAPABILITIES.get(agent_type, [])
        self.config: Dict[str, Any] = config or {}
        self.status: str = AGENT_STATUS_IDLE
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.created_at: datetime = datetime.utcnow()
        self.last_active_at: Optional[datetime] = None
        self.terminated_at: Optional[datetime] = None
        self._handler: Callable[[Dict[str, Any]], Dict[str, Any]] = TASK_HANDLERS[agent_type]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def activate(self) -> None:
        """Transition the agent to active status."""
        if self.status == AGENT_STATUS_TERMINATED:
            raise RuntimeError(f"Agent {self.agent_id} is terminated and cannot be reactivated.")
        self.status = AGENT_STATUS_ACTIVE
        self.last_active_at = datetime.utcnow()
        logger.info("Agent %s (%s) activated", self.agent_id, self.agent_type)

    def pause(self) -> None:
        """Pause a running agent."""
        if self.status not in (AGENT_STATUS_ACTIVE, AGENT_STATUS_BUSY):
            raise RuntimeError(f"Agent {self.agent_id} cannot be paused from status '{self.status}'.")
        self.status = AGENT_STATUS_PAUSED
        logger.info("Agent %s paused", self.agent_id)

    def resume(self) -> None:
        """Resume a paused agent."""
        if self.status != AGENT_STATUS_PAUSED:
            raise RuntimeError(f"Agent {self.agent_id} is not paused.")
        self.status = AGENT_STATUS_ACTIVE
        logger.info("Agent %s resumed", self.agent_id)

    def terminate(self) -> None:
        """Terminate the agent permanently."""
        self.status = AGENT_STATUS_TERMINATED
        self.terminated_at = datetime.utcnow()
        logger.info("Agent %s terminated", self.agent_id)

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a domain-specific task and return the result."""
        if self.status == AGENT_STATUS_TERMINATED:
            raise RuntimeError(f"Agent {self.agent_id} is terminated.")
        if self.status == AGENT_STATUS_PAUSED:
            raise RuntimeError(f"Agent {self.agent_id} is paused.")

        self.status = AGENT_STATUS_BUSY
        self.last_active_at = datetime.utcnow()

        try:
            result = self._handler(task_data)
            self.tasks_completed += 1
            logger.info(
                "Agent %s completed task (total=%d)", self.agent_id, self.tasks_completed
            )
        except Exception as exc:
            self.tasks_failed += 1
            logger.error("Agent %s task failed: %s", self.agent_id, exc)
            self.status = AGENT_STATUS_ACTIVE
            raise
        finally:
            if self.status == AGENT_STATUS_BUSY:
                self.status = AGENT_STATUS_ACTIVE

        return result

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable dictionary representation."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "config": self.config,
            "status": self.status,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "terminated_at": self.terminated_at.isoformat() if self.terminated_at else None,
        }


# ---------------------------------------------------------------------------
# Default capabilities per agent type
# ---------------------------------------------------------------------------

AGENT_DEFAULT_CAPABILITIES: Dict[str, List[str]] = {
    AGENT_TYPE_SALES: ["lead_qualification", "pipeline_management", "deal_tracking", "forecasting"],
    AGENT_TYPE_MARKETING: ["campaign_creation", "content_strategy", "brand_analysis", "seo"],
    AGENT_TYPE_OPERATIONS: ["process_optimization", "resource_allocation", "logistics", "kpi_tracking"],
    AGENT_TYPE_FINANCE: ["budget_analysis", "forecasting", "expense_approval", "reporting"],
    AGENT_TYPE_CUSTOMER_SERVICE: ["ticket_resolution", "escalation", "feedback_analysis", "sla_tracking"],
    AGENT_TYPE_RESEARCH: ["market_analysis", "competitive_intelligence", "trend_detection", "data_synthesis"],
    AGENT_TYPE_DEVELOPMENT: ["feature_planning", "code_review", "technical_debt", "architecture"],
    AGENT_TYPE_QA: ["test_planning", "bug_triage", "quality_metrics", "regression_testing"],
    AGENT_TYPE_HR: ["recruitment", "onboarding", "performance_review", "policy_management"],
    AGENT_TYPE_LEGAL: ["contract_review", "compliance_check", "risk_assessment", "ip_management"],
    AGENT_TYPE_STRATEGY: ["okr_planning", "partnership_evaluation", "growth_analysis", "roadmapping"],
    AGENT_TYPE_PROJECT_MANAGEMENT: ["sprint_planning", "risk_tracking", "stakeholder_updates", "dependency_management"],
}

# ---------------------------------------------------------------------------
# AgentFactory
# ---------------------------------------------------------------------------


class AgentFactory:
    """
    Factory for creating and managing BusinessAgentInstance objects.

    Supports lifecycle management (create, activate, pause, resume, terminate)
    and enforces an optional ceiling on the total number of concurrent agents.
    """

    def __init__(self, max_concurrent_agents: int = 50, creation_enabled: bool = True) -> None:
        self.max_concurrent_agents: int = max_concurrent_agents
        self.creation_enabled: bool = creation_enabled
        self._agents: Dict[str, BusinessAgentInstance] = {}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active_agent_count(self) -> int:
        """Count of non-terminated agents."""
        return sum(
            1 for a in self._agents.values() if a.status != AGENT_STATUS_TERMINATED
        )

    @property
    def all_agents(self) -> List[BusinessAgentInstance]:
        return list(self._agents.values())

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_agent(
        self,
        agent_type: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> BusinessAgentInstance:
        """
        Instantiate and register a new agent.

        Raises:
            RuntimeError: If creation is disabled or the concurrent-agent ceiling is reached.
            ValueError: If agent_type is invalid.
        """
        if not self.creation_enabled:
            raise RuntimeError("Agent creation is currently disabled.")

        if self.active_agent_count >= self.max_concurrent_agents:
            raise RuntimeError(
                f"Maximum concurrent agents ({self.max_concurrent_agents}) reached."
            )

        resolved_name = name or f"{agent_type.replace('_', ' ').title()} Agent"
        agent = BusinessAgentInstance(
            agent_type=agent_type,
            name=resolved_name,
            description=description,
            capabilities=capabilities,
            config=config,
        )
        self._agents[agent.agent_id] = agent
        logger.info("Factory created agent %s (type=%s)", agent.agent_id, agent_type)
        return agent

    def get_agent(self, agent_id: str) -> Optional[BusinessAgentInstance]:
        return self._agents.get(agent_id)

    def get_agents_by_type(self, agent_type: str) -> List[BusinessAgentInstance]:
        return [a for a in self._agents.values() if a.agent_type == agent_type]

    def get_available_agent(self, agent_type: Optional[str] = None) -> Optional[BusinessAgentInstance]:
        """Return the first idle or active (non-busy) agent of the given type."""
        candidates = self._agents.values() if agent_type is None else self.get_agents_by_type(agent_type)
        for agent in candidates:
            if agent.status in (AGENT_STATUS_IDLE, AGENT_STATUS_ACTIVE):
                return agent
        return None

    def terminate_agent(self, agent_id: str) -> None:
        """Terminate an agent by ID."""
        agent = self._agents.get(agent_id)
        if agent is None:
            raise KeyError(f"Agent '{agent_id}' not found.")
        agent.terminate()

    def purge_terminated(self) -> int:
        """Remove terminated agents from the registry. Returns count removed."""
        terminated_ids = [
            agent_id
            for agent_id, agent in self._agents.items()
            if agent.status == AGENT_STATUS_TERMINATED
        ]
        for agent_id in terminated_ids:
            del self._agents[agent_id]
        logger.info("Purged %d terminated agents", len(terminated_ids))
        return len(terminated_ids)

    def summary(self) -> Dict[str, Any]:
        """Return a summary of the factory state."""
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for agent in self._agents.values():
            by_type[agent.agent_type] = by_type.get(agent.agent_type, 0) + 1
            by_status[agent.status] = by_status.get(agent.status, 0) + 1
        return {
            "total_agents": len(self._agents),
            "active_agents": self.active_agent_count,
            "max_concurrent_agents": self.max_concurrent_agents,
            "creation_enabled": self.creation_enabled,
            "by_type": by_type,
            "by_status": by_status,
        }
