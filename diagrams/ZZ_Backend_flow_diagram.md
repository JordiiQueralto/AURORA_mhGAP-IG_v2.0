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

    subgraph ORCH["<b>ORCHESTATION</b>"]
        MAIN["main_api.py"]:::module
    end

    subgraph CLINICAL["<b>CLINICAL LOGIC</b>"]
        FSM_MOD["state_machine.py"]:::module
        PHRASE["phrase_dictionary.py"]:::module
    end

    subgraph GENOUT["<b>RESPONSE GENERATION</b>"]
        GEN["generate_output.py"]:::module
    end

    subgraph LLM_L["<b>LLM LAYER</b>"]
        PB["prompt_builder.py"]:::prompt
        LLM["llm.py\n(Gemini API)"]:::llm
    end

    subgraph DB_L["<b>DATA LAYER</b>"]
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

        SP["<b>main_api.py</b><br/>─────────────────────────────<br/>session_path = datetime.now() + '_session'"]:::module

        SESSION["<b>db.py</b><br/>───────────────────────────<br/>add_user_info()<br/>· · · · · · · · · ·<br/>→ session_path.summary = ''<br/>→ session_path.valoration = ''<br/>→ session_path.risk_level = ''<br/>→ session_path.conversation_history = {}"]:::dbmod

        WELCOME["<b>generate_output.py</b><br/>─────────────────<br/>welcome()"]:::module

        D_STATUS{status ==<br/>'rejected' ?}:::decision

        PRESENTATION["<b>main_api.py</b><br/>────────────────<br/>phase = PRESENTATION<br/>(onboarding: name, age,<br/>reason, terms...)"]:::module

        RESUMING["<b>main_api.py</b><br/>────────────────<br/>phase = RESUMING<br/>(restore last session<br/>checkpoint)"]:::module

        CTX["<b>main_api.py</b><br/>────────────────<br/>_ctx_set()<br/>· · · · · · · · · ·<br/>→ session_path<br/>→ j = 0, k = 0<br/>→ bot_output<br/>→ phase, state = ''<br/>→ variant = 0"]:::module

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

Detalle del flujo principal de `main_api.py`: cómo se recupera el contexto de sesión, qué rama se toma según la fase actual y cómo se persiste el nuevo estado tras cada turno.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"telephone, user_input"| CTX_GET

    subgraph PROCESS_MSG[" "]

        CTX_GET["<b>db.py</b><br/>────────────────────────────────────────<br/>_ctx_get()<br/>→ session_path, last_bot_output, j, k, phase, state, variant"]:::dbmod
        HIST["<b>db.py</b><br/>────────────────────────────────────<br/>add_user_info()"]:::dbmod

        D_PRES{phase ==<br/>PRESENTATION ?}:::decision
        D_RES{phase ==<br/>RESUMING ?}:::decision

        PRES["<b>PRESENTATION flow:</b><br/>— informed consent"]:::flowblock

        RES["<b>RESUMING flow:</b><br/>— recovers last session summary<br/>— recovers phase, state"]:::flowblock

        FSM["<b>state_machine.py</b><br/>───────────────────────<br/>StateMachine()<br/>→ new_phase, new_state, variant"]:::module

        SEC_GATE{new_phase in<br/>DEP_EVAL or CHAT?}:::decision

        SEC["<b>state_machine.py</b><br/>───────────<br/>security_control()"]:::module

        RISK{Risk<br/>detected ?}:::decision

        EMERGENCY["<b>SUI_EVAL !!!</b>"]:::emergency

        GEN_RESP["<b>_generate_response()</b>"]:::module

        CTX_SET["<b>db.py</b><br/>───────────<br/>_ctx_set()"]:::dbmod

        MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

        BOTTOM[ ]:::phantom

        CTX_GET --> HIST
        HIST --> D_PRES

        D_PRES -->|True| PRES ==> GEN_RESP
        D_PRES -->|False| D_RES
        D_RES  -->|True| RES  ==> GEN_RESP
        D_RES  -->|False| FSM --> SEC_GATE

        SEC_GATE -->|True| SEC --> RISK
        RISK -->|True| EMERGENCY ==> GEN_RESP
        RISK ==>|False| GEN_RESP
        SEC_GATE ==>|False| GEN_RESP

        GEN_RESP ==> CTX_SET

        CTX_GET <-.-> MONGO
        HIST -.->|"bot_output_{j}<br/>user_input_{j}<br/>j += 1"| MONGO
        GEN_RESP <-.-> MONGO
        CTX_SET -.->|"j, k, bot_output,<br/>phase, state, variant"| MONGO

        CTX_SET -->|"bot_message, image_path,<br/>is_ended, is_emergency"| BOTTOM

    end

    BOTTOM --> FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef phantom   fill:#ffffff,stroke:#ffffff,color:#ffffff
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
    classDef emergency fill:#ffcdd2,stroke:#b71c1c,color:#b71c1c

    style PROCESS_MSG fill:#fff8f0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 6 3
