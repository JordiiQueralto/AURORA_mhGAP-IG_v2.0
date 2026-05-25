# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mental health support chatbot based on the **WHO mhGAP v2.0 intervention guide**. It acts as a virtual helpline that triages users into clinical protocols (suicide risk, depression) or free-talk mode, with a separate medical specialist dashboard.

## Running the project

**Prerequisites:** Python 3.10+, MongoDB 6.0+ on `localhost:27017`, Google Gemini API key.

```bash
pip install flask flask-cors pymongo google-genai fpdf python-dotenv
```

**Start the two Flask servers (separate terminals):**
```bash
# User API — port 5000
python src/app.py

# Specialist API — port 5001
python src/app_sp.py
```

Open `app/USER/chat_13.html` (user chat) and `app/MEDIC/doctor_dashboard_14.html` (medical panel) directly in a browser.

**Seed medical centers (first time only):**
```bash
python src/seed_medical_centers.py
```

**Generate a PDF report for a user (edit the user ID inside the script first):**
```bash
python src/create_inform.py
```

## Environment

Create `.env` in the project root:
```
GOOGLE_API_KEY=your_gemini_api_key
JWT_SECRET=your_jwt_secret
```

## Architecture

```
app.py (port 5000)          app_sp.py (port 5001)
     │                              │
     ▼                              ▼
main_api.py                 main_api_sp.py
     │
     ├─ state_machine.py     — regex-driven clinical state machine
     ├─ generate_output.py   — LLM call orchestration
     │      └─ prompt_builder.py  — prompt construction
     │      └─ llm.py             — Gemini 2.5 Flash client
     ├─ phrase_dictionary.py — fixed clinical question strings
     └─ db.py                — MongoDB CRUD (CHATBOT_mhGAP)
```

### Conversation flow

Every user message is handled by `main_api.process_message()`. Session context (current phase, state, counters, last bot output) is persisted per-request in the `ctx` subdocument of the user MongoDB document, not in memory.

State transitions use `state_machine.StateMachine(telephone, phase, state, user_input)` which applies regex pattern banks to classify user responses, then returns `(new_phase, new_state, variant)`.

Phases and their progression:
- `PRESENTATION` → `PRESENTATION_ASKED` → `PROFILE` (name/age/reason/expectation/commitment)
- `USE_CASE_EVAL` — LLM classifies to `EMERGENCY` / `ASSISTANCE` / `TALK` / `MISENSE`
- `EMERGENCY` → `SUI_EVAL` → `SUI_PROTOCOLS` (state 1 = call 112, state 2 = call 024)
- `ASSISTANCE` → `DEP_EVAL` (states 1A.1–1C, 2A.1–2A.2, 2B.1–2B.3, 3A–3C)
- `TALK` → `CHAT` (free LLM conversation, re-evaluated every 5 messages)
- `FAREWELL` — session closes, summary/valoration/risk_level generated and saved

### LLM usage pattern

The LLM (`llm.send_prompt`) is used in two modes:
1. **Classification** (temperature=0.0): use-case detection, session valoration, risk level
2. **Natural language wrapping** (temperature=1.0): the bot wraps fixed clinical questions (`phrase_dictionary`) with empathetic connectors, or generates free responses in CHAT/TALK mode

### MongoDB schema key points

Database: `CHATBOT_mhGAP`, collections: `users`, `specialists`, `medicalCenters`, `notifications`.

User document keys:
- `ctx` — live session context: `phase`, `state`, `bot_output`, `session_path`, `j` (turn counter), `K` (chat turn counter), `variant`
- `checkpoint` — where to resume a paused evaluation (`phase`, `state`)
- `DEP_EVAL` / `SUI_EVAL` / `SCREENING` — structured evaluation results from state machine
- `<timestamp>_session` — one key per session, containing `summary`, `valoration`, `risk_level`, `conversation_history`
- `CIRCLE` — support circle: contacts, medical center, privacy settings
- `EMERGENCY` — array of emergency instances
- `FOLLOWUP` — post-emergency follow-up history

Specialists authenticate with JWT (`JWT_SECRET`). Patient data is only visible to specialists from the same `centerName`+`centerCity`.

### Key design decisions

- All source files live under `src/`. The HTML frontends are under `app/USER/` and `app/MEDIC/` (versioned; use the highest-numbered file).
- Images served by `app.py` at `/images/<path>` are read from the `images/` directory one level above `src/`.
- `security_control()` in `state_machine.py` runs as an override during `DEP_EVAL` and `CHAT` phases to detect imminent risk mid-conversation and redirect to `SUI_PROTOCOLS`.
- `time.sleep()` calls in `main_api.py` are intentional pacing delays for a more natural conversation cadence — do not remove them.
