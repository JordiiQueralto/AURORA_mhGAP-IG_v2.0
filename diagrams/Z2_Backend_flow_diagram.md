# Backend Architecture — mhGAP Chatbot v2.0

This document presents the backend flow at progressive levels of detail, following the **C4 model approach** (Context → Container → Component → Code). Each diagram can be referenced independently in the thesis text, and together they provide a complete picture of how a single user message travels through the system — from the HTTP request issued by the frontend to the persisted clinical state in MongoDB.

The system implements the **mhGAP screening protocol** of the World Health Organization for depression and suicide risk, deployed as a conversational agent. The architecture deliberately separates three concerns: **deterministic clinical logic** (encoded as a finite state machine), **natural language generation** (delegated to a large language model), and **session persistence** (a document-oriented database). This separation guarantees that clinical decisions are auditable and reproducible while keeping conversations natural and empathic.

---

## Figure 0 — System overview

High-level view of the six backend layers and the main data flows between them. The diagram intentionally omits internal logic of each module; its purpose is to convey **who calls whom** and which boundaries data crosses.

The system is organized in six concentric layers. The **API layer** (`app.py`) exposes a single Flask REST endpoint that the frontend consumes over HTTPS. The **orchestration layer** (`services_user.py`) acts as the central coordinator: it retrieves the session context from MongoDB, dispatches the user input to the appropriate sub-flow, and persists the new state at the end of each turn. The **clinical logic layer** contains the finite state machine (`state_machine.py`) that drives the mhGAP screening protocol deterministically, and the phrase dictionary (`phrase_dictionary.py`) that holds the clinical question nuclei. The **response generation layer** (`generate_output.py`) wraps each clinical nucleus with an empathic bridge produced by the LLM. The **LLM layer** isolates all calls to the Gemini API through a thin wrapper (`llm.py`) and centralizes prompt construction (`prompt_builder.py`). Finally, the **data layer** (`db.py`) is the single point of contact with MongoDB, exposing CRUD operations on session documents.

```mermaid
flowchart TD
    FE([FRONTEND]):::external

    subgraph API["<b>API REST (Flask)</b>"]
        APP["app.py"]:::module
    end

    subgraph ORCH["<b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;APPLICATION SERVICES (ORCHESTRATION)</b>"]
        MAIN["services_user.py"]:::module
    end

    subgraph CLINICAL["<b>CLINICAL LOGIC &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;</b>"]
        FSM_MOD["state_machine.py"]:::module
        PHRASE["phrase_dictionary.py"]:::module
    end

    subgraph GENOUT["<b>RESPONSE GENERATION &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;</b>"]
        GEN["generate_output.py"]:::module
    end

    subgraph LLM_L["<b>LLM LAYER</b>"]
        PB["prompt_builder.py"]:::prompt
        LLM{{"llm.py<br/>(Gemini API)"}}:::llm
    end

    subgraph DB_L["<b>DATA LAYER &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;</b>"]
        DB["db.py"]:::dbmod
        MONGO[("MongoDB\nCHATBOT_mhGAP")]:::db
    end

    FE ==>|"POST /api/message"| APP
    APP -->|"telephone, message"| MAIN
    MAIN <-->|"fn: _ctx_set / \n_ctx_get"| DB
    MAIN -->|"conversation\nhistory"| DB
    MAIN <-.->|"save / get \ndata"| DB
    MAIN <--> FSM_MOD
    MAIN --> |"alternative\nfunctionalities\n(summarize...)"| GEN
    FSM_MOD -->|"phase, state, variant"| PHRASE
    PHRASE -->|"question nucleus"| GEN
    GEN --> PB
    PB -->|"prompt"| LLM
    LLM -->|"generated output"| GEN
    GEN -->|"bot output"| MAIN
    DB <--> MONGO
    MAIN -->|"JSON response"| APP
    APP ==>|"HTTP == 200<br/>{bot_message, image_url, ended, emergency_flags}"| FE
    FSM_MOD -.-> |"data storage<br/>(flags...)"|DB

    classDef external fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef module  fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef prompt  fill:#ede7f6,stroke:#4527a0,color:#311b92
    classDef llm     fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef dbmod   fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db      fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20

    style API      fill:#f5faff,stroke:#1565c0
    style ORCH     fill:#fff8f0,stroke:#e65100
    style CLINICAL fill:#fff5f8,stroke:#ad1457
    style GENOUT   fill:#fffef0,stroke:#f9a825
    style LLM_L    fill:#f7f3ff,stroke:#4527a0
    style DB_L     fill:#f0faf0,stroke:#2e7d32
```

