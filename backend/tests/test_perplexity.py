"""Tests for Perplexity API endpoints and service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Status / models (no API key required)
# ---------------------------------------------------------------------------

def test_perplexity_status_unconfigured():
    """Status endpoint reports unconfigured when no API key is set."""
    with patch("app.api.perplexity.perplexity_service") as mock_svc:
        mock_svc.is_configured.return_value = False
        response = client.get("/api/v1/perplexity/status")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert "PERPLEXITY_API_KEY" in data["message"]


def test_perplexity_status_configured():
    """Status endpoint reports configured when API key is present."""
    with patch("app.api.perplexity.perplexity_service") as mock_svc:
        mock_svc.is_configured.return_value = True
        response = client.get("/api/v1/perplexity/status")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert isinstance(data["available_models"], list)
    assert len(data["available_models"]) > 0


def test_perplexity_list_models():
    """Models endpoint returns all supported models."""
    response = client.get("/api/v1/perplexity/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "sonar" in data["models"]
    assert "sonar-pro" in data["models"]
    assert "sonar-deep-research" in data["models"]


# ---------------------------------------------------------------------------
# 503 when not configured
# ---------------------------------------------------------------------------

def _unconfigured_service():
    mock = MagicMock()
    mock.is_configured.return_value = False
    return mock


@pytest.mark.parametrize("path,payload", [
    ("/api/v1/perplexity/search", {"query": "test"}),
    ("/api/v1/perplexity/research", {"topic": "test"}),
    ("/api/v1/perplexity/fact-check", {"claim": "test"}),
    ("/api/v1/perplexity/chat", {"messages": [{"role": "user", "content": "hi"}]}),
    ("/api/v1/perplexity/market-analysis", {"market": "AI"}),
    ("/api/v1/perplexity/technical-research", {"subject": "FastAPI"}),
])
def test_returns_503_when_not_configured(path, payload):
    """All write endpoints return 503 when PERPLEXITY_API_KEY is not set."""
    with patch("app.api.perplexity.perplexity_service", _unconfigured_service()):
        response = client.post(path, json=payload)
    assert response.status_code == 503
    assert "PERPLEXITY_API_KEY" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Happy-path with mocked Perplexity responses
# ---------------------------------------------------------------------------

MOCK_RESULT = {
    "content": "This is a test answer.",
    "citations": ["https://example.com"],
    "model": "sonar",
    "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    "finish_reason": "stop",
}


def _configured_service(result=None):
    mock = MagicMock()
    mock.is_configured.return_value = True
    mock.search = AsyncMock(return_value=result or MOCK_RESULT)
    mock.research = AsyncMock(return_value=result or MOCK_RESULT)
    mock.fact_check = AsyncMock(return_value=result or MOCK_RESULT)
    mock.chat = AsyncMock(return_value=result or MOCK_RESULT)
    return mock


def test_search_success():
    """Search endpoint returns content and citations on success."""
    with patch("app.api.perplexity.perplexity_service", _configured_service()):
        response = client.post(
            "/api/v1/perplexity/search",
            json={"query": "What is the NWU Protocol?"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["content"] == "This is a test answer."
    assert data["citations"] == ["https://example.com"]


def test_search_custom_model():
    """Search endpoint forwards the requested model."""
    svc = _configured_service()
    with patch("app.api.perplexity.perplexity_service", svc):
        client.post(
            "/api/v1/perplexity/search",
            json={"query": "hello", "model": "sonar-pro"},
        )
    svc.search.assert_awaited_once()
    _, kwargs = svc.search.call_args
    assert kwargs.get("model") == "sonar-pro"


def test_research_standard_depth():
    """Research endpoint uses standard depth by default."""
    svc = _configured_service()
    with patch("app.api.perplexity.perplexity_service", svc):
        response = client.post(
            "/api/v1/perplexity/research",
            json={"topic": "Distributed AI agents"},
        )
    assert response.status_code == 200
    svc.research.assert_awaited_once()
    _, kwargs = svc.research.call_args
    assert kwargs.get("depth") == "standard"


def test_research_deep_depth():
    """Research endpoint accepts deep depth."""
    svc = _configured_service()
    with patch("app.api.perplexity.perplexity_service", svc):
        response = client.post(
            "/api/v1/perplexity/research",
            json={"topic": "Blockchain consensus", "depth": "deep"},
        )
    assert response.status_code == 200
    _, kwargs = svc.research.call_args
    assert kwargs.get("depth") == "deep"


def test_research_invalid_depth():
    """Research endpoint rejects unknown depth values."""
    with patch("app.api.perplexity.perplexity_service", _configured_service()):
        response = client.post(
            "/api/v1/perplexity/research",
            json={"topic": "test", "depth": "turbo"},
        )
    assert response.status_code == 422


def test_fact_check_success():
    """Fact-check endpoint returns a verdict."""
    with patch("app.api.perplexity.perplexity_service", _configured_service()):
        response = client.post(
            "/api/v1/perplexity/fact-check",
            json={"claim": "The Earth is flat."},
        )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_chat_success():
    """Chat endpoint handles multi-turn conversation."""
    with patch("app.api.perplexity.perplexity_service", _configured_service()):
        response = client.post(
            "/api/v1/perplexity/chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is NWU?"},
                ]
            },
        )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_search_propagates_api_error():
    """Search endpoint wraps Perplexity API errors as 502."""
    svc = MagicMock()
    svc.is_configured.return_value = True
    svc.search = AsyncMock(side_effect=Exception("upstream timeout"))

    with patch("app.api.perplexity.perplexity_service", svc):
        response = client.post("/api/v1/perplexity/search", json={"query": "test"})

    assert response.status_code == 502
    assert "upstream timeout" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_search_empty_query_rejected():
    """Search endpoint rejects empty query string."""
    with patch("app.api.perplexity.perplexity_service", _configured_service()):
        response = client.post("/api/v1/perplexity/search", json={"query": ""})
    assert response.status_code == 422


def test_chat_empty_messages_rejected():
    """Chat endpoint rejects an empty messages list."""
    with patch("app.api.perplexity.perplexity_service", _configured_service()):
        response = client.post("/api/v1/perplexity/chat", json={"messages": []})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# PerplexityService unit tests
# ---------------------------------------------------------------------------

class TestPerplexityService:
    """Unit tests for the PerplexityService class."""

    def test_is_configured_false_without_key(self):
        from app.services.perplexity_service import PerplexityService
        svc = PerplexityService.__new__(PerplexityService)
        svc._api_key = None
        svc._client = None
        assert svc.is_configured() is False

    def test_is_configured_true_with_key(self):
        from app.services.perplexity_service import PerplexityService
        svc = PerplexityService.__new__(PerplexityService)
        svc._api_key = "pplx-test123"
        svc._client = None
        assert svc.is_configured() is True

    def test_get_available_models_returns_dict(self):
        from app.services.perplexity_service import PerplexityService, AVAILABLE_MODELS
        svc = PerplexityService.__new__(PerplexityService)
        svc._api_key = "pplx-test"
        svc._client = None
        models = svc.get_available_models()
        assert isinstance(models, dict)
        assert models == AVAILABLE_MODELS

    @pytest.mark.asyncio
    async def test_search_raises_without_key(self):
        from app.services.perplexity_service import PerplexityService
        svc = PerplexityService.__new__(PerplexityService)
        svc._api_key = None
        svc._client = None
        with pytest.raises(RuntimeError, match="PERPLEXITY_API_KEY"):
            await svc.search("test query")

    @pytest.mark.asyncio
    async def test_chat_raises_without_key(self):
        from app.services.perplexity_service import PerplexityService
        svc = PerplexityService.__new__(PerplexityService)
        svc._api_key = None
        svc._client = None
        with pytest.raises(RuntimeError, match="PERPLEXITY_API_KEY"):
            await svc.chat([{"role": "user", "content": "hi"}])
