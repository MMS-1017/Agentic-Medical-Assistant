"""
Telegram notification service — shared by emergency alerts, reminders, and feedback.
"""

import logging

import requests

from backend.config import settings

logger = logging.getLogger(__name__)
_BASE = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


def send_message(chat_id: str, text: str) -> bool:
    """Send a Telegram message. Returns True on success."""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping notification")
        return False
    try:
        resp = requests.post(
            f"{_BASE}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)
        return False


def notify_emergency(chat_id: str, condition: str, patient_name: str) -> bool:
    msg = (
        f"🚨 <b>EMERGENCY ALERT</b>\n"
        f"Patient: {patient_name}\n"
        f"Condition: {condition}\n"
        f"Ambulance has been dispatched. Hospital staff have been notified."
    )
    return send_message(chat_id, msg)


def notify_appointment(chat_id: str, doctor: str, date: str, clinic: str) -> bool:
    msg = (
        f"📅 <b>Appointment Confirmed</b>\n"
        f"Doctor: {doctor}\n"
        f"Clinic: {clinic}\n"
        f"Date: {date}"
    )
    return send_message(chat_id, msg)


def notify_medication_reminder(chat_id: str, medication_name: str, medication_time: str) -> bool:
    msg = f"💊 Reminder: You should take <b>{medication_name}</b> at {medication_time}."
    return send_message(chat_id, msg)


def notify_feedback_request(chat_id: str, appointment_date: str) -> bool:
    msg = (
        f"📝 How was your appointment on {appointment_date}?\n"
        f"Please reply with your satisfaction score (1-5) and any comments."
    )
    return send_message(chat_id, msg)
