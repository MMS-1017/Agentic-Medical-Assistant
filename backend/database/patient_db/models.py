import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base, relationship

PatientBase = declarative_base()


class Patient(PatientBase):
    __tablename__ = "patients"

    patient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), unique=True)
    phone = Column(String(20))
    telegram_chat_id = Column(String(50))
    loyalty_points = Column(Integer, default=0)
    risk_level = Column(String(50), default="normal")
    ambulance_request_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    medical_history = relationship("MedicalHistory", back_populates="patient", uselist=False)
    diagnoses = relationship("Diagnosis", back_populates="patient")
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="patient")


class MedicalHistory(PatientBase):
    __tablename__ = "medical_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    chronic_conditions = Column(ARRAY(String), default=[])
    allergies = Column(ARRAY(String), default=[])
    current_medications = Column(ARRAY(String), default=[])

    patient = relationship("Patient", back_populates="medical_history")


class Diagnosis(PatientBase):
    __tablename__ = "diagnoses"

    diagnosis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    department = Column(String(100))
    confidence_score = Column(Float)
    urgency_score = Column(Float)
    raw_complaint = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="diagnoses")


class LoyaltyTransaction(PatientBase):
    __tablename__ = "loyalty_transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    points = Column(Integer)
    reason = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="loyalty_transactions")


class Offer(PatientBase):
    __tablename__ = "offers"

    offer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_name = Column(String(255))
    description = Column(Text)
    required_points = Column(Integer)
    discount_percent = Column(Float, default=0)
    is_active = Column(Boolean, default=True)


class HitlCase(PatientBase):
    __tablename__ = "hitl_cases"

    case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True))
    confidence_score = Column(Float)
    suggested_department = Column(String(100))
    case_summary = Column(Text)
    symptoms_report = Column(Text)
    status = Column(String(50), default="pending")
    assigned_doctor_id = Column(String(255))
    doctor_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)


class User(PatientBase):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True)
    password_hash = Column(Text)
    role = Column(String(50), default="patient")
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSession(PatientBase):
    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
