from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.config import settings

Base = declarative_base()

_engines = {
    "patient": create_engine(settings.patient_db_url, pool_pre_ping=True),
    "appointment": create_engine(settings.appointment_db_url, pool_pre_ping=True),
    "prescription": create_engine(settings.prescription_db_url, pool_pre_ping=True),
    "analytics": create_engine(settings.analytics_db_url, pool_pre_ping=True),
}

_session_factories = {name: sessionmaker(bind=engine) for name, engine in _engines.items()}


@contextmanager
def get_session(db_name: str) -> Session:
    factory = _session_factories[db_name]
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_patient_session():
    return get_session("patient")


def get_appointment_session():
    return get_session("appointment")


def get_prescription_session():
    return get_session("prescription")


def get_analytics_session():
    return get_session("analytics")


def create_all_tables():
    from backend.database.patient_db.models import PatientBase
    from backend.database.appointment_db.models import AppointmentBase
    from backend.database.prescription_db.models import PrescriptionBase
    from backend.database.feedback_analytics_db.models import AnalyticsBase

    PatientBase.metadata.create_all(_engines["patient"])
    AppointmentBase.metadata.create_all(_engines["appointment"])
    PrescriptionBase.metadata.create_all(_engines["prescription"])
    AnalyticsBase.metadata.create_all(_engines["analytics"])
