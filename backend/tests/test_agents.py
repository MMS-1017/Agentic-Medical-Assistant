"""
Agent logic tests — mocks LLM and DB to validate agent node behavior.
Run: pytest backend/tests/test_agents.py -v
"""

import json
from unittest.mock import patch, MagicMock


# ── Orchestrator ──────────────────────────────────────────────────────────────

def _make_base_state(**kwargs):
    base = {
        "patient_id": "00000000-0000-0000-0000-000000000001",
        "patient_name": "",
        "query": "I have chest pain",
        "modality": "text",
        "voice_transcript": None,
        "image_findings": None,
        "intent": "",
        "medical_history_summary": None,
        "department": None,
        "confidence_score": None,
        "urgency_score": None,
        "emergency_risk": None,
        "emergency_dispatched": False,
        "hitl_required": False,
        "hitl_case_id": None,
        "appointment_id": None,
        "response": "",
        "error": None,
    }
    base.update(kwargs)
    return base


def test_orchestrator_classifies_emergency():
    from backend.agents.orchestrator.node import orchestrator_node, orchestrator_router

    llm_response = json.dumps({"intent": "emergency", "summary": "Chest pain emergency"})

    with patch("backend.agents.orchestrator.node.get_patient_session") as mock_sess, \
         patch("backend.agents.orchestrator.node.chat", return_value=llm_response):
        mock_db = MagicMock()
        mock_patient = MagicMock()
        mock_patient.first_name = "Ahmed"
        mock_patient.last_name = "Mohamed"
        mock_patient.medical_history = MagicMock(
            chronic_conditions=[], allergies=[], current_medications=[]
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_patient
        mock_sess.return_value.__enter__ = lambda s: mock_db
        mock_sess.return_value.__exit__ = MagicMock(return_value=False)

        state = _make_base_state(query="I have crushing chest pain and my arm hurts")
        result = orchestrator_node(state)
        assert result["intent"] == "emergency"
        assert orchestrator_router(result) == "emergency"


def test_orchestrator_classifies_scheduling():
    from backend.agents.orchestrator.node import orchestrator_node

    llm_response = json.dumps({"intent": "scheduling", "summary": "Wants appointment"})

    with patch("backend.agents.orchestrator.node.get_patient_session") as mock_sess, \
         patch("backend.agents.orchestrator.node.chat", return_value=llm_response):
        mock_db = MagicMock()
        mock_patient = MagicMock()
        mock_patient.first_name = "Test"; mock_patient.last_name = "User"
        mock_patient.medical_history = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_patient
        mock_sess.return_value.__enter__ = lambda s: mock_db
        mock_sess.return_value.__exit__ = MagicMock(return_value=False)

        state = _make_base_state(query="I want to book a cardiology appointment")
        result = orchestrator_node(state)
        assert result["intent"] == "scheduling"


def test_orchestrator_handles_malformed_llm_response():
    from backend.agents.orchestrator.node import orchestrator_node

    with patch("backend.agents.orchestrator.node.get_patient_session") as mock_sess, \
         patch("backend.agents.orchestrator.node.chat", return_value="not valid json at all"):
        mock_db = MagicMock()
        mock_patient = MagicMock()
        mock_patient.first_name = "Test"; mock_patient.last_name = "User"
        mock_patient.medical_history = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_patient
        mock_sess.return_value.__enter__ = lambda s: mock_db
        mock_sess.return_value.__exit__ = MagicMock(return_value=False)

        state = _make_base_state()
        result = orchestrator_node(state)
        # Should fall back to "diagnosis"
        assert result["intent"] == "diagnosis"


# ── Diagnosis ─────────────────────────────────────────────────────────────────

def test_diagnosis_node_high_confidence():
    from backend.agents.diagnosis.node import diagnosis_node, diagnosis_router

    llm_response = json.dumps({
        "department": "Cardiology",
        "confidence_score": 0.92,
        "urgency_score": 0.88,
        "reasoning": "Crushing chest pain with radiation to left arm — classic ACS."
    })

    with patch("backend.agents.diagnosis.node.chat", return_value=llm_response), \
         patch("backend.agents.diagnosis.node.retrieve_medical_context", return_value=["Chest pain guide"]), \
         patch("backend.agents.diagnosis.node._persist_diagnosis"):
        state = _make_base_state(
            query="Crushing chest pain radiating to my left arm",
            medical_history_summary="No chronic conditions",
        )
        result = diagnosis_node(state)
        assert result["department"] == "Cardiology"
        assert result["confidence_score"] == 0.92
        assert result["urgency_score"] == 0.88
        assert result["hitl_required"] is False
        # High urgency → emergency
        assert diagnosis_router({**state, **result}) == "emergency"


def test_diagnosis_node_low_confidence_triggers_hitl():
    from backend.agents.diagnosis.node import diagnosis_node, diagnosis_router

    llm_response = json.dumps({
        "department": "Neurology",
        "confidence_score": 0.55,
        "urgency_score": 0.30,
        "reasoning": "Unclear presentation."
    })

    with patch("backend.agents.diagnosis.node.chat", return_value=llm_response), \
         patch("backend.agents.diagnosis.node.retrieve_medical_context", return_value=[]), \
         patch("backend.agents.diagnosis.node._persist_diagnosis"):
        state = _make_base_state(query="Strange tingling in my face sometimes")
        result = diagnosis_node(state)
        assert result["hitl_required"] is True
        assert diagnosis_router({**state, **result}) == "hitl"


def test_diagnosis_node_moderate_routes_to_scheduling():
    from backend.agents.diagnosis.node import diagnosis_node, diagnosis_router

    llm_response = json.dumps({
        "department": "Ophthalmology",
        "confidence_score": 0.91,
        "urgency_score": 0.25,
        "reasoning": "Red eye with discharge — bacterial conjunctivitis."
    })

    with patch("backend.agents.diagnosis.node.chat", return_value=llm_response), \
         patch("backend.agents.diagnosis.node.retrieve_medical_context", return_value=["Eye care reference"]), \
         patch("backend.agents.diagnosis.node._persist_diagnosis"):
        state = _make_base_state(query="My eye is red with sticky discharge")
        result = diagnosis_node(state)
        assert result["department"] == "Ophthalmology"
        assert result["hitl_required"] is False
        assert diagnosis_router({**state, **result}) == "scheduling"


# ── Feedback ──────────────────────────────────────────────────────────────────

def test_feedback_node_collects_score():
    from backend.agents.feedback.node import feedback_node

    llm_response = json.dumps({
        "satisfaction_score": 4,
        "complaint": "Waiting time was a bit long.",
        "health_status": "improving"
    })

    with patch("backend.agents.feedback.node.chat", return_value=llm_response), \
         patch("backend.agents.feedback.node.get_analytics_session") as mock_sess:
        mock_db = MagicMock()
        mock_sess.return_value.__enter__ = lambda s: mock_db
        mock_sess.return_value.__exit__ = MagicMock(return_value=False)

        state = _make_base_state(query="I'd give it 4 stars, the wait was long but doctor was great")
        result = feedback_node(state)
        assert "4" in result["response"] or "Thank you" in result["response"]
        mock_db.add.assert_called_once()


def test_feedback_node_asks_for_score_when_missing():
    from backend.agents.feedback.node import feedback_node

    llm_response = json.dumps({
        "satisfaction_score": 0,
        "complaint": "",
        "health_status": "unknown"
    })

    with patch("backend.agents.feedback.node.chat", return_value=llm_response), \
         patch("backend.agents.feedback.node.get_analytics_session") as mock_sess:
        mock_db = MagicMock()
        mock_sess.return_value.__enter__ = lambda s: mock_db
        mock_sess.return_value.__exit__ = MagicMock(return_value=False)

        state = _make_base_state(query="It was okay I guess")
        result = feedback_node(state)
        # Should not have added to DB since score=0
        mock_db.add.assert_not_called()


# ── HITL ──────────────────────────────────────────────────────────────────────

def test_hitl_node_creates_case():
    from backend.agents.hitl.node import hitl_node

    with patch("backend.agents.hitl.node.create_hitl_case", return_value="case-abc-123"):
        state = _make_base_state(
            confidence_score=0.55,
            department="Neurology",
            query="Strange visual symptoms",
        )
        result = hitl_node(state)
        assert result["hitl_case_id"] == "case-abc-123"
        assert "case-abc-123" in result["response"]
        assert "doctor" in result["response"].lower()
