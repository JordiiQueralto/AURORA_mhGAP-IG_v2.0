# Mental Health Prevention Chatbot — mhGAP v2.0

Conversational assistant for mental health support and suicide prevention, based on the **mhGAP v2.0 Intervention Guide** of the World Health Organization (WHO). The system combines a clinical state machine with a language model (Gemini 2.5 Flash) to deliver an empathetic, structured, and clinically rigorous experience, together with a separate dashboard for medical specialists.

> **Important notice:** This system is a support and triage tool. It does not replace professional mental health care.

---

## Table of contents

- [Overview](#overview)
- [System architecture](#system-architecture)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the project](#running-the-project)
- [User API](#user-api-app_userpy---port-5000)
- [Specialist API](#specialist-api-app_specialistpy---port-5001)
- [Data model (MongoDB)](#data-model-mongodb)
- [Conversation flow](#conversation-flow)
- [Clinical state machine](#clinical-state-machine)
- [LLM usage](#llm-usage)
- [Specialist dashboard](#specialist-dashboard)
- [PDF report generation](#pdf-report-generation)
- [Security and privacy](#security-and-privacy)
- [Available countries](#available-countries)

---

## Overview

The system acts as a **virtual telephone helpline** for people in situations of psychological risk. Its main capabilities are:

- **Automatic triage**: classifies the user via the LLM into `EMERGENCY`, `ASSISTANCE`, `TALK`, or `MISENSE`.
- **Suicide protocol (SUI)**: detects suicidal ideation and self-harm, and activates emergency protocols with referral to 112 or 024.
- **Depression protocol (DEP)**: assesses depressive and manic symptoms with structured questions drawn from the mhGAP guide, including differential screening for bipolar disorder.
- **Free conversation mode (TALK)**: empathetic companionship without clinical assessment, with automatic re-evaluation of the use case every 5 messages.
- **Cross-cutting safety control**: during the `DEP_EVAL` and `CHAT` phases, a regex-based detection module analyzes every message looking for signs of imminent risk and can interrupt the flow to redirect to the emergency protocols.
- **Post-emergency follow-up (FOLLOWUP)**: in sessions following an emergency, the system checks whether the user contacted the support services and records the outcome.
- **Support circle**: lets the user register trusted contacts and a reference medical center, and sends them automatic notifications when an emergency protocol is activated.
- **Medical dashboard**: specialists can consult patients from their center, add clinical notes, review historical sessions, view statistics, and generate PDF reports.
- **Persistent memory**: each session is automatically summarized by the LLM and stored in MongoDB, allowing the chatbot to personalize greetings and maintain continuity across sessions.

---

## System architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                │
│   chat.html (user)                 doctor_dashboard.html (doctor)│
└──────────┬──────────────────────────────────┬────────────────────┘
           │ HTTP REST                        │ HTTP REST
           ▼                                  ▼
┌────────────────────────┐      ┌──────────────────────────────┐
│  app_user.py           │      │  app_specialist.py           │
│  Port 5000             │      │  Port 5001                   │
└──────────┬─────────────┘      └──────────────┬───────────────┘
           │                                   │
           ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│              services_user.py  /  services_specialist.py         │
│                       Core business logic                        │
└──────┬────────────────┬──────────────────┬───────────────────────┘
       │                │                  │
       ▼                ▼                  ▼
┌──────────────┐ ┌──────────────────┐ ┌────────────────────────────┐
│ state_machine│ │ generate_output  │ │         db.py              │
│ (clinical FSM│ │ (LLM orchestra-  │ │    (MongoDB CRUD)          │
│  + safety    │ │  tion + output)  │ └──────────┬─────────────────┘
│  control)    │ └────────┬─────────┘            │
└──────────────┘          │                      ▼
       │                  ▼              ┌───────────────────────┐
       │         ┌──────────────────┐    │       MongoDB         │
       │         │ prompt_builder   │    │    CHATBOT_mhGAP      │
       │         │ (prompt          │    │  ├─ users             │
       │         │  construction)   │    │  ├─ specialists       │
       │         └────────┬─────────┘    │  ├─ medicalCenters    │
       │                  │              │  └─ notifications     │
       │                  ▼              └───────────────────────┘
       │         ┌──────────────────┐
       │         │     llm.py       │
       │         │  Gemini 2.5 Flash│
       │         └──────────────────┘
       ▼
┌────────────────────┐
│phrase_dictionary   │
│(fixed mhGAP        │
│ clinical questions)│
└────────────────────┘
```

### Flow of a typical request (`POST /api/message`)

1. `app_user.py` receives the message and passes it to `services_user.process_message()`.
2. The full session context is retrieved from MongoDB (phase, state, counters, last bot output).
3. The user input is saved, paired with the bot's previous output, in the conversation history.
4. `state_machine.StateMachine()` evaluates the response with regex pattern banks and returns `(new_phase, new_state, variant)`.
5. `security_control()` runs as an override during `DEP_EVAL` and `CHAT` to detect imminent risk.
6. `generate_output` builds the prompt and calls the LLM to generate the natural response.
7. The new state is persisted back to MongoDB and the JSON response is returned to the frontend.

---

## Repository structure

```
chatbot/
├── src/
│   ├── app_user.py              # Flask API — user endpoints (port 5000)
│   ├── app_specialist.py        # Flask API — specialist endpoints (port 5001)
│   ├── services_user.py         # Orchestrator: start-up, message processing, sessions
│   ├── services_specialist.py   # Orchestrator: auth, patients, reports, statistics
│   ├── state_machine.py         # Clinical FSM (SUI, DEP, FOLLOWUP, PROFILE protocols)
│   ├── generate_output.py       # Response generation (LLM + output logic)
│   ├── prompt_builder.py        # Prompt construction for the LLM
│   ├── llm.py                   # Gemini client (Google GenAI SDK)
│   ├── db.py                    # MongoDB data access layer
│   ├── phrase_dictionary.py     # Dictionary of structured clinical phrases (mhGAP)
│   ├── reportPDF.py             # PDF report generation (fpdf)
│   └── seed_medical_centers.py  # Initial medical-center seeding script
│
├── app/
│   ├── USER/
│   │   └── chat.html            # User interface (chat)
│   └── SPECIALIST/
│       └── doctor_dashboard.html # Specialist control panel
│
├── images/
│   ├── logo.png
│   ├── Basic/                   # General informational images
│   ├── SUI/
│   │   ├── Emergency/           # Material for family members during an emergency
│   │   └── Psicoeducation/      # Psychoeducational guides (user and family, ES/CAT)
│   └── DEP/
│       └── Psicoeducation/      # Psychoeducational material on depression
│
├── diagrams/                    # Mermaid diagrams of architecture and flow
├── .env                         # Environment variables (do not commit to the repository)
├── CLAUDE.md                    # Instructions for Claude Code
└── README.md                    # This file
```

---

## Prerequisites

- **Python** 3.10+
- **MongoDB** 6.0+ running on `localhost:27017`
- An account on [Google AI Studio](https://aistudio.google.com/) with access to the Gemini API

### Python dependencies

```bash
pip install flask flask-cors pymongo google-genai fpdf python-dotenv
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/JordiiQueralto/AURORA_mhGAP-IG_v2.0.git

# 2. Install dependencies
pip install flask flask-cors pymongo google-genai fpdf python-dotenv

# 3. Create the environment-variables file (see the Configuration section)

# 4. Load the medical centers into the database (first time only)
python src/seed_medical_centers.py
```

---

## Configuration

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key
```

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Google Gemini API key (model `gemini-2.5-flash`) | |

---

## Running the project

Start the two Flask servers in separate terminals:

```bash
# Terminal 1 — user API (port 5000)
python src/app_user.py

# Terminal 2 — specialist API (port 5001)
python src/app_specialist.py
```

Then open the frontends directly in the browser:

- **User chat**: `app/USER/chat.html`
- **Medical dashboard**: `app/SPECIALIST/doctor_dashboard.html`

---

## User API (`app_user.py` — Port 5000)

Base URL: `http://localhost:5000`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/verify` | Registers or verifies the user by phone number |
| `POST` | `/api/start` | Starts a new conversation session |
| `POST` | `/api/message` | Processes a user message and returns the bot's response |
| `POST` | `/api/reset` | Closes the active session, generates summary/valoration, and clears context |
| `GET` | `/api/circle?telephone=...` | Retrieves the user's support-circle data |
| `POST` | `/api/circle` | Saves or updates the support circle |
| `GET` | `/api/notifications?telephone=...` | Unread notifications for a family member |
| `POST` | `/api/notifications/read` | Marks notifications as read |
| `POST` | `/api/user/delete` | Permanently deletes the user document |
| `GET` | `/api/medical-centers` | Lists all countries with available medical centers |
| `GET` | `/api/medical-centers/<code>?q=...` | Centers of a country (optional filter by name or city) |
| `GET` | `/images/<path>` | Serves psychoeducational and emergency images |

### Response of `/api/message`

```json
{
  "bot_message": "...",
  "image_url": "http://localhost:5000/images/...",
  "ended": false,
  "emergency_112": false,
  "emergency_024": false
}
```

| Field | Description |
|---|---|
| `bot_message` | The bot's textual response |
| `image_url` | URL of a psychoeducational image (or `null`) |
| `ended` | `true` if the session has finished |
| `emergency_112` | `true` → trigger the 112 (emergency) call notice |
| `emergency_024` | `true` → trigger the suicidal-behavior helpline notice (024) |

---

## Specialist API (`app_specialist.py` — Port 5001)

Base URL: `http://localhost:5001`

Protected endpoints require the header `Authorization: Bearer <token>`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/doctor/register` | No | Register a new specialist |
| `POST` | `/api/doctor/login` | No | Login, returns a JWT token |
| `PUT` | `/api/doctor/profile` | Yes | Update profile data |
| `GET` | `/api/doctor/patients` | Yes | Patients from the specialist's center |
| `PUT` | `/api/doctor/patients/<id>/notes` | Yes | Save a clinical note about a patient |
| `GET` | `/api/doctor/patients/<id>/sessions` | Yes | Patient's session history |
| `GET` | `/api/doctor/patients/<id>/report` | Yes | Generate and download a PDF report |
| `GET` | `/api/doctor/stats` | Yes | Center statistics (risk, sessions, valorations, screening) |
| `GET` | `/api/doctor/stats/debug` | Yes | Dump of each center user's `SCREENING` field (data diagnostics) |
| `GET` | `/api/doctor/countries` | No | Available countries |
| `GET` | `/api/medical-centers/<code>` | No | Centers of a country |

### Specialist registration (`POST /api/doctor/register`)

```json
{
  "collegiateNumber": "28-5678",
  "firstName": "María",
  "lastName": "García López",
  "birthDate": "1985-04-12",
  "email": "maria@hospital.es",
  "password": "MiClave123",
  "countryCode": "ES",
  "centerName": "CAP Les Corts",
  "centerCity": "Barcelona"
}
```

### Center statistics (`GET /api/doctor/stats`)

Returns the data for the dashboard charts:

| Field | Description |
|---|---|
| `riskDistribution` | Distribution of risk levels (stable, low, medium, high) |
| `sessionsByDay` | Sessions per day over the last 30 days |
| `valorationDist` | Distribution of valorations (good, fair, poor) |
| `suiDist` | Distribution of suicide screening |
| `depDist` | Distribution of depression screening |
| `emergencyStats` | Total emergencies, follow-ups, and outcomes |

---

## Data model (MongoDB)

Database: `CHATBOT_mhGAP`

### Collection `users`

```json
{
  "telephone": "+34612345678",
  "name": "María",
  "age (years)": 34,
  "USER_TERMS": { "status": "accepted", "timestamp": "2024-06-01 10:00:00" },
  "PROFILE": {
    "call_reason": "...",
    "expectation": "...",
    "commitment": "Fully commited"
  },
  "CIRCLE": {
    "contacts": [{ "name": "Ana", "phone": "+34600000000", "relation": "mother" }],
    "medicalCenter": { "name": "CAP Florida", "city": "L'Hospitalet de Llobregat" },
    "privacy": { "shareWithHospital": true, "allowContactFamily": true }
  },
  "DEP_EVAL": {
    "1_A1_depressed_mood": true,
    "1_A2_anhedonia": true,
    "1B_1_sleep_alteration": false,
    "1B_2_appetite_weight_change": false,
    "1B_3_fatigue_energy_loss": true,
    "1B_4_concentration_decision_issues": true,
    "1B_5_low_selfworth_guilt": false,
    "1B_6_hopelessness_suicidal_ideation": false,
    "1C_functional_impairment": true,
    "2A_1_on_medication": false,
    "2A_2_physical_conditions": false,
    "2B_1_mania_episode": false
  },
  "SUI_EVAL": {
    "1_self_harm": false,
    "2_A_active_ideation": "none"
  },
  "SCREENING": { "DEP": "depression" },
  "EMERGENCY": [
    {
      "session_id": "2024-06-01 10:30:00_session",
      "trigger_hour": "10:45:00",
      "protocol_applied": "2",
      "referal": "024"
    }
  ],
  "FOLLOWUP": {
    "history": [
      {
        "emergency_date": "2024-06-01 10:30:00",
        "followup_date": "2024-06-03 14:00:00",
        "outcome": "contacted"
      }
    ],
    "last_check": "2024-06-03 14:00:00"
  },
  "checkpoint": { "phase": "DEP_EVAL", "state": "3A" },
  "ctx": {
    "phase": "...", "state": "...", "bot_output": "...",
    "session_path": "...", "j": 5, "K": 0, "variant": 0
  },
  "2024-06-01 10:30:00_session": {
    "summary": "The user showed symptoms of...",
    "valoration": "REGULAR",
    "risk_level": "MODERADO",
    "conversation_history": {
      "bot_output_0": "...",
      "user_input_0": "...",
      "bot_output_1": "...",
      "user_input_1": "..."
    }
  },
  "doctorNotes": {
    "28-5678": { "note": "Stable patient...", "updatedAt": "2024-06-05 09:00:00" }
  }
}
```

**Key fields:**

| Key | Description |
|---|---|
| `ctx` | Active session context: phase, state, turn counter, last output |
| `checkpoint` | Resumption point for interrupted evaluations |
| `DEP_EVAL` | Structured results of the depression assessment |
| `SUI_EVAL` | Results of the suicide-risk assessment |
| `SCREENING` | Final screening: `depression`, `bipolar`, or `others` |
| `EMERGENCY` | Array of recorded emergency instances |
| `FOLLOWUP` | Post-emergency follow-up history |
| `<timestamp>_session` | Closed session with summary, valoration, and risk level |
| `doctorNotes` | Specialist's clinical notes (indexed by collegiate number) |

### Collection `specialists`

```json
{
  "collegiateNumber": "28-5678",
  "email": "doctor@hospital.es",
  "passwordHash": "...",
  "firstName": "Joan",
  "lastName": "García",
  "birthDate": "1985-04-12",
  "centerName": "CAP Florida",
  "centerCity": "L'Hospitalet de Llobregat",
  "countryCode": "ES",
  "sessionToken": "...",
  "profile": { "especialidad": "Psiquiatría", "genero": "dr" }
}
```

### Collection `medicalCenters`

```json
{
  "countryCode": "ES",
  "countryName": "España",
  "centers": [
    { "name": "CAP Florida", "city": "L'Hospitalet de Llobregat" }
  ]
}
```

### Collection `notifications`

Push notifications for family members when an emergency protocol is activated:

```json
{
  "to_telephone": "+34600000000",
  "from_telephone": "+34612345678",
  "from_name": "María",
  "image_path_family": "images/SUI/Emergency/family_esp.png",
  "timestamp": "2024-06-01 10:45:00",
  "read": false
}
```

---

## Conversation flow

```
Start (POST /api/start)
  │
  ├─ New user → PRESENTATION (terms acceptance)
  │                      │
  │                      └─ "Yes, I accept" → PRESENTATION_ASKED → PROFILE
  │                                             │
  │                           Collects: name, age, reason, expectation, commitment
  │                                             │
  │                                      USE_CASE_EVAL ─────────────────────┐
  │                                             │                           │
  │                        ┌────────────────────┼──────────────┬────────────┤
  │                        ▼                    ▼              ▼            ▼
  │                    EMERGENCY           ASSISTANCE        TALK       MISENSE
  │                        │                    │              │         (close)
  │                   SUI_EVAL             DEP_EVAL           CHAT
  │                   (5 questions)          │                  │
  │                        │           Phase 1: Basic signs     │
  │                        │           Phase 2: Differential Dx │
  │                        │           Phase 3: Substances      │
  │                        │                │                   │
  │                   SUI_PROTOCOLS    DEP_PROTOCOLS      Re-evaluation
  │                   ├─ State 1:      (psychoeducation)    every 5 msgs
  │                   │  Call 112                               │
  │                   ├─ State 2:                               ▼
  │                   │  Call 024                          USE_CASE_EVAL
  │                   └─ State 3:                         (may reclassify)
  │                      Psychoeducation
  │                        │
  │                     FAREWELL ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
  │                  (summary + valoration + risk level)
  │
  ├─ Existing user → RESUMING → Resumes from checkpoint
  │
  └─ User with a previous EMERGENCY → FOLLOWUP
                                     (post-emergency check)
```

---

## Clinical state machine

The state machine (`state_machine.py`) manages each clinical-evaluation phase. Each state evaluates the user's response against **regex pattern banks** (affirmation, negation, ambiguity) and produces a transition.

### Depression-protocol phases (`DEP_EVAL`)

| State | Clinical question (mhGAP) | Evaluated variable |
|---|---|---|
| 1A.1 | Persistently low mood | `1_A1_depressed_mood` |
| 1A.2 | Loss of interest/pleasure (anhedonia) | `1_A2_anhedonia` |
| 1B.1 | Sleep disturbances | `1B_1_sleep_alteration` |
| 1B.2 | Appetite/weight changes | `1B_2_appetite_weight_change` |
| 1B.3 | Fatigue/loss of energy | `1B_3_fatigue_energy_loss` |
| 1B.4 | Difficulty concentrating/making decisions | `1B_4_concentration_decision_issues` |
| 1B.5 | Low self-esteem/excessive guilt | `1B_5_low_selfworth_guilt` |
| 1B.6 | Hopelessness/suicidal ideation | `1B_6_hopelessness_suicidal_ideation` |
| 1C | Functional impairment | `1C_functional_impairment` |
| 2A.1–2A.2 | Medication and physical conditions | Differential diagnosis |
| 2B.1–2B.7 | Manic/hypomanic episodes | Bipolar screening |
| 2C | Recent bereavement | Contextual factor |
| 2D.1–2D.5 | Psychotic symptoms and functioning | Severity |
| 2E.1–2E.3 | Prior psychiatric history | Background |
| 3A–3B | Alcohol and substance use | Risk factors |

**Decision logic:**
- If both A criteria (1A.1, 1A.2) are negative → exits to `CHAT` (classification: `others`).
- If at least one A is positive, the B criteria are evaluated.
- If ≥2 B criteria are positive (or ≥1 B + hopelessness) → functional impairment (1C) is evaluated.
- If 1C is positive → classification `depression`, continues to differential diagnosis.
- The 2B block (7 questions) assesses bipolar traits; if ≥3 are positive → classification `bipolar`.

### Suicide-protocol phases (`SUI_EVAL`)

| State | Clinical question | Evaluation |
|---|---|---|
| 1 | Current self-harm | `1_self_harm` |
| 2A | Plans/thoughts of self-harm | Active ideation |
| 2B.1 | Thoughts in the last month | Recent ideation |
| 2B.2 | Self-harm in the last year | History |
| 3 | Mental health treatment | Background |
| 4 | Persistent physical pain | Risk factor |
| 5 | Functional emotional impact | Severity |

### Handling of unclassifiable responses

When the user does not respond in a classifiable way, the system activates **variants**:

| Variant | Situation | Bot's response |
|---|---|---|
| `ambiguity` | "I don't know", "maybe" | Rephrases the question in other words |
| `evasion` | "Change the subject" | Acknowledges the discomfort, gently retries |
| `refusal` | "I don't want to answer" | Respects the refusal, offers alternatives |
| `hostility` | Insults toward the bot | De-escalates with empathy |
| `non_class` | Out-of-pattern response | Repeats the question more directly |

---

## LLM usage

The LLM (Gemini 2.5 Flash via `llm.py`) is used in two distinct modes:

### Classification mode (temperature = 0.0)

Deterministic responses for clinical decisions:
- **Use-case detection**: classifies the conversation into `EMERGENCY` / `ASSISTANCE` / `TALK` / `MISENSE`.
- **Session valoration**: generates `BUENA`, `REGULAR`, or `MALA`.
- **Crisis risk level**: determines `ESTABLE`, `BAJO`, `MODERADO`, or `ALTO`.

### Natural-generation mode (temperature = 1.0)

Varied, empathetic responses:
- **Wrapping of clinical questions**: the LLM receives the fixed "core" of the question (extracted from `phrase_dictionary.py`) and wraps it with natural, empathetic connectors while preserving clinical rigor.
- **Personalized welcome**: uses the user's memory (name, summary of the last session) to generate a contextualized greeting.
- **TALK mode**: free conversation where the LLM receives the last 8 interactions as context.
- **Session summary**: synthesizes the full conversation when the session is closed.

---

## Specialist dashboard

The dashboard (`doctor_dashboard.html`) offers:

- **Registration / Login** with collegiate number, email, and password.
- **Editable profile**: personal data, specialty, and gender.
- **Patient list** from the same medical center who have given consent (`shareWithHospital: true`).
- **Session history** per patient: summary, valoration (BUENA / REGULAR / MALA), and risk level (ESTABLE / BAJO / MODERADO / ALTO).
- **Clinical notes**: the doctor can add and edit private notes per patient (indexed by collegiate number).
- **Center statistics**: charts for risk distribution, sessions per day, valorations, SUI/DEP screening, and emergency statistics.
- **PDF report**: downloads a complete report based on the mhGAP guide.

---

## PDF report generation

The `reportPDF.py` module generates structured reports (via `fpdf`) that include:

- Patient identification data (name, phone, age).
- Suicide-assessment results (`SUI_EVAL`) with an interpretation of each indicator.
- Depression-assessment results (`DEP_EVAL`) and differential diagnosis.
- Session history with summaries and valorations.
- The specialist's clinical notes.
- Recorded emergencies and follow-ups.

Reports are downloaded directly from the medical dashboard (`GET /api/doctor/patients/<id>/report`) and are generated in a temporary file that is deleted after the response is sent.

---

## Security and privacy

- The conversation with AURORA only starts after the user provides informed consent, compliant with the GDPR, LOPDGDD, and the EU AI Act.
- Sharing data with the hospital requires the user's **explicit consent** (`shareWithHospital: true`).
- Notifications to family members require additional consent (`allowContactFamily: true`).
- Emergency protocols follow the guidelines of the **WHO mhGAP v2.0 Intervention Guide**.
- Patient data is only visible to specialists from the **same medical center** (`centerName`).

---

## Available countries

The system includes medical centers for:

Each country also includes an `Otro / No aparece en la lista` ("Other / Not in the list") option for users whose center is not catalogued.

| Country | Code | Centers |
|---|---|---|
| Spain | ES | 52 centers (Barcelona, L'Hospitalet, Madrid, Valencia, Seville, Bilbao...) |
| Argentina | AR | 10 centers (Buenos Aires, Rosario, Córdoba, Mendoza) |
| Costa Rica | CR | 28 centers (San José, Alajuela, Cartago, Heredia...) |
| Mexico | MX | 8 centers (Mexico City, Monterrey, Guadalajara, Puebla, Tijuana) |
| Colombia | CO | 6 centers (Bogotá, Medellín, Cali, Barranquilla) |
| Chile | CL | 5 centers (Santiago, Pudahuel, Valparaíso, Concepción) |
| Peru | PE | 5 centers (Lima, Arequipa, Cusco) |

To add new countries or centers, edit the `MEDICAL_CENTERS_DATA` list in `src/seed_medical_centers.py` and run the script again. **Note:** the script resets the `medicalCenters` collection on every run (it always performs a `drop` before inserting):

```bash
python src/seed_medical_centers.py
```

---

## Relevant design decisions

- **State in the database, not in memory**: all session context (`ctx`) is persisted per request in MongoDB, which enables horizontal scalability and resilience to server restarts.
- **Fixed questions + LLM wrapping**: the clinical questions are hardcoded verbatim in `phrase_dictionary.py` (guaranteeing fidelity to mhGAP), and the LLM only adds empathetic connectors around them.
- **REGEX for response classification**: the state machine uses extensive regex patterns (not the LLM) to classify user responses within the clinical protocols, ensuring determinism and traceability.
- **Intentional delays**: the `time.sleep()` calls in `services_user.py` simulate a natural conversation cadence — they should not be removed.
</content>
</invoke>