The thick arrows (`==>`) trace the **happy path** of a normal message: frontend → API → orchestrator → response generation → frontend. The thin arrows (`-->`) represent internal queries and decisions, while the dotted arrows (`-.->`) indicate side-effect persistence (writes to MongoDB that do not return values used downstream). Reading the diagram from top to bottom matches the chronological order of execution within a single turn.

---

## Figure 1 — User initialization (`init_user`)

Flow executed from `POST /api/verify` **before any chat session begins**. Its job is to ensure that every authenticated phone number has a corresponding user document in MongoDB before the conversation flow can start. If the user is new, the document is initialized with empty clinical structures; if the user already exists, the function is a no-op and simply returns the existing flag.

The result, a boolean `is_new`, is returned to the frontend so it can decide whether to display the onboarding form (terms of service, privacy policy, support circle setup) or jump directly to the chat interface for returning users. This separation between initialization and conversation start is deliberate: it allows the frontend to handle the onboarding UX without polluting the message-processing endpoint, and guarantees that every subsequent call to `process_message` can safely assume the user document exists.

```mermaid
flowchart TD
 
    START(( )):::circle
    FINISH(( )):::circle
 
    START -->|"telephone"| IS_NEW
 
    subgraph INIT_FLOW[" "]
 
        IS_NEW["<b>db.py</b><br/>───────────<br/>is_new()"]:::dbmod
 
        D_NEW{is_new ?}:::decision
 
        CREATE["<b>db.py</b><br/>──────────<br/>create_user()"]:::dbmod

        ADD["<b>db.py</b><br/>─────────────────────────<br/>add_user_info()<br/>· · · · · · · · · ·<br/>→ name = ''<br/>→ age = ''<br/>→ USER_TERMS.status = 'rejected'<br/>→ CIRCLE = {}<br/>→ PROFILE = {}<br/>→ DEP_EVAL = {}<br/>→ SUI_EVAL = {}<br/>→ SCREENING = {}<br/>→ EMERGENCY = []<br/>→ FOLLOWUP.history = []<br/>→ FOLLOWUP.last_check = ''<br/>→ checkpoint.phase = ''<br/>→ checkpoint.state = ''<br/>→ ctx = {}"]:::dbmod
 
        SKIP["User already exists<br/>(skip creation)"]:::flowblock
 
        MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

        BOTTOM(( )):::junction
 
        IS_NEW --> D_NEW
        D_NEW -->|True| CREATE --> ADD --> BOTTOM
        D_NEW -->|False| SKIP --> BOTTOM
 
        MONGO -.->|find_one: telephone| IS_NEW
        CREATE -.-> MONGO
        ADD -.-> MONGO
 
    end
 
    BOTTOM -->|"is_new: True / False"| FINISH
 
    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
 
    style INIT_FLOW fill:#fff8f0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 6 3
```

The initialization populates ten clinical structures with empty defaults: `PROFILE` holds demographic data, `DEP_EVAL` and `SUI_EVAL` will store screening answers, `EMERGENCY` is a list of emergency instances, `FOLLOWUP` tracks post-emergency follow-ups, and `checkpoint` persists the FSM phase and state to support session resumption. Pre-allocating these fields with their empty types simplifies all downstream code, which can use `db.add_user_info(field, value)` without first checking whether the field exists.

---

## Figure 2 — Starting a conversation

Flow executed from `POST /api/start_conversation`, immediately after a user has been initialized (or recognized as returning). This function builds the **session context** that the orchestration layer will read on every subsequent message, and decides whether the conversation must begin with the consent presentation or can resume directly from the user's last clinical checkpoint.

