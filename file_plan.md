# Agentic Medical System Architecture

## Project Overview

An agentic medical system that assists patients through:

1. Multi-modal interaction (Text, Audio Recorded, Images)
2. Appointment scheduling
3. Initial diagnosis and triage
4. Emergency response management
5. Loyalty and feedback management
6. Human-in-the-loop escalation for uncertain cases

---

# High-Level Architecture

```text
                           ┌──────────────────────┐
                           │      Patient         │
                           └──────────┬───────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
             ▼                        ▼                        ▼
      Text Chat                Voice Input              Phone Call
                                                     (Call Agent)

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

# Detailed Workflow

## 1. Authentication

Patient logs in through:

- Web Chat
- Voice Assistant

The orchestrator checks:

- Patient Profile
- Medical History
- Previous Diagnoses
- Previous Ambulance Requests
- Loyalty Points

---

## 2. Scheduling Flow

### Request

Patient requests:

- Doctor Appointment
- Department Appointment

### Scheduling Agent

Queries:

- Appointment Database (Doctors, Clinics, Availability)

### Available Appointment

1. Present available slots.
2. Patient selects slot.
3. Appointment stored.
4. Loyalty points added.
5. Feedback workflow scheduled.

### No Available Appointment

Recommend:

- Emergency Department
- Another Hospital
- Nearest Available Clinic

---

## 3. Diagnosis Flow

### Inputs

Patient may provide:

- Text Complaint
- Voice Complaint
- Medical Image
- Combined Inputs

### Diagnosis Agent

Uses:

- Multimodal LLM
- Medical RAG
- Vector Database

Output:

- Department Classification
- Confidence Score
- Urgency Score

Examples:

| Symptom         | Classification |
| --------------- | -------------- |
| Chest Pain      | Cardiology     |
| Eye Redness     | Ophthalmology  |
| Bone Fracture   | Orthopedics    |
| Severe Headache | Neurology      |

---

## 4. Non-Urgent Cases

Diagnosis Agent → Scheduling Agent

Flow:

Diagnosis → Department → Appointment Booking

Example:

Eye infection detected.

Diagnosis Agent:
"Ophthalmology"

↓

Scheduling Agent:
Find ophthalmologist appointment.

---

## 5. Urgent Cases

Diagnosis Agent identifies:

- Heart Attack
- Stroke
- Severe Trauma
- Internal Bleeding
- Respiratory Failure

### Emergency Agent

Determines:

- Severity
- Ambulance Requirement
- Emergency Alert Priority

### Existing High-Risk Patient

If patient history shows:

- Frequent ambulance requests
- Chronic heart disease
- High-risk status

Immediately generate emergency alert and notify hospital staff.

### New Patient

Set emergency timer according to diagnosis.

### Emergency Actions

- Generate Emergency Alert
- Notify Hospital Staff
- Recommend Ambulance Dispatch

Examples:

| Condition     | Timer     |
| ------------- | --------- |
| Heart Attack  | 30 sec    |
| Stroke        | 60 sec    |
| Severe Trauma | Immediate |

After timeout:

Emergency alert is generated and hospital staff are notified.

---

## 6. Human-in-the-Loop Flow

Triggered when:

- Low confidence diagnosis
- Conflicting symptoms
- Insufficient information
- Unknown disease pattern

### Workflow

Diagnosis Agent generates:

- Patient Summary
- Medical History Summary
- Symptoms Report
- Suggested Department

↓

Emergency Doctor reviews case.

↓

Doctor contacts patient directly.

---

## 7. Loyalty System

During appointment booking:
Our scheduling agent checks if patient has enough points to give them an offer. The orchestrator agent tells the user we have an available slot and tells them:
"You have [number] points. You can use them to get [offer]."

If the user says they want to use points, apply the offer to the payment method.

After appointment booking:

Loyalty Tool:

- Add Points
- Update Patient Profile

Example:

| Points | Benefit           |
| ------ | ----------------- |
| 100    | 5% Discount       |
| 300    | 10% Discount      |
| 500    | Free Consultation |

---

# 8. Medication Reminders

## Purpose

After a patient finishes a doctor consultation and receives a prescription, the system automatically schedules medication reminders.

The goal is to improve medication adherence by notifying patients before their medication time.

---

## Workflow

Doctor Consultation

↓

Prescription Stored in Prescription Database

↓

Reminder Scheduler

(Cron Job)

↓

Telegram Notification

↓

Patient Receives Reminder

---

## Prescription Storage

Each prescription contains:

- Medication Name
- Dosage
- Frequency
- Start Date
- End Date
- Medication Times

Example:

- Augmentin
- 1 Tablet
- Every 12 Hours
- 08:00 AM
- 08:00 PM

---

## Reminder Scheduling

A scheduled job runs periodically and checks upcoming medication times.

Rule:

- Send reminder 30 minutes before medication time.

Example:

Medication Time:

08:00 AM

Reminder Sent:

07:30 AM

Telegram Message:

"Reminder: You should take Augmentin at 08:00 AM."

---

## Notification Channel

For the MVP, reminders are sent using Telegram Bot.

Benefits:

- Free
- Official API
- Easy Integration
- No Meta approval required
- Suitable for graduation projects

---

## Required Components

### Prescription Database

Stores:

- Patient Prescriptions
- Medication Schedule
- Treatment Duration

### Reminder Scheduler

Responsibilities:

- Check upcoming medication times
- Generate reminder events
- Stop reminders when treatment ends

Implementation:

- Cron Job

### Telegram Service

Responsibilities:

- Send reminder messages
- Handle delivery failures
- Log notification history

---

## Data Flow

Doctor

↓

Prescription

↓

PostgreSQL

↓

Reminder Scheduler

↓

Telegram Bot

↓

Patient

---

## Notes

This module is not implemented as an AI Agent because it does not require reasoning or decision-making.

A scheduled background service is sufficient and simpler to maintain.

---

## Notification Service

Used by multiple modules:

- Appointment Notifications
- Medication Reminders
- Feedback Requests

Channel:

- Telegram Bot API

---

## 9. Feedback Agent

Cron Job:

Runs 24 hours after appointment.

Workflow:

1. Contact patient.
2. Collect satisfaction score.
3. Collect complaints if any.
4. Collect health status.
5. Store feedback.

Stored in:

- Feedback & Analytics Database

Used for:

- Service Improvement
- Model Fine-Tuning
- KPI Tracking

---

# Recommended Tech Stack

## Frontend

- Vue.js
- Tailwind CSS

## Backend

- FastAPI
- Python

## Agent Framework

- LangGraph

## LLM Provider

Primary:

- Groq API

Fallback:

- OpenRouter

## Models

**Orchestrator Agent**
- Gemini Flash 2.5

**Diagnosis Agent**
- Llama 3.2 Vision (for image understanding)

**Scheduling Agent**
- Llama 3.2

**Emergency Agent**
- Llama 3.2

**Feedback Agent**
- Llama 3.2 1B

## Speech-to-Text

- Whisper Large V3

## Text-to-Speech

MVP:

- Kokoro TTS

Future Enhancement:

- Arabic / Egyptian Arabic TTS Provider

## Vector Database

- Qdrant

## Relational Database

- PostgreSQL

## Task Scheduling

- Cron Jobs

## Monitoring

- Langfuse

## Notifications

- Telegram Bot API

---

# Suggested Repository Structure

```text
medical-agentic-system/
│
├── frontend/
│
├── backend/
│   ├── agents/
│   │   ├── orchestrator/
│   │   ├── diagnosis/
│   │   ├── scheduling/
│   │   ├── emergency/
│   │   └── feedback/
│   │
│   ├── rag/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   └── vectorstore/
│   │
│   ├── database/
│   │   ├── patient_db/
│   │   ├── appointment_db/
│   │   ├── prescription_db/
│   │   └── feedback_analytics_db/
│   │
│   ├── api/
│   ├── tools/
│   ├── workflows/
│   └── services/
│
├── docs/
│
├── infrastructure/
│
├── tests/
│
└── deployment/
```

---

# MVP Development Order

Phase 1:

- Authentication
- Orchestrator Agent
- Patient Database

Phase 2:

- Scheduling Agent
- Appointment Database (Doctors, Clinics, Slots)

Phase 3:

- Medical RAG
- Diagnosis Agent
- Human-in-the-Loop (HITL) integration

Phase 4:

- Emergency Agent

Phase 5:

- Loyalty System

Phase 6:

- Feedback Agent
- Feedback & Analytics Database

Phase 7:

- Monitoring
- Analytics
- Production Deployment