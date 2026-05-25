# Backend Flow — Chatbot de prevención del suicidio (mhGAP v2.0)

Diagrama de flujo del **happy path completo** de `POST /api/message`, incluyendo el flujo transversal de emergencia (`security_control` → `SUI_PROTOCOLS`) y el flujo de cierre de sesión (`_run_farewell`).

## Leyenda

| Forma | Significado |
|---|---|
| `[Rectángulo]` | Módulo / función Python |
| `{Rombo}` | Decisión condicional |
| `[(Cilindro)]` | Acceso a MongoDB |
| `{{Hexágono}}` | Llamada al LLM (Gemini API) |
| `([Pastilla])` | Entrada / salida HTTP |

---

## Diagrama

```mermaid
flowchart TD
    %% ════════════════════════════════════════════════════════════════
    %% CAPA DE PRESENTACIÓN (app.py)
    %% ════════════════════════════════════════════════════════════════
    subgraph PRESENTATION["🌐 CAPA DE PRESENTACIÓN — app.py (puerto 5000)"]
        START([POST /api/message<br/>desde frontend]):::endpoint
        APP["app.py<br/><b>handle_message</b><br/>━━━━━<br/>parsea telephone + message"]:::module
        RESP_OUT([HTTP JSON Response<br/>bot_message, image_url,<br/>ended, emergency_112,<br/>emergency_024]):::endpoint
    end

    %% ════════════════════════════════════════════════════════════════
    %% CAPA DE ORQUESTACIÓN (main_api.py)
    %% ════════════════════════════════════════════════════════════════
    subgraph ORCHESTRATION["🎯 CAPA DE ORQUESTACIÓN — main_api.py"]
        PROC["main_api.py<br/><b>process_message</b><br/>━━━━━<br/>orquestador central de sesión"]:::module
        CTX_GET[("<b>_ctx_get</b><br/>lee phase, state, variant,<br/>flags, session_path<br/>de MongoDB")]:::db
        CTX_SET[("<b>_ctx_set</b><br/>persiste nuevo estado<br/>y log de conversación<br/>en MongoDB")]:::db
        GEN_RESP["main_api.py<br/><b>_generate_response</b><br/>━━━━━<br/>despacha según new_phase"]:::module
        RUN_FW["main_api.py<br/><b>_run_farewell</b><br/>━━━━━<br/>cierra sesión + resumen + riesgo"]:::module

        D_PRES{¿phase ==<br/>PRESENTATION?}:::decision
        D_RES{¿phase ==<br/>RESUMING?}:::decision

        PRES_FLOW["Flujo PRESENTATION<br/>━━━━━<br/>onboarding + consentimiento<br/>+ verificación de edad"]:::flowblock
        RES_FLOW["Flujo RESUMING<br/>━━━━━<br/>recupera memoria de<br/>sesión anterior"]:::flowblock
    end

    %% ════════════════════════════════════════════════════════════════
    %% CAPA CLÍNICA (state_machine.py)
    %% ════════════════════════════════════════════════════════════════
    subgraph CLINICAL["🩺 CAPA CLÍNICA — state_machine.py"]
        NORM["state_machine.py<br/><b>normalize_text</b><br/>━━━━━<br/>lowercase, sin acentos,<br/>sin puntuación"]:::module
        FSM["state_machine.py<br/><b>StateMachine</b><br/>━━━━━<br/>FSM mhGAP v2.0<br/>retorna (new_phase, new_state, variant)"]:::module
        SEC["state_machine.py<br/><b>security_control</b><br/>━━━━━<br/>REGEX patrones de riesgo<br/>(autolesión, ideación activa)"]:::module
        D_SEC_GATE{¿new_phase ∈<br/>{DEP_EVAL, CHAT}?}:::decision
        D_RISK{¿REGEX<br/>detecta riesgo?}:::decision
        SUI_PROT["<b>SUI_PROTOCOLS</b><br/>━━━━━<br/>override de new_phase<br/>activa derivación 112/024"]:::emergency
    end

    %% ════════════════════════════════════════════════════════════════
    %% CAPA DE GENERACIÓN DE RESPUESTA (generate_output.py + phrase_dictionary.py)
    %% ════════════════════════════════════════════════════════════════
    subgraph RESPGEN["💡 CAPA DE GENERACIÓN — generate_output.py + phrase_dictionary.py"]
        D_USECASE{¿new_phase ==<br/>USE_CASE_EVAL?}:::decision
        D_CHAT{¿new_phase ==<br/>CHAT?}:::decision
        D_FAREWELL{¿new_phase ==<br/>FAREWELL?}:::decision

        UC_CLASS["generate_output.py<br/><b>use_case_class</b><br/>━━━━━<br/>clasifica en EMERGENCY/<br/>ASSISTANCE/TALK/MISENSE"]:::module
        TALK["generate_output.py<br/><b>talk_mode</b><br/>━━━━━<br/>oyente activo (últimos 8 turnos)"]:::module
        FAREWELL["generate_output.py<br/><b>farewell</b><br/>━━━━━<br/>despedida (normal/exit/age)"]:::module
        BOT_OUT["generate_output.py<br/><b>bot_output</b><br/>━━━━━<br/>puente conversacional + núcleo"]:::module

        D_VARIANT{¿variant != 0?}:::decision
        PHRASE_VAR["phrase_dictionary.py<br/><b>variant_dict</b>[phase][state][variant]<br/>━━━━━<br/>núcleo alternativo"]:::module
        PHRASE_BASE["phrase_dictionary.py<br/><b>bot_output_info</b>[phase][state]<br/>━━━━━<br/>núcleo clínico base mhGAP"]:::module

        SUMMARY["generate_output.py<br/><b>session_summary</b><br/><b>session_valoration</b><br/><b>session_risk</b>"]:::module
    end

    %% ════════════════════════════════════════════════════════════════
    %% CAPA LLM (prompt_builder.py + llm.py)
    %% ════════════════════════════════════════════════════════════════
    subgraph LLM_LAYER["🧠 CAPA LLM — prompt_builder.py + llm.py"]
        PB_USE["prompt_builder.py<br/><b>use_case_prompt</b>"]:::prompt
        PB_TALK["prompt_builder.py<br/><b>prompt_talk_mode</b>"]:::prompt
        PB_BOT["prompt_builder.py<br/><b>prompt_bot_output</b>"]:::prompt
        PB_PRES["prompt_builder.py<br/><b>presentation_prompt</b>"]:::prompt
        PB_SUM["prompt_builder.py<br/><b>session_summary_prompt</b><br/><b>session_valoration_prompt</b><br/><b>risk_level_prompt</b>"]:::prompt
        GEMINI{{"llm.py<br/><b>send_prompt</b><br/>━━━━━<br/>Gemini 2.5 Flash API<br/>temperature=1.0 / 0.0"}}:::llm
    end

    %% ════════════════════════════════════════════════════════════════
    %% CAPA DE PERSISTENCIA (db.py + MongoDB)
    %% ════════════════════════════════════════════════════════════════
    subgraph PERSISTENCE["💾 CAPA DE PERSISTENCIA — db.py + MongoDB"]
        DB_INFO[("db.py<br/><b>get_user_info</b>")]:::db
        DB_ADD[("db.py<br/><b>add_user_info</b>")]:::db
        DB_HIST[("db.py<br/><b>conversation_history</b>")]:::db
        DB_MEM[("db.py<br/><b>user_memory</b>")]:::db
        DB_EMERG[("db.py<br/><b>add_emergency_instance</b>")]:::db
        DB_NOTIF[("db.py<br/><b>save_notification</b>")]:::db
        MONGODB[("🗄️ <b>MongoDB</b><br/>CHATBOT_mhGAP<br/>users · specialists ·<br/>notifications · medicalCenters")]:::dbCore
    end

    %% ════════════════════════════════════════════════════════════════
    %% ARISTAS — FLUJO PRINCIPAL
    %% ════════════════════════════════════════════════════════════════

    %% Entrada
    START --> APP
    APP -->|telephone, user_message| PROC
    PROC --> CTX_GET
    CTX_GET --> MONGODB
    CTX_GET -->|"ctx = {phase, state,<br/>variant, session_path}"| D_PRES

    %% Rama PRESENTATION
    D_PRES -->|Sí| PRES_FLOW
    PRES_FLOW --> PB_PRES
    PB_PRES --> GEMINI
    PRES_FLOW -.->|datos demográficos| DB_ADD
    DB_ADD -.-> MONGODB
    PRES_FLOW --> CTX_SET

    %% Rama RESUMING
    D_PRES -->|No| D_RES
    D_RES -->|Sí| RES_FLOW
    RES_FLOW --> DB_MEM
    DB_MEM --> MONGODB
    DB_MEM -->|memoria + summary última sesión| PB_PRES
    RES_FLOW --> CTX_SET

    %% Rama NORMAL — FSM
    D_RES -->|No| NORM
    NORM -->|texto normalizado| FSM
    FSM -->|"(new_phase,<br/>new_state,<br/>variant)"| D_SEC_GATE

    %% Control de seguridad transversal
    D_SEC_GATE -->|Sí| SEC
    SEC --> D_RISK
    D_RISK -->|Sí — riesgo| SUI_PROT
    SUI_PROT --> DB_EMERG
    DB_EMERG --> MONGODB
    SUI_PROT --> DB_NOTIF
    DB_NOTIF --> MONGODB
    SUI_PROT -.->|override phase = SUI_PROTOCOLS| GEN_RESP
    D_RISK -->|No| GEN_RESP
    D_SEC_GATE -->|No| GEN_RESP

    %% Despacho en _generate_response
    GEN_RESP --> D_USECASE

    %% USE_CASE_EVAL
    D_USECASE -->|Sí| DB_HIST
    DB_HIST --> MONGODB
    DB_HIST -->|histórico de conversación| UC_CLASS
    UC_CLASS --> PB_USE
    PB_USE --> GEMINI
    GEMINI -->|"EMERGENCY /<br/>ASSISTANCE /<br/>TALK / MISENSE"| CTX_SET

    %% CHAT
    D_USECASE -->|No| D_CHAT
    D_CHAT -->|Sí| TALK
    TALK --> PB_TALK
    PB_TALK --> GEMINI
    GEMINI -->|"respuesta de oyente activo"| CTX_SET

    %% FAREWELL
    D_CHAT -->|No| D_FAREWELL
    D_FAREWELL -->|Sí| RUN_FW
    RUN_FW --> FAREWELL
    RUN_FW --> SUMMARY
    SUMMARY --> PB_SUM
    PB_SUM --> GEMINI
    GEMINI -->|"summary + valoration + risk"| DB_ADD
    DB_ADD --> MONGODB
    RUN_FW --> CTX_SET

    %% Flujo normal mhGAP (DEP_EVAL, SUI_EVAL, SUI_PROTOCOLS, DEP_PROTOCOLS...)
    D_FAREWELL -->|No| BOT_OUT
    BOT_OUT --> D_VARIANT
    D_VARIANT -->|Sí| PHRASE_VAR
    D_VARIANT -->|No| PHRASE_BASE
    PHRASE_VAR -->|núcleo| PB_BOT
    PHRASE_BASE -->|núcleo| PB_BOT
    DB_INFO --> MONGODB
    DB_INFO -.->|memoria del usuario<br/>name, age, PROFILE| PB_BOT
    PB_BOT --> GEMINI
    GEMINI -->|"puente empático<br/>+ núcleo clínico literal"| CTX_SET

    %% Persistencia final y retorno
    CTX_SET --> MONGODB
    CTX_SET -->|"bot_message, image_path,<br/>ended, emergency flags"| APP
    APP --> RESP_OUT

    %% ════════════════════════════════════════════════════════════════
    %% ESTILOS
    %% ════════════════════════════════════════════════════════════════
    classDef endpoint fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef module fill:#fff3e0,stroke:#e65100,stroke-width:1.5px,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,stroke-width:1.5px,color:#e65100
    classDef decision fill:#fce4ec,stroke:#ad1457,stroke-width:1.5px,color:#880e4f
    classDef db fill:#e8f5e9,stroke:#2e7d32,stroke-width:1.5px,color:#1b5e20
    classDef dbCore fill:#a5d6a7,stroke:#1b5e20,stroke-width:3px,color:#1b5e20
    classDef llm fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#4a148c
    classDef prompt fill:#ede7f6,stroke:#4527a0,stroke-width:1.5px,color:#311b92
    classDef emergency fill:#ffcdd2,stroke:#b71c1c,stroke-width:3px,color:#b71c1c

    %% Estilos de subgrafos
    style PRESENTATION fill:#f5faff,stroke:#1565c0,stroke-width:2px
    style ORCHESTRATION fill:#fff8f0,stroke:#e65100,stroke-width:2px
    style CLINICAL fill:#fff5f8,stroke:#ad1457,stroke-width:2px
    style RESPGEN fill:#fffef0,stroke:#f57f17,stroke-width:2px
    style LLM_LAYER fill:#f7f3ff,stroke:#4527a0,stroke-width:2px
    style PERSISTENCE fill:#f0faf0,stroke:#2e7d32,stroke-width:2px
```

