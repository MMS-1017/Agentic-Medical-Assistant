"""
Recreate all tables across all 4 databases by using CASCADE to clear old schemas/constraints.
"""

import sys
import os
from sqlalchemy import text

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.base import _engines
from backend.database.patient_db.models import PatientBase
from backend.database.appointment_db.models import AppointmentBase
from backend.database.prescription_db.models import PrescriptionBase
from backend.database.feedback_analytics_db.models import AnalyticsBase

def drop_tables_cascade(engine, table_names):
    with engine.begin() as conn:
        for table in table_names:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"  Dropped table {table} (CASCADE) on {engine.url.database}")
            except Exception as e:
                print(f"  Error dropping {table} on {engine.url.database}: {e}")

def main():
    print("Dropping all existing tables across all 4 databases (with CASCADE)...")
    
    # 1. Patient DB
    patient_tables = ["sessions", "users", "hitl_cases", "loyalty_transactions", "diagnoses", "medical_history", "patients", "offers"]
    drop_tables_cascade(_engines["patient"], patient_tables)

    # 2. Appointment DB
    appointment_tables = ["appointments", "availability_slots", "doctors", "clinics"]
    drop_tables_cascade(_engines["appointment"], appointment_tables)

    # 3. Prescription DB
    prescription_tables = ["medication_schedule", "prescription_medications", "prescriptions"]
    drop_tables_cascade(_engines["prescription"], prescription_tables)

    # 4. Analytics DB
    analytics_tables = ["agent_logs", "feedback"]
    drop_tables_cascade(_engines["analytics"], analytics_tables)

    print("\nRecreating all tables...")
    PatientBase.metadata.create_all(_engines["patient"])
    AppointmentBase.metadata.create_all(_engines["appointment"])
    PrescriptionBase.metadata.create_all(_engines["prescription"])
    AnalyticsBase.metadata.create_all(_engines["analytics"])
    print("All tables recreated successfully!")

if __name__ == "__main__":
    main()
