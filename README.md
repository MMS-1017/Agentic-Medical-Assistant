<![CDATA[<div align="center">

# 🏥 Agentic Medical Assistant

**An AI-powered, multi-agent healthcare system** that handles patient triage, appointment scheduling, emergency response, diagnosis, loyalty rewards, medication reminders, and feedback collection — all through a conversational interface.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2-FF6B6B?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC143C?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Agent Flows](#-agent-flows)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Test Data & Accounts](#-test-data--accounts)
- [Running Tests](#-running-tests)
- [Monitoring](#-monitoring)
- [Deployment](#-deployment)
- [Frontend](#-frontend)

---

## 🌟 Overview

The Agentic Medical Assistant is a production-ready backend system that assists patients through a conversational AI interface. Patients can interact via **text, voice, or medical images**. The system intelligently routes each request to a specialized agent:

| Situation | What happens |
|---|---|
| Patient describes symptoms | **Diagnosis Agent** analyzes via multimodal LLM + Medical RAG |
| Diagnosis is urgent | **Emergency Agent** dispatches ambulance, alerts hospital staff |
| Diagnosis is unclear | **HITL** — case queued for doctor review |
| Diagnosis is non-urgent | **Scheduling Agent** books the right department |
| Post-appointment (24h later) | **Feedback Agent** contacts patient automatically |
| Prescription received | **Medication Reminder Service** sends Telegram reminders 30 min before each dose |

---

## 🏗️ Architecture

```
                        ┌─────────────────────────────┐
                        │          Patient             │
                        └──────┬──────┬──────┬────────┘
                               │      │      │
                           Text    Voice   Image
                               │      │      │
                               └──────┼──────┘
                                      │
                           ┌──────────▼──────────┐
                           │   Orchestrator Agent │  ◄── Gemini Flash 2.5
                           │  • Authenticate      │
                           │  • Load history      │
                           │  • Classify intent   │
                           └──────────┬───────────┘
                                      │
              ┌───────────┬───────────┼───────────┬───────────┐
              │           │           │           │           │
              ▼           ▼           ▼           ▼           ▼
         Scheduling   Diagnosis   Emergency   Feedback    HITL Queue
           Agent       Agent       Agent       Agent
         (Llama 3.2) (Llama 3.3 (Llama 3.2) (Llama 3.2
                      + Vision)              1B)
              │           │           │           │           │
              ▼           ▼           ▼           ▼           ▼
        Appointment   Vector DB   Ambulance   Analytics   Doctor
           Booking    + RAG       Dispatch    Database    Review
              │
              ▼
         Loyalty Points
         + Telegram Notification
```

### Infrastructure Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PostgreSQL  │  │   Qdrant     │  │  Langfuse    │  │
│  │  (4 logical  │  │  Vector DB   │  │  Monitoring  │  │
│  │  databases)  │  │  Port 6333   │  │  Port 3000   │  │
│  │  Port 5432   │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Agent Flows

### Full Request Lifecycle

```
Patient Message
      │
      ▼
Multimodal Processing
  ├── Voice → Whisper Large V3 → Transcript
  ├── Image → Llama 3.2 Vision → Medical Findings
  └── Text → Pass through
      │
      ▼
Orchestrator Agent (Gemini Flash 2.5)
  ├── Load patient profile + medical history
  ├── Classify intent: scheduling / diagnosis / emergency / feedback
      │
      ├── scheduling ──────────────────────────────────────────────┐
      │                                                            │
      ├── diagnosis                                                │
      │      │                                                     │
      │      ▼                                                     │
      │   Diagnosis Agent (Llama 3.3)                              │
      │   + RAG (Qdrant + MiniLM)                                  │
      │   + Patient History                                        │
      │      │                                                     │
      │      ├── confidence < 0.70 → HITL Queue ──► Doctor        │
      │      ├── urgency ≥ 0.85   → Emergency Agent               │
      │      └── normal           ──────────────────────────────► ┤
      │                                                            │
      ├── emergency                                                │
      │      │                                                     │
      │      ▼                                                     │
      │   Emergency Agent (Llama 3.2)                             │
      │   ├── High-risk patient  → Immediate dispatch              │
      │   └── First-time patient → Timer-based dispatch            │
      │         Heart Attack: 30s                                  │
      │         Stroke: 60s                                        │
      │         Severe Trauma: Immediate                           │
      │                                                            │
      └── feedback                                                 │
             │                                                     │
             ▼                                                     │
           Feedback Agent (Llama 3.2 1B)                           │
          Collect score + store in Analytics DB                   │
                                                                  │
                              Scheduling Agent (Llama 3.2) ◄──────┘
                              ├── Find available slots
                              ├── Check loyalty offers
                              ├── Book appointment
                              ├── Add loyalty points
                              └── Schedule feedback job (+24h)
```

### Background Services (Non-Agentic)

```
Prescription Created
        │
        ▼
APScheduler Job
        │
        ▼
30 min before each dose
        │
        ▼
Telegram Notification → Patient

Appointment Completed
        │
        ▼
+24 hours (APScheduler)
        │
        ▼
Feedback Agent triggered → Telegram → Patient
```

---

## ✨ Features

### 🧠 Multi-Agent Orchestration
- LangGraph state machine with conditional routing
- Intent classification via Gemini Flash 2.5
- Each sub-agent uses a purpose-optimized model

### 🎤 Multimodal Input
- **Text** — direct chat
- **Voice** — Whisper Large V3 transcription
- **Medical Images** — Qwen2.5-VL visual analysis

### 🔬 AI Diagnosis
- Medical RAG (Qdrant + sentence-transformers)
- 7 comprehensive medical knowledge documents
- Structured output: department + confidence + urgency score
- Automatic HITL escalation when confidence < 70%

### 🚨 Emergency Response
- High-risk patient detection from medical history
- Timer-based ambulance dispatch (30s → Heart Attack, 60s → Stroke)
- Immediate dispatch for known high-risk patients
- Real-time Telegram alerts to patient

### 📅 Smart Scheduling
- Department-aware slot search
- Loyalty points awarded on every booking
- Automatic offer presentation when eligible
- Fallback recommendations when no slots available

### 💊 Medication Reminders
- Auto-scheduled 30 min before each dose
- Telegram-delivered reminders
- Stops automatically when treatment ends

### 🏆 Loyalty System
| Points | Reward |
|--------|--------|
| 100 | 5% Discount |
| 300 | 10% Discount |
| 500 | Free Consultation |

### 👨‍⚕️ Human-in-the-Loop (HITL)
- Low-confidence diagnoses queued for doctor review
- Doctor portal via admin API endpoints
- Full case summary with patient history and symptoms

### 📊 Monitoring
- Langfuse tracing on all agent invocations
- Agent logs stored in Analytics DB
- Performance metrics per agent

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API Framework** | FastAPI 0.115 | REST API, OpenAPI docs |
| **Agent Framework** | LangGraph 0.2 | Multi-agent state graph |
| **LLM Calls** | LangChain + OpenAI SDK | Unified LLM interface |
| **Primary LLM Provider** | Groq API | Llama 3.2, Llama 3.3, Llama 3.2 Vision |
| **Fallback LLM Provider** | OpenRouter | Gemini Flash 2.5, model fallback |
| **Orchestrator Model** | Gemini Flash 2.5 | Intent classification |
| **Diagnosis Model** | Llama 3.3 (70B) | Clinical reasoning |
| **Vision Model** | Llama 3.2 Vision (11B) | Medical image analysis |
| **Scheduling Model** | Llama 3.2 3B | Appointment booking |
| **Emergency Model** | Llama 3.2 3B | Emergency triage |
| **Feedback Model** | Llama 3.2 1B | Feedback collection |
| **Speech-to-Text** | Whisper Large V3 | Voice transcription |
| **Text-to-Speech** | Kokoro TTS | (future) |
| **Vector Database** | Qdrant | Medical knowledge RAG |
| **Embeddings** | all-MiniLM-L6-v2 | Document embeddings |
| **Relational DB** | PostgreSQL 16 | Patients, appointments, etc. |
| **ORM** | SQLAlchemy 2.0 | Database models |
| **Auth** | JWT (python-jose) + bcrypt | Secure authentication |
| **Task Scheduling** | APScheduler 3.10 | Reminders, feedback jobs |
| **Notifications** | Telegram Bot API | Patient messaging |
| **Monitoring** | Langfuse | Agent tracing & analytics |
| **Containerization** | Docker Compose | Infrastructure orchestration |

---

## 📁 Project Structure

```
medical-agentic-system/
│
├── 📄 requirements.txt              # Python dependencies
├── 📄 pytest.ini                    # Test configuration
├── 📄 .env.example                  # Environment variables template
│
├── 🐳 infrastructure/
│   ├── docker-compose.yml           # Postgres, Qdrant, Langfuse
│   └── init-db.sql                  # Creates the 4 logical databases
│
├── 📚 docs/medical/                 # Medical knowledge for RAG
│   ├── cardiology.txt
│   ├── ophthalmology.txt
│   ├── orthopedics.txt
│   ├── neurology.txt
│   ├── general_medicine.txt
│   ├── emergency_medicine.txt
│   └── dermatology_and_other.txt
│
├── 🐍 scripts/
│   └── setup.py                     # One-shot setup (seed + ingest)
│
└── 🧠 backend/
    ├── app.py                       # FastAPI entrypoint
    ├── config.py                    # Pydantic settings (.env loader)
    │
    ├── llm/
    │   ├── provider.py              # Groq → OpenRouter fallback wrapper
    │   ├── registry.py              # Model ID constants
    │   └── langfuse_handler.py      # Observability callback
    │
    ├── agents/
    │   ├── state.py                 # Shared AgentState TypedDict
    │   ├── graph.py                 # LangGraph assembly
    │   ├── orchestrator/node.py     # Intent classification + routing
    │   ├── scheduling/node.py       # Appointment booking (ReAct)
    │   ├── diagnosis/node.py        # Clinical diagnosis + RAG
    │   ├── emergency/node.py        # Emergency dispatch (ReAct)
    │   ├── feedback/node.py         # Feedback collection
    │   └── hitl/node.py             # Low-confidence case escalation
    │
    ├── rag/
    │   ├── vectorstore/client.py    # Qdrant client factory
    │   ├── ingestion/pipeline.py    # Doc loader → chunk → embed → upsert
    │   └── retrieval/retriever.py   # Semantic search for diagnosis
    │
    ├── database/
    │   ├── base.py                  # Multi-DB engine + session factories
    │   ├── seed.py                  # Comprehensive fake data seed
    │   ├── patient_db/models.py     # Patient, History, Diagnosis, Loyalty, HITL
    │   ├── appointment_db/models.py # Doctor, Clinic, Slot, Appointment
    │   ├── prescription_db/models.py# Prescription, Medication, Schedule
    │   └── feedback_analytics_db/   # Feedback, AgentLog
    │
    ├── api/
    │   ├── auth.py                  # POST /register, POST /token
    │   ├── chat.py                  # POST /chat/text|voice|image
    │   ├── patients.py              # GET/PUT /patients/me/**
    │   ├── prescriptions.py         # POST/GET /prescriptions
    │   └── admin.py                 # HITL case management
    │
    ├── tools/
    │   ├── scheduling.py            # find_slots, book_slot, recommend_alternative
    │   ├── loyalty.py               # check_offers, add_points, redeem_points
    │   ├── emergency.py             # assess_risk, ambulance_count, get_timer
    │   └── rag.py                   # search_medical_knowledge
    │
    ├── services/
    │   ├── auth.py                  # JWT, bcrypt, register/login
    │   ├── session.py               # In-memory conversation history
    │   ├── notification.py          # Telegram Bot API
    │   ├── hitl.py                  # HITL case creation/resolution
    │   └── multimodal.py            # Whisper + Qwen-VL fusion
    │
    ├── workflows/
    │   ├── medication_reminders.py  # APScheduler cron for drug reminders
    │   └── feedback_scheduler.py    # APScheduler job 24h post-appointment
    │
    └── tests/
        ├── test_smoke.py            # 27 unit tests (no DB/LLM needed)
        ├── test_api.py              # API tests with mocked services
        └── test_agents.py           # Agent node logic tests
```

---

## ✅ Prerequisites

Make sure you have the following installed:

| Requirement | Version | Install |
|-------------|---------|---------|
| **Python** | 3.11+ | [python.org](https://python.org) |
| **Docker Desktop** | Latest | [docker.com](https://docker.com) |
| **Git** | Latest | [git-scm.com](https://git-scm.com) |

You will also need API keys for:

| Service | Purpose | Get Key |
|---------|---------|---------|
| **Groq** | Primary LLM provider | [console.groq.com](https://console.groq.com) |
| **OpenRouter** | Fallback + Gemini Flash 2.5 | [openrouter.ai](https://openrouter.ai) |
| **Telegram Bot** | Patient notifications | [@BotFather](https://t.me/BotFather) on Telegram |
| **Langfuse** *(optional)* | Agent monitoring | [langfuse.com](https://langfuse.com) or self-hosted |

---

## 🚀 Quick Start

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-org/medical-agentic-system.git
cd medical-agentic-system
```

### Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

```env
# Required
GROQ_API_KEY=your_groq_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional (enables Telegram notifications)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Optional (enables Langfuse monitoring)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

> The database URLs and Qdrant URL are pre-filled for local Docker — no changes needed for local development.

### Step 3 — Start infrastructure services

```bash
cd infrastructure
docker compose up -d
cd ..
```

Wait ~10 seconds for PostgreSQL to initialize, then verify:

```bash
docker compose -f infrastructure/docker-compose.yml ps
```

You should see all services as `healthy` or `running`.

### Step 4 — Install Python dependencies

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5 — Run one-shot setup (seed DB + ingest RAG)

```bash
python scripts/setup.py
```

This will:
- ✅ Create all database tables across all 4 logical databases
- ✅ Seed 5 patients, 5 doctors, 5 clinics, 210 appointment slots
- ✅ Add prescriptions, feedback records, loyalty transactions, and HITL cases
- ✅ Ingest 7 medical knowledge documents into the Qdrant vector database

Expected output:
```
============================================================
Agentic Medical Assistant — Project Setup
============================================================

[1/2] Seeding databases...
  Patient DB seeded: 5 patients, histories, diagnoses, loyalty, offers, HITL cases, users.
  Appointment DB seeded: 5 doctors, 5 clinics, 210 slots, 8 appointments.
  Prescription DB seeded: 4 prescriptions, 8 medications, 10 schedules.
  Analytics DB seeded: 3 feedback records, 8 agent logs.

[2/2] Ingesting medical knowledge into Qdrant RAG...
Ingested N chunks from cardiology.txt
...

Setup complete!
```

### Step 6 — Start the API server

```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### Step 7 — Explore the API

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Interactive Swagger UI |
| `http://localhost:8000/redoc` | ReDoc documentation |
| `http://localhost:8000/health` | Health check |
| `http://localhost:3000` | Langfuse monitoring dashboard |

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ | — | Groq API key |
| `GROQ_BASE_URL` | — | `https://api.groq.com/openai/v1` | Groq endpoint |
| `OPENROUTER_API_KEY` | ✅ | — | OpenRouter API key (for Gemini Flash 2.5) |
| `OPENROUTER_BASE_URL` | — | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `PATIENT_DB_URL` | — | `postgresql+psycopg2://admin:secretpass@localhost:5432/patient_db` | Patient DB connection |
| `APPOINTMENT_DB_URL` | — | `postgresql+psycopg2://admin:secretpass@localhost:5432/appointment_db` | Appointment DB |
| `PRESCRIPTION_DB_URL` | — | `postgresql+psycopg2://admin:secretpass@localhost:5432/prescription_db` | Prescription DB |
| `ANALYTICS_DB_URL` | — | `postgresql+psycopg2://admin:secretpass@localhost:5432/analytics_db` | Analytics DB |
| `QDRANT_URL` | — | `http://localhost:6333` | Qdrant vector DB |
| `QDRANT_COLLECTION` | — | `medical_knowledge` | Collection name |
| `SECRET_KEY` | ✅ | `change-me` | JWT signing secret (change in production!) |
| `ALGORITHM` | — | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | — | `7` | Refresh token lifetime |
| `TELEGRAM_BOT_TOKEN` | — | — | Telegram Bot API token |
| `LANGFUSE_PUBLIC_KEY` | — | — | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | — | — | Langfuse secret key |
| `LANGFUSE_HOST` | — | `http://localhost:3000` | Langfuse instance URL |
| `LOG_LEVEL` | — | `INFO` | Logging level |

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register a new patient account |
| `POST` | `/api/auth/token` | Login — returns JWT access + refresh tokens |

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Pass123!","first_name":"Your","last_name":"Name"}'

# Login
curl -X POST http://localhost:8000/api/auth/token \
  -F "username=ahmed.m@example.com" \
  -F "password=Password123!"
```

### Chat

All chat endpoints require `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/text` | Send a text message to the medical AI |
| `POST` | `/api/chat/voice` | Upload an audio file (WAV/MP3) |
| `POST` | `/api/chat/image` | Upload a medical image (+ optional text complaint) |

```bash
# Text chat
curl -X POST http://localhost:8000/api/chat/text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "I have been having chest pain that radiates to my left arm"}'

# Voice
curl -X POST http://localhost:8000/api/chat/voice \
  -H "Authorization: Bearer $TOKEN" \
  -F "audio=@recording.wav"

# Image
curl -X POST http://localhost:8000/api/chat/image \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@xray.jpg" \
  -F "complaint=I have knee pain after a fall"
```

**Text chat response:**
```json
{
  "response": "Based on your symptoms of chest pain radiating to the left arm, I'm routing you to Cardiology...",
  "intent": "diagnosis",
  "department": "Cardiology",
  "confidence_score": 0.92,
  "urgency_score": 0.88,
  "hitl_required": false,
  "emergency_dispatched": false
}
```

### Patient Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/patients/me` | Get full patient profile |
| `PUT` | `/api/patients/me/history` | Update medical history |
| `PATCH` | `/api/patients/me/telegram` | Set Telegram chat ID for notifications |
| `GET` | `/api/patients/me/diagnoses` | Last 10 diagnoses |
| `GET` | `/api/patients/me/appointments` | Appointment history |
| `GET` | `/api/patients/me/loyalty` | Points balance + transaction history |

### Prescriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/prescriptions/` | Create prescription (triggers reminder scheduler) |
| `GET` | `/api/prescriptions/me` | View my prescriptions + medication times |

### Admin (HITL)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/hitl/cases` | List all pending doctor-review cases |
| `POST` | `/api/admin/hitl/cases/{case_id}/resolve` | Resolve a case with doctor notes |

---

## 🗄️ Database Architecture

The system uses **4 logical PostgreSQL databases** to cleanly separate concerns. Cross-database references use plain UUIDs (no foreign keys across databases — enforced in the service layer).

```
patient_db                appointment_db
├── patients              ├── doctors
├── medical_history       ├── clinics
├── diagnoses             ├── availability_slots
├── loyalty_transactions  └── appointments
├── offers
├── hitl_cases
├── users
└── sessions

prescription_db           analytics_db
├── prescriptions         ├── feedback
├── prescription_meds     └── agent_logs
└── medication_schedule
```

---

## 🧪 Test Data & Accounts

After running `python scripts/setup.py`, the following test accounts are available.

**All accounts use password: `Password123!`**

| Email | Patient | Scenario |
|-------|---------|----------|
| `ahmed.m@example.com` | Ahmed Mohamed | Normal patient, 150 loyalty points, short antibiotic course |
| `fatima.ali@example.com` | Fatima Ali | **HIGH-RISK** — heart disease + diabetes, 350 pts, ambulance count = 4 |
| `omar.k@example.com` | Omar Khaled | Hypertension, 50 points, resolved HITL case |
| `nour.h@example.com` | Nour Hassan | Healthy, pending HITL case (low-confidence neurology) |
| `yasmine.i@example.com` | Yasmine Ibrahim | Asthma, **500 points** — eligible for Free Consultation |

### Test Scenarios

```bash
# Scenario 1: Normal diagnosis → scheduling
# Login as ahmed.m@example.com, then:
{"query": "My eye is red and has sticky discharge since yesterday"}
# Expected: Ophthalmology, high confidence, routes to scheduling

# Scenario 2: Emergency (high-risk patient)
# Login as fatima.ali@example.com, then:
{"query": "I have crushing chest pain and my arm is numb"}
# Expected: Emergency agent dispatched, immediate alert triggered

# Scenario 3: HITL escalation
# Login as nour.h@example.com, then:
{"query": "I get strange visual auras and then headaches"}
# Expected: Low confidence → HITL queue, "a doctor will contact you"

# Scenario 4: Appointment booking
{"query": "I want to book a cardiology appointment"}
# Expected: Scheduling agent presents slots + loyalty offer

# Scenario 5: Loyalty redemption
# Login as yasmine.i@example.com (500 pts = Free Consultation):
{"query": "Book me a general medicine appointment and use my loyalty points"}
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run only smoke / unit tests (no infrastructure needed)
pytest backend/tests/test_smoke.py -v

# Run API tests (mocked — no DB/LLM needed)
pytest backend/tests/test_api.py -v

# Run agent logic tests (mocked LLM/DB)
pytest backend/tests/test_agents.py -v

# Run with coverage
pip install pytest-cov
pytest --cov=backend --cov-report=term-missing
```

**Test suite covers:**
- ✅ Orchestrator intent routing (all 5 intents)
- ✅ Diagnosis routing (HITL / Emergency / Scheduling thresholds)
- ✅ Multimodal input fusion
- ✅ JWT auth — create, decode, reject invalid
- ✅ Session history management (max 20 messages)
- ✅ Agent node behavior with mocked LLM responses
- ✅ Feedback score extraction and storage
- ✅ HITL case creation
- ✅ All API endpoints with mocked dependencies
- ✅ Graph compilation

---

## 📊 Monitoring

Langfuse captures every agent invocation automatically.

```
http://localhost:3000   ←  Langfuse dashboard (after docker-compose up)
```

What you can track:
- **Traces** — end-to-end request through all agents
- **Latency** — per-agent response times
- **Model usage** — tokens and costs per model
- **Success rates** — agent errors and retries
- **Agent logs** — also stored in `analytics_db.agent_logs`

To use Langfuse cloud instead of self-hosted, update your `.env`:
```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 🔄 Re-ingesting Medical Knowledge

To add new medical documents to the RAG knowledge base:

```bash
# Add your .txt files to docs/medical/
# Then re-run ingestion:
python -m backend.rag.ingestion.pipeline --docs-dir ./docs/medical
```

---

## 🏗️ Extending the System

### Adding a new agent
1. Create `backend/agents/my_agent/node.py` with a `my_agent_node(state) -> dict` function
2. Add a `@tool` function in `backend/tools/` if it needs DB access
3. Wire it into `backend/agents/graph.py` with `workflow.add_node()` and edges

### Adding a new model
Update `backend/llm/registry.py` with the model ID, and add it to `_GROQ_MODELS` or `_OPENROUTER_ALIAS` in `backend/llm/provider.py`.

### Adding a notification channel
Implement a new sender in `backend/services/notification.py` alongside `send_message()`.

---

## 📦 Dependencies Overview

```
fastapi          — REST API framework
uvicorn          — ASGI server
langgraph        — Multi-agent state machine
langchain-core   — Tool definitions and LLM interfaces
langchain-openai — ChatOpenAI for Groq/OpenRouter
sqlalchemy       — ORM for all 4 databases
psycopg2-binary  — PostgreSQL driver
pydantic-settings— Environment variable management
qdrant-client    — Vector database client
sentence-transformers — MiniLM embeddings for RAG
apscheduler      — Background job scheduling
python-jose      — JWT encoding/decoding
passlib[bcrypt]  — Password hashing
langfuse         — LLM observability
openai           — OpenAI-compatible SDK (used with Groq/OpenRouter)
httpx            — Async HTTP client (multimodal uploads)
requests         — Telegram Bot API calls
python-multipart — File upload handling
```

---

## 🚀 Deployment

### Docker — single machine

```bash
# 1. Clone & configure
git clone <repo-url> && cd Agentic_Medical_Assistant
cp .env.example .env
# → fill in all secrets in .env

# 2. Full production stack (backend + nginx + frontend SPA + all infra)
docker compose up -d --build

# 3. Seed data & ingest RAG knowledge (run once)
make setup
# or manually:
docker compose exec backend python -m backend.database.seed
docker compose exec backend python -m backend.rag.ingestion.pipeline ./docs/medical
```

The stack exposes:
| URL | Service |
|---|---|
| `http://<host>/` | Vue 3 frontend SPA |
| `http://<host>/api/` | FastAPI backend |
| `http://<host>/monitor/` | Langfuse observability |

### GitHub Actions CI/CD

The pipeline in [.github/workflows/ci.yml](.github/workflows/ci.yml) runs automatically on every push to `main`:

```
push to main
  ├─ test-backend   → pytest (Python 3.11)
  ├─ test-frontend  → npm run build (Node 20)
  ├─ build-and-push → Docker image → ghcr.io/<org>/mediassist-ai:<sha>
  └─ deploy         → SSH into server → docker compose pull + up -d
```

**Required GitHub Secrets:**

| Secret | Description |
|---|---|
| `DEPLOY_HOST` | Production server IP or hostname |
| `DEPLOY_USER` | SSH username (e.g. `ubuntu`) |
| `DEPLOY_KEY` | SSH private key (PEM) |
| `DEPLOY_PATH` | Absolute path on server (e.g. `/opt/mediassist`) |
| `GHCR_TOKEN` | GitHub token with `write:packages` scope |

### Server-side deploy script

For manual deploys or when CI is not available:

```bash
# On the production server
export APP_DIR=/opt/mediassist
export REPO_URL=https://github.com/<org>/mediassist
./deployment/deploy.sh

# Skip seed (subsequent deploys)
./deployment/deploy.sh --skip-seed
```

### SSL / HTTPS

The nginx config includes a commented SSL server block. To enable:

1. Obtain a cert (e.g. `certbot --nginx -d yourdomain.com`)
2. Uncomment the `server { listen 443 ssl; … }` block in `nginx/nginx.conf`
3. Replace the placeholder paths with your cert locations
4. `docker compose restart nginx`

---

## 🖥️ Frontend

The Vue 3 frontend lives in [`frontend/`](frontend/) and is built into the nginx image automatically.

### Run locally (dev hot-reload)

```bash
# Requires backend running at localhost:8000
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Pages

| Route | Description |
|---|---|
| `/login` | Login / Register |
| `/` | AI Chat (text · voice · image) |
| `/appointments` | Appointment history (upcoming / past tabs) |
| `/prescriptions` | Active prescriptions with dose schedules |
| `/profile` | Medical history editor · loyalty offers · Telegram setup |

### Tech

- **Vue 3** Composition API + `<script setup>`
- **Pinia** — auth store (JWT in localStorage, patient profile)
- **Vue Router 4** — auth guard, lazy-loaded views
- **Tailwind CSS 3** — custom `medical` / `emergency` / `urgent` / `safe` color palette
- **Axios** — JWT interceptor, 120s timeout for AI responses
- **MediaRecorder API** — voice capture → multipart upload

---

## 📜 License

This project is developed as an academic/graduation project. All medical information in the knowledge base is for demonstration purposes only and **should not be used as a substitute for professional medical advice**.

---

<div align="center">

Built with ❤️ using **LangGraph**, **FastAPI**, and **Groq**

</div>
]]>