"""
In-process conversation session store keyed by patient_id.
Holds recent message history for multi-turn context.
"""

from collections import defaultdict
from typing import Any

_sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
_last_slots: dict[str, list[str]] = {}
_last_offers: dict[str, list[str]] = {}
MAX_HISTORY = 20


def get_history(patient_id: str) -> list[dict]:
    return _sessions[patient_id][-MAX_HISTORY:]


def append_message(patient_id: str, role: str, content: str) -> None:
    _sessions[patient_id].append({"role": role, "content": content})


def clear_session(patient_id: str) -> None:
    _sessions.pop(patient_id, None)
    _last_slots.pop(patient_id, None)
    _last_offers.pop(patient_id, None)


def set_last_slots(patient_id: str, slot_ids: list[str]) -> None:
    """Remember the slot_ids most recently shown to this patient, in display order,
    so a follow-up like "book the first one" can be resolved without the raw slot_id."""
    _last_slots[patient_id] = slot_ids


def get_last_slots(patient_id: str) -> list[str]:
    return _last_slots.get(patient_id, [])


def set_last_offers(patient_id: str, offer_ids: list[str]) -> None:
    """Remember the offer_ids most recently shown to this patient, in display order,
    so a follow-up like "redeem the first one" can be resolved without the raw offer_id."""
    _last_offers[patient_id] = offer_ids


def get_last_offers(patient_id: str) -> list[str]:
    return _last_offers.get(patient_id, [])
