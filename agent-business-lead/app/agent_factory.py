"""Agent Factory - Creates and manages specialized agents."""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialized agents."""
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCE = "finance"
    CUSTOMER_SERVICE = "customer_service"
    RESEARCH = "research"
    DEVELOPMENT = "development"
    QUALITY_ASSURANCE = "quality_assurance"
    HUMAN_RESOURCES = "human_resources"
    LEGAL = "legal"
    STRATEGY = "strategy"
    PROJECT_MANAGEMENT = "project_management"


class AgentStatus(Enum):
    """Agent status states."""
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


class SpecializedAgent:
    """Base class for specialized agents."""

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        name: str,
        capabilities: List[str],
        config: Dict[str, Any]
    ):
        """Initialize specialized agent."""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.capabilities = capabilities
        self.config = config
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.tasks_completed = 0
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task assigned to this agent."""
        self.status = AgentStatus.BUSY
        self.current_task = task
        self.last_active = datetime.utcnow()

        try:
            logger.info(f"Agent {self.name} ({self.agent_type.value}) executing task: {task.get('task_id')}")
            result = await self._process_task(task)
            self.tasks_completed += 1
            self.status = AgentStatus.IDLE
            self.current_task = None
            return result
        except Exception as e:
            logger.error(f"Agent {self.name} task execution failed: {e}")
            self.status = AgentStatus.ERROR
            raise

    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process the specific task (to be overridden by subclasses)."""
        raise NotImplementedError("Subclasses must implement _process_task")

    def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.name,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }

    def pause(self):
        """Pause the agent."""
        self.status = AgentStatus.PAUSED
        logger.info(f"Agent {self.name} paused")

    def resume(self):
        """Resume the agent."""
        self.status = AgentStatus.IDLE
        logger.info(f"Agent {self.name} resumed")

    def terminate(self):
        """Terminate the agent."""
        self.status = AgentStatus.TERMINATED
        logger.info(f"Agent {self.name} terminated")


class AgentFactory:
    """Factory for creating and managing specialized agents."""

    def __init__(self, max_agents: int = 10):
        """Initialize the agent factory."""
        self.max_agents = max_agents
        self.agents: Dict[str, SpecializedAgent] = {}
        self.agent_types = {
            AgentType.SALES: self._create_sales_agent,
            AgentType.MARKETING: self._create_marketing_agent,
            AgentType.OPERATIONS: self._create_operations_agent,
            AgentType.FINANCE: self._create_finance_agent,
            AgentType.CUSTOMER_SERVICE: self._create_customer_service_agent,
            AgentType.RESEARCH: self._create_research_agent,
            AgentType.DEVELOPMENT: self._create_development_agent,
            AgentType.QUALITY_ASSURANCE: self._create_qa_agent,
            AgentType.HUMAN_RESOURCES: self._create_hr_agent,
            AgentType.LEGAL: self._create_legal_agent,
            AgentType.STRATEGY: self._create_strategy_agent,
            AgentType.PROJECT_MANAGEMENT: self._create_pm_agent,
        }

    def create_agent(
        self,
        agent_type: AgentType,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[SpecializedAgent]:
        """Create a new specialized agent."""
        if len(self.agents) >= self.max_agents:
            logger.warning(f"Cannot create agent: maximum capacity ({self.max_agents}) reached")
            return None

        agent_id = str(uuid.uuid4())
        if name is None:
            name = f"{agent_type.value}-{agent_id[:8]}"

        if config is None:
            config = {}

        if agent_type in self.agent_types:
            agent = self.agent_types[agent_type](agent_id, name, config)
            self.agents[agent_id] = agent
            logger.info(f"Created agent: {name} ({agent_type.value}) with ID {agent_id}")
            return agent
        else:
            logger.error(f"Unknown agent type: {agent_type}")
            return None

    def get_agent(self, agent_id: str) -> Optional[SpecializedAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def get_agents_by_type(self, agent_type: AgentType) -> List[SpecializedAgent]:
        """Get all agents of a specific type."""
        return [agent for agent in self.agents.values() if agent.agent_type == agent_type]

    def get_available_agents(self) -> List[SpecializedAgent]:
        """Get all idle agents."""
        return [agent for agent in self.agents.values() if agent.status == AgentStatus.IDLE]

    def get_all_agents(self) -> List[SpecializedAgent]:
        """Get all agents."""
        return list(self.agents.values())

    def terminate_agent(self, agent_id: str) -> bool:
        """Terminate and remove an agent."""
        agent = self.agents.get(agent_id)
        if agent:
            agent.terminate()
            del self.agents[agent_id]
            logger.info(f"Terminated agent: {agent.name} ({agent_id})")
            return True
        return False

    def get_factory_status(self) -> Dict[str, Any]:
        """Get factory status."""
        return {
            "total_agents": len(self.agents),
            "max_agents": self.max_agents,
            "available_capacity": self.max_agents - len(self.agents),
            "agents_by_type": {
                agent_type.value: len(self.get_agents_by_type(agent_type))
                for agent_type in AgentType
            },
            "agents_by_status": {
                status.value: len([a for a in self.agents.values() if a.status == status])
                for status in AgentStatus
            }
        }

    # Agent creation methods for each type
    def _create_sales_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a sales agent."""
        from .agents.sales_agent import SalesAgent
        return SalesAgent(
            agent_id=agent_id,
            agent_type=AgentType.SALES,
            name=name,
            capabilities=["lead_generation", "client_outreach", "deal_closing", "relationship_management"],
            config=config
        )

    def _create_marketing_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a marketing agent."""
        from .agents.marketing_agent import MarketingAgent
        return MarketingAgent(
            agent_id=agent_id,
            agent_type=AgentType.MARKETING,
            name=name,
            capabilities=["content_creation", "campaign_management", "social_media", "analytics"],
            config=config
        )

    def _create_operations_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create an operations agent."""
        from .agents.operations_agent import OperationsAgent
        return OperationsAgent(
            agent_id=agent_id,
            agent_type=AgentType.OPERATIONS,
            name=name,
            capabilities=["process_optimization", "resource_management", "workflow_automation", "monitoring"],
            config=config
        )

    def _create_finance_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a finance agent."""
        from .agents.finance_agent import FinanceAgent
        return FinanceAgent(
            agent_id=agent_id,
            agent_type=AgentType.FINANCE,
            name=name,
            capabilities=["budget_management", "financial_reporting", "forecasting", "invoice_processing"],
            config=config
        )

    def _create_customer_service_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a customer service agent."""
        from .agents.customer_service_agent import CustomerServiceAgent
        return CustomerServiceAgent(
            agent_id=agent_id,
            agent_type=AgentType.CUSTOMER_SERVICE,
            name=name,
            capabilities=["ticket_management", "customer_support", "issue_resolution", "feedback_collection"],
            config=config
        )

    def _create_research_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a research agent."""
        from .agents.research_agent import ResearchAgent
        return ResearchAgent(
            agent_id=agent_id,
            agent_type=AgentType.RESEARCH,
            name=name,
            capabilities=["market_research", "competitive_analysis", "trend_analysis", "data_collection"],
            config=config
        )

    def _create_development_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a development agent."""
        from .agents.development_agent import DevelopmentAgent
        return DevelopmentAgent(
            agent_id=agent_id,
            agent_type=AgentType.DEVELOPMENT,
            name=name,
            capabilities=["code_development", "bug_fixing", "feature_implementation", "code_review"],
            config=config
        )

    def _create_qa_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a QA agent."""
        from .agents.qa_agent import QAAgent
        return QAAgent(
            agent_id=agent_id,
            agent_type=AgentType.QUALITY_ASSURANCE,
            name=name,
            capabilities=["testing", "quality_control", "bug_detection", "test_automation"],
            config=config
        )

    def _create_hr_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create an HR agent."""
        from .agents.hr_agent import HRAgent
        return HRAgent(
            agent_id=agent_id,
            agent_type=AgentType.HUMAN_RESOURCES,
            name=name,
            capabilities=["recruitment", "onboarding", "performance_review", "training"],
            config=config
        )

    def _create_legal_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a legal agent."""
        from .agents.legal_agent import LegalAgent
        return LegalAgent(
            agent_id=agent_id,
            agent_type=AgentType.LEGAL,
            name=name,
            capabilities=["contract_review", "compliance_check", "risk_assessment", "legal_research"],
            config=config
        )

    def _create_strategy_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a strategy agent."""
        from .agents.strategy_agent import StrategyAgent
        return StrategyAgent(
            agent_id=agent_id,
            agent_type=AgentType.STRATEGY,
            name=name,
            capabilities=["strategic_planning", "goal_setting", "performance_analysis", "decision_support"],
            config=config
        )

    def _create_pm_agent(self, agent_id: str, name: str, config: Dict[str, Any]) -> SpecializedAgent:
        """Create a project management agent."""
        from .agents.pm_agent import PMAgent
        return PMAgent(
            agent_id=agent_id,
            agent_type=AgentType.PROJECT_MANAGEMENT,
            name=name,
            capabilities=["project_planning", "task_tracking", "team_coordination", "milestone_management"],
            config=config
        )
