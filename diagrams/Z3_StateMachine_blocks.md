# Diagramas de bloques de la función `StateMachine()`

Este documento contiene tres diagramas de bloques complementarios que capturan el comportamiento de la función `StateMachine()` del módulo `state_machine.py`, desde la vista de conjunto hasta el patrón interno que se replica en cada uno de sus estados.

- **Figura 1** — Comportamiento general: firma, normalización, dispatcher de fases y salida.
- **Figura 2** — Patrón canónico de decisión por estado: cómo se determina cada transición.
- **Figura 3** — Cascada interna de `variant_search()`.

---

## Figura 1 — Comportamiento general de `StateMachine()`

Captura el rol de la función como **dispatcher determinista**: recibe la tupla de contexto desde `services_user.py`, normaliza el texto, identifica la fase actual y delega a uno de los cinco sub-bloques internos. La salida es siempre la tripleta `(new_phase, new_state, variant)`, sin generación de texto.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"telephone, phase,<br/>state, user_input"| NORM

    subgraph FSM_CORE[" "]

        NORM["<b>state_machine.py</b><br/>───────────────<br/>normalize_text(user_input)<br/>· · · · · · · · · ·<br/>→ lowercase<br/>→ strip_accents<br/>→ remove punctuation<br/>→ collapse whitespace"]:::module

        INIT["<b>Inicialización</b><br/>· · · · · · · · · ·<br/>variant = 0"]:::flowblock

        DISPATCH{<b>Dispatcher</b><br/>if / elif<br/>phase == ?}:::decision

        PROFILE["<b>Bloque PROFILE</b><br/>───────────────<br/>Onboarding clínico<br/>· · · · · · · · · ·<br/>name → age → reason →<br/>expectation → commitment"]:::flowblock

        CHAT["<b>Bloque CHAT</b><br/>───────────────<br/>Passthrough<br/>· · · · · · · · · ·<br/>return (phase, state, 0)<br/>(la FSM no decide)"]:::flowblock

        DEP["<b>Bloque DEP_EVAL</b><br/>───────────────<br/>Cribado depresión mhGAP<br/>· · · · · · · · · ·<br/>1A.* → 1B.* → 1C →<br/>2A.* → 2B.* → 2C →<br/>2D.* → 2E.* → 3A / 3B"]:::flowblock

        SUI["<b>Bloque SUI_EVAL</b><br/>───────────────<br/>Riesgo suicida estructurado<br/>· · · · · · · · · ·<br/>1 → 2A → 2B.1 → 2B.2 →<br/>3 → 4 → 5"]:::flowblock

        FU["<b>Bloque FOLLOWUP</b><br/>───────────────<br/>Seguimiento post-emergencia<br/>· · · · · · · · · ·<br/>emergency_followup →<br/>non_contact_reason →<br/>second_try → post_help →<br/>continuity_plan → family"]:::flowblock

        BOTTOM(( )):::junction

        NORM -->|"n_user_input"| INIT
        INIT --> DISPATCH

        DISPATCH -->|"'PROFILE'"| PROFILE
        DISPATCH -->|"'CHAT'"| CHAT
        DISPATCH -->|"'DEP_EVAL'"| DEP
        DISPATCH -->|"'SUI_EVAL'"| SUI
        DISPATCH -->|"'FOLLOWUP'"| FU

        PROFILE --> BOTTOM
        CHAT --> BOTTOM
        DEP --> BOTTOM
        SUI --> BOTTOM
        FU --> BOTTOM

    end

    BOTTOM -->|"(new_phase, new_state, variant)"| FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f

    style FSM_CORE fill:#fff8f0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 6 3
