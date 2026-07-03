"""
Feedback agent — collects post-appointment satisfaction data.
Model: Llama 3.2 1B via Groq.
"""

import json
import logging
import uuid

from backend.agents.state import AgentState
from backend.database.base import get_analytics_session
from backend.database.feedback_analytics_db.models import Feedback
from backend.llm.provider import chat
from backend.llm.registry import FEEDBACK_MODEL
from backend.services import session as session_svc

logger = logging.getLogger(__name__)

_SYSTEM = """You are a patient feedback collector for a hospital system.
Extract the satisfaction score and any complaints from the patient's message.
Output ONLY this JSON:
{"satisfaction_score": <1–5 integer>, "complaint": "<text or empty string>", "health_status": "<improving|stable|worsening|unknown>"}

If the patient hasn't provided a clear score, ask them to rate 1–5 in your response instead (then output score=0)."""


def feedback_node(state: AgentState) -> dict:
    patient_id = state["patient_id"]
    query = state.get("query", "")

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": query},
    ]

    try:
        raw = chat(FEEDBACK_MODEL, messages, temperature=0.1)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        parsed = json.loads(raw[start:end])
        score = int(parsed.get("satisfaction_score", 0))
        complaint = parsed.get("complaint", "")
        health_status = parsed.get("health_status", "unknown")
    except Exception as exc:
        logger.warning("Feedback parsing failed: %s", exc)
        score, complaint, health_status = 0, "", "unknown"

    if score > 0:
        with get_analytics_session() as db:
            db.add(
                Feedback(
                    patient_id=uuid.UUID(patient_id),
                    satisfaction_score=score,
                    complaint=complaint,
                    health_status=health_status,
                )
            )
        response = f"Thank you for your feedback! We've recorded your score of {score}/5."
        if complaint:
            response += " We take your comments seriously and will work to improve."
    else:
        response = raw  # Model asked for clarification

    session_svc.append_message(patient_id, "assistant", response)
    return {"response": response}
