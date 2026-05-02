"""Perplexity API Service - Real-time web search and research for NWU agents."""

import logging
from typing import Optional, List, Dict, Any
import httpx

from ..config import settings

logger = logging.getLogger(__name__)

PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

AVAILABLE_MODELS = {
    "sonar": "Fast, cost-efficient search with grounded web results",
    "sonar-pro": "Advanced search with deeper context and source citations",
    "sonar-reasoning": "Step-by-step reasoning with live web search",
    "sonar-reasoning-pro": "Extended reasoning chains with pro-level search",
    "sonar-deep-research": "Multi-step expert-level research with comprehensive synthesis",
}


class PerplexityService:
    """
    Client for the Perplexity AI API.

    Provides web-grounded search, multi-step research, and conversational
    capabilities to NWU agents via Perplexity's sonar model family.
    """

    def __init__(self):
        self._api_key: Optional[str] = getattr(settings, "perplexity_api_key", None)
        self._client: Optional[httpx.AsyncClient] = None

    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=PERPLEXITY_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        model: str = "sonar",
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        return_citations: bool = True,
    ) -> Dict[str, Any]:
        """
        Run a single-turn web-grounded search query.

        Args:
            query: The search question or prompt.
            model: Perplexity model to use.
            system_prompt: Optional system message to guide the model.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (lower = more factual).
            return_citations: Whether to include citation URLs.

        Returns:
            Dict with keys: content, citations, model, usage.
        """
        if not self.is_configured():
            raise RuntimeError("PERPLEXITY_API_KEY is not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if return_citations:
            payload["return_citations"] = True

        client = await self._get_client()
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        return {
            "content": choice["message"]["content"],
            "citations": data.get("citations", []),
            "model": data.get("model", model),
            "usage": data.get("usage", {}),
            "finish_reason": choice.get("finish_reason"),
        }

    async def research(
        self,
        topic: str,
        depth: str = "standard",
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct in-depth research on a topic.

        Args:
            topic: Research topic or question.
            depth: "standard" uses sonar-pro; "deep" uses sonar-deep-research.
            system_prompt: Optional guidance for the research scope.

        Returns:
            Dict with keys: content, citations, model, usage.
        """
        model = "sonar-deep-research" if depth == "deep" else "sonar-pro"
        default_system = (
            "You are an expert research assistant. Provide comprehensive, "
            "well-structured analysis with accurate citations. Cover multiple "
            "perspectives and synthesize information into actionable insights."
        )
        return await self.search(
            query=topic,
            model=model,
            system_prompt=system_prompt or default_system,
            max_tokens=4096,
            temperature=0.1,
        )

    async def fact_check(self, claim: str) -> Dict[str, Any]:
        """
        Fact-check a specific claim using live web sources.

        Args:
            claim: The statement to verify.

        Returns:
            Dict with verdict, explanation, citations.
        """
        system_prompt = (
            "You are a rigorous fact-checker. Evaluate the claim using current, "
            "authoritative web sources. Return: 1) Verdict (True/False/Partially True/Unverifiable), "
            "2) Explanation with evidence, 3) Key sources. Be concise and objective."
        )
        result = await self.search(
            query=f"Fact check this claim: {claim}",
            model="sonar-pro",
            system_prompt=system_prompt,
            max_tokens=1024,
            temperature=0.1,
        )
        return result

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "sonar",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Multi-turn conversation with web search grounding.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}.
            model: Perplexity model to use.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature.

        Returns:
            Dict with keys: content, citations, model, usage.
        """
        if not self.is_configured():
            raise RuntimeError("PERPLEXITY_API_KEY is not configured")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "return_citations": True,
        }

        client = await self._get_client()
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        return {
            "content": choice["message"]["content"],
            "citations": data.get("citations", []),
            "model": data.get("model", model),
            "usage": data.get("usage", {}),
            "finish_reason": choice.get("finish_reason"),
        }

    def get_available_models(self) -> Dict[str, str]:
        return AVAILABLE_MODELS


# Global service instance
perplexity_service = PerplexityService()
