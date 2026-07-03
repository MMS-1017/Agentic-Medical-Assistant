"""
Medication reminder scheduler — non-agentic background service.
Runs as a cron job via APScheduler; sends Telegram reminder 30 min before each dose.
"""

import logging
from datetime import datetime, timedelta, time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database.base import get_prescription_session, get_patient_session
from backend.database.prescription_db.models import MedicationSchedule, PrescriptionMedication, Prescription
from backend.database.patient_db.models import Patient
from backend.services.notification import notify_medication_reminder

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()


def _reminder_for(schedule_id: str, medication_name: str, medication_time: str, patient_id: str):
    """Fetch patient telegram id and send the reminder."""
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == __import__("uuid").UUID(patient_id)
        ).first()
        if not patient or not patient.telegram_chat_id:
            logger.warning("No telegram id for patient %s — skipping reminder", patient_id)
            return
        notify_medication_reminder(patient.telegram_chat_id, medication_name, medication_time)


def _calc_reminder_time(med_time: time) -> tuple[int, int]:
    """Return (hour, minute) 30 minutes before medication_time."""
    dt = datetime(2000, 1, 1, med_time.hour, med_time.minute) - timedelta(minutes=30)
    return dt.hour, dt.minute


def schedule_all_active_reminders() -> None:
    """Load all active prescriptions and schedule reminder jobs."""
    with get_prescription_session() as db:
        schedules = (
            db.query(MedicationSchedule, PrescriptionMedication, Prescription)
            .join(PrescriptionMedication, MedicationSchedule.medication_id == PrescriptionMedication.medication_id)
            .join(Prescription, PrescriptionMedication.prescription_id == Prescription.prescription_id)
            .filter(Prescription.end_date >= datetime.utcnow().date())
            .all()
        )
        for sched, med, prescription in schedules:
            job_id = f"med_{sched.schedule_id}"
            if _scheduler.get_job(job_id):
                continue
            rh, rm = _calc_reminder_time(sched.medication_time)
            _scheduler.add_job(
                _reminder_for,
                CronTrigger(hour=rh, minute=rm),
                args=[
                    str(sched.schedule_id),
                    med.medication_name,
                    sched.medication_time.strftime("%H:%M"),
                    str(prescription.patient_id),
                ],
                id=job_id,
                replace_existing=True,
            )
    logger.info("Medication reminders scheduled")


def start_reminder_scheduler() -> None:
    _scheduler.start()
    # Reload active prescriptions every hour
    _scheduler.add_job(
        schedule_all_active_reminders,
        "interval",
        hours=1,
        id="reload_reminders",
        replace_existing=True,
    )
    schedule_all_active_reminders()


def stop_reminder_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
