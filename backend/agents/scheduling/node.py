"""
Scheduling agent — books appointments and manages loyalty points.
Model: Llama 3.2 via Groq.
"""

import logging
import re

from langchain_core.messages import ToolMessage
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
2. Check loyalty offers with check_available_offers.
3. When the patient selects a slot, use book_slot to confirm. Always pass patient_id and department.
4. If no slots are available, use recommend_alternative.

Be concise and friendly. Do not repeat a tool call whose result you already have — if a tool
already reported failure (e.g. a slot is already booked), stop and tell the patient instead
of retrying the same call."""

# add_points is intentionally NOT exposed to the model: on a batched or repeated tool
# call it was observed awarding points for bookings that had already failed. Points
# are credited deterministically in code below, only when book_slot truly succeeds.
_base_tools = [find_available_slots, recommend_alternative, check_available_offers]
_agents: dict[tuple[bool, bool], object] = {}

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def _build_response(messages: list, fallback_text: str, awarded_points: str | None) -> str:
    """Tool outputs are already complete, human-readable strings — render the
    response straight from them instead of trusting the model to retype them,
    since smaller models are unreliable at faithfully restating tool results."""
    by_name = {}
    for msg in messages:
        if isinstance(msg, ToolMessage):
            by_name[msg.name] = msg.content

    if "book_slot" in by_name:
        parts = [by_name["book_slot"]]
        if awarded_points:
            parts.append(awarded_points)
        return "\n\n".join(parts)
    if "recommend_alternative" in by_name:
        return by_name["recommend_alternative"]
    if "find_available_slots" in by_name:
        parts = [by_name["find_available_slots"]]
        if "check_available_offers" in by_name:
            parts.append(by_name["check_available_offers"])
        parts.append("Reply with the slot_id you'd like to book.")
        return "\n\n".join(parts)
    return fallback_text


def _get_agent(allow_booking: bool, allow_redeem: bool):
    key = (allow_booking, allow_redeem)
    if key not in _agents:
        llm = ChatOpenAI(
            model=SCHEDULING_MODEL,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0.2,
        )
        tools = list(_base_tools)
        if allow_booking:
            tools.append(book_slot)
        if allow_redeem:
            tools.append(redeem_points)
        _agents[key] = create_react_agent(llm, tools, state_modifier=_SYSTEM)
    return _agents[key]


def scheduling_node(state: AgentState) -> dict:
    department = state.get("department") or "General Medicine"
    patient_id = state["patient_id"]
    query = state["query"]

    # book_slot and redeem_points have real side effects (creating an appointment,
    # spending points), so they must never be reachable unless the patient's message
    # actually asks for that action — relying on prompt instructions alone let the
    # model book appointments and redeem offers on its own initiative.
    allow_booking = bool(_UUID_RE.search(query))
    allow_redeem = "redeem" in query.lower()

    user_msg = (
        f"Patient ID: {patient_id}\n"
        f"Recommended department: {department}\n"
        f"Patient request: {query}"
    )

    try:
        result = _get_agent(allow_booking, allow_redeem).invoke(
            {"messages": [("human", user_msg)]},
            config={"recursion_limit": 10},
        )
        messages = result["messages"]
        awarded_points = None
        booked = any(
            isinstance(m, ToolMessage) and m.name == "book_slot" and m.content.startswith("Appointment confirmed")
            for m in messages
        )
        if booked:
            awarded_points = add_points.invoke({"patient_id": patient_id, "reason": "Appointment booked"})
        response = _build_response(messages, messages[-1].content, awarded_points)
    except Exception as exc:
        logger.error("Scheduling agent error: %s", exc)
        response = "I'm sorry, I encountered an issue with scheduling. Please try again."

    session_svc.append_message(patient_id, "assistant", response)
    return {"response": response}