```

---

## Figura 2 — Patrón canónico de decisión por estado

Diagrama del comportamiento que se repite, con pequeñas variantes, en **cada uno de los estados** dentro de los bloques `PROFILE`, `DEP_EVAL`, `SUI_EVAL` y `FOLLOWUP`. Captura la lógica de evaluación de patrones REGEX, persistencia en MongoDB y decisión de transición.

Es importante notar que la persistencia ocurre **solo cuando hay match positivo** (es decir, cuando la respuesta del usuario se ha podido interpretar). Si la respuesta es ambigua, evasiva o no clasificable, no se guarda ningún dato clínico y el estado se mantiene para reformular la pregunta.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"(n_user_input, phase, state)"| LOCAL

    subgraph STATE_LOGIC[" "]

        LOCAL["<b>Pattern definition (depends on each state)</b><br/> ──────────────────────<br/>PATTERNS_YES = [ regex, ... ]<br/>PATTERNS_NO  = [ regex, ... ]<br/>.<br/>.<br/>.<br/>PATTERNS_*"]:::flowblock

        PS_NO["_pattern_search()"]:::module
        D_NO{match<br/>NO ?}:::decision

        PS_YES["_pattern_search()"]:::module
        D_YES{match<br/>YES ?}:::decision

        VS[["<b>_variant_search()</b>"]]:::module

        SAVE_YES["<b>db.py</b><br/>───────────────<br/>add_user_info()<br/>· · · · · · · · · ·<br/>→ clinical_key = True<br/><br/>save_flow()<br/>· · · · · · · · · ·<br/>→ checkpoint.phase<br/>→ checkpoint.state"]:::dbmod

        SAVE_NO["<b>db.py</b><br/>───────────────<br/>add_user_info()<br/>· · · · · · · · · ·<br/>→ clinical_key = False<br/><br/>save_flow()<br/>· · · · · · · · · ·<br/>→ checkpoint.phase<br/>→ checkpoint.state"]:::dbmod

        OUT_YES["new_phase = phase_yes<br/>new_state = state_yes"]:::flowblock

        OUT_NO["new_phase = phase_no<br/>new_state = state_no"]:::flowblock

        OUT_STAY["new_phase = phase<br/>new_state = state<br/>variant"]:::flowblock

        MONGO[("MongoDB<br/>CHATBOT_mhGAP")]:::db

        BOTTOM(( )):::junction

        LOCAL --> PS_NO --> D_NO
        D_NO -->|True| OUT_NO --> SAVE_NO
        D_NO -->|False| PS_YES --> D_YES
        D_YES -->|True| OUT_YES --> SAVE_YES
        D_YES -->|False| VS --> OUT_STAY --> BOTTOM
        SAVE_YES --> BOTTOM
        SAVE_NO --> BOTTOM

        SAVE_YES -.-> MONGO
        SAVE_NO -.-> MONGO

    end

    BOTTOM -->|"(new_phase, new_state, variant)"| FINISH

    classDef circle    fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction  fill:#000000,stroke:#000000,color:#000000
    classDef module    fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision  fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef dbmod     fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef db        fill:#c8e6c9,stroke:#1b5e20,color:#1b5e20

    style STATE_LOGIC fill:#fff5f8,stroke:#ad1457,stroke-width:2px,stroke-dasharray: 6 3
```

> **Nota** — Algunos estados específicos (por ejemplo `PROFILE.name`, `PROFILE.age`, `FOLLOWUP.non_contact_reason`) usan un único bloque de patrones específico en lugar del par `YES`/`NO` clásico, pero la lógica subyacente es idéntica: si hay match, se persiste y se avanza; si no, se llama a `variant_search()` (o se devuelve `variant = "repeat"` en los casos más simples) y se mantiene el estado.

---

## Figura 3 — Cascada interna de `variant_search()`

Esta función auxiliar se invoca **únicamente cuando los patrones principales del estado actual no han dado match**, es decir, cuando la respuesta del usuario no se ha podido interpretar como afirmación o negación clara. Su rol es **clasificar el tipo de respuesta no esperada** en una de cinco categorías, para que el resto del sistema (en particular `phrase_dictionary.variant_dict()`) pueda elegir una repregunta adecuada al contexto.

