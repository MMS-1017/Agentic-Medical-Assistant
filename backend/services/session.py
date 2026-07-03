"""
In-process conversation session store keyed by patient_id.
Holds recent message history for multi-turn context.
"""

from collections import defaultdict
from typing import Any

_sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
MAX_HISTORY = 20


def get_history(patient_id: str) -> list[dict]:
    return _sessions[patient_id][-MAX_HISTORY:]


def append_message(patient_id: str, role: str, content: str) -> None:
    _sessions[patient_id].append({"role": role, "content": content})


def clear_session(patient_id: str) -> None:
    _sessions.pop(patient_id, None)