The decision hinges on `USER_TERMS.status`: if the user has not yet accepted the informed consent (`status == 'rejected'`, the default for new users), the flow enters the `PRESENTATION` phase, where the bot will display the consent text and wait for explicit acceptance. If consent has already been granted in a previous session, the flow enters the `RESUMING` phase, which recovers the last conversation summary and the FSM checkpoint, allowing the user to pick up where they left off without re-explaining their situation.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"telephone"| INIT

    subgraph START_CONV[" "]

        INIT["<b>db.py</b><br/>───────────<br/>user_memory()<br/>user_status()"]:::dbmod

        SP["<b>services_user.py</b><br/>─────────────────────────────<br/>session_path = datetime.now() + '_session'"]:::module

        SESSION["<b>db.py</b><br/>───────────────────────────<br/>add_user_info()<br/>· · · · · · · · · ·<br/>→ session_path.summary = ''<br/>→ session_path.valoration = ''<br/>→ session_path.risk_level = ''<br/>→ session_path.conversation_history = {}"]:::dbmod

        WELCOME["<b>generate_output.py</b><br/>─────────────────<br/>welcome()"]:::module

        D_STATUS{status ==<br/>'rejected' ?}:::decision

        CTX["<b>services_user.py</b><br/>────────────────<br/>_ctx_set()<br/>· · · · · · · · · ·<br/>→ session_path<br/>→ j = 0, k = 0<br/>→ bot_output<br/>→ phase, state = ''<br/>→ variant = 0"]:::module

        BOTTOM(( )):::junction

        MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

        INIT -->|"memory, status"| SP
        SP -->|"session_path"| SESSION
        SESSION --> WELCOME -->|"bot_output"| D_STATUS
        D_STATUS -->|"True"| PRESENTATION -->|"phase"| CTX
        D_STATUS -->|"False"| RESUMING -->|"phase"| CTX

        MONGO -.-> INIT
        CTX -.-> MONGO
        SESSION -.-> MONGO
        CTX --> BOTTOM

    end

    BOTTOM -->|"bot_output"| FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20

    style START_CONV fill:#fff8f0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 6 3
