```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"telephone, user_input"| CTX_GET

    subgraph PROCESS_MSG[" "]

        CTX_GET["<b>db.py</b><br/>────────────────────────────────────────<br/>_ctx_get()<br/>→ session_path, last_bot_output, j, k, phase, state, variant"]:::dbmod
        HIST["<b>db.py</b><br/>─────────────<br/>add_user_info()"]:::dbmod

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