```

---

## Figura 4 — Generación de respuesta (`_generate_response`)

Detalle interno de `_generate_response`: las cuatro ramas mutuamente excluyentes según `new_phase` y la arquitectura híbrida de nucleo clínico fijo + puente generado por LLM.

```mermaid
flowchart TD
    ENTRY(["_generate_response\nnew_phase, new_state, variant"]):::entry

    D_UC{new_phase ==\nUSE_CASE_EVAL?}:::decision
    D_CH{new_phase ==\nCHAT?}:::decision
    D_FW{new_phase ==\nFAREWELL?}:::decision

    subgraph BRANCH_UC["Rama A — Clasificacion de caso de uso"]
        DB_H[("db.py\nconversation_history\nhistorico de sesion")]:::db
        UC["generate_output.py\nuse_case_class"]:::module
        PB_UC["prompt_builder.py\nuse_case_prompt"]:::prompt
        LLM_UC{{"llm.py — Gemini\ntemp = 0.0\nretorna: EMERGENCY /\nASSISTANCE / TALK / MISENSE"}}:::llm
    end

    subgraph BRANCH_CH["Rama B — Conversacion libre TALK"]
        TALK["generate_output.py\ntalk_mode\nultimos 8 turnos"]:::module
        PB_TK["prompt_builder.py\nprompt_talk_mode"]:::prompt
        LLM_TK{{"llm.py — Gemini\ntemp = 1.0\noyente activo empático"}}:::llm
    end

    subgraph BRANCH_FW["Rama C — Cierre de sesion FAREWELL"]
        FW["generate_output.py\nfarewell\nnormal / exit / age"]:::module
        RUN_FW["main_api.py\n_run_farewell"]:::module
    end

    subgraph BRANCH_NM["Rama D — Flujo clinico mhGAP (DEP_EVAL, SUI_EVAL, etc.)"]
        D_VAR{variant != 0?}:::decision
        PVAR["phrase_dictionary.py\nvariant_dict\nnucleo alternativo"]:::phrase
        PBASE["phrase_dictionary.py\nbot_output_info\nnucleo clinico base mhGAP"]:::phrase
        MEM[("db.py\nuser_memory\nnombre, edad, PROFILE\nsummary ultima sesion")]:::db
        BOUT["generate_output.py\nbot_output"]:::module
        PB_BO["prompt_builder.py\nprompt_bot_output\nnucleo + contexto + memoria"]:::prompt
        LLM_BO{{"llm.py — Gemini\ntemp = 1.0\ngenerada: puente empatico\n+ nucleo clinico literal"}}:::llm
    end

    RESULT(["bot_message\nimage_url\nis_ended, is_emergency"]):::entry

    ENTRY --> D_UC

    D_UC -->|Si| DB_H --> UC --> PB_UC --> LLM_UC --> RESULT
    D_UC -->|No| D_CH

    D_CH -->|Si| TALK --> PB_TK --> LLM_TK --> RESULT
    D_CH -->|No| D_FW

    D_FW -->|Si| FW & RUN_FW --> RESULT
    D_FW -->|No| D_VAR

    D_VAR -->|Si| PVAR --> BOUT
    D_VAR -->|No| PBASE --> BOUT
    MEM -->|memoria de usuario| BOUT
    BOUT --> PB_BO --> LLM_BO --> RESULT

    classDef entry    fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef module   fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef decision fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef db       fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef llm      fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef prompt   fill:#ede7f6,stroke:#4527a0,color:#311b92
    classDef phrase   fill:#e8eaf6,stroke:#283593,color:#1a237e

    style BRANCH_UC fill:#e3f2fd,stroke:#1565c0
    style BRANCH_CH fill:#e8f5e9,stroke:#2e7d32
    style BRANCH_FW fill:#fce4ec,stroke:#ad1457
    style BRANCH_NM fill:#fffde7,stroke:#f57f17
