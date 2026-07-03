"""
Patient profile management endpoints.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.database.base import get_patient_session, get_appointment_session
from backend.database.patient_db.models import Patient, MedicalHistory, Diagnosis, LoyaltyTransaction
from backend.database.appointment_db.models import Appointment, Doctor, Clinic
from backend.services.auth import get_current_patient_id, oauth2_scheme

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("/me")
def get_my_profile(token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_patient_session() as db:
        patient = db.query(Patient).filter(Patient.patient_id == uuid.UUID(patient_id)).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        history = patient.medical_history
        return {
            "patient_id": str(patient.patient_id),
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "email": patient.email,
            "phone": patient.phone,
            "telegram_chat_id": patient.telegram_chat_id,
            "loyalty_points": patient.loyalty_points,
            "risk_level": patient.risk_level,
            "ambulance_request_count": patient.ambulance_request_count,
            "medical_history": {
                "chronic_conditions": history.chronic_conditions if history else [],
                "allergies": history.allergies if history else [],
                "current_medications": history.current_medications if history else [],
            } if history else None,
        }


class UpdateTelegramRequest(BaseModel):
    telegram_chat_id: str


@router.patch("/me/telegram")
def update_telegram(body: UpdateTelegramRequest, token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_patient_session() as db:
        patient = db.query(Patient).filter(Patient.patient_id == uuid.UUID(patient_id)).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        patient.telegram_chat_id = body.telegram_chat_id
        return {"status": "updated", "telegram_chat_id": body.telegram_chat_id}


class MedicalHistoryRequest(BaseModel):
    chronic_conditions: list[str] = []
    allergies: list[str] = []
    current_medications: list[str] = []


@router.put("/me/history")
def update_medical_history(body: MedicalHistoryRequest, token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_patient_session() as db:
        history = db.query(MedicalHistory).filter(
            MedicalHistory.patient_id == uuid.UUID(patient_id)
        ).first()
        if history:
            history.chronic_conditions = body.chronic_conditions
            history.allergies = body.allergies
            history.current_medications = body.current_medications
        else:
            db.add(MedicalHistory(
                patient_id=uuid.UUID(patient_id),
                chronic_conditions=body.chronic_conditions,
                allergies=body.allergies,
                current_medications=body.current_medications,
            ))
        return {"status": "updated"}


@router.get("/me/diagnoses")
def get_my_diagnoses(token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_patient_session() as db:
        diagnoses = (
            db.query(Diagnosis)
            .filter(Diagnosis.patient_id == uuid.UUID(patient_id))
            .order_by(Diagnosis.created_at.desc())
            .limit(10)
            .all()
        )
        return [
            {
                "diagnosis_id": str(d.diagnosis_id),
                "department": d.department,
                "confidence_score": d.confidence_score,
                "urgency_score": d.urgency_score,
                "raw_complaint": d.raw_complaint,
                "created_at": d.created_at.isoformat(),
            }
            for d in diagnoses
        ]


@router.get("/me/appointments")
def get_my_appointments(token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_appointment_session() as db:
        appointments = (
            db.query(Appointment, Doctor, Clinic)
            .join(Doctor, Appointment.doctor_id == Doctor.doctor_id)
            .join(Clinic, Appointment.clinic_id == Clinic.clinic_id)
            .filter(Appointment.patient_id == uuid.UUID(patient_id))
            .order_by(Appointment.appointment_date.desc())
            .all()
        )
        return [
            {
                "appointment_id": str(a.appointment_id),
                "doctor": d.full_name,
                "clinic": c.clinic_name,
                "department": a.department,
                "appointment_date": a.appointment_date.isoformat(),
                "status": a.status,
            }
            for a, d, c in appointments
        ]


@router.get("/me/loyalty")
def get_loyalty(token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_patient_session() as db:
        patient = db.query(Patient).filter(Patient.patient_id == uuid.UUID(patient_id)).first()
        transactions = (
            db.query(LoyaltyTransaction)
            .filter(LoyaltyTransaction.patient_id == uuid.UUID(patient_id))
            .order_by(LoyaltyTransaction.created_at.desc())
            .limit(20)
            .all()
        )
        return {
            "current_points": patient.loyalty_points if patient else 0,
            "transactions": [
                {
                    "points": t.points,
                    "reason": t.reason,
                    "created_at": t.created_at.isoformat(),
                }
                for t in transactions
            ],
        }