```

The `session_path` is a timestamp-based identifier (e.g. `2026-05-28T14:30_session`) that namespaces all data persisted during this conversation. It allows multiple sessions per user to coexist in the same document without overwriting each other, and it becomes the key used by the closing flow (Figure 6) to retrieve the conversation transcript for summarization. The counters `j` (user turn) and `k` (LLM-generated turn within CHAT mode) are also initialized here and incremented on every subsequent message.

---

## Figure 3 — Orchestration flow (`process_message`)

Main execution path of `services_user.py`, invoked once per user message. The function reads the current session context from MongoDB, dispatches the user input to the appropriate sub-flow according to the current phase, applies a transversal security check when the conversation is in clinical territory, and persists the resulting state back to the database.

The dispatching is structured as a four-way switch on the current `phase`. The first three branches (`PRESENTATION`, `PRESENTATION_ASKED`, `RESUMING`) handle the conversation lifecycle and bypass the FSM entirely, going straight to response generation. The fourth branch (`else`) is the normal clinical path: the user input is fed into the finite state machine, which returns a new phase, state, and variant. Once the FSM has produced its decision, a **second switch** on `new_phase` determines what happens next: if the conversation is in `DEP_EVAL` or `CHAT`, a transversal `security_control()` scans the input for risk patterns (suicidal ideation, self-harm, immediate danger) and may override the FSM's decision to escalate the conversation to `SUI_EVAL`; if `new_phase` is `SUI_PROTOCOLS`, the system bypasses normal response generation and triggers the emergency protocols (see Figure 5); otherwise, the flow proceeds to `_generate_response()` as usual.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"telephone, user_input"| CTX_GET

    subgraph PROCESS_MSG[" "]

        CTX_GET["<b>db.py</b><br/>──────────<br/>_ctx_get()"]:::dbmod
        HIST["<b>db.py</b><br/>─────────────<br/>add_user_info()<br/>· · · · · · · · · ·<br/>bot_output_{j}<br/>user_input_{j}<br/>j += 1"]:::dbmod

        SWITCH{phase == ?}:::decision

        PRES["<b>PRESENTATION</b><br/>───────────<br/>— informed consent"]:::flowblock

        PRES_ASK["<b>PRESENTATION_ASKED</b><br/>────────────────<br/>— continues with PROFILE"]:::flowblock

        RES["<b>RESUMING</b><br/>─────────────────────<br/>— recovers last session summary<br/>— recovers phase, state"]:::flowblock

        FSM["<b>state_machine.py</b><br/>─────────────<br/>StateMachine()"]:::module

        FSM_GATE{new_phase == ?}:::decision

        SEC["<b>state_machine.py</b><br/>───────────<br/>security_control()"]:::module

        RISK{Risk<br/>detected ?}:::decision

        EMERGENCY["<b>SUI_EVAL !!!</b>"]:::emergency

        SUI_PROT["<b>SUI_PROTOCOLS !!!</b>"]:::emergency

        GEN_RESP[["<b>_generate_response()</b>"]]:::module

        CTX_SET["<b>db.py</b><br/>───────────<br/>_ctx_set()"]:::dbmod

        MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

        BOTTOM(( )):::junction

        CTX_GET --> HIST
        HIST -->|"j += 1"| SWITCH

        SWITCH -->|"PRESENTATION"| PRES ==> GEN_RESP
        SWITCH -->|"PRESENTATION_ASKED"| PRES_ASK ==> GEN_RESP
        SWITCH -->|"RESUMING"| RES ==> GEN_RESP
        SWITCH -->|"else"| FSM

        FSM -->|"(new_phase, new_state, variant)"| FSM_GATE
        FSM_GATE -->|"DEP_EVAL or CHAT"| SEC --> RISK
        FSM_GATE ==>|"else"| GEN_RESP
        FSM_GATE -->|"SUI_PROTOCOLS"| SUI_PROT -->|"*generation_args"| BOTTOM
        
        RISK -->|True| EMERGENCY ==> GEN_RESP
        RISK ==>|False| GEN_RESP

        GEN_RESP ==>|"*generation_args"| CTX_SET

        MONGO -.->|"session_path<br/>last_bot_output<br/>j, k<br/>phase, state, variant"| CTX_GET
        HIST -.->|"bot_output_{j}<br/>user_input_{j}"| MONGO
        CTX_SET --> BOTTOM
        CTX_SET -.->|"j, k, bot_output,<br/>phase, state, variant"| MONGO
        GEN_RESP <-.-> MONGO
        SUI_PROT -.->|"emergency_instance<br/>family notifications"| MONGO

    end

    BOTTOM -->|"(bot_output, image_path, is_ended, emergency_112, emergency_024)"| FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
    classDef emergency fill:#ffcdd2,stroke:#b71c1c,color:#b71c1c

    style PROCESS_MSG fill:#fff8f0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 6 3
```

The conversation history is persisted **before** any decision is made (`HIST` block), so that the user's message is recorded even if downstream code raises an exception. This append-only design simplifies debugging and audit: every turn produced by every user is available for forensic analysis. The two-phase persistence pattern — read context at the start, write it back at the end — guarantees that each call is atomic from the database's perspective.

---

## Figure 4.0 — USE_CASE_EVAL

Detailed view of the `use_case_class()` function within `generate_output.py`. This block is activated when the FSM enters the `USE_CASE_EVAL` phase, which happens either at the very beginning of the conversation (right after `PROFILE` completes) or periodically inside the free conversation mode (every five turns of `CHAT`, see Figure 4). Its job is to read the recent conversation transcript and classify the user's overall intent into one of four categories, then route the conversation accordingly.

The classification is delegated to the LLM with **temperature 0.0** — the lowest setting available — to ensure the output is deterministic and reproducible. Unlike empathic generation, this is a pure classification task where creativity would be harmful: the same input should always yield the same label, and the label must come from a closed vocabulary of four values. The result is then matched against a four-way switch that sets the next phase and state.

