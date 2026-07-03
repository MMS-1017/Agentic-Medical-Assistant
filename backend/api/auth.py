from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.services.auth import register_user, authenticate_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str = ""


@router.post("/register")
def register(body: RegisterRequest):
    return register_user(body.email, body.password, body.first_name, body.last_name, body.phone)


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    return authenticate_user(form.username, form.password)