Internamente es una **cascada estricta**: las cuatro listas de patrones se evalúan en orden de prioridad clínica (ambigüedad primero, hostilidad al final) y la función retorna en cuanto encuentra el primer match. Si ninguna lista coincide, devuelve `non_class` como categoría por defecto.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"n_user_input"| DEFS

    subgraph VARIANT_SEARCH[" "]

        DEFS["<b>Pattern definition (depends on each state)</b><br/>────────────────────────────<br/>PATTERNS_AMBIGUITY = [regex,...]<br/>PATTERNS_EVASION = [regex,...]<br/>PATTERNS_DIRECT_REFUSAL = [regex,...]<br/>PATTERNS_HOSTILITY = [regex,...]"]:::flowblock

        PS1["_pattern_search()"]:::module

        D1{AMBIGUITY\nmatch ?}:::decision

        PS2["_pattern_search()"]:::module

        D2{EVASION\nmatch ?}:::decision

        PS3["_pattern_search()"]:::module

        D3{DIRECT REFUSAL\nmatch ?}:::decision

        PS4["_pattern_search()"]:::module

        D4{HOSTILITY\nmatch ?}:::decision

        R1["<b>variant = 'ambiguity'</b>"]:::variant_amb

        R2["<b>variant = 'evasion'"]:::variant_eva

        R3["<b>variant = 'refusal'"]:::variant_ref

        R4["<b>variant = 'hostility'"]:::variant_hos

        R5["<b>variant = 'non_class'"]:::variant_def

        BOTTOM(( )):::junction

        DEFS --> PS1 --> D1
        D1 -->|True| R1 --> BOTTOM
        D1 -->|False| PS2 --> D2
        D2 -->|True| R2 --> BOTTOM
        D2 -->|False| PS3 --> D3
        D3 -->|True| R3 --> BOTTOM
        D3 -->|False| PS4 --> D4
        D4 -->|True| R4 --> BOTTOM
        D4 -->|False| R5 --> BOTTOM

    end

    BOTTOM -->|"variant"| FINISH

    classDef circle      fill:#ffffff,stroke:#9370db,stroke-width:2px,color:#ffffff
    classDef junction    fill:#000000,stroke:#000000,color:#000000
    classDef module      fill:#fff3e0,stroke:#e65100,color:#bf360c
    classDef flowblock   fill:#fffde7,stroke:#f57f17,color:#e65100
    classDef decision    fill:#fce4ec,stroke:#ad1457,color:#880e4f
    classDef variant_amb fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef variant_eva fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef variant_ref fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef variant_hos fill:#ffcdd2,stroke:#b71c1c,color:#b71c1c
    classDef variant_def fill:#f5f5f5,stroke:#616161,color:#212121

    style VARIANT_SEARCH fill:#fff5f8,stroke:#ad1457,stroke-width:2px,stroke-dasharray: 6 3
```

---

## Tabla resumen — Etiquetas de `variant` y su uso aguas abajo

| Etiqueta | Origen | Significado clínico | Consumo posterior |
|---|---|---|---|
| `0` | Default tras match exitoso | Respuesta interpretada, la FSM avanza | `phrase_dictionary.bot_output_info()` → núcleo clínico base |
| `"repeat"` | Asignación directa en estados simples | Matcher principal sin coincidencia | `phrase_dictionary.bot_output_info()` → se repite la misma pregunta |
| `"ambiguity"` | `variant_search()` | Vaguedad, duda, "no sé" | `phrase_dictionary.variant_dict()` → reformulación más simple |
| `"evasion"` | `variant_search()` | Cambio de tema o minimización | `phrase_dictionary.variant_dict()` → redirección amable |
| `"refusal"` | `variant_search()` | Negativa explícita a responder | `phrase_dictionary.variant_dict()` → validación + reintento |
| `"hostility"` | `variant_search()` | Insulto o desconfianza hacia el bot | `phrase_dictionary.variant_dict()` → desescalada |
| `"non_class"` | `variant_search()` (default) | No encaja en ningún patrón conocido | `phrase_dictionary.variant_dict()` → repregunta neutra |

---

## Cómo exportar a imagen

```bash
npm install -g @mermaid-js/mermaid-cli

# Un SVG por figura
mmdc -i StateMachine_blocks.md -o fig1_overview.svg
mmdc -i StateMachine_blocks.md -o fig2_state_pattern.svg
mmdc -i StateMachine_blocks.md -o fig3_variant_search.svg

# PNG de alta resolución
mmdc -i StateMachine_blocks.md -o fig1_overview.png -w 2400
```

O pega cada bloque en **https://mermaid.live** para previsualizar individualmente.
