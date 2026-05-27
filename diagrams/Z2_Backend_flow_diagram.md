# Arquitectura del Backend — Chatbot mhGAP v2.0

Este documento presenta el flujo del backend en cuatro niveles de detalle progresivo, siguiendo el enfoque C4 (Context → Container → Component → Code). Cada diagrama puede ser referenciado de forma independiente en el texto del TFG.

---

## Figura 0 — Vista general del sistema

Visión de alto nivel de las seis capas del backend y los flujos de datos entre ellas. Muestra qué módulo llama a quién, sin entrar en la lógica interna de cada uno.

```mermaid
flowchart TD
    FE([FRONTEND]):::external

    subgraph API["<b>API REST (Flask)</b>"]
        APP["app.py"]:::module
    end

    subgraph ORCH["<b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;APPLICATION SERVICES (ORCHESTATION)</b>"]
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
        %% CAMBIO AQUÍ: Uso de llaves { } para generar el rombo y <br/> para el salto de línea
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
    MAIN --> |"alternative\nfunctionalities\n(summaryze...)"| GEN
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

---
## Figura 1 — Inicialización de usuario (`init_user`)
 
Flujo ejecutado desde `POST /api/verify` antes de cualquier sesión de chat. Comprueba si el usuario existe en la base de datos y, si no, crea su documento. Devuelve `is_new` al frontend para que sepa si debe mostrar el onboarding.
 
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

---
## Figura 2 - Empezar conversación

Inició session detallado

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

---
## Figura 3 — Flujo de orquestación (`process_message`)

Detalle del flujo principal de `services_user.py`: cómo se recupera el contexto de sesión, qué rama se toma según la fase actual y cómo se persiste el nuevo estado tras cada turno.

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

---

## Figura 4.0 - USE CASE EVAL

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

---

## Figura 4 — Generación de respuesta (`_generate_response`)

Detalle interno de `_generate_response`: las cuatro ramas mutuamente excluyentes según `new_phase` y la arquitectura híbrida de nucleo clínico fijo + puente generado por LLM.

CHAT: Periodic re-evaluation?\n(every 5 turns)

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

---

## Figura 5 — SUI Protocols 

Flujo del módulo REGEX de detección de riesgo activo que actúa de forma transversal durante las fases `DEP_EVAL` y `CHAT`.

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

### 6 — Cierre de sesión (`_run_farewell`)

Flujo completo del proceso de cierre: generación de resumen clínico, valoración de la sesión y nivel de riesgo, con persistencia en MongoDB.

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

---

## Cómo exportar a imagen

```bash
npm install -g @mermaid-js/mermaid-cli

# Un SVG por figura (recomendado para incluir en LaTeX o Word)
mmdc -i backend_flow_diagram.md -o fig1_overview.svg
mmdc -i backend_flow_diagram.md -o fig2_orchestration.svg

# PNG de alta resolución
mmdc -i backend_flow_diagram.md -o fig1_overview.png -w 2400
```

O pega cada bloque de código en **https://mermaid.live** para previsualizar y exportar de forma individual.
