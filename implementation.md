# Implementation Plan – Agentic Medical System

> Execution guide derived from [file_plan.md](file_plan.md) (architecture) and
> [tech_approach.md](tech_approach.md) (technical design). This document turns the
> design into an ordered, buildable set of tasks. Follow the phases top to bottom;
> each phase ends in a working, demoable slice.

---

## 0. Conventions & Ground Rules

- **Language/Runtime:** Python 3.11+ (backend), Node 18+ (frontend).
- **Agent framework:** LangGraph; API layer: FastAPI.
- **ORM:** SQLAlchemy 2.x against PostgreSQL. One engine/session factory per logical DB
  (patient, appointment, prescription, analytics). Cross-DB links are plain UUID columns
  (no FK across databases) — enforce integrity in the service layer.
- **Models (final assignment, from tech_approach):**
  | Component | Model | Provider |
  |-----------|-------|----------|
  | Orchestrator | Gemini Flash 2.5 | OpenRouter |
  | Diagnosis reasoning | Llama 3.3 | Groq |
  | Diagnosis vision | Llama 3.2 Vision | Groq |
  | Scheduling / Emergency | Llama 3.2 | Groq |
  | Feedback | Llama 3.2 1B | Groq |
  | STT | Whisper Large V3 | Groq |
  | TTS | Kokoro TTS | local |
- **Config:** all secrets via `.env` (see `tech_approach.md` `.env` block). Never hardcode.
- **Observability:** wrap every agent/graph invocation with Langfuse tracing from day one.
- **Definition of done per task:** code + unit test + manual smoke via API docs (`/docs`).

---

## 1. Repository Bootstrap (do first)

Target structure (from file_plan.md, expanded with concrete files):

```text
medical-agentic-system/
├── frontend/                      # Vue 3 + Tailwind (Phase 7 polish; stub early)
├── backend/
│   ├── app.py                     # FastAPI entrypoint
│   ├── config.py                  # pydantic-settings, loads .env
│   ├── llm/
│   │   ├── provider.py            # Groq client + OpenRouter fallback wrapper
│   │   └── registry.py            # model -> client mapping
│   ├── agents/
│   │   ├── state.py               # shared AgentState TypedDict
│   │   ├── graph.py               # top-level LangGraph assembly
│   │   ├── orchestrator/
│   │   ├── diagnosis/
│   │   ├── scheduling/
│   │   ├── emergency/
│   │   └── feedback/
│   ├── rag/
│   │   ├── ingestion/             # doc loaders + chunking + embed + upsert
│   │   ├── retrieval/             # retrieve_medical_context()
│   │   └── vectorstore/           # Qdrant client factory
│   ├── database/
│   │   ├── base.py                # declarative_base + engine/session factories
│   │   ├── patient_db/models.py
│   │   ├── appointment_db/models.py
│   │   ├── prescription_db/models.py
│   │   └── feedback_analytics_db/models.py
│   ├── api/                       # FastAPI routers (auth, chat, voice, admin)
│   ├── tools/                     # @tool definitions used by agents
│   ├── workflows/                 # cron/scheduled jobs (reminders, feedback)
│   ├── services/                  # auth, notification(telegram), session, hitl
│   └── tests/
├── infrastructure/                # docker-compose (postgres, qdrant, langfuse)
├── deployment/
└── docs/
```

**Bootstrap tasks**
1. Create the tree above; add `backend/pyproject.toml` (or `requirements.txt`) with:
   `fastapi`, `uvicorn`, `langgraph`, `langchain-core`, `langchain-community`,
   `sqlalchemy`, `psycopg2-binary`, `pydantic-settings`, `qdrant-client`,
   `sentence-transformers`, `apscheduler`, `python-jose[cryptography]`,
   `passlib[bcrypt]`, `python-multipart`, `requests`, `langfuse`,
   `openai` (for OpenRouter-compatible calls), `httpx`.
2. `infrastructure/docker-compose.yml` services: `postgres:16`, `qdrant/qdrant`,
   `langfuse` (+ its postgres). Create the 4 logical databases on init.
3. `backend/config.py` — load every var from the `.env` example in tech_approach.
4. `backend/llm/provider.py` — single `chat(model, messages, **kw)` that tries Groq,
   falls back to OpenRouter on error/timeout. All agents call through this.
5. Verify: `uvicorn backend.app:app --reload` serves a `/health` route; docker stack up.

---

## 2. Phase 1 — Authentication, Orchestrator, Patient DB

