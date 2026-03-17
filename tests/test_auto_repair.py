"""Tests for the auto-repair control API and service."""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


# ── Config endpoints ──────────────────────────────────────────────

def test_get_default_config():
    """Test that the default config is returned."""
    response = client.get("/api/v1/auto-repair/config")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["mode"] == "moderate"
    assert data["max_retries"] == 3
    assert data["auto_rollback"] is True
    assert data["require_approval"] is False
    assert isinstance(data["allowed_repair_types"], list)
    assert len(data["allowed_repair_types"]) > 0


def test_update_config_partial():
    """Test partial config update preserves unchanged fields."""
    response = client.put(
        "/api/v1/auto-repair/config",
        json={"mode": "aggressive", "max_retries": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "aggressive"
    assert data["max_retries"] == 5
    # Unchanged fields
    assert data["enabled"] is True
    assert data["auto_rollback"] is True


def test_update_config_disable():
    """Test disabling auto-repair via config update."""
    response = client.put(
        "/api/v1/auto-repair/config",
        json={"enabled": False},
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    # Re-enable for subsequent tests
    client.put("/api/v1/auto-repair/config", json={"enabled": True})


# ── Status endpoint ───────────────────────────────────────────────

def test_get_status():
    """Test status endpoint returns expected fields."""
    response = client.get("/api/v1/auto-repair/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "paused" in data
    assert "mode" in data
    assert "total_repairs" in data
    assert "successful_repairs" in data
    assert "failed_repairs" in data
    assert "active_repairs" in data


# ── Pause / Resume ────────────────────────────────────────────────

def test_pause_and_resume():
    """Test pausing and resuming the auto-repair system."""
    # Pause
    response = client.post("/api/v1/auto-repair/pause")
    assert response.status_code == 200
    assert response.json()["paused"] is True

    # Resume
    response = client.post("/api/v1/auto-repair/resume")
    assert response.status_code == 200
    assert response.json()["paused"] is False


# ── Trigger / History / Event lifecycle ───────────────────────────

def test_trigger_repair_event():
    """Test manually triggering a repair event."""
    response = client.post(
        "/api/v1/auto-repair/trigger",
        params={"event_type": "linting", "description": "Manual lint fix"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "linting"
    assert data["status"] == "in_progress"
    assert data["description"] == "Manual lint fix"
    assert data["id"].startswith("repair_")


def test_trigger_while_paused_fails():
    """Triggering a repair while paused should return 409."""
    client.post("/api/v1/auto-repair/pause")

    response = client.post(
        "/api/v1/auto-repair/trigger",
        params={"event_type": "linting"},
    )
    assert response.status_code == 409

    # Resume for subsequent tests
    client.post("/api/v1/auto-repair/resume")


def test_trigger_while_disabled_fails():
    """Triggering a repair while disabled should return 409."""
    client.put("/api/v1/auto-repair/config", json={"enabled": False})

    response = client.post(
        "/api/v1/auto-repair/trigger",
        params={"event_type": "security"},
    )
    assert response.status_code == 409

    # Re-enable
    client.put("/api/v1/auto-repair/config", json={"enabled": True})


def test_get_repair_event():
    """Test retrieving a specific repair event."""
    # Create an event
    create_resp = client.post(
        "/api/v1/auto-repair/trigger",
        params={"event_type": "dependency", "description": "dep update"},
    )
    event_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/auto-repair/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["id"] == event_id


def test_get_nonexistent_event():
    """Test 404 for a missing event."""
    response = client.get("/api/v1/auto-repair/events/repair_does_not_exist")
    assert response.status_code == 404


def test_complete_repair_event():
    """Test marking a repair event as completed."""
    create_resp = client.post(
        "/api/v1/auto-repair/trigger",
        params={"event_type": "security", "description": "npm audit fix"},
    )
    event_id = create_resp.json()["id"]

    response = client.post(f"/api/v1/auto-repair/events/{event_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


def test_fail_repair_event_with_auto_rollback():
    """Test failing an event with auto-rollback enabled (default)."""
    create_resp = client.post(
        "/api/v1/auto-repair/trigger",
        params={"event_type": "test_fix", "description": "test repair"},
    )
    event_id = create_resp.json()["id"]

    response = client.post(
        f"/api/v1/auto-repair/events/{event_id}/fail",
        params={"error_message": "tests still failing"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rolled_back"
    assert data["error_message"] == "tests still failing"


def test_get_repair_history():
    """Test that history returns recorded events."""
    response = client.get("/api/v1/auto-repair/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_repair_history_with_filter():
    """Test filtering history by event type."""
    response = client.get(
        "/api/v1/auto-repair/history",
        params={"event_type": "linting"},
    )
    assert response.status_code == 200
    data = response.json()
    for event in data:
        assert event["event_type"] == "linting"


def test_status_reflects_counts():
    """Test that status counters reflect completed/failed events."""
    response = client.get("/api/v1/auto-repair/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_repairs"] > 0
    assert data["successful_repairs"] > 0
    assert data["last_repair_at"] is not None
