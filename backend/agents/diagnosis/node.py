"""
Diagnosis agent — multimodal complaint analysis → department + confidence + urgency.
Model: Qwen 3 for reasoning; Qwen2.5-VL for images (handled upstream by multimodal service).
"""

import json
import logging
import uuid
from datetime import datetime

from backend.agents.state import AgentState
from backend.database.base import get_patient_session
from backend.database.patient_db.models import Diagnosis
from backend.llm.provider import chat
from backend.llm.registry import DIAGNOSIS_MODEL
from backend.rag.retrieval.retriever import retrieve_medical_context
from backend.services import session as session_svc
from backend.services.multimodal import fuse_inputs

logger = logging.getLogger(__name__)

_SYSTEM = """You are a clinical diagnosis AI assistant. Analyze the patient's complaint and
medical context, then output a structured JSON diagnosis.

Output ONLY this JSON (no markdown):
{
  "department": "<medical department, e.g. Cardiology, Orthopedics, Neurology>",
  "confidence_score": <0.0–1.0>,
  "urgency_score": <0.0–1.0>,
  "reasoning": "<brief clinical reasoning>"
}

Urgency scoring guide:
- 0.9–1.0: Life-threatening (heart attack, stroke, severe trauma)
- 0.7–0.89: Urgent (fracture, high fever, severe pain)
- 0.4–0.69: Moderate (infections, moderate pain)
- 0.0–0.39: Low (minor complaints, follow-ups)

Confidence scoring: how certain you are of the department assignment.
If confidence < 0.70, note that human review may be needed."""


def _persist_diagnosis(patient_id: str, department: str, confidence: float, urgency: float, complaint: str):
    with get_patient_session() as db:
        db.add(
            Diagnosis(
                patient_id=uuid.UUID(patient_id),
                department=department,
                confidence_score=confidence,
                urgency_score=urgency,
                raw_complaint=complaint[:1000],
            )
        )


def diagnosis_node(state: AgentState) -> dict:
    patient_id = state["patient_id"]
    query = state.get("query", "")
    transcript = state.get("voice_transcript") or ""
    image_findings = state.get("image_findings") or ""
    history_summary = state.get("medical_history_summary", "No history available.")

    fused = fuse_inputs(text=query, transcript=transcript, image_findings=image_findings)
    rag_chunks = retrieve_medical_context(fused, k=3)
    rag_context = "\n---\n".join(rag_chunks) if rag_chunks else "No reference data available."

    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Patient medical history: {history_summary}\n\n"
                f"Complaint: {fused}\n\n"
                f"Relevant medical knowledge:\n{rag_context}"
            ),
        },
    ]

    try:
        raw = chat(DIAGNOSIS_MODEL, messages, temperature=0.1)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        parsed = json.loads(raw[start:end])
        department = parsed.get("department", "General Medicine")
        confidence = float(parsed.get("confidence_score", 0.5))
        urgency = float(parsed.get("urgency_score", 0.3))
    except Exception as exc:
        logger.error("Diagnosis parsing error: %s", exc)
        department, confidence, urgency = "General Medicine", 0.5, 0.3

    _persist_diagnosis(patient_id, department, confidence, urgency, fused)

    hitl_required = confidence < 0.70
    session_svc.append_message(
        patient_id,
        "assistant",
        f"Assessed: {department} (confidence {confidence:.0%}, urgency {urgency:.0%})",
    )

    return {
        "department": department,
        "confidence_score": confidence,
        "urgency_score": urgency,
        "hitl_required": hitl_required,
    }


def diagnosis_router(state: AgentState) -> str:
    if state.get("hitl_required"):
        return "hitl"
    urgency = state.get("urgency_score", 0.0)
    if urgency >= 0.85:
        return "emergency"
    return "scheduling"
