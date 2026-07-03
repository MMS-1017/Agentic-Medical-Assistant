import uuid
from datetime import datetime

from langchain_core.tools import tool

from backend.database.base import get_appointment_session
from backend.database.appointment_db.models import AvailabilitySlot, Appointment, Doctor, Clinic


@tool
def find_available_slots(department: str, limit: int = 5) -> str:
    """Find available appointment slots for a given medical department."""
    with get_appointment_session() as db:
        rows = (
            db.query(AvailabilitySlot, Doctor, Clinic)
            .join(Doctor, AvailabilitySlot.doctor_id == Doctor.doctor_id)
            .join(Clinic, AvailabilitySlot.clinic_id == Clinic.clinic_id)
            .filter(
                Clinic.department.ilike(f"%{department}%"),
                AvailabilitySlot.is_booked == False,
                AvailabilitySlot.start_time > datetime.utcnow(),
            )
            .order_by(AvailabilitySlot.start_time)
            .limit(limit)
            .all()
        )
        if not rows:
            return f"No available slots found for {department}."
        lines = []
        for slot, doctor, clinic in rows:
            lines.append(
                f"[{slot.slot_id}] Dr. {doctor.full_name} — {clinic.clinic_name} "
                f"on {slot.start_time.strftime('%Y-%m-%d %H:%M')}"
            )
        return "Available slots:\n" + "\n".join(lines)


@tool
def book_slot(slot_id: str, patient_id: str, department: str) -> str:
    """Book an available appointment slot for a patient."""
    with get_appointment_session() as db:
        slot = db.query(AvailabilitySlot).filter(
            AvailabilitySlot.slot_id == uuid.UUID(slot_id)
        ).first()
        if not slot:
            return "Slot not found."
        if slot.is_booked:
            return "Slot is already booked. Please choose another."
        slot.is_booked = True
        appointment = Appointment(
            patient_id=uuid.UUID(patient_id),
            doctor_id=slot.doctor_id,
            clinic_id=slot.clinic_id,
            appointment_date=slot.start_time,
            department=department,
        )
        db.add(appointment)
        db.flush()
        return (
            f"Appointment confirmed. ID: {appointment.appointment_id}. "
            f"Date: {slot.start_time.strftime('%Y-%m-%d %H:%M')}."
        )


@tool
def recommend_alternative(department: str) -> str:
    """Suggest alternative options when no appointment slot is available."""
    return (
        f"No slots available for {department} right now. Options:\n"
        "1. Visit the nearest Emergency Department.\n"
        "2. Try a partner hospital — ask staff for referral.\n"
        "3. Check back tomorrow for new openings."
    )
