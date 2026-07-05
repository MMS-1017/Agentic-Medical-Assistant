"""
Scheduling agent — books appointments and manages loyalty points.

Design note: this node is fully deterministic, with no LLM involved. It started
as an LLM tool-calling agent, but testing surfaced a long list of small-model
failure modes around it: skipping find_available_slots and wrongly reporting "no
slots", batching book_slot together with unrelated tool calls, retrying a call
whose failure it had already seen, awarding loyalty points for bookings that had
failed, and calling book_slot/redeem_points on its own initiative without the
patient asking. None of the logic here actually requires reasoning — "look up
slots for this department", "resolve which one the patient means", "book it" —
so it's implemented as a plain decision tree instead.
"""

import re

from backend.agents.state import AgentState
from backend.tools.scheduling import find_available_slots, book_slot, recommend_alternative
from backend.tools.loyalty import check_available_offers, add_points, redeem_points
from backend.services import session as session_svc

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
_ID_PREFIX_RE = re.compile(r"^\[[0-9a-f-]{36}\]\s*", re.I)

_ORDINAL_WORDS = {
    "first": 0, "1st": 0,
    "second": 1, "2nd": 1,
    "third": 2, "3rd": 2,
    "fourth": 3, "4th": 3,
    "fifth": 4, "5th": 4,
}
_ACTION_INTENT_RE = re.compile(r"\bbook\b|\bconfirm\b|\byes\b|\bschedule\b|\bredeem\b|\bapply\b", re.I)
_DIGIT_REF_RE = re.compile(r"\b(?:slot|option|offer|number)\s*#?\s*(\d+)\b|^\s*(\d+)\s*$", re.I)


def _resolve_reference(query: str, candidates: list[str]) -> str | None:
    """Resolve a natural-language reference ("the first one", "slot 2", "book it")
    against a list of ids most recently shown to the patient, so they aren't
    forced to paste a raw id back."""
    if not candidates:
        return None
    q = query.lower().strip()
    for word, idx in _ORDINAL_WORDS.items():
        if re.search(rf"\b{word}\b", q) and idx < len(candidates):
            return candidates[idx]
    m = _DIGIT_REF_RE.search(q)
    if m:
        idx = int(m.group(1) or m.group(2)) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]
    if len(candidates) == 1 and _ACTION_INTENT_RE.search(q):
        return candidates[0]
    return None


def _numbered_for_display(raw: str) -> str:
    """Tool output embeds slot_id/offer_id in brackets for internal tracking —
    patients shouldn't have to read or repeat a UUID, so replace it with a
    plain running number ("1.", "2.", ...) in what they actually see."""
    lines = raw.split("\n")
    numbered = []
    n = 0
    for line in lines:
        if _ID_PREFIX_RE.match(line):
            n += 1
            numbered.append(f"{n}. {_ID_PREFIX_RE.sub('', line)}")
        else:
            numbered.append(line)
    return "\n".join(numbered)


def _try_book(query: str, patient_id: str, department: str) -> str | None:
    slot_id = _UUID_RE.search(query)
    slot_id = slot_id.group(0) if slot_id else _resolve_reference(query, session_svc.get_last_slots(patient_id))
    if not slot_id:
        return None
    result = book_slot.invoke({"slot_id": slot_id, "patient_id": patient_id, "department": department})
    if result.startswith("Appointment confirmed"):
        awarded = add_points.invoke({"patient_id": patient_id, "reason": "Appointment booked"})
        session_svc.set_last_slots(patient_id, [])
        return f"{result}\n\n{awarded}"
    return result


def _try_redeem(query: str, patient_id: str) -> str | None:
    if "redeem" not in query.lower():
        return None
    offer_id = _UUID_RE.search(query)
    offer_id = offer_id.group(0) if offer_id else _resolve_reference(query, session_svc.get_last_offers(patient_id))
    if not offer_id:
        return "Please tell me which offer you'd like to redeem, e.g. \"redeem the first one\"."
    return redeem_points.invoke({"patient_id": patient_id, "offer_id": offer_id})


def _list_slots_and_offers(patient_id: str, department: str) -> str:
    slots_text = find_available_slots.invoke({"department": department})
    offers_text = check_available_offers.invoke({"patient_id": patient_id})
    session_svc.set_last_offers(patient_id, _UUID_RE.findall(offers_text))

    if not _UUID_RE.search(slots_text):
        session_svc.set_last_slots(patient_id, [])
        return recommend_alternative.invoke({"department": department})

    session_svc.set_last_slots(patient_id, _UUID_RE.findall(slots_text))
    parts = [
        _numbered_for_display(slots_text),
        _numbered_for_display(offers_text),
        'Reply with which one you\'d like, e.g. "book the first one" or "book slot 2".',
    ]
    return "\n\n".join(parts)


def scheduling_node(state: AgentState) -> dict:
    department = state.get("department") or "General Medicine"
    patient_id = state["patient_id"]
    query = state["query"]

    # redeem is checked first: it has an explicit "redeem" keyword gate, whereas
    # _try_book's ordinal matching ("the first one") would otherwise misfire on
    # phrases like "redeem the first one" and book a slot instead of an offer.
    response = _try_redeem(query, patient_id) or _try_book(query, patient_id, department)
    if response is None:
        response = _list_slots_and_offers(patient_id, department)

    session_svc.append_message(patient_id, "assistant", response)
    return {"response": response}