**Goal:** A patient can authenticate and send a text query that the orchestrator
classifies and routes (routing can stub the downstream agents for now).

1. **Patient DB models** — implement `patients`, `medical_history`, `diagnoses`,
   `loyalty_transactions`, `offers` exactly per tech_approach ORM block. Add the
   `users` and `sessions` auth tables.
2. **Auth service** (`services/auth.py`, `api/auth.py`):
   - Register / login → bcrypt password hashing.
   - `create_access_token` / refresh using `python-jose` (HS256), `OAuth2PasswordBearer`.
   - `get_current_user` dependency for protected routes.
3. **Session management** — persist refresh tokens in `sessions`; in-memory or DB-backed
   conversation session keyed by `patient_id`.
4. **Shared `AgentState`** (`agents/state.py`): `patient_id`, `query`, `intent`,
   `modality`, `diagnosis`, `response`, plus carry-through fields used later.
5. **Orchestrator node** (`agents/orchestrator/`):
   - Loads patient profile + history (Patient DB) into state.
   - LLM intent classification (Gemini Flash 2.5) → sets `state.intent`.
   - `orchestrator_router` conditional edge (per tech_approach snippet) → scheduling /
     diagnosis / emergency / feedback / END.
6. **Top-level graph** (`agents/graph.py`): add orchestrator + stub nodes; compile.
7. **Chat API** (`api/chat.py`): `POST /chat` → runs graph, returns response.
8. **Langfuse**: attach callback handler to graph invocation.

**Demo:** login → `POST /chat {"query":"I want an appointment"}` → routes to scheduling stub.

---

## 3. Phase 2 — Scheduling Agent & Appointment DB

**Goal:** Real appointment booking with loyalty awareness.

1. **Appointment DB models**: `doctors`, `clinics`, `availability_slots`, `appointments`
   (per tech_approach). Seed script with sample doctors/clinics/slots.
2. **Tools** (`tools/scheduling.py`): `find_available_slots(department|doctor)`,
   `book_slot(slot_id, patient_id)` (sets `is_booked=True`, writes `appointments`),
   `check_available_offers(patient_id)`, `add_points(patient_id, n)`,
   `redeem_points(patient_id, offer_id)`.
3. **Scheduling agent** (Llama 3.2): present slots → confirm selection → book →
   `add_points` → surface eligible offer ("You have N points…") → on accept, apply offer.
4. **Fallback workflow** (`recommend_alternative_clinic`): when no slot, suggest nearest
   clinic → another hospital → emergency department.
5. **Feedback hook**: on successful booking, schedule a feedback job for +24h (wired in
   Phase 6; leave a TODO + queue entry now).

**Demo:** book an appointment end-to-end; points increment; offer presented.

---

## 4. Phase 3 — Medical RAG, Diagnosis Agent, HITL

**Goal:** Multimodal complaint → department + confidence + urgency, with low-confidence
escalation to a human review queue.

1. **Vector store** (`rag/vectorstore/`): Qdrant client; create `medical_knowledge`
   collection (embedding dim = MiniLM 384).
2. **Ingestion** (`rag/ingestion/`): load medical docs → chunk → embed
   (`all-MiniLM-L6-v2`) → upsert with `{text, source}` payload. Provide a CLI runner.
3. **Retrieval** (`rag/retrieval/`): `retrieve_medical_context(query, k=3)` per snippet.
4. **Multimodal pipeline** (`services/multimodal.py`):
   - Voice → Whisper Large V3 → text.
   - Image → Qwen2.5-VL → findings text.
   - Fusion: concat text + transcript + image findings → diagnosis input.
5. **Diagnosis agent** (Qwen 3 reasoning + Qwen2.5-VL vision):
   - Input: fused complaint + medical history + RAG context.
   - Output (structured): `department`, `confidence_score`, `urgency_score`.
   - Persist to `diagnoses`.
6. **Routing after diagnosis** (conditional edges):
   - `confidence < 0.70` (or conflicting/unknown/missing info) → **HITL**.
   - `urgency` high → **Emergency**.
   - else → **Scheduling** (with `department` prefilled).
7. **HITL service** (`services/hitl.py` + `hitl_cases` table): generate case summary
   (patient + history + symptoms + suggested dept), enqueue, expose admin endpoint for
   doctor review/resolution.

**Demo:** text/image complaint → "Ophthalmology, conf 0.88" → routes to scheduling;
a low-confidence case lands in the HITL queue.