---

## Notas sobre el flujo

### 1. Punto de entrada (`POST /api/message`)
`app.py:handle_message` recibe el JSON con `telephone` y `message`, valida los campos obligatorios y delega en `main_api.process_message()`.

### 2. Recuperación de contexto (`_ctx_get`)
Antes de cualquier decisión, `main_api` consulta el documento del usuario en MongoDB (colección `users`) para reconstruir el estado de sesión: fase actual de la FSM, sub-estado, variante de pregunta, e identificador de sesión activa (`YYYY-MM-DD HH:MM:SS_session`).

### 3. Tres ramas de entrada
- **PRESENTATION** → primera interacción de la sesión: onboarding, validación de edad, consentimiento informado.
- **RESUMING** → usuario que vuelve tras una sesión previa: se inyecta como contexto el `summary` de la última sesión almacenada.
- **Flujo normal** → se ejecuta la FSM clínica.

### 4. Control transversal de seguridad (`security_control`)
Durante las fases `DEP_EVAL` y `CHAT`, cada mensaje se evalúa con un conjunto de **REGEX deterministas** que detectan patrones de ideación activa, plan suicida o autolesión inminente. Si hay match → `SUI_PROTOCOLS` sobreescribe la fase devuelta por la FSM. Esta arquitectura cumple el requisito de **explicabilidad** del sistema: cada activación es trazable a una expresión concreta (justificable bajo el AI Act).

