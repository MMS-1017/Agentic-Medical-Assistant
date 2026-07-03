"""
Admin endpoints — HITL case management and seeding.
In production, secure these behind a doctor/admin role check.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.hitl import list_pending_cases, resolve_hitl_case

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/hitl/cases")
def get_pending_cases():
    return list_pending_cases()


class ResolveRequest(BaseModel):
    doctor_id: str
    notes: str


@router.post("/hitl/cases/{case_id}/resolve")
def resolve_case(case_id: str, body: ResolveRequest):
    success = resolve_hitl_case(case_id, body.doctor_id, body.notes)
    if not success:
        return {"error": "Case not found"}
    return {"status": "resolved"}
