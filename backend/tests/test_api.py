"""
API integration tests using FastAPI TestClient with mocked LLM and DB calls.
Run: pytest backend/tests/test_api.py -v
"""

import json
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Build a TestClient with DB and LLM mocked out."""
    # Patch DB session factories so no real Postgres is needed
    with patch("backend.database.base._engines", {}), \
         patch("backend.database.base._session_factories", {}), \
         patch("backend.database.base.create_all_tables"), \
         patch("backend.workflows.medication_reminders.start_reminder_scheduler"), \
         patch("backend.workflows.medication_reminders.stop_reminder_scheduler"), \
         patch("backend.workflows.feedback_scheduler.start_feedback_scheduler"), \
         patch("backend.workflows.feedback_scheduler.stop_feedback_scheduler"):
        from backend.app import app
        with TestClient(app) as c:
            yield c


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Auth ──────────────────────────────────────────────────────────────────────

def _mock_register_user(*args, **kwargs):
    return {"user_id": "u-001", "patient_id": "p-001"}


def _mock_authenticate_user(*args, **kwargs):
    from backend.services.auth import create_access_token
    token = create_access_token({"sub": "u-001", "patient_id": "p-001"})
    return {"access_token": token, "refresh_token": "dummy-refresh", "token_type": "bearer"}


def test_register(client):
    with patch("backend.api.auth.register_user", side_effect=_mock_register_user):
        resp = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "Pass123!",
            "first_name": "Test",
            "last_name": "User",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "patient_id" in data


def test_login(client):
    with patch("backend.api.auth.authenticate_user", side_effect=_mock_authenticate_user):
        resp = client.post("/api/auth/token", data={
            "username": "test@example.com",
            "password": "Pass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


def _get_test_token():
    from backend.services.auth import create_access_token
    return create_access_token({"sub": "u-001", "patient_id": "p-001"})


# ── Chat ──────────────────────────────────────────────────────────────────────

def _mock_graph_invoke(state, config=None):
    state["response"] = "Mock response from the agent."
    state["intent"] = "diagnosis"
    state["department"] = "General Medicine"
    state["confidence_score"] = 0.88
    state["urgency_score"] = 0.25
    state["hitl_required"] = False
    state["emergency_dispatched"] = False
    return state


def test_chat_text_endpoint(client):
    token = _get_test_token()
    with patch("backend.api.chat.graph") as mock_graph:
        mock_graph.invoke.side_effect = _mock_graph_invoke
        resp = client.post(
            "/api/chat/text",
            json={"query": "I have a headache"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert data["intent"] == "diagnosis"
        assert data["department"] == "General Medicine"


def test_chat_text_requires_auth(client):
    resp = client.post("/api/chat/text", json={"query": "hello"})
    assert resp.status_code == 401


# ── Patient profile ───────────────────────────────────────────────────────────

def _mock_patient_profile(patient_id):
    return {
        "patient_id": "p-001",
        "first_name": "Ahmed",
        "last_name": "Mohamed",
        "email": "ahmed.m@example.com",
        "phone": "+201001234567",
        "telegram_chat_id": "100000001",
        "loyalty_points": 150,
        "risk_level": "normal",
        "ambulance_request_count": 0,
        "medical_history": {
            "chronic_conditions": [],
            "allergies": [],
            "current_medications": ["vitamin D"],
        },
    }


def test_get_my_profile(client):
    token = _get_test_token()
    with patch("backend.api.patients.get_patient_session") as mock_session, \
         patch("backend.api.patients.get_appointment_session"):
        # Build a mock context manager that returns a mock db
        mock_db = MagicMock()
        mock_patient = MagicMock()
        mock_patient.patient_id = "p-001"
        mock_patient.first_name = "Ahmed"
        mock_patient.last_name = "Mohamed"
        mock_patient.email = "ahmed.m@example.com"
        mock_patient.phone = "+201001234567"
        mock_patient.telegram_chat_id = "100000001"
        mock_patient.loyalty_points = 150
        mock_patient.risk_level = "normal"
        mock_patient.ambulance_request_count = 0
        mock_history = MagicMock()
        mock_history.chronic_conditions = []
        mock_history.allergies = []
        mock_history.current_medications = ["vitamin D"]
        mock_patient.medical_history = mock_history
        mock_db.query.return_value.filter.return_value.first.return_value = mock_patient
        mock_session.return_value.__enter__ = lambda s: mock_db
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        resp = client.get(
            "/api/patients/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Ahmed"
        assert data["loyalty_points"] == 150


# ── Admin HITL ────────────────────────────────────────────────────────────────

def test_get_hitl_cases(client):
    with patch("backend.api.admin.list_pending_cases", return_value=[
        {
            "case_id": "c-001",
            "patient_id": "p-003",
            "confidence_score": 0.55,
            "suggested_department": "Neurology",
            "case_summary": "Low confidence case",
            "created_at": "2026-06-25T10:00:00",
        }
    ]):
        resp = client.get("/api/admin/hitl/cases")
        assert resp.status_code == 200
        cases = resp.json()
        assert len(cases) == 1
        assert cases[0]["suggested_department"] == "Neurology"


def test_resolve_hitl_case(client):
    with patch("backend.api.admin.resolve_hitl_case", return_value=True):
        resp = client.post(
            "/api/admin/hitl/cases/c-001/resolve",
            json={"doctor_id": "dr-001", "notes": "Holter ordered. Likely benign."},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"


def test_resolve_hitl_case_not_found(client):
    with patch("backend.api.admin.resolve_hitl_case", return_value=False):
        resp = client.post(
            "/api/admin/hitl/cases/bad-id/resolve",
            json={"doctor_id": "dr-001", "notes": "notes"},
        )
        assert resp.status_code == 200
        assert "error" in resp.json()
