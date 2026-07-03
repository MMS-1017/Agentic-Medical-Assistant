import uuid
from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.config import settings
from backend.database.base import get_patient_session
from backend.database.patient_db.models import User, UserSession, Patient

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def register_user(email: str, password: str, first_name: str, last_name: str, phone: str = "") -> dict:
    with get_patient_session() as db:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        patient = Patient(first_name=first_name, last_name=last_name, email=email, phone=phone)
        db.add(patient)
        db.flush()
        user = User(email=email, password_hash=hash_password(password), patient_id=patient.patient_id)
        db.add(user)
        db.flush()
        return {"user_id": str(user.user_id), "patient_id": str(patient.patient_id)}


def authenticate_user(email: str, password: str) -> dict:
    with get_patient_session() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        access = create_access_token({"sub": str(user.user_id), "patient_id": str(user.patient_id)})
        refresh = create_refresh_token({"sub": str(user.user_id)})
        expires = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        session = UserSession(user_id=user.user_id, refresh_token=refresh, expires_at=expires)
        db.add(session)
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def get_current_patient_id(token: str) -> str:
    payload = decode_token(token)
    patient_id = payload.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return patient_id
