"""
Prescription management — create prescriptions and view medication schedule.
Called by doctors via the admin interface or directly after consultation.
"""

import uuid
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.database.base import get_prescription_session
from backend.database.prescription_db.models import Prescription, PrescriptionMedication, MedicationSchedule
from backend.services.auth import get_current_patient_id, oauth2_scheme
from backend.workflows.medication_reminders import schedule_all_active_reminders

router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])


class MedicationIn(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    times: list[str]   # e.g. ["08:00", "20:00"]


class PrescriptionCreateRequest(BaseModel):
    doctor_id: str
    appointment_id: str
    start_date: date
    end_date: date
    notes: str = ""
    medications: list[MedicationIn]


@router.post("/")
def create_prescription(body: PrescriptionCreateRequest, token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_prescription_session() as db:
        rx = Prescription(
            patient_id=uuid.UUID(patient_id),
            doctor_id=uuid.UUID(body.doctor_id),
            appointment_id=uuid.UUID(body.appointment_id),
            start_date=body.start_date,
            end_date=body.end_date,
            notes=body.notes,
        )
        db.add(rx)
        db.flush()
        for med in body.medications:
            m = PrescriptionMedication(
                prescription_id=rx.prescription_id,
                medication_name=med.medication_name,
                dosage=med.dosage,
                frequency=med.frequency,
            )
            db.add(m)
            db.flush()
            for t_str in med.times:
                hour, minute = map(int, t_str.split(":"))
                db.add(MedicationSchedule(
                    medication_id=m.medication_id,
                    medication_time=time(hour, minute),
                ))
    # Reload reminder scheduler so new schedules are picked up
    try:
        schedule_all_active_reminders()
    except Exception:
        pass
    return {"prescription_id": str(rx.prescription_id), "status": "created"}


@router.get("/me")
def get_my_prescriptions(token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    with get_prescription_session() as db:
        prescriptions = (
            db.query(Prescription)
            .filter(Prescription.patient_id == uuid.UUID(patient_id))
            .order_by(Prescription.created_at.desc())
            .all()
        )
        result = []
        for rx in prescriptions:
            meds = []
            for med in rx.medications:
                schedules = [s.medication_time.strftime("%H:%M") for s in med.schedules]
                meds.append({
                    "medication_name": med.medication_name,
                    "dosage": med.dosage,
                    "frequency": med.frequency,
                    "times": schedules,
                })
            result.append({
                "prescription_id": str(rx.prescription_id),
                "start_date": rx.start_date.isoformat(),
                "end_date": rx.end_date.isoformat(),
                "notes": rx.notes,
                "medications": meds,
            })
        return result
