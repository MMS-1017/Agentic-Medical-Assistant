"""
Scheduling agent — books appointments and manages loyalty points.
Model: Llama 3.2 via Groq.
"""

import logging

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from backend.agents.state import AgentState
from backend.config import settings
from backend.llm.registry import SCHEDULING_MODEL
from backend.tools.scheduling import find_available_slots, book_slot, recommend_alternative
from backend.tools.loyalty import check_available_offers, add_points, redeem_points
from backend.services import session as session_svc

logger = logging.getLogger(__name__)

_SYSTEM = """You are a medical scheduling assistant. Help patients book appointments.

Steps:
1. If the patient has a department recommendation, use find_available_slots with that department.
2. Present the available slots clearly (date, time, doctor, clinic).
3. Check loyalty offers with check_available_offers — tell the patient if they can redeem points.
4. When the patient selects a slot, use book_slot to confirm. Always pass patient_id and department.
5. After a successful booking, call add_points to award loyalty points.
6. If no slots are available, use recommend_alternative.

Always be concise and friendly. Confirm the appointment date and time explicitly."""

_tools = [find_available_slots, book_slot, recommend_alternative, check_available_offers, add_points, redeem_points]
_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        llm = ChatOpenAI(
            model=SCHEDULING_MODEL,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0.2,
        )
        _agent = create_react_agent(llm, _tools, state_modifier=_SYSTEM)
    return _agent


def scheduling_node(state: AgentState) -> dict:
    department = state.get("department") or "General Medicine"
    patient_id = state["patient_id"]
    query = state["query"]

    user_msg = (
        f"Patient ID: {patient_id}\n"
        f"Recommended department: {department}\n"
        f"Patient request: {query}"
    )

    try:
        result = _get_agent().invoke({"messages": [("human", user_msg)]})
        response = result["messages"][-1].content
    except Exception as exc:
        logger.error("Scheduling agent error: %s", exc)
        response = "I'm sorry, I encountered an issue with scheduling. Please try again."

    session_svc.append_message(patient_id, "assistant", response)
    return {"response": response}
