"""
Comprehensive seed script — populates all 4 databases with realistic fake data.
Run: python -m backend.database.seed
"""

import uuid
from datetime import datetime, timedelta, time, date

from backend.database.base import create_all_tables, get_patient_session, get_appointment_session, get_prescription_session, get_analytics_session
from backend.database.patient_db.models import Patient, MedicalHistory, Diagnosis, LoyaltyTransaction, Offer, User, UserSession, HitlCase
from backend.database.appointment_db.models import Doctor, Clinic, AvailabilitySlot, Appointment
from backend.database.prescription_db.models import Prescription, PrescriptionMedication, MedicationSchedule
from backend.database.feedback_analytics_db.models import Feedback, AgentLog
from backend.services.auth import hash_password


# ─── IDs we reuse across DB inserts (plain UUIDs, no FK enforcement) ──────────
PATIENT_IDS = [uuid.uuid4() for _ in range(5)]
USER_IDS = [uuid.uuid4() for _ in range(5)]
DOCTOR_IDS = [uuid.uuid4() for _ in range(5)]
CLINIC_IDS = [uuid.uuid4() for _ in range(5)]
APPOINTMENT_IDS = [uuid.uuid4() for _ in range(8)]


# ═══════════════════════════════════════════════════════════════════════════════
# PATIENT DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def seed_patients():
    with get_patient_session() as db:
        if db.query(Patient).count() > 0:
            print("  Patient DB already seeded — skipping.")
            return

        # ── 5 Patients ────────────────────────────────────────────────────────
        patients_data = [
            # (index, first, last, email, phone, telegram, loyalty, risk, ambulance_count)
            (0, "Ahmed",   "Mohamed", "ahmed.m@example.com",   "+201001234567", "100000001", 150,  "normal", 0),
            (1, "Fatima",  "Ali",     "fatima.ali@example.com","+201002345678", "100000002", 350,  "high",   4),
            (2, "Omar",    "Khaled",  "omar.k@example.com",    "+201003456789", "100000003", 50,   "normal", 1),
            (3, "Nour",    "Hassan",  "nour.h@example.com",    "+201004567890", "100000004", 0,    "normal", 0),
            (4, "Yasmine", "Ibrahim", "yasmine.i@example.com", "+201005678901", "100000005", 500,  "normal", 0),
        ]

        for idx, first, last, email, phone, telegram, points, risk, amb in patients_data:
            db.add(Patient(
                patient_id=PATIENT_IDS[idx],
                first_name=first, last_name=last, email=email,
                phone=phone, telegram_chat_id=telegram,
                loyalty_points=points, risk_level=risk,
                ambulance_request_count=amb,
            ))

        db.flush()

        # ── Medical Histories ─────────────────────────────────────────────────
        histories = [
            (0, [],                                      [],              ["vitamin D"]),
            (1, ["heart disease", "type 2 diabetes"],    ["penicillin"],  ["metformin", "aspirin", "metoprolol"]),
            (2, ["hypertension"],                         ["aspirin"],     ["amlodipine"]),
            (3, [],                                      [],              []),
            (4, ["asthma"],                              ["ibuprofen"],   ["salbutamol inhaler"]),
        ]
        for idx, chronic, allergies, meds in histories:
            db.add(MedicalHistory(
                patient_id=PATIENT_IDS[idx],
                chronic_conditions=chronic,
                allergies=allergies,
                current_medications=meds,
            ))

        db.flush()

        # ── Past Diagnoses ────────────────────────────────────────────────────
        db.add(Diagnosis(patient_id=PATIENT_IDS[0], department="General Medicine", confidence_score=0.88, urgency_score=0.20, raw_complaint="Mild fatigue and cold symptoms", created_at=datetime.utcnow() - timedelta(days=30)))
        db.add(Diagnosis(patient_id=PATIENT_IDS[1], department="Cardiology",       confidence_score=0.95, urgency_score=0.90, raw_complaint="Crushing chest pain radiating to left arm", created_at=datetime.utcnow() - timedelta(days=60)))
        db.add(Diagnosis(patient_id=PATIENT_IDS[2], department="Cardiology",       confidence_score=0.82, urgency_score=0.55, raw_complaint="Occasional chest tightness on exertion", created_at=datetime.utcnow() - timedelta(days=15)))
        db.add(Diagnosis(patient_id=PATIENT_IDS[3], department="Ophthalmology",    confidence_score=0.91, urgency_score=0.25, raw_complaint="Red eye with discharge since yesterday", created_at=datetime.utcnow() - timedelta(days=7)))
        db.add(Diagnosis(patient_id=PATIENT_IDS[4], department="General Medicine", confidence_score=0.78, urgency_score=0.30, raw_complaint="Persistent cough and mild fever", created_at=datetime.utcnow() - timedelta(days=45)))

        db.flush()

        # ── Loyalty Transactions ──────────────────────────────────────────────
        db.add(LoyaltyTransaction(patient_id=PATIENT_IDS[0], points=100, reason="Appointment booked", created_at=datetime.utcnow() - timedelta(days=60)))
        db.add(LoyaltyTransaction(patient_id=PATIENT_IDS[0], points=50,  reason="Appointment booked", created_at=datetime.utcnow() - timedelta(days=30)))
        db.add(LoyaltyTransaction(patient_id=PATIENT_IDS[1], points=150, reason="Appointment booked", created_at=datetime.utcnow() - timedelta(days=90)))
        db.add(LoyaltyTransaction(patient_id=PATIENT_IDS[1], points=200, reason="Appointment booked", created_at=datetime.utcnow() - timedelta(days=60)))
        db.add(LoyaltyTransaction(patient_id=PATIENT_IDS[2], points=50,  reason="Appointment booked", created_at=datetime.utcnow() - timedelta(days=20)))
        db.add(LoyaltyTransaction(patient_id=PATIENT_IDS[4], points=500, reason="Appointment booked", created_at=datetime.utcnow() - timedelta(days=120)))

        db.flush()

        # ── Offers ────────────────────────────────────────────────────────────
        offers = [
            Offer(offer_name="5% Discount",        description="5% off your next consultation",   required_points=100, discount_percent=5.0),
            Offer(offer_name="10% Discount",       description="10% off your next consultation",  required_points=300, discount_percent=10.0),
            Offer(offer_name="Free Consultation",  description="One free consultation session",   required_points=500, discount_percent=100.0),
        ]
        for o in offers:
            db.add(o)

        db.flush()

        # ── HITL Cases ────────────────────────────────────────────────────────
        db.add(HitlCase(
            patient_id=PATIENT_IDS[3],
            confidence_score=0.55,
            suggested_department="Neurology",
            case_summary="Patient: Nour Hassan\nChronic conditions: none\nSuggested department: Neurology\nConfidence: 0.55\n",
            symptoms_report="Recurring headaches with visual aura for 3 weeks",
            status="pending",
            created_at=datetime.utcnow() - timedelta(days=3),
        ))
        db.add(HitlCase(
            patient_id=PATIENT_IDS[2],
            confidence_score=0.62,
            suggested_department="Cardiology",
            case_summary="Patient: Omar Khaled\nChronic conditions: hypertension\nSuggested department: Cardiology\nConfidence: 0.62\n",
            symptoms_report="Palpitations with occasional dizziness",
            status="resolved",
            assigned_doctor_id="dr-001",
            doctor_notes="Holter monitor ordered. Likely benign ectopic beats. Follow up in 2 weeks.",
            created_at=datetime.utcnow() - timedelta(days=14),
            resolved_at=datetime.utcnow() - timedelta(days=12),
        ))

        # ── Users (auth) ──────────────────────────────────────────────────────
        users_data = [
            (0, "ahmed.m@example.com"),
            (1, "fatima.ali@example.com"),
            (2, "omar.k@example.com"),
            (3, "nour.h@example.com"),
            (4, "yasmine.i@example.com"),
        ]
        for idx, email in users_data:
            db.add(User(
                user_id=USER_IDS[idx],
                email=email,
                password_hash=hash_password("Password123!"),
                role="patient",
                patient_id=PATIENT_IDS[idx],
            ))

    print("  Patient DB seeded: 5 patients, histories, diagnoses, loyalty, offers, HITL cases, users.")


