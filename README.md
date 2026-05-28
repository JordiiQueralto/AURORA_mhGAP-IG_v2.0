# Chatbot de Prevención en Salud Mental — mhGAP v2.0

Asistente conversacional de apoyo en salud mental y prevención del suicidio, basado en la **Guía de Intervención mhGAP v2.0** de la Organización Mundial de la Salud (OMS). El sistema combina una máquina de estados clínica con un modelo de lenguaje (Gemini 2.5 Flash) para ofrecer una experiencia empática, estructurada y clínicamente rigurosa, junto con un panel separado para especialistas médicos.

> **Aviso importante:** Este sistema es una herramienta de apoyo y triaje. No sustituye la atención profesional de salud mental.

---

## Tabla de contenidos

- [Descripción general](#descripción-general)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [API de usuario](#api-de-usuario-app_userpy---puerto-5000)
- [API de especialistas](#api-de-especialistas-app_specialistpy---puerto-5001)
- [Modelo de datos (MongoDB)](#modelo-de-datos-mongodb)
- [Flujo de conversación](#flujo-de-conversación)
- [Máquina de estados clínica](#máquina-de-estados-clínica)
- [Uso del LLM](#uso-del-llm)
- [Panel de especialistas](#panel-de-especialistas)
- [Generación de informes PDF](#generación-de-informes-pdf)
- [Seguridad y privacidad](#seguridad-y-privacidad)
- [Países disponibles](#países-disponibles)

---

## Descripción general

El sistema actúa como una **línea de apoyo telefónico virtual** para personas en situación de riesgo psicológico. Sus capacidades principales son:

- **Triaje automático**: clasifica al usuario mediante el LLM en `EMERGENCY`, `ASSISTANCE`, `TALK` o `MISENSE`.
- **Protocolo de suicidio (SUI)**: detecta ideación suicida y autolesión, y activa protocolos de emergencia con derivación al 112 o al 024.
- **Protocolo de depresión (DEP)**: evalúa síntomas depresivos y maníacos con preguntas estructuradas extraídas de la guía mhGAP, incluyendo cribado diferencial de trastorno bipolar.
- **Modo conversacional libre (TALK)**: acompañamiento empático sin evaluación clínica, con reevaluación automática del caso de uso cada 5 mensajes.
- **Control de seguridad transversal**: durante las fases `DEP_EVAL` y `CHAT`, un módulo de detección por regex analiza cada mensaje buscando señales de riesgo inminente y puede interrumpir el flujo para redirigir a los protocolos de emergencia.
- **Seguimiento post-emergencia (FOLLOWUP)**: en sesiones posteriores a una emergencia, el sistema verifica si el usuario contactó con los servicios de ayuda y registra el resultado.
- **Círculo de apoyo**: permite al usuario registrar contactos de confianza y un centro médico de referencia, y les envía notificaciones automáticas al activarse un protocolo de emergencia.
- **Panel médico**: los especialistas pueden consultar pacientes de su centro, añadir notas clínicas, revisar sesiones históricas, visualizar estadísticas y generar informes PDF.
- **Memoria persistente**: cada sesión se resume automáticamente por el LLM y queda almacenada en MongoDB, permitiendo al chatbot personalizar las bienvenidas y mantener continuidad entre sesiones.

---

## Arquitectura del sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                │
│   chat.html (usuario)              doctor_dashboard.html (médico)│
└──────────┬──────────────────────────────────┬────────────────────┘
           │ HTTP REST                        │ HTTP REST
           ▼                                  ▼
┌────────────────────────┐      ┌──────────────────────────────┐
│  app_user.py           │      │  app_specialist.py           │
│  Puerto 5000           │      │  Puerto 5001                 │
└──────────┬─────────────┘      └──────────────┬───────────────┘
           │                                   │
           ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│              services_user.py  /  services_specialist.py         │
│                    Lógica de negocio principal                    │
└──────┬────────────────┬──────────────────┬───────────────────────┘
       │                │                  │
       ▼                ▼                  ▼
┌──────────────┐ ┌──────────────────┐ ┌────────────────────────────┐
│ state_machine│ │ generate_output  │ │         db.py              │
│ (FSM clínica │ │ (orquestación    │ │    (MongoDB CRUD)          │
│  + control   │ │  LLM + salida)   │ └──────────┬─────────────────┘
│  seguridad)  │ └────────┬─────────┘            │
└──────────────┘          │                      ▼
       ▲                  ▼              ┌───────────────────────┐
       │         ┌──────────────────┐    │       MongoDB         │
       │         │ prompt_builder   │    │    CHATBOT_mhGAP      │
       │         │ (construcción    │    │  ├─ users             │
       │         │  de prompts)     │    │  ├─ specialists       │
       │         └────────┬─────────┘    │  ├─ medicalCenters    │
       │                  │              │  └─ notifications     │
       │                  ▼              └───────────────────────┘
       │         ┌──────────────────┐
       │         │     llm.py       │
       │         │  Gemini 2.5 Flash│
       │         └──────────────────┘
       │
┌──────┴───────────┐
│phrase_dictionary  │
│(preguntas clínicas│
│ mhGAP fijas)      │
└───────────────────┘
```

### Flujo de una petición típica (`POST /api/message`)

1. `app_user.py` recibe el mensaje y lo pasa a `services_user.process_message()`.
2. Se recupera el contexto completo de la sesión desde MongoDB (fase, estado, contadores, último output del bot).
3. Se guarda el input del usuario emparejado con la salida previa del bot en el historial de conversación.
4. `state_machine.StateMachine()` evalúa la respuesta con bancos de patrones regex y devuelve `(new_phase, new_state, variant)`.
5. `security_control()` se ejecuta como override durante `DEP_EVAL` y `CHAT` para detectar riesgo inminente.
6. `generate_output` construye el prompt y llama al LLM para generar la respuesta natural.
7. Se persiste el nuevo estado de vuelta a MongoDB y se devuelve la respuesta JSON al frontend.

---

## Estructura del repositorio

```
chatbot/
├── src/
│   ├── app_user.py              # Flask API — endpoints de usuario (puerto 5000)
│   ├── app_specialist.py        # Flask API — endpoints de especialistas (puerto 5001)
│   ├── services_user.py         # Orquestador: inicio, procesado de mensajes, sesiones
│   ├── services_specialist.py   # Orquestador: auth, pacientes, informes, estadísticas
│   ├── state_machine.py         # FSM clínica (protocolos SUI, DEP, FOLLOWUP, PROFILE)
│   ├── generate_output.py       # Generación de respuestas (LLM + lógica de salida)
│   ├── prompt_builder.py        # Construcción de prompts para el LLM
│   ├── llm.py                   # Cliente Gemini (Google GenAI SDK)
│   ├── db.py                    # Capa de acceso a datos MongoDB
│   ├── phrase_dictionary.py     # Diccionario de frases clínicas estructuradas (mhGAP)
│   ├── reportPDF.py             # Generación de informes PDF (fpdf)
│   └── seed_medical_centers.py  # Script de carga inicial de centros médicos
│
├── app/
│   ├── USER/
│   │   └── chat.html            # Interfaz de usuario (chat)
│   └── SPECIALIST/
│       └── doctor_dashboard.html # Panel de control del especialista
│
├── images/
│   ├── logo.png
│   ├── Basic/                   # Imágenes informativas generales
│   ├── SUI/
│   │   ├── Emergency/           # Material para familiares en emergencia
│   │   └── Psicoeducation/      # Guías psicoeducativas (usuario y familia, ES/CAT)
│   └── DEP/
│       └── Psicoeducation/      # Material psicoeducativo sobre depresión
│
├── diagrams/                    # Diagramas Mermaid de arquitectura y flujo
├── .env                         # Variables de entorno (no subir a repositorio)
├── CLAUDE.md                    # Instrucciones para Claude Code
└── README.md                    # Este archivo
```

---

## Requisitos previos

- **Python** 3.10+
- **MongoDB** 6.0+ ejecutándose en `localhost:27017`
- Cuenta en [Google AI Studio](https://aistudio.google.com/) con acceso a la API de Gemini

### Dependencias Python

```bash
pip install flask flask-cors pymongo google-genai fpdf python-dotenv
```

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd chatbot

# 2. Instalar dependencias
pip install flask flask-cors pymongo google-genai fpdf python-dotenv

# 3. Crear el archivo de variables de entorno (ver sección Configuración)

# 4. Cargar los centros médicos en la base de datos (primera vez)
python src/seed_medical_centers.py
```

---

## Configuración

Crea un archivo `.env` en la raíz del proyecto:

```env
GOOGLE_API_KEY=tu_api_key_de_gemini
JWT_SECRET=una_clave_secreta_para_tokens_jwt
```

| Variable | Descripción |
|---|---|
| `GOOGLE_API_KEY` | Clave de API de Google Gemini (modelo `gemini-2.5-flash`) |
| `JWT_SECRET` | Secreto para firmar los tokens JWT del panel de especialistas |

---

## Ejecución

Arranca los dos servidores Flask en terminales separadas:

```bash
# Terminal 1 — API de usuario (puerto 5000)
python src/app_user.py

# Terminal 2 — API de especialistas (puerto 5001)
python src/app_specialist.py
```

Luego abre los frontends directamente en el navegador:

- **Chat de usuario**: `app/USER/chat.html`
- **Panel médico**: `app/SPECIALIST/doctor_dashboard.html`

---

## API de usuario (`app_user.py` — Puerto 5000)

Base URL: `http://localhost:5000`

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/verify` | Registra o verifica al usuario por teléfono |
| `POST` | `/api/start` | Inicia una nueva sesión de conversación |
| `POST` | `/api/message` | Procesa un mensaje del usuario y devuelve la respuesta del bot |
| `POST` | `/api/reset` | Cierra la sesión activa, genera resumen/valoración y limpia contexto |
| `GET` | `/api/circle?telephone=...` | Obtiene los datos del círculo de apoyo del usuario |
| `POST` | `/api/circle` | Guarda o actualiza el círculo de apoyo |
| `GET` | `/api/notifications?telephone=...` | Notificaciones no leídas para un familiar |
| `POST` | `/api/notifications/read` | Marca las notificaciones como leídas |
| `GET` | `/api/medical-centers` | Lista todos los países con centros médicos disponibles |
| `GET` | `/api/medical-centers/<code>?q=...` | Centros de un país (filtrado opcional por nombre o ciudad) |
| `GET` | `/images/<path>` | Sirve imágenes psicoeducativas y de emergencia |

### Respuesta de `/api/message`

```json
{
  "bot_message": "...",
  "image_url": "http://localhost:5000/images/...",
  "ended": false,
  "emergency_112": false,
  "emergency_024": false
}
```

| Campo | Descripción |
|---|---|
| `bot_message` | Respuesta textual del bot |
| `image_url` | URL de imagen psicoeducativa (o `null`) |
| `ended` | `true` si la sesión ha finalizado |
| `emergency_112` | `true` → activar aviso de llamada al 112 (emergencias) |
| `emergency_024` | `true` → activar aviso de la línea de atención a la conducta suicida (024) |

---

## API de especialistas (`app_specialist.py` — Puerto 5001)

Base URL: `http://localhost:5001`

Los endpoints protegidos requieren la cabecera `Authorization: Bearer <token>`.

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| `POST` | `/api/doctor/register` | No | Registro de nuevo especialista |
| `POST` | `/api/doctor/login` | No | Login, devuelve token JWT |
| `PUT` | `/api/doctor/profile` | Sí | Actualizar datos del perfil |
| `GET` | `/api/doctor/patients` | Sí | Pacientes del centro del especialista |
| `PUT` | `/api/doctor/patients/<id>/notes` | Sí | Guardar nota clínica sobre un paciente |
| `GET` | `/api/doctor/patients/<id>/sessions` | Sí | Historial de sesiones del paciente |
| `GET` | `/api/doctor/patients/<id>/report` | Sí | Generar y descargar informe PDF |
| `GET` | `/api/doctor/stats` | Sí | Estadísticas del centro (riesgo, sesiones, valoraciones, cribado) |
| `GET` | `/api/doctor/countries` | No | Países disponibles |
| `GET` | `/api/medical-centers/<code>` | No | Centros de un país |

### Registro de especialista (`POST /api/doctor/register`)

```json
{
  "collegiateNumber": "28-5678",
  "firstName": "María",
  "lastName": "García López",
  "birthDate": "1985-04-12",
  "email": "maria@hospital.es",
  "password": "MiClave123",
  "countryCode": "ES",
  "centerName": "CAP Les Corts",
  "centerCity": "Barcelona"
}
```

### Estadísticas del centro (`GET /api/doctor/stats`)

Devuelve datos para los gráficos del dashboard:

| Campo | Descripción |
|---|---|
| `riskDistribution` | Distribución de niveles de riesgo (estable, bajo, medio, alto) |
| `sessionsByDay` | Sesiones por día en los últimos 30 días |
| `valorationDist` | Distribución de valoraciones (buena, regular, mala) |
| `suiDist` | Distribución de cribado de suicidio |
| `depDist` | Distribución de cribado de depresión |
| `emergencyStats` | Total de emergencias, seguimientos y outcomes |

---

## Modelo de datos (MongoDB)

Base de datos: `CHATBOT_mhGAP`

### Colección `users`

```json
{
  "telephone": "+34612345678",
  "name": "María",
  "age (years)": 34,
  "USER_TERMS": { "status": "accepted", "timestamp": "2024-06-01 10:00:00" },
  "PROFILE": {
    "call_reason": "...",
    "expectation": "...",
    "commitment": "Fully commited"
  },
  "CIRCLE": {
    "contacts": [{ "name": "Ana", "phone": "+34600000000", "relation": "madre" }],
    "medicalCenter": { "name": "CAP Florida", "city": "L'Hospitalet de Llobregat" },
    "privacy": { "shareWithHospital": true, "allowContactFamily": true }
  },
  "DEP_EVAL": {
    "1_A1_depressed_mood": true,
    "1_A2_anhedonia": true,
    "1B_1_sleep_alteration": false,
    "1B_2_appetite_weight_change": false,
    "1B_3_fatigue_energy_loss": true,
    "1B_4_concentration_decision_issues": true,
    "1B_5_low_selfworth_guilt": false,
    "1B_6_hopelessness_suicidal_ideation": false,
    "1C_functional_impairment": true,
    "2A_1_on_medication": false,
    "2A_2_physical_conditions": false,
    "2B_1_mania_episode": false
  },
  "SUI_EVAL": {
    "1_self_harm": false,
    "2_A_active_ideation": "none"
  },
  "SCREENING": { "DEP": "depression" },
  "EMERGENCY": [
    {
      "session_id": "2024-06-01 10:30:00_session",
      "trigger_hour": "10:45:00",
      "protocol_applied": "2",
      "referal": "024"
    }
  ],
  "FOLLOWUP": {
    "history": [
      {
        "emergency_date": "2024-06-01 10:30:00",
        "followup_date": "2024-06-03 14:00:00",
        "outcome": "contacted"
      }
    ],
    "last_check": "2024-06-03 14:00:00"
  },
  "checkpoint": { "phase": "DEP_EVAL", "state": "3A" },
  "ctx": {
    "phase": "...", "state": "...", "bot_output": "...",
    "session_path": "...", "j": 5, "K": 0, "variant": 0
  },
  "2024-06-01 10:30:00_session": {
    "summary": "El usuario mostró síntomas de...",
    "valoration": "REGULAR",
    "risk_level": "MODERADO",
    "conversation_history": {
      "bot_output_0": "...",
      "user_input_0": "...",
      "bot_output_1": "...",
      "user_input_1": "..."
    }
  },
  "doctorNotes": {
    "28-5678": { "note": "Paciente estable...", "updatedAt": "2024-06-05 09:00:00" }
  }
}
```

**Claves principales:**

| Clave | Descripción |
|---|---|
| `ctx` | Contexto de sesión activa: fase, estado, contador de turnos, último output |
| `checkpoint` | Punto de reanudación para evaluaciones interrumpidas |
| `DEP_EVAL` | Resultados estructurados de la evaluación de depresión |
| `SUI_EVAL` | Resultados de la evaluación de riesgo suicida |
| `SCREENING` | Cribado final: `depression`, `bipolar` u `others` |
| `EMERGENCY` | Array de instancias de emergencia registradas |
| `FOLLOWUP` | Historial de seguimiento post-emergencia |
| `<timestamp>_session` | Sesión cerrada con resumen, valoración y nivel de riesgo |
| `doctorNotes` | Notas clínicas del especialista (indexadas por número de colegiado) |

### Colección `specialists`

```json
{
  "collegiateNumber": "28-5678",
  "email": "medico@hospital.es",
  "passwordHash": "...",
  "firstName": "Joan",
  "lastName": "García",
  "birthDate": "1985-04-12",
  "centerName": "CAP Florida",
  "centerCity": "L'Hospitalet de Llobregat",
  "countryCode": "ES",
  "sessionToken": "...",
  "profile": { "especialidad": "Psiquiatría", "genero": "dr" }
}
```

### Colección `medicalCenters`

```json
{
  "countryCode": "ES",
  "countryName": "España",
  "centers": [
    { "name": "CAP Florida", "city": "L'Hospitalet de Llobregat" }
  ]
}
```

### Colección `notifications`

Notificaciones push para familiares cuando se activa un protocolo de emergencia:

```json
{
  "to_telephone": "+34600000000",
  "from_telephone": "+34612345678",
  "from_name": "María",
  "image_path_family": "images/SUI/Emergency/family_esp.png",
  "timestamp": "2024-06-01 10:45:00",
  "read": false
}
```

---

## Flujo de conversación

```
Inicio (POST /api/start)
  │
  ├─ Usuario nuevo → PRESENTATION (aceptación de términos)
  │                      │
  │                      └─ "Sí, acepto" → PRESENTATION_ASKED → PROFILE
  │                                             │
  │                           Recoge: nombre, edad, motivo, expectativa, compromiso
  │                                             │
  │                                      USE_CASE_EVAL ─────────────────────┐
  │                                             │                           │
  │                        ┌────────────────────┼──────────────┬────────────┤
  │                        ▼                    ▼              ▼            ▼
  │                    EMERGENCY           ASSISTANCE        TALK       MISENSE
  │                        │                    │              │         (cierre)
  │                   SUI_EVAL             DEP_EVAL          CHAT
  │                   (5 preguntas)         │                  │
  │                        │           Fase 1: Criterios A+B  │
  │                        │           Fase 2: Dx diferencial  │
  │                        │           Fase 3: Sustancias      │
  │                        │                │                  │
  │                   SUI_PROTOCOLS    DEP_PROTOCOLS      Reevaluación
  │                   ├─ Estado 1:     (psicoeducación)    cada 5 msgs
  │                   │  Llamar 112                            │
  │                   ├─ Estado 2:                             ▼
  │                   │  Llamar 024                      USE_CASE_EVAL
  │                   └─ Estado 3:                       (puede reclasificar)
  │                      Psicoeducación
  │                        │
  │                     FAREWELL ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
  │                  (resumen + valoración + nivel de riesgo)
  │
  ├─ Usuario existente → RESUMING → Reanuda desde checkpoint
  │
  └─ Usuario con EMERGENCY previo → FOLLOWUP
                                     (verificación post-emergencia)
```

---

## Máquina de estados clínica

La máquina de estados (`state_machine.py`) gestiona cada fase de evaluación clínica. Cada estado evalúa la respuesta del usuario contra **bancos de patrones regex** (afirmación, negación, ambigüedad) y produce una transición.

### Fases del protocolo de depresión (`DEP_EVAL`)

| Estado | Pregunta clínica (mhGAP) | Variable evaluada |
|---|---|---|
| 1A.1 | Estado de ánimo persistentemente bajo | `1_A1_depressed_mood` |
| 1A.2 | Pérdida de interés/placer (anhedonia) | `1_A2_anhedonia` |
| 1B.1 | Alteraciones del sueño | `1B_1_sleep_alteration` |
| 1B.2 | Cambios de apetito/peso | `1B_2_appetite_weight_change` |
| 1B.3 | Fatiga/pérdida de energía | `1B_3_fatigue_energy_loss` |
| 1B.4 | Dificultad de concentración/decisiones | `1B_4_concentration_decision_issues` |
| 1B.5 | Baja autoestima/culpabilidad excesiva | `1B_5_low_selfworth_guilt` |
| 1B.6 | Desesperanza/ideación suicida | `1B_6_hopelessness_suicidal_ideation` |
| 1C | Deterioro funcional | `1C_functional_impairment` |
| 2A.1–2A.2 | Medicación y condiciones físicas | Diagnóstico diferencial |
| 2B.1–2B.7 | Episodios maníacos/hipomaníacos | Cribado bipolar |
| 2C | Duelo reciente | Factor contextual |
| 2D.1–2D.5 | Síntomas psicóticos y funcionalidad | Severidad |
| 2E.1–2E.3 | Historial psiquiátrico previo | Antecedentes |
| 3A–3B | Consumo de alcohol y sustancias | Factores de riesgo |

**Lógica de decisión:**
- Si ambos criterios A (1A.1, 1A.2) son negativos → sale a `CHAT` (clasificación: `others`).
- Si al menos un A es positivo, se evalúan los criterios B.
- Si ≥2 criterios B son positivos (o ≥1 B + desesperanza) → se evalúa deterioro funcional (1C).
- Si 1C es positivo → clasificación `depression`, continúa a diagnóstico diferencial.
- El bloque 2B (7 preguntas) evalúa rasgos bipolares; si ≥3 positivos → clasificación `bipolar`.

### Fases del protocolo de suicidio (`SUI_EVAL`)

| Estado | Pregunta clínica | Evaluación |
|---|---|---|
| 1 | Autolesión actual | `1_self_harm` |
| 2A | Planes/pensamientos de hacerse daño | Ideación activa |
| 2B.1 | Pensamientos en el último mes | Ideación reciente |
| 2B.2 | Autolesión en el último año | Historial |
| 3 | Tratamiento de salud mental | Antecedentes |
| 4 | Dolor físico persistente | Factor de riesgo |
| 5 | Impacto emocional funcional | Severidad |

### Gestión de respuestas no clasificables

Cuando el usuario no responde de forma clasificable, el sistema activa **variantes**:

| Variante | Situación | Respuesta del bot |
|---|---|---|
| `ambiguity` | "No sé", "quizás" | Reformula la pregunta con otras palabras |
| `evasion` | "Cambia de tema" | Reconoce la incomodidad, reintenta suavemente |
| `refusal` | "No quiero contestar" | Respeta la negativa, ofrece alternativas |
| `hostility` | Insultos al bot | Desescala con empatía |
| `non_class` | Respuesta fuera de patrón | Repite la pregunta de forma más directa |

---

## Uso del LLM

El LLM (Gemini 2.5 Flash vía `llm.py`) se utiliza en dos modos diferenciados:

### Modo clasificación (temperature = 0.0)

Respuestas deterministas para decisiones clínicas:
- **Detección de caso de uso**: clasifica la conversación en `EMERGENCY` / `ASSISTANCE` / `TALK` / `MISENSE`.
- **Valoración de sesión**: genera `BUENA`, `REGULAR` o `MALA`.
- **Nivel de riesgo de crisis**: determina `ESTABLE`, `BAJO`, `MODERADO` o `ALTO`.

### Modo generación natural (temperature = 1.0)

Respuestas variadas y empáticas:
- **Envoltorio de preguntas clínicas**: el LLM recibe el "núcleo" fijo de la pregunta (extraído de `phrase_dictionary.py`) y lo envuelve con conectores naturales y empáticos, manteniendo el rigor clínico.
- **Bienvenida personalizada**: usa la memoria del usuario (nombre, resumen de la última sesión) para generar un saludo contextualizado.
- **Modo TALK**: conversación libre donde el LLM recibe las últimas 8 interacciones como contexto.
- **Resumen de sesión**: sintetiza la conversación completa al cerrar la sesión.

---

## Panel de especialistas

El dashboard (`doctor_dashboard.html`) ofrece:

- **Registro / Login** con número de colegiado, email y contraseña.
- **Perfil editable**: datos personales, especialidad y género.
- **Lista de pacientes** del mismo centro médico que han dado consentimiento (`shareWithHospital: true`).
- **Historial de sesiones** por paciente: resumen, valoración (BUENA / REGULAR / MALA) y nivel de riesgo (ESTABLE / BAJO / MODERADO / ALTO).
- **Notas clínicas**: el médico puede añadir y editar anotaciones privadas por paciente (indexadas por número de colegiado).
- **Estadísticas del centro**: gráficos de distribución de riesgo, sesiones por día, valoraciones, cribado SUI/DEP y estadísticas de emergencia.
- **Informe PDF**: descarga un informe completo basado en la guía mhGAP.

---

## Generación de informes PDF

El módulo `reportPDF.py` genera informes estructurados (vía `fpdf`) que incluyen:

- Datos identificativos del paciente (nombre, teléfono, edad).
- Resultados de la evaluación de suicidio (`SUI_EVAL`) con interpretación de cada indicador.
- Resultados de la evaluación de depresión (`DEP_EVAL`) y diagnóstico diferencial.
- Historial de sesiones con resúmenes y valoraciones.
- Notas clínicas del especialista.
- Emergencias registradas y seguimientos.

Los informes se descargan directamente desde el panel médico (`GET /api/doctor/patients/<id>/report`) y se generan en un fichero temporal que se elimina tras el envío.

---

## Seguridad y privacidad

- Las contraseñas de especialistas se almacenan **hasheadas** (SHA-256; en producción se recomienda migrar a bcrypt/argon2).
- La autenticación del panel médico usa **tokens de sesión** aleatorios de 64 caracteres hex.
- Los datos de pacientes solo son visibles para especialistas del **mismo centro médico** (`centerName`).
- El compartir datos con el hospital requiere **consentimiento explícito** del usuario (`shareWithHospital: true`).
- Las notificaciones a familiares requieren consentimiento adicional (`allowContactFamily: true`).
- Los protocolos de emergencia siguen las directrices de la **Guía mhGAP v2.0 de la OMS**.
- Los informes PDF se generan en ficheros temporales y se eliminan inmediatamente tras el envío.
- CORS está configurado para aceptar peticiones desde `file://` (desarrollo local) y `localhost`.

---

## Países disponibles

El sistema incluye centros médicos para:

| País | Código | Centros |
|---|---|---|
| España | ES | 44 centros (Barcelona, Madrid, Valencia, Sevilla, Bilbao...) |
| Argentina | AR | 10 centros (Buenos Aires, Rosario, Córdoba, Mendoza) |
| Costa Rica | CR | 27 centros (San José, Alajuela, Cartago, Heredia...) |
| México | MX | 8 centros (CDMX, Monterrey, Guadalajara, Puebla, Tijuana) |
| Colombia | CO | 6 centros (Bogotá, Medellín, Cali, Barranquilla) |
| Chile | CL | 5 centros (Santiago, Pudahuel, Valparaíso, Concepción) |
| Perú | PE | 5 centros (Lima, Arequipa, Cusco) |

Para añadir nuevos países o centros, edita `src/seed_medical_centers.py` y ejecuta:

```bash
python src/seed_medical_centers.py --drop
```

---

## Decisiones de diseño relevantes

- **Estado en base de datos, no en memoria**: todo el contexto de sesión (`ctx`) se persiste por petición en MongoDB, lo que permite escalabilidad horizontal y resistencia a reinicios del servidor.
- **Preguntas fijas + envoltorio LLM**: las preguntas clínicas están codificadas literalmente en `phrase_dictionary.py` (garantizando fidelidad a mhGAP), y el LLM solo añade conectores empáticos alrededor.
- **Regex para clasificación de respuestas**: la máquina de estados usa patrones regex extensivos (no el LLM) para clasificar las respuestas del usuario en los protocolos clínicos, garantizando determinismo y trazabilidad.
- **Retardos intencionales**: las llamadas a `time.sleep()` en `services_user.py` simulan una cadencia natural de conversación — no deben eliminarse.
- **Imágenes psicoeducativas bilingües**: el material visual está disponible en castellano y catalán, con versiones separadas para el usuario y para la familia.
