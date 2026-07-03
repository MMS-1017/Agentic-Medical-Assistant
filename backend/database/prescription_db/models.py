import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Date, Time, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

PrescriptionBase = declarative_base()


class Prescription(PrescriptionBase):
    __tablename__ = "prescriptions"

    prescription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True))       # cross-DB ref
    doctor_id = Column(UUID(as_uuid=True))        # cross-DB ref
    appointment_id = Column(UUID(as_uuid=True))   # cross-DB ref
    start_date = Column(Date)
    end_date = Column(Date)
    notes = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)

    medications = relationship("PrescriptionMedication", back_populates="prescription")


class PrescriptionMedication(PrescriptionBase):
    __tablename__ = "prescription_medications"

    medication_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.prescription_id"))
    medication_name = Column(String(255))
    dosage = Column(String(100))
    frequency = Column(String(100))

    prescription = relationship("Prescription", back_populates="medications")
    schedules = relationship("MedicationSchedule", back_populates="medication")


class MedicationSchedule(PrescriptionBase):
    __tablename__ = "medication_schedule"

    schedule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("prescription_medications.medication_id"))
    medication_time = Column(Time)
    reminder_sent = Column(Boolean, default=False)

    medication = relationship("PrescriptionMedication", back_populates="schedules")
