import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.base import create_all_tables
from backend.workflows.medication_reminders import start_reminder_scheduler, stop_reminder_scheduler
from backend.workflows.feedback_scheduler import start_feedback_scheduler, stop_feedback_scheduler

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — creating tables and starting schedulers...")
    create_all_tables()
    start_reminder_scheduler()
    start_feedback_scheduler()
    yield
    logger.info("Shutting down schedulers...")
    stop_reminder_scheduler()
    stop_feedback_scheduler()


app = FastAPI(
    title="Agentic Medical Assistant",
    version="1.0.0",
    description="AI-powered patient assistant with scheduling, diagnosis, and emergency response.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.admin import router as admin_router
from backend.api.patients import router as patients_router
from backend.api.prescriptions import router as prescriptions_router

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(patients_router)
app.include_router(prescriptions_router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "env": settings.app_env}
