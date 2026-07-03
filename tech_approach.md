# Technical Approach – Agentic Medical System

**Framework:** LangGraph + FastAPI

---

## 1. Orchestrator Agent

**Function:**
Acts as the central coordinator and the only agent that communicates directly with patients. Responsible for authentication, session management, query understanding, and routing requests to the appropriate agent.

**Input:**
- Patient Profile
- Medical History
- Patient Query (Text / Voice / Image)

**Output:**
- Routes request to Scheduling Agent, Diagnosis Agent, Emergency Agent, or Feedback Agent
- Returns final response to patient

**Tools:**
- Patient Database
- Session Management Service

**Model:**
- Gemini Flash 2.5

**Implementation Snippet (LangGraph Routing):**
```python
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict, Literal

class AgentState(TypedDict):
    patient_id: str
    query: str
    intent: str
    response: str

def orchestrator_router(state: AgentState) -> Literal["scheduling", "diagnosis", "emergency", "feedback", END]:
    intent = state.get("intent", "").lower()
    if "appointment" in intent:
        return "scheduling"
    elif "pain" in intent or "sick" in intent:
        return "diagnosis"
    elif "emergency" in intent or "chest pain" in intent:
        return "emergency"
    elif "feedback" in intent:
        return "feedback"
    return END

# Workflow setup
workflow = StateGraph(AgentState)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("scheduling", scheduling_node)
# ... add other nodes
workflow.add_conditional_edges("orchestrator", orchestrator_router)
```

---

## 2. Scheduling Agent

**Function:**
Handles appointment booking and clinic availability checks. Manages loyalty points and applies eligible offers during payment.

**Input:**
- Orchestrator Output
- Appointment Request
- Department Recommendation

**Output:**
- Available Appointment Slots
- Booking Confirmation
- Loyalty Information

**Tools:**
- Appointment Database (Read / Write)
- `add_points()`
- `check_available_offers()`

**Model:**
- Llama 3.2

**Implementation Snippet (SQLAlchemy Tool Definition):**
```python
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from database.patient_db.models import Patient, Offer

@tool
def check_available_offers(patient_id: str, db: Session) -> str:
    """Checks the Patient Database for loyalty points and returns applicable offers."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return "Patient not found."
    
    # Query offers that the patient can afford with their current points
    offers = db.query(Offer).filter(Offer.required_points <= patient.loyalty_points).all()
    offer_names = [offer.offer_name for offer in offers]
    
    return f"Patient has {patient.loyalty_points} points. Eligible for: {', '.join(offer_names)}"
```

---

## 3. Diagnosis Agent

**Function:**
Analyzes patient symptoms and medical data to determine the most appropriate department and urgency level.

**Input:**
- Patient Complaint (Text / Voice / Image)
- Medical History

**Output:**
- Department Classification
- Confidence Score
- Urgency Score
- Recommendation to Scheduling Agent or Emergency Agent

**Tools:**
- Medical RAG System (Retrieval Layer)
- Vector Database (Qdrant)

**Model:**
- Llama 3.2 Vision (for image understanding)

---

## 4. Emergency Agent

**Function:**
Handles urgent and life-threatening situations. Determines ambulance requirements and generates emergency alerts.

**Input:**
- Diagnosis Agent Output
- Patient Risk Profile

**Output:**
- Emergency Alert
- Ambulance Recommendation
- Hospital Notification

**Tools:**
- Emergency Rules Engine
- Patient Database

**Model:**
- Llama 3.2

---

## 5. Feedback Agent

**Function:**
Collects patient feedback after appointments and stores insights for analytics and future model improvements.

**Input:**
- Completed Appointment Information

**Output:**
- Satisfaction Score
- Complaint Records
- Patient Health Status Updates

**Tools:**
- Feedback & Analytics Database

**Model:**
- Llama 3.2 1B

---

## Supporting Services

### Medical RAG Service

**Function:**
Provides medical knowledge retrieval for the Diagnosis Agent. Source medical documents act as the knowledge base and are ingested into the vector database.

**Components:**
- Document Ingestion Pipeline
- Embedding Model
- Qdrant Vector Database
- Retrieval Layer

