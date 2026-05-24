"""Tests for the NSR (Neuro-Symbolic Reasoning) API endpoints and core components."""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unavailable_service():
    mock = MagicMock()
    mock.is_available.return_value = False
    return mock


def _available_service(**overrides):
    mock = MagicMock()
    mock.is_available.return_value = True
    mock.get_system_status = AsyncMock(return_value={
        "available": True,
        "rhns": {"layer_count": 1, "registered_agents": 0, "layers": {}},
        "override": {"state": "idle", "bypass_active": False},
    })
    mock.get_state_sync = AsyncMock(return_value={
        "platform": "UEEP",
        "core_architecture": "RHNS",
        "current_module": "Neuro-Symbolic Integration",
        "constraints": "edge computing",
        "knowledge_cutoff": "2026-05-24",
    })
    mock.process_intent = AsyncMock(return_value={
        "outcome": "passed",
        "agent_id": "agent-1",
        "layer_id": "default",
        "depth": 0,
        "grounded_atoms": ["deploy_service"],
        "skv_state": "closed",
        "resolution": "PASS",
        "escalated": False,
        "override_active": False,
        "timestamp": time.time(),
        "error": None,
    })
    mock.validate_policy = AsyncMock(return_value={
        "success": True,
        "passed": True,
        "resolution": "PASS",
        "breaker_state": "closed",
        "conflicts": [],
    })
    mock.detect_policy_conflicts = AsyncMock(return_value={
        "success": True,
        "conflict_count": 0,
        "conflicts": [],
        "resolutions": {},
    })
    mock.arm_override = AsyncMock(return_value={
        "success": True,
        "state": "armed",
        "message": "Override armed successfully",
        "expires_at": time.time() + 30,
    })
    mock.confirm_override = AsyncMock(return_value={
        "success": True,
        "state": "confirmed",
        "message": "Override confirmed — bypass active",
    })
    mock.get_override_status = AsyncMock(return_value={
        "state": "idle",
        "bypass_active": False,
    })
    for k, v in overrides.items():
        setattr(mock, k, v)
    return mock


# ---------------------------------------------------------------------------
# Status endpoint
# ---------------------------------------------------------------------------

