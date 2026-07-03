import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

AnalyticsBase = declarative_base()


class Feedback(AnalyticsBase):
    __tablename__ = "feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True))  # cross-DB ref
    patient_id = Column(UUID(as_uuid=True))      # cross-DB ref
    satisfaction_score = Column(Integer)
    complaint = Column(Text)
    health_status = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentLog(AnalyticsBase):
    __tablename__ = "agent_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100))
    patient_id = Column(UUID(as_uuid=True))  # cross-DB ref
    action_taken = Column(Text)
    result = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