**Implementation Snippet (Qdrant Retrieval):**
```python
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceEmbeddings

def retrieve_medical_context(query: str) -> list:
    """Retrieves relevant medical documents from Qdrant."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    query_vector = embeddings.embed_query(query)
    
    client = QdrantClient(url="http://localhost:6333")
    search_results = client.search(
        collection_name="medical_knowledge",
        query_vector=query_vector,
        limit=3
    )
    return [hit.payload['text'] for hit in search_results]
```

---

### Notification Service

**Function:**
Sends notifications to patients.

**Used For:**
- Appointment Reminders
- Medication Reminders
- Feedback Requests
- Emergency Alerts

**Channel:**
- Telegram Bot API

---

### Medication Reminder Service

**Function:**
Automatically schedules medication reminders after prescriptions are stored.

**Input:**
- Prescription Data

**Output:**
- Reminder Notifications

**Tools:**
- Prescription Database
- Cron Jobs
- Telegram Bot API

**Implementation Snippet (APScheduler):**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests

def send_telegram_reminder(chat_id: str, message: str):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": chat_id, "text": message})

def schedule_medication_reminders(medication_time: str, medication_name: str, chat_id: str):
    """Schedules a reminder 30 minutes before the medication time."""
    hour, minute = map(int, medication_time.split(":"))
    
    # Calculate reminder time (30 mins prior)
    reminder_minute = (minute - 30) % 60
    reminder_hour = hour - 1 if minute < 30 else hour
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_telegram_reminder,
        CronTrigger(hour=reminder_hour, minute=reminder_minute),
        args=[chat_id, f"Reminder: You should take {medication_name} at {medication_time}."],
        id=f"med_{medication_name}_{chat_id}"
    )
    scheduler.start()
```

---

## Databases

### Patient Database
Stores core patient information, medical history, diagnostic outputs, and loyalty program data.
**Tables:** `patients`, `medical_history`, `diagnoses`, `loyalty_transactions`, `offers`

### Appointment Database
Stores doctor profiles, clinic information, availability slots, and scheduled appointments.
**Tables:** `doctors`, `clinics`, `availability_slots`, `appointments`

### Prescription Database
Stores prescription records linked to appointments and patient medication schedules.
**Tables:** `prescriptions`, `prescription_medications`, `medication_schedule`

### Feedback & Analytics Database
Stores patient feedback, agent execution logs, and service KPIs for monitoring and improvement.
**Tables:** `feedback`, `agent_logs`

---

## Monitoring

**Tool:**
- Langfuse

**Purpose:**
- Agent Tracing
- Workflow Monitoring
- Performance Evaluation

---

## Technology Stack

**Frontend:**
- Vue.js
- Tailwind CSS

**Backend:**
- FastAPI
- Python

**Agent Framework:**
- LangGraph

**Models:**
- Llama 3.3
- Llama 3.2 Vision

**Speech-to-Text:**
- Whisper Large V3

**Text-to-Speech:**
- Kokoro TTS

**Vector Database:**
- Qdrant

**Relational Database & ORM:**
- PostgreSQL
- SQLAlchemy

**Monitoring:**
- Langfuse

**Notifications:**
- Telegram Bot API

---

# Database Schema Design

*(Schema grouped by the logical databases defined above. All schemas execute in PostgreSQL. Mappings are written using SQLAlchemy ORM to ensure strict consistency across the project).*

## Patient Database

### ORM Models
```python
import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), unique=True)
    phone = Column(String(20))
    loyalty_points = Column(Integer, default=0)
    risk_level = Column(String(50))
    
    medical_history = relationship("MedicalHistory", back_populates="patient")
    diagnoses = relationship("Diagnosis", back_populates="patient")

class MedicalHistory(Base):
    __tablename__ = "medical_history"
    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    chronic_conditions = Column(ARRAY(String))
    allergies = Column(ARRAY(String))
    medications = Column(ARRAY(String))
    
    patient = relationship("Patient", back_populates="medical_history")

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    diagnosis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    department = Column(String(100))
    confidence_score = Column(Float)
    urgency_score = Column(Float)
    
    patient = relationship("Patient", back_populates="diagnoses")

