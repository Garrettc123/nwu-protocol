"""Research Agent - NWU agent powered by Perplexity for real-time web intelligence."""

import logging
from typing import Dict, Any, Optional

from .base_agent import BaseAgent
from .agent_orchestrator import AgentType, AgentStatus
from .perplexity_service import perplexity_service

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent - Uses Perplexity AI to answer questions with live web data.

    Handles tasks: web_search, research_topic, fact_check,
    market_analysis, technical_research.
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, AgentType.RESEARCHER, config)
        self._default_model: str = config.get("model", "sonar") if config else "sonar"

    async def initialize(self):
        logger.info(f"Research Agent {self.agent_id} initializing...")
        if not perplexity_service.is_configured():
            logger.warning(
                f"Research Agent {self.agent_id}: PERPLEXITY_API_KEY not set — "
                "search tasks will fail until the key is configured."
            )
        else:
            logger.info(f"Research Agent {self.agent_id} ready (Perplexity configured)")

    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        dispatch = {
            "web_search": self._web_search,
            "research_topic": self._research_topic,
            "fact_check": self._fact_check,
            "market_analysis": self._market_analysis,
            "technical_research": self._technical_research,
        }
        handler = dispatch.get(task_type)
        if handler is None:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
        return await handler(task_data)

    # ------------------------------------------------------------------
    # Task handlers
    # ------------------------------------------------------------------

    async def _web_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        query = data.get("query", "")
        if not query:
            return {"success": False, "error": "Missing 'query' field"}

        model = data.get("model", self._default_model)
        system_prompt = data.get("system_prompt")
        max_tokens = int(data.get("max_tokens", 1024))

        logger.info(f"Research Agent {self.agent_id} searching: {query[:80]}")
        try:
            result = await perplexity_service.search(
                query=query,
                model=model,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )
            return {"success": True, "agent_id": self.agent_id, **result}
        except Exception as exc:
            logger.error(f"Research Agent {self.agent_id} search failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def _research_topic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        topic = data.get("topic", "")
        if not topic:
            return {"success": False, "error": "Missing 'topic' field"}

        depth = data.get("depth", "standard")
        system_prompt = data.get("system_prompt")

        logger.info(f"Research Agent {self.agent_id} researching ({depth}): {topic[:80]}")
        try:
            result = await perplexity_service.research(
                topic=topic,
                depth=depth,
                system_prompt=system_prompt,
            )
            return {"success": True, "agent_id": self.agent_id, **result}
        except Exception as exc:
            logger.error(f"Research Agent {self.agent_id} research failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def _fact_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        claim = data.get("claim", "")
        if not claim:
            return {"success": False, "error": "Missing 'claim' field"}

        logger.info(f"Research Agent {self.agent_id} fact-checking: {claim[:80]}")
        try:
            result = await perplexity_service.fact_check(claim=claim)
            return {"success": True, "agent_id": self.agent_id, **result}
        except Exception as exc:
            logger.error(f"Research Agent {self.agent_id} fact-check failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def _market_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        market = data.get("market", "")
        if not market:
            return {"success": False, "error": "Missing 'market' field"}

        system_prompt = (
            "You are a financial and market analyst. Provide a structured analysis covering: "
            "1) Current market overview, 2) Key trends and drivers, 3) Major players, "
            "4) Risks and opportunities, 5) Short-term outlook. Use current data and cite sources."
        )
        query = f"Provide a comprehensive market analysis for: {market}"
        logger.info(f"Research Agent {self.agent_id} market analysis: {market[:80]}")
        try:
            result = await perplexity_service.search(
                query=query,
                model="sonar-pro",
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.1,
            )
            return {"success": True, "agent_id": self.agent_id, "market": market, **result}
        except Exception as exc:
            logger.error(f"Research Agent {self.agent_id} market analysis failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def _technical_research(self, data: Dict[str, Any]) -> Dict[str, Any]:
        subject = data.get("subject", "")
        if not subject:
            return {"success": False, "error": "Missing 'subject' field"}

        system_prompt = (
            "You are a senior software engineer and technical researcher. "
            "Provide in-depth technical analysis with: architecture patterns, best practices, "
            "code examples where relevant, known limitations, and authoritative documentation links."
        )
        query = f"Technical deep-dive: {subject}"
        logger.info(f"Research Agent {self.agent_id} technical research: {subject[:80]}")
        try:
            result = await perplexity_service.search(
                query=query,
                model="sonar-pro",
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.2,
            )
            return {"success": True, "agent_id": self.agent_id, "subject": subject, **result}
        except Exception as exc:
            logger.error(f"Research Agent {self.agent_id} technical research failed: {exc}")
            return {"success": False, "error": str(exc)}
