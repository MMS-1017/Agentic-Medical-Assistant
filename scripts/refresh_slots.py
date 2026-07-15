"""
Refresh availability slots — run this whenever slots expire (i.e. seeded slots are in the past).

Usage:
    python scripts/refresh_slots.py

What it does:
  1. Deletes all un-booked slots whose start_time is in the past.
  2. Inserts fresh slots for the next 14 days across all active doctors / clinics.
"""

from datetime import datetime, timedelta

from backend.database.base import get_appointment_session
from backend.database.appointment_db.models import Doctor, Clinic, AvailabilitySlot


SLOT_HOURS = [9, 10, 11, 14, 15, 16]
DAYS_AHEAD = 14


def refresh():
    with get_appointment_session() as db:
        # ── 1. Remove stale un-booked slots ───────────────────────────────────
        deleted = (
            db.query(AvailabilitySlot)
            .filter(
                AvailabilitySlot.is_booked == False,
                AvailabilitySlot.start_time <= datetime.utcnow(),
            )
            .delete(synchronize_session=False)
        )
        print(f"  Deleted {deleted} expired un-booked slots.")

        # ── 2. Fetch doctors & clinics paired by index ─────────────────────────
        doctors = db.query(Doctor).filter(Doctor.is_active == True).order_by(Doctor.doctor_id).all()
        clinics = db.query(Clinic).filter(Clinic.is_active == True).order_by(Clinic.clinic_id).all()

        if not doctors or not clinics:
            print("  No active doctors or clinics found — run the main seed first.")
            return

        # Pair each doctor with the same-index clinic (same pairing as seed.py).
        pairs = list(zip(doctors, clinics))

        now = datetime.utcnow()
        inserted = 0
        for doctor, clinic in pairs:
            for day in range(1, DAYS_AHEAD + 1):
                for hour in SLOT_HOURS:
                    start = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day)
                    db.add(AvailabilitySlot(
                        doctor_id=doctor.doctor_id,
                        clinic_id=clinic.clinic_id,
                        start_time=start,
                        end_time=start + timedelta(minutes=30),
                        is_booked=False,
                    ))
                    inserted += 1

        db.flush()
        print(f"  Inserted {inserted} fresh slots for the next {DAYS_AHEAD} days.")

    print("Done! Slots are now available.")


if __name__ == "__main__":
    refresh()