class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    points = Column(Integer)

class Offer(Base):
    __tablename__ = "offers"
    offer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_name = Column(String(255))
    required_points = Column(Integer)
```

### Raw SQL Equivalent
```sql
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    loyalty_points INTEGER DEFAULT 0,
    risk_level VARCHAR(50)
);

CREATE TABLE medical_history (
    history_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(patient_id),
    chronic_conditions TEXT[],
    allergies TEXT[],
    medications TEXT[]
);

CREATE TABLE diagnoses (
    diagnosis_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(patient_id),
    department VARCHAR(100),
    confidence_score FLOAT,
    urgency_score FLOAT
);

CREATE TABLE loyalty_transactions (
    transaction_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(patient_id),
    points INTEGER
);

CREATE TABLE offers (
    offer_id UUID PRIMARY KEY,
    offer_name VARCHAR(255),
    required_points INTEGER
);
```

## Appointment Database

### ORM Models
```python
class Doctor(Base):
    __tablename__ = "doctors"
    doctor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255))
    specialty = Column(String(100))
    
    slots = relationship("AvailabilitySlot", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")

class Clinic(Base):
    __tablename__ = "clinics"
    clinic_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_name = Column(String(255))
    department = Column(String(100))
    
    slots = relationship("AvailabilitySlot", back_populates="clinic")
    appointments = relationship("Appointment", back_populates="clinic")

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    slot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id"))
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.clinic_id"))
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    is_booked = Column(Boolean, default=False)
    
    doctor = relationship("Doctor", back_populates="slots")
    clinic = relationship("Clinic", back_populates="slots")

class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True)) # Cross-database reference
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.doctor_id"))
    clinic_id = Column(UUID(as_uuid=True), ForeignKey("clinics.clinic_id"))
    appointment_date = Column(TIMESTAMP)
    
    doctor = relationship("Doctor", back_populates="appointments")
    clinic = relationship("Clinic", back_populates="appointments")
```

## Prescription Database

### ORM Models
```python
from sqlalchemy import Time

class Prescription(Base):
    __tablename__ = "prescriptions"
    prescription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True)) # Cross-database reference
    doctor_id = Column(UUID(as_uuid=True))  # Cross-database reference
    appointment_id = Column(UUID(as_uuid=True)) # Cross-database reference
    
    medications = relationship("PrescriptionMedication", back_populates="prescription")

class PrescriptionMedication(Base):
    __tablename__ = "prescription_medications"
    medication_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.prescription_id"))
    medication_name = Column(String(255))
    
    prescription = relationship("Prescription", back_populates="medications")
    schedules = relationship("MedicationSchedule", back_populates="medication")

class MedicationSchedule(Base):
    __tablename__ = "medication_schedule"
    schedule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("prescription_medications.medication_id"))
    medication_time = Column(Time)
    
    medication = relationship("PrescriptionMedication", back_populates="schedules")
```

## Feedback & Analytics Database

### ORM Models
```python
from sqlalchemy import Text

class Feedback(Base):
    __tablename__ = "feedback"
    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True)) # Cross-database reference
    patient_id = Column(UUID(as_uuid=True))     # Cross-database reference
    satisfaction_score = Column(Integer)

class AgentLog(Base):
    __tablename__ = "agent_logs"
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100))
    patient_id = Column(UUID(as_uuid=True)) # Cross-database reference
    action_taken = Column(Text)
```

---

# Project Configuration (`.env` example)

To ensure all services connect properly, use the following environment variable structure:

```env
# LLM Providers
GROQ_API_KEY=your_groq_key
OPENROUTER_API_KEY=your_openrouter_key

# SQLAlchemy PostgreSQL Connection Strings
PATIENT_DB_URL=postgresql+psycopg2://admin:secretpass@localhost:5432/patient_db
APPOINTMENT_DB_URL=postgresql+psycopg2://admin:secretpass@localhost:5432/appointment_db
PRESCRIPTION_DB_URL=postgresql+psycopg2://admin:secretpass@localhost:5432/prescription_db
ANALYTICS_DB_URL=postgresql+psycopg2://admin:secretpass@localhost:5432/analytics_db

