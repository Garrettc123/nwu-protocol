"""Perplexity API routes - Web-grounded search and research endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from ..services.perplexity_service import perplexity_service, AVAILABLE_MODELS

router = APIRouter(prefix="/api/v1/perplexity", tags=["perplexity"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query or question")
    model: str = Field("sonar", description="Perplexity model to use")
    system_prompt: Optional[str] = Field(None, description="Optional system-level instruction")
    max_tokens: int = Field(1024, ge=64, le=8192, description="Maximum tokens in response")
    temperature: float = Field(0.2, ge=0.0, le=2.0, description="Sampling temperature")


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Topic or question to research")
    depth: str = Field("standard", description="'standard' (sonar-pro) or 'deep' (sonar-deep-research)")
    system_prompt: Optional[str] = Field(None, description="Optional research guidance")


class FactCheckRequest(BaseModel):
    claim: str = Field(..., min_length=1, description="The claim or statement to verify")


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, description="Conversation history")
    model: str = Field("sonar", description="Perplexity model to use")
    max_tokens: int = Field(1024, ge=64, le=8192, description="Maximum tokens in response")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")


class PerplexityResponse(BaseModel):
    success: bool
    content: str
    citations: List[str] = []
    model: str
    usage: Dict[str, Any] = {}
    finish_reason: Optional[str] = None


class MarketAnalysisRequest(BaseModel):
    market: str = Field(..., min_length=1, description="Market, sector, or asset to analyze")


class TechnicalResearchRequest(BaseModel):
    subject: str = Field(..., min_length=1, description="Technology, library, or concept to research")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/status")
async def perplexity_status():
    """Check whether the Perplexity service is configured and ready."""
    configured = perplexity_service.is_configured()
    return {
        "configured": configured,
        "message": "Perplexity API is ready" if configured else "PERPLEXITY_API_KEY is not set",
        "available_models": list(AVAILABLE_MODELS.keys()),
    }


@router.get("/models")
async def list_models():
    """Return all supported Perplexity models with descriptions."""
    return {"models": AVAILABLE_MODELS}


@router.post("/search", response_model=PerplexityResponse, status_code=status.HTTP_200_OK)
async def search(request: SearchRequest):
    """
    Run a fast, web-grounded search query.

    Uses Perplexity's sonar family to answer questions with live internet data
    and inline source citations.
    """
    _require_configured()
    try:
        result = await perplexity_service.search(
            query=request.query,
            model=request.model,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        return PerplexityResponse(success=True, **result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/research", response_model=PerplexityResponse, status_code=status.HTTP_200_OK)
async def research(request: ResearchRequest):
    """
    Conduct in-depth research on a topic.

    'standard' depth uses sonar-pro; 'deep' depth uses sonar-deep-research
    for multi-step, expert-level synthesis (longer latency, richer output).
    """
    _require_configured()
    if request.depth not in ("standard", "deep"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'depth' must be 'standard' or 'deep'",
        )
    try:
        result = await perplexity_service.research(
            topic=request.topic,
            depth=request.depth,
            system_prompt=request.system_prompt,
        )
        return PerplexityResponse(success=True, **result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/fact-check", response_model=PerplexityResponse, status_code=status.HTTP_200_OK)
async def fact_check(request: FactCheckRequest):
    """
    Verify a claim against live web sources.

    Returns a verdict (True / False / Partially True / Unverifiable),
    a concise explanation, and supporting citations.
    """
    _require_configured()
    try:
        result = await perplexity_service.fact_check(claim=request.claim)
        return PerplexityResponse(success=True, **result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/chat", response_model=PerplexityResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Multi-turn conversational search.

    Send a conversation history and receive a web-grounded reply.
    Each assistant turn can include live citations.
    """
    _require_configured()
    messages = [m.model_dump() for m in request.messages]
    try:
        result = await perplexity_service.chat(
            messages=messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        return PerplexityResponse(success=True, **result)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/market-analysis", response_model=PerplexityResponse, status_code=status.HTTP_200_OK)
async def market_analysis(request: MarketAnalysisRequest):
    """
    Generate a structured market analysis using live web data.

    Covers current overview, trends, key players, risks, and near-term outlook.
    """
    _require_configured()
    try:
        from ..services.research_agent import ResearchAgent
        agent = ResearchAgent("api-market-agent", {"model": "sonar-pro"})
        result = await agent._market_analysis({"market": request.market})
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.get("error"))
        return PerplexityResponse(
            success=True,
            content=result["content"],
            citations=result.get("citations", []),
            model=result.get("model", "sonar-pro"),
            usage=result.get("usage", {}),
            finish_reason=result.get("finish_reason"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/technical-research", response_model=PerplexityResponse, status_code=status.HTTP_200_OK)
async def technical_research(request: TechnicalResearchRequest):
    """
    Deep technical research on a technology, library, or concept.

    Returns architecture patterns, best practices, code examples, limitations,
    and links to authoritative documentation.
    """
    _require_configured()
    try:
        from ..services.research_agent import ResearchAgent
        agent = ResearchAgent("api-tech-agent", {"model": "sonar-pro"})
        result = await agent._technical_research({"subject": request.subject})
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.get("error"))
        return PerplexityResponse(
            success=True,
            content=result["content"],
            citations=result.get("citations", []),
            model=result.get("model", "sonar-pro"),
            usage=result.get("usage", {}),
            finish_reason=result.get("finish_reason"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _require_configured():
    if not perplexity_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Perplexity API is not configured. Set PERPLEXITY_API_KEY in your environment.",
        )