```mermaid
flowchart TD

    START(( )):::circle
    JUNCTION(( )):::junction
    FINISH(( )):::circle

    MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

    CTX["<b>db.py</b><br/>──────────────<br/>conversation_history()<br/>"]:::dbmod

    subgraph UC_BLOCK["&nbsp;&nbsp;<b>generate_output.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b>— use_case_class()&nbsp;&nbsp;"]
        PB["<b>prompt_builder.py</b><br/>──────────────────<br/>use_case_prompt()"]:::prompt
        LLM{{"<b>llm.py</b><br/>──────────────<br/>temp = 0.0<br/>send_prompt()"}}:::llm
    end

    SWITCH{use_case == ?}:::decision

    EM["new_phase = 'SUI_EVAL'<br/>new_state = '1'"]:::emergency

    AS["new_phase = 'DEP_EVAL'<br/>new_state = '1A.1'<br/>· · · · · · · · · ·<br/><b>db.py</b> — save_flow()"]:::dbmod

    TK["new_phase = 'CHAT'<br/>new_state = ''"]:::flowblock

    MS["new_phase = 'FAREWELL'<br/>new_state = 'misuse'"]:::farewell

    START -->|"telephone, phase, state"| CTX
    CTX -->|"conversation_transcript"| PB
    PB -->|"prompt"| LLM
    LLM -->|"use_case label"| SWITCH

    SWITCH -->|"EMERGENCY"| EM --> JUNCTION
    SWITCH -->|"TALK"| TK --> JUNCTION
    SWITCH -->|"ASSISTANCE"| AS --> JUNCTION 
    SWITCH -->|"else"| MS --> JUNCTION

    MONGO -.-> CTX
    AS -.->|"checkpoint.phase\ncheckpoint.state"| MONGO

    JUNCTION -->|"(new_phase, new_state)"| FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
    classDef prompt    fill:#ede7f6,stroke:#4527a0,color:#311b92
    classDef llm       fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef emergency fill:#ffcdd2,stroke:#b71c1c,color:#b71c1c
    classDef farewell  fill:#fce4ec,stroke:#880e4f,color:#880e4f

    style UC_BLOCK fill:#f7f3ff,stroke:#4527a0,stroke-width:2px
```

The four labels reflect mutually exclusive intent categories. **EMERGENCY** indicates that the user has expressed an immediate crisis (suicidal ideation, acute distress) and triggers the suicide risk evaluation. **ASSISTANCE** routes the user to the formal mhGAP depression screening; this is the only branch that explicitly persists the checkpoint to MongoDB, since the user has consented to a structured clinical assessment. **TALK** keeps the user in the free conversation mode, allowing for venting or non-clinical dialogue. The default branch **MISUSE** catches anything that does not fit the previous categories (off-topic, abuse, testing the bot) and gracefully ends the session.

---

## Figure 4 — Response generation (`_generate_response`)

Internal detail of `_generate_response()`: four mutually exclusive branches selected by `*_phase` (which can mean either the incoming `phase` or the new `new_phase` produced by the FSM, depending on the branch). The function implements the **hybrid response architecture** that defines this chatbot: a fixed clinical nucleus retrieved from a deterministic phrase dictionary, wrapped by an empathic bridge generated by the LLM at temperature 1.0.

The four branches embody different generation strategies. **Branch A** (`USE_CASE_EVAL`) re-classifies the user intent — see Figure 4.0. **Branch B** (`CHAT`) is free conversation mode with an additional inner check: every five turns, the system silently re-runs use case classification to detect if the user has drifted into clinical territory (suicidal ideation, request for help), in which case it can leave CHAT and re-enter the screening flow. **Branch C** (`FAREWELL`) generates the closing message and triggers the session-closing flow described in Figure 6. **Branch D** is the **default clinical path**: the phrase dictionary returns either the base nucleus (`bot_output_info`) or a variant nucleus (`variant_dict`, used when the user response was evasive, ambiguous, hostile, or otherwise unexpected), and the LLM produces an empathic bridge that incorporates user memory (name, age, profile, prior summaries) to personalize the question without altering its clinical content.

> *Note on the `*_phase` notation*: the wildcard `*_phase` in the decision diamonds indicates that the condition applies to **either** `phase` or `new_phase`, depending on the calling context. This is necessary because branches B and C can be entered both directly (the FSM had already set the phase to CHAT or FAREWELL in a previous turn) or as a fresh transition (`new_phase` just changed to CHAT or FAREWELL in the current turn).