# Qdrant Vector DB
QDRANT_URL=http://localhost:6333

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Langfuse Monitoring
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

---

# Additional Sections Required for Full Plan Compliance

## Authentication Service

### Purpose
Responsible for:
- Login
- Registration
- JWT Authentication
- Session Management
- Token Refresh

### FastAPI Security Example

```python
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")
```

### Authentication Database Schema

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    password_hash TEXT,
    role VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID,
    refresh_token TEXT,
    expires_at TIMESTAMP
);
```

---

## Human-in-the-Loop (HITL) Service

### Trigger Conditions

- Confidence Score < 0.70
- Conflicting Symptoms
- Unknown Disease Pattern
- Missing Critical Information

### Workflow

```text
Diagnosis Agent
      │
      ▼
Generate Case Summary
      │
      ▼
Doctor Review Queue
      │
      ▼
Emergency Doctor Review
      │
      ▼
Patient Contact
```

### HITL Queue Schema

```sql
CREATE TABLE hitl_cases (
    case_id UUID PRIMARY KEY,
    patient_id UUID,
    confidence_score FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP
);
```

---

## Emergency Escalation Engine

### Existing High-Risk Patient

Checks:

- Chronic Heart Disease
- Frequent Ambulance Usage
- High Risk Flag

Immediate Actions:

- Hospital Notification
- Emergency Alert
- Ambulance Recommendation

### First-Time Patient

Timer-based escalation:

| Condition | Timer |
|-----------|--------|
| Heart Attack | 30 sec |
| Stroke | 60 sec |
| Severe Trauma | Immediate |

### Emergency Workflow

```text
Diagnosis Agent
      │
      ▼
Emergency Agent
      │
      ├── High Risk → Immediate Alert
      │
      └── New Patient
              │
              ▼
        Emergency Timer
              │
              ▼
         Alert Triggered
```

---

## Phone Call Agent

### Components

- SIP/Twilio Gateway
- Whisper Large V3
- Orchestrator Agent
- Kokoro TTS

### Call Flow

```text
Phone Call
    │
    ▼
Speech To Text
    │
    ▼
Orchestrator
    │
    ▼
Selected Agent
    │
    ▼
Text To Speech
    │
    ▼
Caller
```

---

## Appointment Fallback Workflow

When no appointment is available:

1. Suggest nearest clinic
2. Suggest another hospital
3. Suggest emergency department

```python
def recommend_alternative_clinic(department: str):
    return search_partner_hospitals(department)
```

---

## Loyalty Redemption Workflow

### Booking Flow

```text
Book Appointment
      │
      ▼
Check Loyalty Points
      │
      ▼
Available Offer?
      │
      ▼
Apply Discount
      │
      ▼
Update Balance
```

### Tool Example

```python
@tool
def redeem_points(patient_id: str, offer_id: str):
    ...
```

---

## Feedback Scheduling Service

### Trigger

24 hours after appointment completion.

### Scheduler Example

```python
scheduler.add_job(
    send_feedback_request,
    trigger="date",
    run_date=appointment_completed_at + timedelta(hours=24)
)
```

---

## Multimodal Processing Pipeline

### Voice

```text
Audio
  │
Whisper
  │
Text
```

### Images

```text
Image
  │
Qwen2.5-VL
  │
Findings
```

### Fusion Layer

```text
Text + Voice + Image
          │
          ▼
   Diagnosis Agent
```

---

## Complete LangGraph Flow

```text
START
  │
Authentication
  │
Orchestrator
  │
  ├── Scheduling
  ├── Diagnosis
  │      ├── Scheduling
  │      ├── Emergency
  │      └── HITL
  └── Feedback
  │
 END
```

---

## Model Assignment (Final)

| Component | Model |
|-----------|--------|
| Orchestrator | Gemini Flash 2.5 |
| Diagnosis Reasoning | Llama 3.3 |
| Diagnosis Vision | Llama 3.2 Vision |
| Scheduling | Llama 3.2 |
| Emergency | Llama 3.2 |
| Feedback | Llama 3.2 1B |
| STT | Whisper Large V3 |
| TTS | Kokoro TTS |