def test_nsr_status_unavailable():
    with patch("app.api.nsr.nsr_service", _unavailable_service()):
        resp = client.get("/api/v1/nsr/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is False


def test_nsr_status_available():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.get("/api/v1/nsr/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert "rhns" in data


# ---------------------------------------------------------------------------
# State-sync endpoint
# ---------------------------------------------------------------------------

def test_state_sync_returns_required_keys():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.get("/api/v1/nsr/state-sync")
    assert resp.status_code == 200
    data = resp.json()
    assert "state_sync" in data
    assert "context_header" in data
    assert "[SYSTEM STATE SYNC]" in data["context_header"]


def test_state_sync_503_when_unavailable():
    with patch("app.api.nsr.nsr_service", _unavailable_service()):
        resp = client.get("/api/v1/nsr/state-sync")
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Intent endpoint
# ---------------------------------------------------------------------------

def test_intent_passed():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.post("/api/v1/nsr/intent", json={
            "agent_id": "agent-1",
            "embedding": [0.1, 0.9, 0.3, 0.5],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["outcome"] == "passed"


def test_intent_blocked_when_skv_open():
    svc = _available_service()
    svc.process_intent = AsyncMock(return_value={
        "outcome": "blocked",
        "agent_id": "agent-bad",
        "layer_id": "default",
        "depth": 0,
        "grounded_atoms": ["forbidden_action"],
        "skv_state": "open",
        "resolution": "BLOCKED",
        "escalated": False,
        "override_active": False,
        "timestamp": time.time(),
        "error": None,
    })
    with patch("app.api.nsr.nsr_service", svc):
        resp = client.post("/api/v1/nsr/intent", json={
            "agent_id": "agent-bad",
            "embedding": [0.5] * 4,
        })
    assert resp.status_code == 200
    assert resp.json()["data"]["outcome"] == "blocked"


def test_intent_503_when_unavailable():
    with patch("app.api.nsr.nsr_service", _unavailable_service()):
        resp = client.post("/api/v1/nsr/intent", json={
            "agent_id": "x",
            "embedding": [0.1],
        })
    assert resp.status_code == 503


def test_intent_empty_embedding_rejected():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.post("/api/v1/nsr/intent", json={
            "agent_id": "x",
            "embedding": [],
        })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Policy endpoints
# ---------------------------------------------------------------------------

def test_policy_validate_success():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.post("/api/v1/nsr/policy/validate", json={
            "agent_id": "agent-1",
            "atoms": ["deploy_service"],
            "rules": [
                {"rule_id": "r1", "modality": "OBLIGATION",
                 "predicate": "deploy_service", "priority": 2},
            ],
        })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_policy_conflicts_no_conflicts():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.post("/api/v1/nsr/policy/conflicts", json={
            "policies": [
                {"agent_id": "a1", "positions": {"deploy": "OBLIGATED"}, "priority": 2},
                {"agent_id": "a2", "positions": {"deploy": "PERMITTED"},  "priority": 1},
            ]
        })
    assert resp.status_code == 200
    assert resp.json()["data"]["conflict_count"] == 0


def test_policy_conflicts_detected():
    svc = _available_service()
    svc.detect_policy_conflicts = AsyncMock(return_value={
        "success": True,
        "conflict_count": 1,
        "conflicts": [{"action": "deploy", "agent_ids": ["a1", "a2"]}],
        "resolutions": {"deploy": {"outcome": "permitted", "reasoning": "priority"}},
    })
    with patch("app.api.nsr.nsr_service", svc):
        resp = client.post("/api/v1/nsr/policy/conflicts", json={
            "policies": [
                {"agent_id": "a1", "positions": {"deploy": "OBLIGATED"}, "priority": 2},
                {"agent_id": "a2", "positions": {"deploy": "FORBIDDEN"},  "priority": 1},
            ]
        })
    assert resp.status_code == 200
    assert resp.json()["data"]["conflict_count"] == 1


# ---------------------------------------------------------------------------
# Override endpoints
# ---------------------------------------------------------------------------

def test_override_arm_success():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.post("/api/v1/nsr/override/arm", json={
            "key_id": "key-alpha",
            "token": "nonce:12345:abc",
        })
    assert resp.status_code == 200
    assert resp.json()["data"]["state"] == "armed"


def test_override_arm_failure_returns_400():
    svc = _available_service()
    svc.arm_override = AsyncMock(return_value={
        "success": False,
        "state": "idle",
        "message": "HMAC verification failed",
        "expires_at": None,
    })
    with patch("app.api.nsr.nsr_service", svc):
        resp = client.post("/api/v1/nsr/override/arm", json={
            "key_id": "key-alpha",
            "token": "bad_token",
        })
    assert resp.status_code == 400
    assert "HMAC" in resp.json()["detail"]


def test_override_confirm_same_key_rejected():
    svc = _available_service()
    svc.confirm_override = AsyncMock(return_value={
        "success": False,
        "state": "armed",
        "message": "Confirm key_id must differ from arm key_id",
    })
    with patch("app.api.nsr.nsr_service", svc):
        resp = client.post("/api/v1/nsr/override/confirm", json={
            "key_id": "key-alpha",
            "token": "some_token",
        })
    assert resp.status_code == 400


def test_override_status():
    with patch("app.api.nsr.nsr_service", _available_service()):
        resp = client.get("/api/v1/nsr/override/status")
    assert resp.status_code == 200
    assert "state" in resp.json()


# ---------------------------------------------------------------------------
# DualOverride unit tests (pure Python — no HTTP)
# ---------------------------------------------------------------------------

class TestDualOverride:
    SECRET = b"test-secret-key"

    def _make(self, **kwargs):
        import sys, os
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "nwu_protocol"
        ))
        from nwu_protocol.core.neuro_symbolic.dual_override import DualOverride
        return DualOverride(secret=self.SECRET, audit_log_path="/dev/null", **kwargs)

    def test_generate_token_format(self):
        do = self._make()
        token = do.generate_token("key-a")
        parts = token.split(":")
        assert len(parts) == 3

    def test_arm_valid_token(self):
        do = self._make()
        token = do.generate_token("key-a")
        result = do.arm("key-a", token)
        assert result.success
        assert result.state.value == "armed"

    def test_arm_bad_token(self):
        do = self._make()
        result = do.arm("key-a", "bad:token:here")
        assert not result.success

    def test_confirm_happy_path(self):
        do = self._make()
        t_a = do.generate_token("key-a")
        do.arm("key-a", t_a)
        t_b = do.generate_token("key-b")
        result = do.confirm("key-b", t_b)
        assert result.success
        assert do.is_active()

    def test_confirm_same_key_rejected(self):
        do = self._make(require_different_keys=True)
        t_a = do.generate_token("key-a")
        do.arm("key-a", t_a)
        t_b = do.generate_token("key-a")
        result = do.confirm("key-a", t_b)
        assert not result.success

    def test_token_single_use(self):
        do = self._make()
        token = do.generate_token("key-a")
        do.arm("key-a", token)
        # reset to idle
        do.deactivate()
        # try reusing same token
        result = do.arm("key-a", token)
        assert not result.success

    def test_window_expiry(self):
        do = self._make(window_seconds=0.01)
        t_a = do.generate_token("key-a")
        do.arm("key-a", t_a)
        time.sleep(0.05)
        assert not do.is_active()


# ---------------------------------------------------------------------------
# IntentMapper unit tests
# ---------------------------------------------------------------------------

class TestIntentMapper:
    def _make(self):
        import sys, os
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "nwu_protocol"
        ))
        from nwu_protocol.core.neuro_symbolic.intent_mapper import IntentMapper, Atom, TruthValue
        import numpy as np
        mapper = IntentMapper()
        mapper.register_atom(Atom("deploy_service", np.array([1.0, 0.0, 0.0])))
        mapper.register_atom(Atom("halt_process",   np.array([0.0, 1.0, 0.0])))
        mapper.register_atom(Atom("read_data",      np.array([0.0, 0.0, 1.0])))
        return mapper, Atom, TruthValue

    def test_exact_match_is_true(self):
        import numpy as np
        mapper, Atom, TruthValue = self._make()
        results = mapper.map(np.array([1.0, 0.0, 0.0]))
        assert results[0].atom.name == "deploy_service"
        assert results[0].truth_value == TruthValue.TRUE

    def test_orthogonal_is_false(self):
        import numpy as np
        mapper, Atom, TruthValue = self._make()
        results = mapper.map(np.array([0.0, 1.0, 0.0]))
        # deploy_service should be FALSE for [0,1,0]
        deploy = next(r for r in results if r.atom.name == "deploy_service")
        assert deploy.truth_value == TruthValue.FALSE

    def test_l2_normalisation(self):
        import numpy as np
        mapper, Atom, TruthValue = self._make()
        # Un-normalised query vector — same direction as deploy_service
        results = mapper.map(np.array([100.0, 0.0, 0.0]))
        assert results[0].atom.name == "deploy_service"
        assert abs(results[0].similarity - 1.0) < 1e-6

    def test_ground_returns_above_threshold(self):
        import numpy as np
        mapper, Atom, TruthValue = self._make()
        grounded = mapper.ground(np.array([1.0, 0.0, 0.0]), threshold=0.7)
        assert any(a.name == "deploy_service" for a in grounded)
        assert not any(a.name == "halt_process" for a in grounded)

    def test_zero_norm_raises(self):
        import numpy as np
        from nwu_protocol.core.neuro_symbolic.intent_mapper import IntentMapper
        mapper = IntentMapper()
        with pytest.raises(ValueError):
            mapper.map(np.zeros(3))