# ═══════════════════════════════════════════════════════════════════════════════
# APPOINTMENT DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def seed_appointments():
    with get_appointment_session() as db:
        if db.query(Doctor).count() > 0:
            print("  Appointment DB already seeded — skipping.")
            return

        # ── Doctors ───────────────────────────────────────────────────────────
        doctors = [
            (0, "Dr. Ahmed Hassan",   "Cardiology",       "ahmed.hassan@hospital.com", "+2011000001"),
            (1, "Dr. Sara Ali",       "Ophthalmology",    "sara.ali@hospital.com",     "+2011000002"),
            (2, "Dr. Omar Khalil",    "Orthopedics",      "omar.khalil@hospital.com",  "+2011000003"),
            (3, "Dr. Nadia Ibrahim",  "Neurology",        "nadia.ibrahim@hospital.com","+2011000004"),
            (4, "Dr. Youssef Mahmoud","General Medicine", "youssef.m@hospital.com",    "+2011000005"),
        ]
        for idx, name, specialty, email, phone in doctors:
            db.add(Doctor(doctor_id=DOCTOR_IDS[idx], full_name=name, specialty=specialty, email=email, phone=phone))

        db.flush()

        # ── Clinics ───────────────────────────────────────────────────────────
        clinics_data = [
            (0, "Cardiology Clinic",       "Cardiology",       "Main Hospital, Floor 3, Wing A"),
            (1, "Eye Clinic",              "Ophthalmology",    "Main Hospital, Floor 2, Wing B"),
            (2, "Bone & Joint Center",     "Orthopedics",      "Annex Building, Floor 1"),
            (3, "Neuroscience Center",     "Neurology",        "Main Hospital, Floor 4, Wing A"),
            (4, "General Medicine Clinic", "General Medicine", "Main Hospital, Floor 1, Wing C"),
        ]
        for idx, name, dept, addr in clinics_data:
            db.add(Clinic(clinic_id=CLINIC_IDS[idx], clinic_name=name, department=dept, address=addr))

        db.flush()

        # ── Availability Slots (future: next 7 days) ──────────────────────────
        slot_hours = [9, 10, 11, 14, 15, 16]
        now = datetime.utcnow()
        for doc_idx in range(5):
            for day in range(1, 8):
                for hour in slot_hours:
                    start = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day)
                    db.add(AvailabilitySlot(
                        doctor_id=DOCTOR_IDS[doc_idx],
                        clinic_id=CLINIC_IDS[doc_idx],
                        start_time=start,
                        end_time=start + timedelta(minutes=30),
                        is_booked=False,
                    ))

        # ── Past Appointments (completed — for feedback testing) ──────────────
        past_dates = [
            datetime.utcnow() - timedelta(days=d) for d in [25, 60, 5, 8, 14, 20, 2, 1]
        ]
        appointments_data = [
            (0, 0, 0, 0, "Cardiology",       "completed", False),
            (1, 1, 0, 0, "Cardiology",       "completed", True),   # feedback already sent
            (2, 2, 1, 1, "Ophthalmology",    "completed", False),
            (3, 3, 2, 2, "Orthopedics",      "completed", True),
            (4, 4, 3, 3, "Neurology",        "completed", False),
            (5, 0, 4, 4, "General Medicine", "completed", True),
            (6, 1, 0, 0, "Cardiology",       "scheduled", False),   # upcoming
            (7, 2, 4, 4, "General Medicine", "scheduled", False),   # upcoming
        ]
        for appt_idx, patient_idx, doc_idx, clinic_idx, dept, status, fb_sched in appointments_data:
            db.add(Appointment(
                appointment_id=APPOINTMENT_IDS[appt_idx],
                patient_id=PATIENT_IDS[patient_idx],
                doctor_id=DOCTOR_IDS[doc_idx],
                clinic_id=CLINIC_IDS[clinic_idx],
                appointment_date=past_dates[appt_idx],
                department=dept,
                status=status,
                feedback_scheduled=fb_sched,
            ))

    print("  Appointment DB seeded: 5 doctors, 5 clinics, 210 slots, 8 appointments.")


