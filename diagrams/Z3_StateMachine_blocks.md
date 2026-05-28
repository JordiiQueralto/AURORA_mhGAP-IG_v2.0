# Block diagrams of the `StateMachine()` function

This document presents three complementary block diagrams that capture the behavior of the `StateMachine()` function in `state_machine.py` — the **clinical brain** of the mhGAP chatbot. Because the function is large (roughly fifty states distributed across five phases) and the same internal pattern repeats inside every state, a single diagram would either lose detail or become unreadable. The chosen decomposition therefore moves from the most abstract view (what the function does as a whole) to the most concrete (how individual decisions are made), with each figure focusing on one level of granularity.

- **Figure 1** — General behavior: signature, normalization, phase dispatcher, and output.
- **Figure 2** — Canonical decision pattern per state: how each transition is determined.
- **Figure 3** — Internal cascade of `variant_search()`.

A summary table at the end consolidates the meaning of every `variant` value and how it is consumed downstream by `phrase_dictionary.py`.

---

## Figure 1 — General behavior of `StateMachine()`

Captures the role of the function as a **deterministic dispatcher**: it receives the session context tuple from `services_user.py`, normalizes the user input, identifies the current phase, and delegates execution to one of five internal sub-blocks. The output is always the triple `(new_phase, new_state, variant)` — never a string of natural language. This separation is deliberate: by isolating clinical decisions in a function that produces only structured data, the system guarantees that every transition is auditable and reproducible, leaving the unpredictability of natural language confined to the downstream generation layer.

The function begins with `_normalize_text()`, which lowercases the input, strips accents, removes punctuation, and collapses whitespace. This normalization is essential because the REGEX patterns used by downstream blocks would otherwise fail on trivial orthographic variations ("Sí, claro", "si claro!", "SI") that all express the same semantic content. After normalization, a single switch on `phase` dispatches the execution to the corresponding block. Each block is responsible for advancing through its own internal sequence of states, applying the canonical decision pattern described in Figure 2.

```mermaid
flowchart TD

    START(( )):::circle
    FINISH(( )):::circle

    START -->|"telephone, phase,<br/>state, user_input"| NORM

    subgraph FSM_CORE[" "]

        NORM["_normalize_text()"]:::module

        DISPATCH{phase == ?}:::decision

        PROFILE["<b>PROFILE block</b><br/>───────────────────<br/>Clinical onboarding<br/>· · · · · · · · · ·<br/>name → age → reason →<br/>expectation → commitment"]:::flowblock

        CHAT["<b>CHAT block</b><br/>───────────────<br/>Passthrough"]:::flowblock

        DEP["<b>DEP_EVAL block</b><br/>───────────────<br/>mhGAP depression screening<br/>· · · · · · · · · ·<br/>1A.x → 1B.x → 1C →<br/>2A.x → 2B.x → 2C →<br/>2D.x → 2E.x → 3A → 3B"]:::flowblock

        SUI["<b>SUI_EVAL block</b><br/>───────────────<br/>mhGAP suicide risk\nscreening<br/>· · · · · · · · · ·<br/>1 → 2A → 2B.1 → 2B.2 →<br/>3 → 4 → 5"]:::flowblock

        FU["<b>FOLLOWUP block</b><br/>───────────────<br/>Post-emergency follow-up<br/>· · · · · · · · · ·<br/>emergency_followup →<br/>non_contact_reason →<br/>second_try → post_help →<br/>continuity_plan → family"]:::flowblock

        BOTTOM(( )):::junction

        NORM -->|"n_user_input"| DISPATCH

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

    style FSM_CORE fill:#fff5f8,stroke:#ad1457,stroke-width:2px,stroke-dasharray: 6 3
```

The five blocks correspond to the five phases of the conversation lifecycle. **PROFILE** is the clinical onboarding sequence — name, age, reason for contacting, expectation, and commitment to screening — and acts as a gate to the rest of the system: users under 18 are redirected to `FAREWELL`, while users who decline screening are redirected to `USE_CASE_EVAL`. **CHAT** is a pure passthrough: when the conversation is in free-talk mode, the FSM has no decision to make and simply returns the same phase and state, letting the LLM handle the conversation downstream. **DEP_EVAL** is the most complex block, implementing the mhGAP depression screening protocol with three sections and roughly thirty states. **SUI_EVAL** handles the structured suicide risk evaluation. **FOLLOWUP** manages the post-emergency check-ins that occur in subsequent sessions after a suicide-risk emergency has been registered.

---

## Figure 2 — Canonical decision pattern per state

This diagram captures the behavior that repeats, with minor variations, in **every state** within the `PROFILE`, `DEP_EVAL`, `SUI_EVAL`, and `FOLLOWUP` blocks. It abstracts the logic of REGEX pattern evaluation, MongoDB persistence, and transition decision into a single reusable template.

The pattern is structured as a **two-stage cascade**: first, the user input is tested against the negative pattern set (`PATTERNS_NO`), and only if that fails is it tested against the positive set (`PATTERNS_YES`). The order matters because negations in Spanish often contain words that would also match affirmation patterns (for example "no me siento bien" contains "bien" which could match a positive pattern), so testing `NO` first prevents false positives. If neither matcher succeeds, the system falls back to `_variant_search()` to classify the type of unexpected response.