# ---------------------------------------------------------------------------
# PolicyResolver unit tests
# ---------------------------------------------------------------------------

class TestPolicyResolver:
    def _make(self):
        import sys, os
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "nwu_protocol"
        ))
        from nwu_protocol.core.neuro_symbolic.policy_resolver import (
            PolicyResolver, AgentPolicy, NormativePosition, ResolutionOutcome,
        )
        return PolicyResolver, AgentPolicy, NormativePosition, ResolutionOutcome

    def test_no_conflict_permitted(self):
        PR, AP, NP, RO = self._make()
        r = PR()
        r.add_policy(AP("a1", {"deploy": NP.OBLIGATED}, priority=1))
        res = r.resolve("a1", "deploy")
        assert res.outcome == RO.PERMITTED

    def test_obligation_beats_prohibition(self):
        PR, AP, NP, RO = self._make()
        r = PR()
        r.add_policy(AP("a1", {"deploy": NP.OBLIGATED}, priority=5))
        r.add_policy(AP("a2", {"deploy": NP.FORBIDDEN},  priority=1))
        res = r.resolve("a1", "deploy")
        assert res.outcome == RO.PERMITTED

    def test_prohibition_beats_obligation(self):
        PR, AP, NP, RO = self._make()
        r = PR()
        r.add_policy(AP("a1", {"deploy": NP.OBLIGATED}, priority=1))
        r.add_policy(AP("a2", {"deploy": NP.FORBIDDEN},  priority=5))
        res = r.resolve("a1", "deploy")
        assert res.outcome == RO.BLOCKED

    def test_tie_is_abstain(self):
        PR, AP, NP, RO = self._make()
        r = PR()
        r.add_policy(AP("a1", {"deploy": NP.OBLIGATED}, priority=3))
        r.add_policy(AP("a2", {"deploy": NP.FORBIDDEN},  priority=3))
        res = r.resolve("a1", "deploy")
        assert res.outcome == RO.ABSTAIN

    def test_detect_global_conflicts(self):
        PR, AP, NP, RO = self._make()
        r = PR()
        r.add_policy(AP("a1", {"deploy": NP.OBLIGATED}, priority=2))
        r.add_policy(AP("a2", {"deploy": NP.FORBIDDEN},  priority=1))
        conflicts = r.detect_global_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0].action == "deploy"

    def test_no_policy_abstains(self):
        PR, AP, NP, RO = self._make()
        r = PR()
        res = r.resolve("a1", "deploy")
        assert res.outcome == RO.ABSTAIN