### 5. Despacho en `_generate_response`
Cuatro vías mutuamente excluyentes según `new_phase`:

| Vía | Trigger | Estrategia |
|---|---|---|
| `USE_CASE_EVAL` | clasificación inicial | LLM clasifica → `{EMERGENCY, ASSISTANCE, TALK, MISENSE}` |
| `CHAT` | usuario en modo conversación libre | LLM puro como oyente activo (últimos 8 turnos) |
| `FAREWELL` | cierre de sesión | `_run_farewell` genera `summary` + `valoration` + `risk` y los persiste |
| Resto (flujo mhGAP) | evaluación clínica | Núcleo fijo desde `phrase_dictionary` + puente generado por LLM |

### 6. Arquitectura híbrida (núcleo + puente)
En el flujo clínico, el **núcleo** de la pregunta es **literal e inmutable** (validado por mhGAP v2.0). El LLM solo genera la **introducción de transición** (≤ 20 palabras) para suavizar el cambio de tema. Esto garantiza:
- Seguridad clínica: las preguntas sensibles no las redacta el LLM.
- Fluidez conversacional: el LLM aporta naturalidad sin tocar contenido validado.

### 7. Variantes (`variant_dict` vs `bot_output_info`)
Cuando la FSM detecta una respuesta ambigua o necesita reformular, devuelve `variant != 0` → se usa una versión alternativa del núcleo desde `variant_dict[phase][state][variant]`.

### 8. Persistencia final (`_ctx_set`)
Cada turno termina con un `_ctx_set` que actualiza el documento del usuario en MongoDB: nuevo estado de la FSM, nuevo par `user_input_N` / `bot_output_N` dentro de `conversation_history`, y flags (`emergency_112`, `emergency_024`, `ended`) que `app.py` devuelve al frontend.

---

## Cómo exportar el diagrama

Para generar un SVG/PNG de alta resolución para incluir en el PDF del TFG:

```bash
# Instala mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Exporta a SVG (recomendado para LaTeX/Word)
mmdc -i backend_flow_diagram.md -o backend_flow.svg

# Exporta a PNG de alta resolución
mmdc -i backend_flow_diagram.md -o backend_flow.png -w 3000 -H 4000
```

O bien, copia el bloque `mermaid` en:
- **Mermaid Live Editor**: https://mermaid.live → exporta SVG/PNG directamente.
- **VS Code**: extensión *Markdown Preview Mermaid Support*.
- **Notion / GitHub / GitLab**: renderizan Mermaid de forma nativa.
