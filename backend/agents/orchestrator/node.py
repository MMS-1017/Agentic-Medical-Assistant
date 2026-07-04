"""
Orchestrator agent — classifies intent and loads patient context.
Model: Gemini Flash 2.5 (via OpenRouter).
"""

import uuid
import json
import logging

from backend.agents.state import AgentState
from backend.database.base import get_patient_session
from backend.database.patient_db.models import Patient, MedicalHistory
from backend.llm.provider import chat
from backend.llm.registry import ORCHESTRATOR_MODEL
from backend.services import session as session_svc

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the orchestrator of a medical AI system. Your job is to:
1. Understand what the patient needs.
2. Classify their intent as exactly ONE of: scheduling, diagnosis, emergency, feedback.

Rules:
- If they mention chest pain, difficulty breathing, stroke, severe bleeding, or any life-threatening symptom → emergency
- If they describe any illness, pain, or medical symptom → diagnosis
- If they want to book, cancel, or reschedule an appointment → scheduling
- If they want to provide feedback or rate a past appointment → feedback
- When in doubt between diagnosis and scheduling, choose diagnosis.

Respond ONLY with a JSON object:
{"intent": "<one of: scheduling|diagnosis|emergency|feedback>", "summary": "<one sentence summary>"}
"""


def _load_patient_context(patient_id: str) -> tuple[str, str]:
    """Returns (patient_name, history_summary)."""
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        if not patient:
            return "Unknown", ""
        name = f"{patient.first_name} {patient.last_name}"
        history = patient.medical_history
        if history:
            chronic = ", ".join(history.chronic_conditions) if history.chronic_conditions else "none"
            allergies = ", ".join(history.allergies) if history.allergies else "none"
            meds = ", ".join(history.current_medications) if history.current_medications else "none"
            summary = f"Chronic: {chronic}. Allergies: {allergies}. Medications: {meds}."
        else:
            summary = "No medical history on file."
        return name, summary


def orchestrator_node(state: AgentState) -> dict:
    patient_id = state["patient_id"]
    query = state["query"]

    name, history_summary = _load_patient_context(patient_id)

    history = session_svc.get_history(patient_id)
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Patient: {name}\n"
                f"Medical history: {history_summary}\n"
                f"Recent conversation:\n{history_text}\n\n"
                f"Current message: {query}"
            ),
        },
    ]

    try:
        raw = chat(ORCHESTRATOR_MODEL, messages, temperature=0.1, max_tokens=200)
        # Extract JSON even if model wraps it in markdown
        start = raw.find("{")
        end = raw.rfind("}") + 1
        parsed = json.loads(raw[start:end])
        intent = parsed.get("intent", "diagnosis")
    except Exception as exc:
        logger.warning("Orchestrator parsing failed: %s — defaulting to diagnosis", exc)
        intent = "diagnosis"

    session_svc.append_message(patient_id, "user", query)

    return {
        "patient_name": name,
        "medical_history_summary": history_summary,
        "intent": intent,
        "emergency_dispatched": False,
        "hitl_required": False,
    }


def orchestrator_router(state: AgentState) -> str:
    intent = state.get("intent", "diagnosis")
    if intent in {"scheduling", "diagnosis", "emergency", "feedback"}:
        return intent
    return "diagnosis"
