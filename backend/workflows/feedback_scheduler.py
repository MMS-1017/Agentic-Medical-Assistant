"""
Feedback scheduler — triggers feedback collection 24h after appointment completion.
"""

import logging
import uuid
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from backend.database.base import get_appointment_session, get_patient_session
from backend.database.appointment_db.models import Appointment
from backend.database.patient_db.models import Patient
from backend.services.notification import notify_feedback_request

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(daemon=True)


def _send_feedback_request(appointment_id: str, patient_id: str, appointment_date: str):
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        if not patient or not patient.telegram_chat_id:
            return
        notify_feedback_request(patient.telegram_chat_id, appointment_date)

    # Mark feedback as scheduled so we don't resend
    with get_appointment_session() as db:
        appt = db.query(Appointment).filter(
            Appointment.appointment_id == uuid.UUID(appointment_id)
        ).first()
        if appt:
            appt.feedback_scheduled = True


def schedule_feedback(appointment_id: str, patient_id: str, appointment_date: datetime):
    """Call this immediately after an appointment is booked."""
    fire_at = appointment_date + timedelta(hours=24)
    job_id = f"feedback_{appointment_id}"
    _scheduler.add_job(
        _send_feedback_request,
        trigger="date",
        run_date=fire_at,
        args=[appointment_id, patient_id, appointment_date.strftime("%Y-%m-%d %H:%M")],
        id=job_id,
        replace_existing=True,
    )
    logger.info("Feedback job %s scheduled for %s", job_id, fire_at)


def start_feedback_scheduler():
    if not _scheduler.running:
        _scheduler.start()


def stop_feedback_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
