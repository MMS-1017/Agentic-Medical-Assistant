"""
Emergency agent — evaluates urgency, dispatches ambulance, sends alerts.
Model: Llama 3.2 via Groq.
"""

import logging
import threading
import uuid

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from backend.agents.state import AgentState
from backend.config import settings
from backend.database.base import get_patient_session
from backend.database.patient_db.models import Patient
from backend.llm.registry import EMERGENCY_MODEL
from backend.services import session as session_svc
from backend.services.notification import notify_emergency
from backend.tools.emergency import assess_emergency_risk, increment_ambulance_count, get_emergency_timer

logger = logging.getLogger(__name__)

_SYSTEM = """You are an emergency response AI. A patient has a potentially life-threatening condition.

Your steps:
1. Call assess_emergency_risk(patient_id) to check if the patient is high-risk.
2. Call get_emergency_timer(condition) with the primary condition to get the escalation delay in seconds.
3. If risk is 'high' OR timer is '0', state that ambulance is being dispatched IMMEDIATELY.
4. Otherwise state the timer that will trigger ambulance dispatch.
5. Call increment_ambulance_count(patient_id) after deciding to dispatch.
6. Provide clear, calm instructions to the patient while help is on the way.

Keep your response brief — every second counts."""

_tools = [assess_emergency_risk, get_emergency_timer, increment_ambulance_count]
_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        llm = ChatOpenAI(
            model=EMERGENCY_MODEL,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0.1,
        )
        _agent = create_react_agent(llm, _tools, state_modifier=_SYSTEM)
    return _agent


def _get_patient_telegram(patient_id: str) -> tuple[str, str]:
    with get_patient_session() as db:
        p = db.query(Patient).filter(Patient.patient_id == uuid.UUID(patient_id)).first()
        if p:
            return p.telegram_chat_id or "", f"{p.first_name} {p.last_name}"
        return "", "Unknown"


def _dispatch_after_delay(patient_id: str, condition: str, delay_seconds: int):
    def _fire():
        import time
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        chat_id, name = _get_patient_telegram(patient_id)
        if chat_id:
            notify_emergency(chat_id, condition, name)
        logger.info("Emergency alert fired for patient %s (delay=%ds)", patient_id, delay_seconds)
    threading.Thread(target=_fire, daemon=True).start()


def emergency_node(state: AgentState) -> dict:
    patient_id = state["patient_id"]
    query = state.get("query", "")
    department = state.get("department") or "Emergency"

    user_msg = (
        f"Patient ID: {patient_id}\n"
        f"Diagnosed condition: {department}\n"
        f"Patient complaint: {query}"
    )

    try:
        result = _get_agent().invoke({"messages": [("human", user_msg)]})
        response = result["messages"][-1].content
    except Exception as exc:
        logger.error("Emergency agent error: %s", exc)
        response = "Emergency services are being contacted. Please stay calm and do not hang up."

    chat_id, name = _get_patient_telegram(patient_id)
    if chat_id:
        _dispatch_after_delay(patient_id, department, delay_seconds=0)

    session_svc.append_message(patient_id, "assistant", response)
    return {"response": response, "emergency_dispatched": True}