---

## 5. Phase 4 — Emergency Agent

**Goal:** Urgent cases trigger correct escalation path.

1. **Emergency rules engine** (`agents/emergency/rules.py`):
   - High-risk check: chronic heart disease / frequent ambulance use / high-risk flag
     (from Patient DB + medical_history) → **immediate** alert + ambulance + hospital notify.
   - First-time patient → timer by condition (Heart Attack 30s, Stroke 60s, Severe Trauma
     immediate). On timeout → generate alert + notify staff.
2. **Emergency agent** (Llama 3.2): determines severity, ambulance requirement, alert
   priority; calls notification service.
3. **Timers**: APScheduler one-shot jobs; cancellable if patient/doctor intervenes.
4. **Notifications** via Telegram (built in Phase 6 stub now, or build Telegram service
   here since Emergency needs it — recommended to build `services/notification.py` now).

**Demo:** "crushing chest pain" → emergency path; high-risk patient → immediate alert.

---

## 6. Phase 5 — Loyalty System

**Goal:** Points accrual + redemption fully wired.

1. Seed `offers` (100→5%, 300→10%, 500→Free Consultation).
2. Finalize `add_points` (on booking/completion), `check_available_offers`,
   `redeem_points` (validates points, writes `loyalty_transactions`, applies discount).
3. Orchestrator surfaces offer copy; scheduling applies to payment on accept.

**Demo:** repeated bookings cross a threshold; redeem on next booking.

---

## 7. Phase 6 — Feedback Agent, Notifications, Medication Reminders

**Goal:** Background services (non-agentic where noted) close the loop.

1. **Notification service** (`services/notification.py`): Telegram Bot API
   `sendMessage`; retry on failure; log to `agent_logs`/notification history. Shared by
   appointments, reminders, feedback, emergency.
2. **Medication reminders** (`workflows/medication_reminders.py`):
   - Prescription DB models: `prescriptions`, `prescription_medications`,
     `medication_schedule` (per tech_approach).
   - APScheduler job: send Telegram reminder 30 min before each `medication_time`; stop at
     treatment end. (Background service — *not* an agent.)
3. **Feedback agent** (Qwen 0.5) + `feedback`/`agent_logs` tables:
   - Scheduled +24h after appointment completion (APScheduler `date` trigger).
   - Collect satisfaction score, complaints, health status → store in analytics DB.

**Demo:** booking → 24h later feedback request fires; prescription → timed reminder.

---

## 8. Phase 7 — Monitoring, Frontend, Voice/Phone, Deployment

1. **Monitoring/Analytics**: Langfuse dashboards for agent traces, latency, success
   rates; KPI queries over `feedback`/`agent_logs`.
2. **Frontend** (Vue 3 + Tailwind): auth, chat (text), audio record upload, image upload,
   appointment view. Talks to FastAPI.
3. **Phone Call Agent** (optional/stretch): SIP/Twilio gateway → Whisper → orchestrator →
   Kokoro TTS → caller.
4. **Deployment**: Dockerize backend; compose with postgres/qdrant/langfuse; env-driven
   config; healthchecks; basic CI.

---

## 9. Cross-Cutting Checklist

- [ ] Every agent invocation traced in Langfuse.
- [ ] LLM calls go through `llm/provider.py` (Groq → OpenRouter fallback).
- [ ] Structured outputs (diagnosis dept/confidence/urgency) validated before routing.
- [ ] Cross-DB UUID references validated in service layer (no DB-level FKs across DBs).
- [ ] Secrets only from `.env`; nothing committed.
- [ ] Each new tool has a unit test; each phase has one end-to-end smoke test.
- [ ] HITL and Emergency paths have explicit audit logging.

---

## 10. Build Order Summary

| Phase | Deliverable | Key components |
|-------|-------------|----------------|
| 0–1 | Repo + bootstrap | docker, config, llm provider |
| 1 | Auth + routing | Patient DB, auth, orchestrator, graph |
| 2 | Booking | Appointment DB, scheduling agent, fallback |
| 3 | Diagnosis | RAG/Qdrant, multimodal, diagnosis agent, HITL |
| 4 | Emergency | rules engine, timers, notifications |
| 5 | Loyalty | offers, points, redemption |
| 6 | Background loop | Telegram, reminders, feedback agent |
| 7 | Productionize | Langfuse, frontend, voice, deploy |

Start at **Section 1 (Repository Bootstrap)**, then proceed phase by phase.
