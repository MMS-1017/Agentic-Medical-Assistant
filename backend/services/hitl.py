"""
Human-in-the-Loop (HITL) service.
Enqueues low-confidence cases for doctor review.
"""

import uuid
from datetime import datetime

from backend.database.base import get_patient_session
from backend.database.patient_db.models import HitlCase, Patient, MedicalHistory


def create_hitl_case(
    patient_id: str,
    confidence_score: float,
    suggested_department: str,
    symptoms_report: str,
) -> str:
    """Insert a HITL case into the queue and return the case_id."""
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        history = (
            db.query(MedicalHistory)
            .filter(MedicalHistory.patient_id == uuid.UUID(patient_id))
            .first()
        )
        name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
        chronic = ", ".join(history.chronic_conditions) if history else "None"
        summary = (
            f"Patient: {name}\n"
            f"Chronic conditions: {chronic}\n"
            f"Suggested department: {suggested_department}\n"
            f"Confidence: {confidence_score:.2f}\n"
        )
        case = HitlCase(
            patient_id=uuid.UUID(patient_id),
            confidence_score=confidence_score,
            suggested_department=suggested_department,
            case_summary=summary,
            symptoms_report=symptoms_report,
        )
        db.add(case)
        db.flush()
        return str(case.case_id)


def resolve_hitl_case(case_id: str, doctor_id: str, notes: str) -> bool:
    """Mark a HITL case as resolved by a doctor."""
    with get_patient_session() as db:
        case = db.query(HitlCase).filter(
            HitlCase.case_id == uuid.UUID(case_id)
        ).first()
        if not case:
            return False
        case.status = "resolved"
        case.assigned_doctor_id = doctor_id
        case.doctor_notes = notes
        case.resolved_at = datetime.utcnow()
        return True


def list_pending_cases() -> list[dict]:
    with get_patient_session() as db:
        cases = db.query(HitlCase).filter(HitlCase.status == "pending").all()
        return [
            {
                "case_id": str(c.case_id),
                "patient_id": str(c.patient_id),
                "confidence_score": c.confidence_score,
                "suggested_department": c.suggested_department,
                "case_summary": c.case_summary,
                "created_at": c.created_at.isoformat(),
            }
            for c in cases
        ]