```mermaid
flowchart TD

    START(( )):::circle
    JUNCTION(( )):::junction
    FINISH(( )):::circle

    MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

    D_UC{phase ==<br/>USE_CASE_EVAL?}:::decision
    D_CH{*_phase ==<br/>CHAT?}:::decision
    D_FW{*_phase ==<br/>FAREWELL?}:::decision

    BRANCH_UC[["<b>Branch A:\nUSE CASE classification</b>"]]:::external

    subgraph BRANCH_CH["<b>Branch B: Free conversation TALK</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"]
        TALK["<b>generate_output.py</b><br/>───────────<br/>talk_mode()"]:::module
        LLM_TK{{"temp = 1.0"}}:::llm
        KCHAT{"k is multiple \nof 5 ?"}:::decision
    end

    subgraph BRANCH_FW["<b>Branch C: Session closing FAREWELL</b>"]
        FW["<b>generate_output.py</b><br/>───────────<br/>farewell()"]:::module
        LLM_FW{{"temp = 1.0"}}:::llm
    end

    subgraph BRANCH_NM["<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Branch D: Clinical flow mhGAP</b>"]
        D_VAR{Variant\nrequired ?}:::decision
        PVAR["<b>phrase_dictionary.py</b><br/>───────────────<br/>variant_dict()"]:::phrase
        PBASE["<b>phrase_dictionary.py</b><br/>───────────────<br/>bot_output_info()"]:::phrase
        BOUT["<b>generate_output.py</b><br/>──────────────<br/>bot_output()"]:::module
        LLM_BO{{"temp = 1.0"}}:::llm
    end

    START -->|"(telephone, phase, state, variant, k, *memory_args)"| D_UC
    
    D_UC -->|True| BRANCH_UC
    D_UC -->|False| D_CH

    KCHAT -->|True| BRANCH_UC
    D_CH -->|False| D_FW
    D_CH -->|True| KCHAT

    KCHAT -->|False| TALK
    TALK --> LLM_TK -->|"bot_output\nk += 1"| JUNCTION

    BRANCH_UC -->|"(new_phase, new_state)"| D_CH

    D_FW -->|True| FW --> LLM_FW -->|"bot_output"| JUNCTION
    D_FW -->|False| D_VAR

    D_VAR -->|True| PVAR -->|"nucleus"| BOUT
    D_VAR -->|False| PBASE -->|"nucleus"| BOUT
    MONGO -.->|"user memory"| BOUT
    BOUT --> LLM_BO -->|"bot_output"| JUNCTION

    JUNCTION -->|"(bot_output, k, *output_args)"| FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
    classDef phrase    fill:#e8eaf6,stroke:#283593,color:#1a237e
    classDef llm       fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef external  fill:#e3f2fd,stroke:#1565c0,color:#0d47a1

    style BRANCH_CH fill:#e8f5e9,stroke:#2e7d32,stroke-dasharray: 6 3
    style BRANCH_FW fill:#fce4ec,stroke:#ad1457,stroke-dasharray: 6 3
    style BRANCH_NM fill:#fffde7,stroke:#f57f17,stroke-dasharray: 6 3
```

The temperature of 1.0 used in branches B, C, and D is the key parameter that gives the bot its natural conversational tone. Higher temperatures cause the LLM to sample from a broader probability distribution over tokens, yielding more varied and creative phrasing — desirable when the clinical content is already fixed by the phrase dictionary, and the LLM's only job is to make the question sound human rather than scripted. This contrasts sharply with the temperature 0.0 used for classification tasks (see Figure 4.0) and is one of the most important architectural decisions of the system.

---

## Figure 5 — SUI Protocols

Detailed flow of the suicide intervention protocols, triggered when the FSM enters the `SUI_PROTOCOLS` phase. This block executes outside the normal response generation path: instead of calling `_generate_response()`, the system directly retrieves the bot message from the phrase dictionary and triggers a series of side effects — image dispatch, family notification, emergency registry, and a forced transition to the post-emergency follow-up phase.