# ---------------------------------------------------------------------------
# SKV unit tests
# ---------------------------------------------------------------------------

class TestSymbolicKnowledgeVault:
    def _make(self):
        import sys, os
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "nwu_protocol"
        ))
        from nwu_protocol.core.neuro_symbolic.symbolic_knowledge_vault import (
            SymbolicKnowledgeVault, DeonticRule, DeonticModality, SKVState,
        )
        return SymbolicKnowledgeVault, DeonticRule, DeonticModality, SKVState

    def test_no_rules_passes(self):
        SKV, DR, DM, SS = self._make()
        skv = SKV()
        result = skv.validate("agent-1", ["deploy_service"])
        assert result.passed
        assert result.resolution == "PASS"

    def test_obligation_only_passes(self):
        SKV, DR, DM, SS = self._make()
        skv = SKV()
        skv.register_rule(DR("r1", "agent-1", DM.OBLIGATION, "deploy_service", priority=1))
        result = skv.validate("agent-1", ["deploy_service"])
        assert result.passed

    def test_conflict_obligation_beats_prohibition(self):
        SKV, DR, DM, SS = self._make()
        skv = SKV()
        skv.register_rule(DR("r1", "agent-1", DM.OBLIGATION,   "deploy_service", priority=2))
        skv.register_rule(DR("r2", "agent-1", DM.PROHIBITION,  "deploy_service", priority=1))
        result = skv.validate("agent-1", ["deploy_service"])
        assert result.passed
        assert result.resolution == "PASS"

    def test_conflict_prohibition_blocks(self):
        SKV, DR, DM, SS = self._make()
        skv = SKV()
        skv.register_rule(DR("r1", "agent-1", DM.OBLIGATION,  "deploy_service", priority=1))
        skv.register_rule(DR("r2", "agent-1", DM.PROHIBITION, "deploy_service", priority=3))
        result = skv.validate("agent-1", ["deploy_service"])
        assert not result.passed

    def test_breaker_opens_after_threshold(self):
        SKV, DR, DM, SS = self._make()
        skv = SKV(failure_threshold=2)
        skv.register_rule(DR("r1", "*", DM.OBLIGATION,  "x", priority=1))
        skv.register_rule(DR("r2", "*", DM.PROHIBITION, "x", priority=3))
        skv.validate("a", ["x"])
        skv.validate("a", ["x"])
        assert skv.state == SS.OPEN

    def test_reset_closes_breaker(self):
        SKV, DR, DM, SS = self._make()
        skv = SKV(failure_threshold=1)
        skv.register_rule(DR("r1", "*", DM.OBLIGATION,  "x", priority=1))
        skv.register_rule(DR("r2", "*", DM.PROHIBITION, "x", priority=3))
        skv.validate("a", ["x"])
        assert skv.state == SS.OPEN
        skv.reset()
        assert skv.state == SS.CLOSED