# ═══════════════════════════════════════════════════════════════════════════════
# PRESCRIPTION DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def seed_prescriptions():
    with get_prescription_session() as db:
        if db.query(Prescription).count() > 0:
            print("  Prescription DB already seeded — skipping.")
            return

        today = date.today()

        # ── Patient 1 (Fatima — cardiac + diabetic) ───────────────────────────
        rx1 = Prescription(
            patient_id=PATIENT_IDS[1],
            doctor_id=DOCTOR_IDS[0],
            appointment_id=APPOINTMENT_IDS[0],
            start_date=today - timedelta(days=25),
            end_date=today + timedelta(days=65),
            notes="Cardiac + diabetes management. Monitor BP and blood sugar daily.",
        )
        db.add(rx1); db.flush()

        med1a = PrescriptionMedication(prescription_id=rx1.prescription_id, medication_name="Aspirin",   dosage="100mg",  frequency="Once daily")
        med1b = PrescriptionMedication(prescription_id=rx1.prescription_id, medication_name="Metformin", dosage="500mg",  frequency="Twice daily")
        med1c = PrescriptionMedication(prescription_id=rx1.prescription_id, medication_name="Metoprolol",dosage="25mg",   frequency="Once daily")
        db.add_all([med1a, med1b, med1c]); db.flush()

        db.add(MedicationSchedule(medication_id=med1a.medication_id, medication_time=time(8, 0)))
        db.add(MedicationSchedule(medication_id=med1b.medication_id, medication_time=time(8, 0)))
        db.add(MedicationSchedule(medication_id=med1b.medication_id, medication_time=time(20, 0)))
        db.add(MedicationSchedule(medication_id=med1c.medication_id, medication_time=time(8, 0)))

        # ── Patient 2 (Omar — hypertension) ──────────────────────────────────
        rx2 = Prescription(
            patient_id=PATIENT_IDS[2],
            doctor_id=DOCTOR_IDS[4],
            appointment_id=APPOINTMENT_IDS[2],
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=85),
            notes="Hypertension management. Reduce sodium intake.",
        )
        db.add(rx2); db.flush()

        med2a = PrescriptionMedication(prescription_id=rx2.prescription_id, medication_name="Amlodipine", dosage="5mg", frequency="Once daily")
        db.add(med2a); db.flush()
        db.add(MedicationSchedule(medication_id=med2a.medication_id, medication_time=time(9, 0)))

        # ── Patient 4 (Yasmine — asthma) ─────────────────────────────────────
        rx3 = Prescription(
            patient_id=PATIENT_IDS[4],
            doctor_id=DOCTOR_IDS[4],
            appointment_id=APPOINTMENT_IDS[4],
            start_date=today - timedelta(days=45),
            end_date=today + timedelta(days=45),
            notes="Asthma — use reliever only when needed. Seek emergency if not responding.",
        )
        db.add(rx3); db.flush()

        med3a = PrescriptionMedication(prescription_id=rx3.prescription_id, medication_name="Salbutamol inhaler", dosage="2 puffs", frequency="When needed (max 4x/day)")
        med3b = PrescriptionMedication(prescription_id=rx3.prescription_id, medication_name="Fluticasone inhaler", dosage="1 puff",  frequency="Twice daily")
        db.add_all([med3a, med3b]); db.flush()
        db.add(MedicationSchedule(medication_id=med3b.medication_id, medication_time=time(8,  0)))
        db.add(MedicationSchedule(medication_id=med3b.medication_id, medication_time=time(20, 0)))

        # ── Patient 0 (Ahmed — short course antibiotics) ─────────────────────
        rx4 = Prescription(
            patient_id=PATIENT_IDS[0],
            doctor_id=DOCTOR_IDS[4],
            appointment_id=APPOINTMENT_IDS[5],
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=5),
            notes="Augmentin for chest infection. Complete full course.",
        )
        db.add(rx4); db.flush()

        med4a = PrescriptionMedication(prescription_id=rx4.prescription_id, medication_name="Augmentin", dosage="1 tablet (625mg)", frequency="Every 12 hours")
        db.add(med4a); db.flush()
        db.add(MedicationSchedule(medication_id=med4a.medication_id, medication_time=time(8,  0)))
        db.add(MedicationSchedule(medication_id=med4a.medication_id, medication_time=time(20, 0)))

    print("  Prescription DB seeded: 4 prescriptions, 8 medications, 10 schedules.")