It is critical to note that **persistence occurs only when a positive match is found** (either YES or NO branch). If the response is ambiguous, evasive, or unclassifiable, no clinical data is saved and the state remains unchanged so that the next turn can reformulate the question. This design guarantees that the MongoDB record reflects only **interpreted** answers, never assumptions made by the system.

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

> **Note** — Some specific states (for example `PROFILE.name`, `PROFILE.age`, `FOLLOWUP.non_contact_reason`) use a single specialized pattern block instead of the classical `YES` / `NO` pair, but the underlying logic is identical: if a match exists, persist and advance; otherwise, call `variant_search()` (or assign `variant = "repeat"` in the simplest cases) and keep the current state.

The dual persistence on positive matches — saving the clinical data via `add_user_info()` and the FSM checkpoint via `save_flow()` — is what enables **session resumption**. If the user disconnects mid-screening, the next time they open the conversation the orchestrator (Figure 2 of the architecture document) will retrieve the checkpoint and continue exactly where they left off, without re-asking questions that have already been answered. This is one of the most important guarantees of the design: clinical progress is never lost.

---

## Figure 3 — Internal cascade of `variant_search()`

This auxiliary function is invoked **only when the main patterns of the current state have failed to match**, that is, when the user's response could not be interpreted as a clear affirmation or negation. Its role is to **classify the type of unexpected response** into one of five categories, so that the rest of the system — specifically `phrase_dictionary.variant_dict()` — can choose a follow-up message appropriate to the context. A user who answered "I don't know" needs a gentler reformulation, while a user who insulted the bot needs a de-escalation; the variant label is what allows the response generator to make this distinction without any LLM call.

Internally the function is a **strict cascade**: the four pattern lists are evaluated in order of clinical priority (ambiguity first, hostility last), and the function returns as soon as it finds the first match. The order is not arbitrary — it follows from the observation that the categories are not mutually exclusive at the surface level (an evasive answer may also be ambiguous), so the priority must reflect what the system should prioritize attending to. Ambiguity is most common and least concerning; hostility is rarest but most disruptive, so it is checked last only as a final filter before the catchall.

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

The five output categories are visually color-coded by severity. **Ambiguity** (blue) covers vague answers such as "no sé", "tal vez", "depende"; the system treats these as honest uncertainty and reformulates the question in simpler terms. **Evasion** (green) catches topic shifts or minimization, where the user is steering the conversation away from the clinical question; the bot redirects amicably without confronting the deflection. **Refusal** (orange) is an explicit unwillingness to answer ("no quiero hablar de eso"); the bot validates the refusal before gently reattempting. **Hostility** (red) covers insults or distrust directed at the bot itself; the bot de-escalates rather than confronting. The catchall **non_class** (gray) is the default returned when nothing matched, and triggers a neutral reformulation.

---

## Summary table — `variant` labels and downstream consumption

The `variant` field is the **bridge** between the deterministic FSM and the response generation layer. The FSM produces it as one of seven possible values; `phrase_dictionary.py` consumes it to decide which clinical nucleus or alternative phrasing to retrieve. The table below consolidates the meaning of each value, where it originates, and what response strategy it triggers.

| Label | Origin | Clinical meaning | Downstream consumption |
|---|---|---|---|
| `0` | Default after successful match | Response interpreted; FSM advances | `phrase_dictionary.bot_output_info()` → base clinical nucleus |
| `"repeat"` | Direct assignment in simple states | Main matcher failed | `phrase_dictionary.bot_output_info()` → same question repeated |
| `"ambiguity"` | `variant_search()` | Vagueness, doubt, "I don't know" | `phrase_dictionary.variant_dict()` → simpler reformulation |
| `"evasion"` | `variant_search()` | Topic shift or minimization | `phrase_dictionary.variant_dict()` → gentle redirection |
| `"refusal"` | `variant_search()` | Explicit refusal to answer | `phrase_dictionary.variant_dict()` → validation + retry |
| `"hostility"` | `variant_search()` | Insult or distrust toward the bot | `phrase_dictionary.variant_dict()` → de-escalation |
| `"non_class"` | `variant_search()` (default) | Does not match any known pattern | `phrase_dictionary.variant_dict()` → neutral reformulation |

This design ensures that **no user response is ever ignored**: even when the answer is unintelligible to the FSM, the system produces an appropriate clinical response rather than failing silently or generating a generic LLM hallucination. The combination of deterministic classification (`variant`) and templated phrasing (`phrase_dictionary`) guarantees that every bot turn is clinically grounded, regardless of how unexpected the user's input was.

---

## How to export to image

```bash
npm install -g @mermaid-js/mermaid-cli

# One SVG per figure
mmdc -i StateMachine_blocks.md -o fig1_overview.svg
mmdc -i StateMachine_blocks.md -o fig2_state_pattern.svg
mmdc -i StateMachine_blocks.md -o fig3_variant_search.svg

# High-resolution PNG
mmdc -i StateMachine_blocks.md -o fig1_overview.png -w 2400
```

Alternatively, paste each block into **https://mermaid.live** for individual preview and export.