# Arquitectura del Backend — Chatbot mhGAP v2.0

Este documento presenta el flujo del backend en cuatro niveles de detalle progresivo, siguiendo el enfoque C4 (Context → Container → Component → Code). Cada diagrama puede ser referenciado de forma independiente en el texto del TFG.

---

## Figura 1 — Vista general del sistema

Visión de alto nivel de las seis capas del backend y los flujos de datos entre ellas. Muestra qué módulo llama a quién, sin entrar en la lógica interna de cada uno.

```mermaid
flowchart TD
    FE([Frontend HTML\nchat_13.html]):::external

    subgraph API["API REST — Flask"]
        APP["app.py\nPuerto 5000"]:::module
    end

    subgraph ORCH["Orquestación"]
        MAIN["main_api.py\nprocess_message\n_generate_response\n_run_farewell"]:::module
    end

    subgraph CLINICAL["Lógica Clínica"]
        FSM_MOD["state_machine.py\nStateMachine\nsecurity_control\nnormalize_text"]:::module
        PHRASE["phrase_dictionary.py\nbot_output_info\nvariant_dict"]:::module
    end

    subgraph GENOUT["Generación de Respuesta"]
        GEN["generate_output.py\nuse_case_class\ntalk_mode\nbot_output\nfarewell\nsession_summary"]:::module
    end

    subgraph LLM_L["Capa LLM"]
        PB["prompt_builder.py\nprompts especializados"]:::prompt
        LLM["llm.py\nGemini 2.5 Flash API"]:::llm
    end

    subgraph DB_L["Capa de Datos"]
        DB["db.py\nget / add / update\nuser_info, memory\nnotifications"]:::dbmod
        MONGO[("MongoDB\nCHATBOT_mhGAP")]:::db
    end

    FE -->|"POST /api/message"| APP
    APP -->|"telephone, message"| MAIN
    MAIN <-->|"ctx lectura/escritura"| DB
    MAIN --> FSM_MOD
    MAIN --> GEN
    FSM_MOD -->|"nucleo clinico"| PHRASE
    PHRASE -->|"nucleo"| GEN
    GEN --> PB
    PB -->|"prompt"| LLM
    LLM -->|"respuesta generada"| GEN
    GEN -->|"bot_message"| MAIN
    DB <--> MONGO
    MAIN -->|"JSON response"| APP
    APP -->|"HTTP 200"| FE

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

## Figura 2 — Flujo de orquestación (`process_message`)

Detalle del flujo principal de `main_api.py`: cómo se recupera el contexto de sesión, qué rama se toma según la fase actual y cómo se persiste el nuevo estado tras cada turno.

```mermaid
flowchart TD
    START([POST /api/message]):::endpoint

    APP["app.py\nhandle_message"]:::module

    CTX_GET[("db.py — _ctx_get\nlee phase, state, variant,\nsession_path desde MongoDB")]:::db

    D_PRES{phase ==\nPRESENTATION?}:::decision

    D_RES{phase ==\nRESOURCE?}:::decision

    PRES["Flujo PRESENTATION\nonboarding — nombre — edad\nconsentimiento informado\naceptacion de terminos"]:::flowblock

    RES["Flujo RESUMING\nrecupera summary de\nla ultima sesion\ncomo contexto de memoria"]:::flowblock

    NORM["state_machine.py\nnormalize_text\nlowercase — sin acentos\nsin puntuacion"]:::module

    FSM["state_machine.py\nStateMachine\nFSM clinica mhGAP v2.0\nretorna: new_phase, new_state, variant"]:::module

    SEC_GATE{new_phase in\nDEP_EVAL or CHAT?}:::decision

    SEC["security_control\nREGEX sobre texto\ndetecta riesgo activo"]:::module

    RISK{Riesgo\ndetectado?}:::decision

    EMERGENCY["SUI_PROTOCOLS\nsobreescribe new_phase\nactiva flags 112 y 024"]:::emergency

    GEN_RESP["main_api.py\n_generate_response\nnew_phase, new_state, variant"]:::module

    CTX_SET[("db.py — _ctx_set\npersiste new_phase, new_state\nlog user_input_N, bot_output_N\nflags de emergencia")]:::db

    RESP_OUT([HTTP JSON Response\nbot_message, image_url\nended, emergency flags]):::endpoint

    START --> APP --> CTX_GET --> D_PRES

    D_PRES -->|Si| PRES --> CTX_SET
    D_PRES -->|No| D_RES
    D_RES  -->|Si| RES  --> CTX_SET
    D_RES  -->|No| NORM --> FSM --> SEC_GATE

    SEC_GATE -->|Si| SEC --> RISK
    RISK -->|Si| EMERGENCY --> GEN_RESP
    RISK -->|No| GEN_RESP
    SEC_GATE -->|No| GEN_RESP

    GEN_RESP --> CTX_SET --> APP --> RESP_OUT

    classDef endpoint  fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef db        fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef emergency fill:#ffcdd2,stroke:#b71c1c,color:#b71c1c
```

---

## Figura 3 — Generación de respuesta (`_generate_response`)

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

## Figura 4 — Seguridad y cierre de sesión

### 4a — Control de seguridad transversal (`security_control`)

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

### 4b — Cierre de sesión (`_run_farewell`)

Flujo completo del proceso de cierre: generación de resumen clínico, valoración de la sesión y nivel de riesgo, con persistencia en MongoDB.

```mermaid
flowchart TD
    IN(["_run_farewell\ntelephone, session_path"]):::entry

    CONV[("db.py\nget_user_info\nconversation_history\nde la sesion activa")]:::db

    subgraph PARALLEL["Procesamiento paralelo — llm.py Gemini temp 0.0"]
        PB_S["prompt_builder.py\nsession_summary_prompt\n150-300 palabras\npunto de entrada, temas clave\nestado emocional, recursos"]:::prompt
        PB_V["prompt_builder.py\nsession_valoration_prompt\nclasifica: BUENA / REGULAR / MALA\ntrayectoria emocional del usuario"]:::prompt
        PB_R["prompt_builder.py\nrisk_level_prompt\nclasifica: ESTABLE / BAJO /\nMODERADO / ALTO"]:::prompt
        LLM_S{{"llm.py\nsession_summary"}}:::llm
        LLM_V{{"llm.py\nsession_valoration"}}:::llm
        LLM_R{{"llm.py\nsession_risk"}}:::llm
    end

    DB_SAVE[("db.py — add_user_info\nguarda en session_path:\nsummary, valoration, risk_level\ntimestamp de cierre")]:::db

    FW["generate_output.py\nfarewell\nmensaje de despedida\nsegun estado: normal / exit / age"]:::module

    OUT(["bot_message = farewell_text\nis_ended = True\nsesion cerrada en MongoDB"]):::entry

    IN --> CONV
    CONV --> PB_S & PB_V & PB_R
    PB_S --> LLM_S
    PB_V --> LLM_V
    PB_R --> LLM_R
    LLM_S & LLM_V & LLM_R --> DB_SAVE
    DB_SAVE --> FW --> OUT

    classDef entry    fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef module   fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef prompt   fill:#ede7f6,stroke:#4527a0,color:#311b92
    classDef llm      fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef db       fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20

    style PARALLEL fill:#f7f3ff,stroke:#4527a0
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