# ═══════════════════════════════════════════════════════════════════════════════
# FEEDBACK & ANALYTICS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def seed_analytics():
    with get_analytics_session() as db:
        if db.query(Feedback).count() > 0:
            print("  Analytics DB already seeded — skipping.")
            return

        # ── Feedback Records ──────────────────────────────────────────────────
        feedback_data = [
            (APPOINTMENT_IDS[1], PATIENT_IDS[1], 5, "",                       "improving"),
            (APPOINTMENT_IDS[3], PATIENT_IDS[3], 4, "Waiting time was long.", "stable"),
            (APPOINTMENT_IDS[5], PATIENT_IDS[0], 3, "Doctor seemed rushed.",  "stable"),
        ]
        for appt_id, patient_id, score, complaint, health in feedback_data:
            db.add(Feedback(
                appointment_id=appt_id,
                patient_id=patient_id,
                satisfaction_score=score,
                complaint=complaint,
                health_status=health,
                created_at=datetime.utcnow() - timedelta(days=1),
            ))

        # ── Agent Logs ────────────────────────────────────────────────────────
        log_data = [
            ("orchestrator", PATIENT_IDS[0], "Classified intent as 'diagnosis'",           "success", 320),
            ("diagnosis",    PATIENT_IDS[0], "Diagnosed General Medicine — conf 0.88",      "success", 1450),
            ("scheduling",   PATIENT_IDS[0], "Booked slot at Cardiology Clinic",            "success", 980),
            ("orchestrator", PATIENT_IDS[1], "Classified intent as 'emergency'",            "success", 280),
            ("emergency",    PATIENT_IDS[1], "Dispatched ambulance — high-risk cardiac",    "success", 420),
            ("orchestrator", PATIENT_IDS[3], "Classified intent as 'diagnosis'",            "success", 310),
            ("diagnosis",    PATIENT_IDS[3], "Low confidence 0.55 — routed to HITL",        "hitl",    890),
            ("feedback",     PATIENT_IDS[1], "Collected feedback: score=5",                 "success", 560),
        ]
        for agent, patient_id, action, result, duration in log_data:
            db.add(AgentLog(
                agent_name=agent,
                patient_id=patient_id,
                action_taken=action,
                result=result,
                duration_ms=duration,
                created_at=datetime.utcnow() - timedelta(days=1),
            ))

    print("  Analytics DB seeded: 3 feedback records, 8 agent logs.")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def run_seed():
    print("Creating tables...")
    create_all_tables()
    print("Seeding databases...")
    seed_patients()
    seed_appointments()
    seed_prescriptions()
    seed_analytics()
    print("\nAll done. Test credentials: email=ahmed.m@example.com password=Password123!")
    print("Patient IDs for direct API testing:")
    for i, pid in enumerate(PATIENT_IDS):
        print(f"  Patient {i}: {pid}")


if __name__ == "__main__":
    run_seed()
