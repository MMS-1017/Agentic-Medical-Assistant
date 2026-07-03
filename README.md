# CarePulse

CarePulse is an AI-powered multi-agent healthcare assistant for triage,
scheduling, emergency response, prescriptions, and patient follow-up.

## Table of Contents

- Overview
- Quick Start
- Development
- Project Structure
- Contributing
- License

## Overview

CarePulse coordinates specialized agents to handle patient interactions
via text, voice, or medical images. It provides:

- Symptom triage and diagnostic assistance
- Emergency detection and dispatch support
- Appointment scheduling and loyalty rewards
- Medication reminders and feedback collection

## Quick Start

### Step 1 — Clone & configure

```bash
git clone <repo-url> && cd Agentic-Medical-Assistant
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env` and fill in at minimum:
- `GROQ_API_KEY` — your [Groq API key](https://console.groq.com)
- `OPENROUTER_API_KEY` — your [OpenRouter key](https://openrouter.ai)
- `SECRET_KEY` — any long random string

### Step 2 — Start infrastructure services

```bash
# Dev only — starts postgres, qdrant, langfuse
docker compose -f infrastructure/docker-compose.yml up -d
```

Wait ~10 seconds, then verify all services are running:

```bash
docker compose -f infrastructure/docker-compose.yml ps
```

### Step 3 — Install Python dependencies

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### Step 4 — Seed databases & ingest medical knowledge

```bash
python scripts/setup.py
```

### Step 5 — Start the API server

```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### Step 6 — (Optional) Run the frontend

```bash
cd frontend && npm install && npm run dev
# → http://localhost:5173
```

### Step 7 — Explore the API

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Interactive Swagger UI |
| `http://localhost:8000/redoc` | ReDoc documentation |
| `http://localhost:8000/health` | Health check |
| `http://localhost:3000` | Langfuse monitoring dashboard |

## Development

- Run tests:

```bash
pytest -q
```

- Lint & format (if available in your environment):

```bash
ruff .
black .
```

## Project Structure

```
Agentic-Medical-Assistant/
├── backend/                  # FastAPI app, agents, services, and database models
│   ├── agents/               # LangGraph agent nodes (orchestrator, diagnosis, etc.)
│   ├── api/                  # FastAPI routers (auth, chat, patients, prescriptions, admin)
│   ├── database/             # SQLAlchemy models for all 4 logical databases
│   ├── llm/                  # LLM provider abstraction (Groq + OpenRouter)
│   ├── rag/                  # RAG pipeline (ingestion, retrieval, Qdrant client)
│   ├── services/             # Auth, HITL, multimodal, notification, session services
│   ├── tools/                # LangChain tools for DB access (scheduling, emergency, etc.)
│   ├── workflows/            # Background schedulers (medication reminders, feedback)
│   ├── tests/                # pytest test suite
│   ├── app.py                # FastAPI application entry point
│   └── config.py             # Pydantic settings (reads from .env)
├── frontend/                 # Vue 3 SPA (Chat UI & views)
├── docs/medical/             # Medical documents used for RAG ingestion
├── infrastructure/           # Dev-only Docker Compose (postgres + qdrant + langfuse)
├── nginx/                    # Nginx config + Dockerfile (serves frontend, proxies API)
├── scripts/                  # One-shot setup script (seeds DB + ingests RAG)
├── deployment/               # Production deploy shell script
├── docker-compose.yml        # Full production stack (all services)
├── Dockerfile                # Backend Docker image
├── Makefile                  # Developer shortcuts
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variable template
```

## Contributing

If you'd like to contribute, please open an issue or pull request. Follow
the Python project conventions and include tests for new features.

## License

This project is provided under the MIT License. See LICENSE for details.
 
---

## Agents Architecture

```text
                           ┌──────────────────────┐
                           │      Patient         │
                           └──────────┬───────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
             ▼                        ▼                        ▼
      Text Chat                Voice Input              Medical Image

                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │        Orchestrator Agent       │
                    │                                 │
                    │ - Authentication                │
                    │ - Session Management            │
                    │ - Routing Decisions             │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
         Scheduling Request             Medical Complaint
                    │                             │
                    ▼                             ▼
         ┌──────────────────┐       ┌────────────────────────┐
         │ Scheduling Agent │       │    Diagnosis Agent     │
         └────────┬─────────┘       └───────────┬────────────┘
                  │                             │
                  ▼                             ▼
        Appointment Database          Medical Knowledge Base
                                     (Vector Database + RAG)

                  │                             │
                  ▼                             ▼
      Available? Yes / No            Diagnosis Success?
                  │                             │
          ┌───────┴────────┐          ┌─────────┴─────────┐
          │                │          │                   │
          ▼                ▼          ▼                   ▼
     Available         Not Available Success          Failed
          │                │          │                   │
          ▼                ▼          ▼                   ▼
  Booking Confirmation  Suggest  Classify Case      Human Doctor
                         Another      │             (HITL)
                        Hospital       │
                                      ▼
                           ┌──────────────────┐
                           │ Urgent ?         │
                           └──────┬───────────┘
                                  │
                      ┌───────────┴───────────┐
                      │                       │
                      ▼                       ▼
               Non-Urgent                 Urgent
                      │                       │
                      ▼                       ▼
              Scheduling Agent      Emergency Agent
                                              │
                         ┌────────────────────┴──────────────────┐
                         │                                       │
                         ▼                                       ▼
            Frequent Ambulance User?                    First-Time User
                         │                                       │
                  ┌──────┴──────┐                         Set Timer
                  │             │                         Based On
                  ▼             ▼                         Diagnosis
            Yes (Direct)       No                              │
                  │             │                              ▼
                  ▼             └────────────────────► Ambulance Dispatch
          Ambulance Dispatch
```
---

### Overview

CarePulse uses a lightweight orchestrator that receives a patient request and
routes it to purpose-built agent nodes. Each agent is an independently
deployable node with a well-defined interface and responsibility (diagnosis,
emergency, scheduling, feedback, HITL, etc.). Agents may call LLM providers
and the RAG retriever and report telemetry to Langfuse.

### Components

- Orchestrator: intent classification, authentication, session lookup,
  routing, and aggregation of agent responses.
- Diagnosis Agent: multimodal clinical reasoning with RAG support; outputs
  department, confidence and urgency scores.
- Emergency Agent: evaluates urgency thresholds, triggers dispatcher and
  notifications when required.
- Scheduling Agent: finds and books slots, applies loyalty rules, and
  schedules follow-up jobs (feedback / reminders).
- Feedback Agent: collects post-appointment feedback and writes analytics.
- HITL Agent: queues low-confidence cases for clinician review and supports
  doctor resolution APIs.
- Background Workers: APScheduler / task queue for reminders and delayed jobs.

### Agent Interface (JSON contract)

Request (from Orchestrator):

```json
{
  "request_id": "uuid",
  "patient_id": "uuid",
  "context": {"history": [], "last_message": "..."},
  "input": {"text": "...", "image_url": null, "audio_url": null}
}
```

Response (from Agent):

```json
{
  "request_id": "uuid",
  "agent": "diagnosis",
  "intent": "diagnosis",
  "department": "Cardiology",
  "confidence": 0.91,
  "urgency": 0.87,
  "hitl": false,
  "actions": [
    {"type": "schedule", "payload": {"department": "Cardiology"}}
  ],
  "explainability": "structured findings and supporting docs"
}
```

Agents MUST include `request_id` and `patient_id` and return numeric
confidence/urgency scores in [0,1]. The `actions` array lets the orchestrator
execute follow-up steps (e.g., booking, dispatching).

### State & Persistence

- Agents are stateless by design; all persistent data lives in the
  appropriate PostgreSQL logical database or Qdrant for vector data.
- Conversation session state is stored in `patient_db.sessions` and is
  referenced by `session_id` in agent requests when needed.
- HITL cases write structured payloads to `patient_db.hitl_cases` for review.

### Async Flows & Tasking

- Emergency dispatch is synchronous: the Emergency Agent returns a `dispatch`
  action which the orchestrator converts into an immediate notification and
  an analytics log entry.
- Scheduling and reminders use APScheduler jobs that call the Scheduling
  Agent or Notification service at scheduled times.

### Observability & Monitoring

- Langfuse traces every agent call with inputs, outputs, latency and model
  choices. Store try/response metadata in `analytics_db.agent_logs` for
  auditing and replay.
- Export Prometheus metrics (latency, error rate, queue depth) from each
  agent container for dashboarding.


### Scaling & Reliability

- Run each agent as a small containerized service with horizontal scaling
  behind a Kubernetes Deployment or Docker Compose replicas for local dev.
- Use retries + exponential backoff for transient LLM or Qdrant failures.
- Circuit-breaker patterns protect the orchestrator from slow downstream
  agents; fail closed with a helpful user-facing message.

### Deployment Notes

- Agents are packaged under `backend/agents/*` and expose an internal Python
  API invoked by the orchestrator; treat them as modules when running a single
  process for dev, or as separate services in production.
- Keep secrets per-service (LLM keys, DB URLs) scoped via environment
  variables and use a secrets manager in production.

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
| `WHISPER_API_URL` | — | `https://api.groq.com/openai/v1/audio/transcriptions` | Groq Whisper STT endpoint |
| `APP_ENV` | — | `development` | Application environment |
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
| `SERVER_HOST` | Production server IP or hostname |
| `SERVER_USER` | SSH username (e.g. `ubuntu`) |
| `SERVER_SSH_KEY` | SSH private key (PEM) |

> **Note:** The workflow uses the automatically provided `GITHUB_TOKEN` to push
> Docker images to GitHub Container Registry — no additional registry secret is needed.

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