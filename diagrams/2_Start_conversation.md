mermaid```
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