The protocol level is determined by `state`. **PROTOCOL 1** is the most critical: it routes the user to the Spanish 112 emergency number and is reserved for situations where the user has expressed immediate intent or has a specific plan. **PROTOCOLS 2 and 3** route to the 024 psychological emergency line and cover less acute but still serious ideation; they share the same referral because their clinical handling is identical, differing only in the message content (psychoeducation, support reinforcement). All three protocols then converge into a shared pipeline that retrieves the appropriate clinical phrase, dispatches an image (a visual support card for the user, plus optionally one for their family circle), and registers the emergency in MongoDB.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle
    MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db
    MONGO2[("MongoDB<br/>CHATBOT_mhGAP")]:::db

    SWITCH{state == ?}:::decision

    S1["<b>PROTOCOL 1</b><br/>referral = '112'"]:::emergency
    S2["<b>PROTOCOL 2</b><br/>referral = '024'"]:::emergency
    S3["<b>PROTOCOL 3</b><br/>referral = '024'"]:::emergency

    PD["<b>phrase_dictionary.py</b><br/>───────────────<br/>bot_output_info()"]:::phrase

    IMG["<b>generate_output.py</b><br/>───────────────<br/>bot_output_image()"]:::module

    D_IMG{image_path<br/>_family ?}:::decision

    CONSENT["<b>db.py</b><br/>───────────────<br/>get_user_info()<br/>· · · · · · · · · ·<br/>→ CIRCLE.privacy"]:::dbmod

    D_CONS{family share<br/>consent ?}:::decision

    CONTACTS["<b>db.py</b><br/>───────────────<br/>get_user_info()<br/>· · · · · · · · · ·<br/>→ CIRCLE.contacts"]:::dbmod

    NOTIF["<b>db.py</b><br/>───────────────<br/>save_notification()<br/>· · · · · · · · · ·<br/>∀ contact in contacts"]:::dbmod

    EMG["<b>db.py</b><br/>───────────────<br/>add_emergency_instance()"]:::dbmod

    FLOW["<b>db.py</b><br/>───────────────<br/>save_flow()"]:::dbmod

    BOTTOM(( )):::junction

    START -->|"state"| SWITCH
    SWITCH -->|"3"| S3
    SWITCH -->|"2"| S2
    SWITCH -->|"1"| S1

    S1 & S2 & S3 --> PD
    PD -->|"bot_output"| IMG
    IMG -->|"*image_paths"| D_IMG

    D_IMG -->|False| EMG
    D_IMG -->|True| CONSENT --> D_CONS
    D_CONS -->|False| EMG
    D_CONS -->|True| CONTACTS --> NOTIF --> EMG

    EMG --> FLOW --> BOTTOM

    MONGO2 -.->|"family_consent"| CONSENT
    MONGO2 -.->|"*contacts"| CONTACTS
    NOTIF -.->|"{notification}"| MONGO
    EMG -.->|"{emergency_instance}"| MONGO
    FLOW -.->|"(phase = 'FOLLOWUP',<br/>state = 'emergency_followup')"| MONGO

    BOTTOM -->|"(bot_output, image_path_user,<br/>*emergency_referral)"| FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
    classDef phrase    fill:#e8eaf6,stroke:#283593,color:#1a237e
    classDef emergency fill:#ffcdd2,stroke:#b71c1c,color:#b71c1c
