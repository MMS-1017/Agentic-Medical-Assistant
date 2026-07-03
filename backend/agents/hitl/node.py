"""
HITL node — enqueues low-confidence cases for doctor review.
"""

from backend.agents.state import AgentState
from backend.services.hitl import create_hitl_case
from backend.services import session as session_svc


def hitl_node(state: AgentState) -> dict:
    patient_id = state["patient_id"]
    confidence = state.get("confidence_score", 0.0)
    department = state.get("department", "General Medicine")
    query = state.get("query", "")

    case_id = create_hitl_case(
        patient_id=patient_id,
        confidence_score=confidence,
        suggested_department=department,
        symptoms_report=query,
    )

    response = (
        "Your case requires review by one of our doctors. "
        f"A specialist will contact you shortly. (Case ID: {case_id})"
    )
    session_svc.append_message(patient_id, "assistant", response)
    return {"response": response, "hitl_case_id": case_id}
