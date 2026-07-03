from typing import Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Identity
    patient_id: str
    patient_name: str

    # Input
    query: str
    modality: str               # "text" | "voice" | "image" | "mixed"
    voice_transcript: Optional[str]
    image_findings: Optional[str]

    # Routing
    intent: str                 # "scheduling" | "diagnosis" | "emergency" | "feedback" | "unknown"

    # Medical context
    medical_history_summary: Optional[str]

    # Diagnosis output
    department: Optional[str]
    confidence_score: Optional[float]
    urgency_score: Optional[float]

    # Emergency
    emergency_risk: Optional[str]   # "high" | "normal"
    emergency_dispatched: bool

    # HITL
    hitl_required: bool
    hitl_case_id: Optional[str]

    # Scheduling
    appointment_id: Optional[str]

    # Final response
    response: str
    error: Optional[str]