```

The **family notification subflow** is one of the most sensitive paths in the system and is governed by explicit user consent. When a family-targeted image exists for the current protocol (`image_path_family`), the system reads the user's `CIRCLE.privacy.allowContactFamily` flag from MongoDB. Only if the user has explicitly opted in during onboarding will the system iterate over the user's emergency contacts (`CIRCLE.contacts`) and dispatch a notification to each one. This design enforces the principle that **no third party is contacted without prior consent**, even in life-threatening situations — a constraint dictated by both legal and ethical considerations.

Finally, `save_flow()` forces the FSM to transition to `FOLLOWUP / emergency_followup` so that the next interaction with the user (which may happen hours or days later) will trigger the post-emergency follow-up flow rather than continuing the previous clinical screening. This guarantees that no emergency goes without a follow-up check.

---

## Figure 6 — Session closing (`_run_farewell`)

Full flow of the closing process: clinical summary generation, session valuation, risk level assessment, and persistence to MongoDB. This function is invoked at the end of every session, regardless of how it ended (normal farewell, age-related rejection, misuse exit, or post-emergency wrap-up). Its purpose is to produce three pieces of structured metadata that will be consumed in future sessions: a **summary** of what was discussed, a **valuation** of the user's emotional progression during the session, and a **risk level** numeric score.

The three artifacts are generated **in parallel**: the same conversation transcript is fed into three different prompts (`session_summary_prompt`, `session_valoration_prompt`, `risk_level_prompt`) and the LLM is called three times with different temperatures. The summary uses temperature 1.0 because the output is free-form prose where natural language fluency matters; the valuation and risk level use temperature 0.0 because they produce structured outputs (a categorical valuation, a numeric score) that must be reproducible. Running them in parallel rather than sequentially is a deliberate optimization: each LLM call takes 1-3 seconds, so the parallel pattern reduces total latency from ~9 seconds to ~3 seconds.

```mermaid
flowchart TD
    START(( )):::circle
    FINISH(( )):::circle

    START -->|"telephone, session_path"| CONV

    subgraph RUN_FAREWELL[" "]

        CONV["<b>db.py</b><br/>───────────────<br/>get_user_info()<br/>→ conversation_transcript"]:::dbmod

        subgraph PARALLEL["<b>generate_output.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b>"]
            PB_S["<b>prompt_builder.py</b><br/>──────────────────<br/>session_summary_prompt()"]:::prompt
            PB_V["<b>prompt_builder.py</b><br/>──────────────────<br/>session_valoration_prompt()"]:::prompt
            PB_R["<b>prompt_builder.py</b><br/>───────────────<br/>risk_level_prompt()"]:::prompt
            LLM_S{{"<b>llm.py</b><br/>──────────────<br/>temp = 1.0\nsend_prompt()"}}:::llm
            LLM_V{{"<b>llm.py</b><br/>──────────────<br/>temp = 0.0\nsend_prompt()"}}:::llm
            LLM_R{{"<b>llm.py</b><br/>──────────────<br/>temp = 0.0\nsend_prompt()"}}:::llm
        end

        DB_SAVE["<b>db.py</b><br/>─────────────<br/>add_user_info()<br/>get_user_info()"]:::dbmod

        MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

        D_CTX{ctx.emergency_followup<br/>exists ?}:::decision

        FU["<b>db.py</b><br/>───────────────────────<br/>add_to_list()<br/>· · · · · · · · · ·<br/>→ new_instance = {<br/>emergency_date,<br/>followup_date,<br/>outcome }"]:::dbmod

        BOTTOM(( )):::junction

        CONV --> PB_S & PB_V & PB_R

        PB_S -->|"prompt"| LLM_S
        PB_V -->|"prompt"| LLM_V
        PB_R -->|"prompt"| LLM_R

        LLM_S -->|"summary"| DB_SAVE
        LLM_V -->|"valoration"| DB_SAVE
        LLM_R -->|"risk"| DB_SAVE

        MONGO -.-> CONV
        DB_SAVE -.-> MONGO
        MONGO -.->|"ctx"| DB_SAVE

        DB_SAVE --> D_CTX

        D_CTX -->|False| BOTTOM
        D_CTX -->|True| FU --> BOTTOM

        FU -.->|"FOLLOWUP.history"| MONGO

    end

    BOTTOM --> FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef prompt    fill:#ede7f6,stroke:#4527a0,color:#311b92
    classDef llm       fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f

    style RUN_FAREWELL fill:#fff8f0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 6 3
    style PARALLEL     fill:#f7f3ff,stroke:#4527a0,stroke-width:2px
```

After the three artifacts are persisted, the flow checks whether the closing session was triggered by a previous emergency (`ctx.emergency_followup` exists). If so, a new follow-up instance is appended to the user's `FOLLOWUP.history` list, recording the date of the original emergency, the date of this follow-up, and the outcome (which may be derived from the risk level computed above). This list is later consulted by the orchestrator to remind the user to check in periodically after an emergency event, closing the safety loop that the architecture is designed to provide.

---

## How to export to image

```bash
npm install -g @mermaid-js/mermaid-cli

# One SVG per figure (recommended for LaTeX or Word documents)
mmdc -i backend_flow_diagram.md -o fig1_overview.svg
mmdc -i backend_flow_diagram.md -o fig2_orchestration.svg

# High-resolution PNG
mmdc -i backend_flow_diagram.md -o fig1_overview.png -w 2400
```

Alternatively, paste each code block into **https://mermaid.live** for individual preview and export.