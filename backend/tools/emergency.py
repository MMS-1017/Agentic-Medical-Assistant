import uuid

from langchain_core.tools import tool

from backend.database.base import get_patient_session
from backend.database.patient_db.models import Patient, MedicalHistory

# Conditions triggering immediate (no-timer) dispatch for high-risk patients
HIGH_RISK_CONDITIONS = {"heart disease", "cardiac", "stroke history", "chronic heart"}

# Urgency timer per condition (seconds)
EMERGENCY_TIMERS = {
    "heart attack": 30,
    "stroke": 60,
    "severe trauma": 0,
    "internal bleeding": 30,
    "respiratory failure": 30,
}


@tool
def assess_emergency_risk(patient_id: str) -> str:
    """
    Check if a patient is high-risk based on medical history and ambulance usage.
    Returns a risk assessment string.
    """
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        if not patient:
            return "unknown|Patient not found."
        history = patient.medical_history
        chronic = [c.lower() for c in (history.chronic_conditions if history else [])]
        is_cardiac = any(kw in c for c in chronic for kw in HIGH_RISK_CONDITIONS)
        frequent_amb = patient.ambulance_request_count >= 3
        if patient.risk_level == "high" or is_cardiac or frequent_amb:
            return f"high|Patient has high-risk profile (risk_level={patient.risk_level}, ambulances={patient.ambulance_request_count})."
        return f"normal|Patient has standard risk profile."


@tool
def increment_ambulance_count(patient_id: str) -> str:
    """Record that an ambulance was dispatched for this patient."""
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        if not patient:
            return "Patient not found."
        patient.ambulance_request_count += 1
        return f"Ambulance count updated: {patient.ambulance_request_count}."


@tool
def get_emergency_timer(condition: str) -> str:
    """
    Return the escalation timer in seconds for an emergency condition.
    Returns '0' for immediate dispatch.
    """
    condition_lower = condition.lower()
    for key, seconds in EMERGENCY_TIMERS.items():
        if key in condition_lower:
            return str(seconds)
    return "60"
