import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

AppointmentBase = declarative_base()


class Doctor(AppointmentBase):
    __tablename__ = "doctors"

    doctor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255))
    specialty = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)

    slots = relationship("AvailabilitySlot", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")


class Clinic(AppointmentBase):
    __tablename__ = "clinics"

    clinic_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_name = Column(String(255))
    department = Column(String(100))
    address = Column(String(500))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)

    slots = relationship("AvailabilitySlot", back_populates="clinic")
    appointments = relationship("Appointment", back_populates="clinic")


class AvailabilitySlot(AppointmentBase):
    __tablename__ = "availability_slots"

    slot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id"))
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.clinic_id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_booked = Column(Boolean, default=False)

    doctor = relationship("Doctor", back_populates="slots")
    clinic = relationship("Clinic", back_populates="slots")


class Appointment(AppointmentBase):
    __tablename__ = "appointments"

    appointment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True))  # cross-DB ref
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id"))
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.clinic_id"))
    appointment_date = Column(DateTime)
    department = Column(String(100))
    status = Column(String(50), default="scheduled")
    feedback_scheduled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="appointments")
    clinic = relationship("Clinic", back_populates="appointments")