```

---

## Figura 5 — Seguridad 

Flujo del módulo REGEX de detección de riesgo activo que actúa de forma transversal durante las fases `DEP_EVAL` y `CHAT`.

```mermaid
flowchart TD
    IN(["Texto del usuario\nnormalizado"]):::entry

    SEC["state_machine.py\nsecurity_control\nbusca patrones de riesgo\nmediante REGEX"]:::module

    D_R1{Patron de\nautolesion?}:::decision
    D_R2{Patron de\nideacion activa?}:::decision
    D_R3{Patron de\nplan o metodo?}:::decision

    SUI1["SUI_PROTOCOLS\nstado: 1 — Emergencia\nprotocolo 112"]:::emergency
    SUI2["SUI_PROTOCOLS\nstado: 2 — Psicoeducacion\nprotocolo 024"]:::emergency

    DB_E[("db.py\nadd_emergency_instance\nsession_path, trigger_hour\nprotocol, referral")]:::db
    DB_N[("db.py\nsave_notification\nalerta a familiares\ndel circulo de apoyo")]:::db

    IMG["generate_output.py\nbot_output_image\nselecciona imagen\nsegun estado SUI"]:::module

    OUT(["new_phase = SUI_PROTOCOLS\nnew_state, image_path_user\nimage_path_family\nis_emergency = True"]):::entry

    IN --> SEC
    SEC --> D_R1
    D_R1 -->|Si| SUI1
    D_R1 -->|No| D_R2
    D_R2 -->|Si| SUI2
    D_R2 -->|No| D_R3
    D_R3 -->|Si| SUI1
    D_R3 -->|No| OUT

    SUI1 & SUI2 --> DB_E & DB_N & IMG --> OUT

    classDef entry    fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef module   fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef decision fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef db       fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef emergency fill:#ffcdd2,stroke:#b71c1c,color:#b71c1c
```

### 6 — Cierre de sesión (`_run_farewell`)

Flujo completo del proceso de cierre: generación de resumen clínico, valoración de la sesión y nivel de riesgo, con persistencia en MongoDB.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    CONV["<b>db.py</b><br/>───────────────<br/>get_user_info()<br/>→ conversation_transcript"]:::dbmod

    subgraph PARALLEL["<b>generate_output.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b>"]
        PB_S["<b>prompt_builder.py</b><br/>──────────────────<br/>session_summary_prompt()"]:::prompt
        PB_V["<b>prompt_builder.py</b><br/>──────────────────<br/>session_valoration_prompt()"]:::prompt
        PB_R["<b>prompt_builder.py</b><br/>───────────────<br/>risk_level_prompt()"]:::prompt
        LLM_S{{"<b>llm.py</b><br/>──────────────<br/>session_summary()"}}:::llm
        LLM_V{{"<b>llm.py</b><br/>──────────────<br/>session_valoration()"}}:::llm
        LLM_R{{"<b>llm.py</b><br/>──────────────<br/>session_risk()"}}:::llm
    end

    DB_SAVE["<b>db.py</b><br/>─────────────<br/>add_user_info()<br/>get_user_info()"]:::dbmod

    MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

    D_CTX{ctx.emergency_followup<br/>exists ?}:::decision

    FU["<b>db.py</b><br/>───────────────────────<br/>add_to_list()<br/>· · · · · · · · · ·<br/>→ new_instance = {<br/>emergency_date,<br/>followup_date,<br/>outcome }"]:::dbmod

    START -->|"telephone, session_path"| CONV
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

    D_CTX -->|False| FINISH
    D_CTX -->|True| FU --> FINISH

    FU -.->|"FOLLOWUP.history"| MONGO

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef prompt    fill:#ede7f6,stroke:#4527a0,color:#311b92
    classDef llm       fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f

    style PARALLEL fill:#f7f3ff,stroke:#4527a0,stroke-width:2px
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
