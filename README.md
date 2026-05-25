# 🧠 Chatbot de Prevención en Salud Mental — mhGAP

Asistente conversacional de apoyo en salud mental y prevención del suicidio, basado en la **Guía de Intervención mhGAP v2.0** de la OMS. El sistema combina una máquina de estados clínica con un LLM (Gemini) para ofrecer una experiencia empática, estructurada y segura, con un panel separado para especialistas médicos.

---

## 📋 Tabla de contenidos

- [Descripción general](#descripción-general)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [API de usuario (`app.py`)](#api-de-usuario-apppy)
- [API de especialistas (`app_sp.py`)](#api-de-especialistas-app_sppy)
- [Modelo de datos (MongoDB)](#modelo-de-datos-mongodb)
- [Flujo de conversación](#flujo-de-conversación)
- [Panel de especialistas](#panel-de-especialistas)
- [Generación de informes PDF](#generación-de-informes-pdf)

---

## Descripción general

El sistema actúa como una **línea de apoyo telefónico** virtual para personas en situación de riesgo psicológico. Sus capacidades principales son:

- **Triaje automático**: clasifica al usuario en `EMERGENCY`, `ASSISTANCE`, `TALK` o `MISENSE` usando el LLM.
- **Protocolo de suicidio (SUI)**: detecta ideación suicida y activa protocolos de emergencia (112 / 024).
- **Protocolo de depresión (DEP)**: evalúa síntomas depresivos con preguntas estructuradas.
- **Modo conversacional libre (TALK)**: acompañamiento empático sin evaluación clínica.
- **Círculo de apoyo**: permite al usuario registrar contactos de confianza y un centro médico de referencia.
- **Panel médico**: los especialistas pueden consultar pacientes de su centro, añadir notas clínicas y generar informes PDF.
- **Memoria persistente**: cada sesión se resume automáticamente y queda almacenada en MongoDB para futuras interacciones.

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│   chat_13.html (usuario)   doctor_dashboard_14.html (médico)│
└──────────────┬──────────────────────────┬───────────────────┘
               │ HTTP REST                │ HTTP REST
               ▼                          ▼
┌─────────────────────┐      ┌────────────────────────┐
│  app.py  (port 5000)│      │ app_sp.py  (port 5001) │
│  API de usuario     │      │ API de especialistas   │
└────────┬────────────┘      └──────────┬─────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────┐
│                    main_api.py / main_api_sp.py      │
│              Lógica de negocio principal             │
└────────┬──────────────────┬──────────────────────────┘
         │                  │
         ▼                  ▼
┌──────────────┐   ┌──────────────────┐   ┌────────────────┐
│ state_machine│   │ generate_output  │   │   db.py        │
│  (flujos     │   │  (LLM + prompts) │   │ (MongoDB CRUD) │
│   clínicos)  │   └────────┬─────────┘   └───────┬────────┘
└──────────────┘            │                      │
                            ▼                      ▼
                   ┌──────────────┐    ┌───────────────────────┐
                   │    llm.py    │    │  MongoDB               │
                   │  Gemini API  │    │  CHATBOT_mhGAP         │
                   └──────────────┘    │  ├─ users              │
                                       │  ├─ specialists        │
                   ┌──────────────┐    │  ├─ medicalCenters     │
                   │prompt_builder│    │  └─ notifications      │
                   │  (prompts)   │    └───────────────────────┘
                   └──────────────┘
```

---

## Estructura del repositorio

```
.
├── app.py                  # Flask API — endpoints de usuario (puerto 5000)
├── app_sp.py               # Flask API — endpoints de especialistas (puerto 5001)
├── main_api.py             # Orquestador principal: inicio, procesado de mensajes, sesiones
├── main_api_sp.py          # Orquestador para especialistas: auth, pacientes, informes
├── state_machine.py        # Máquina de estados clínica (protocolos SUI, DEP, etc.)
├── generate_output.py      # Generación de respuestas del bot (LLM + lógica de salida)
├── prompt_builder.py       # Construcción de prompts para el LLM
├── llm.py                  # Cliente Gemini (Google GenAI SDK)
├── db.py                   # Capa de acceso a datos MongoDB
├── phrase_dictionary.py    # Diccionario de frases clínicas estructuradas
├── reportPDF.py            # Generación de informes PDF detallados (para médicos)
├── create_inform.py        # Script auxiliar de generación de informe por ID de usuario
├── seed_medical_centers.py # Script de carga inicial de centros médicos en MongoDB
├── chat_13.html            # Interfaz de usuario (chat)
└── doctor_dashboard_14.html # Panel de control del especialista
```

---

## Requisitos previos

- Python 3.10+
- MongoDB 6.0+ corriendo localmente en `localhost:27017`
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
cd <nombre-del-repositorio>

# 2. Instalar dependencias
pip install flask flask-cors pymongo google-genai fpdf python-dotenv

# 3. Cargar los centros médicos en la base de datos
python seed_medical_centers.py

# 4. Crear el archivo de variables de entorno (ver sección Configuración)
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
# Terminal 1 — API de usuario
python app.py

# Terminal 2 — API de especialistas
python app_sp.py
```

Luego abre los frontends directamente en el navegador:

- **Chat de usuario**: `chat_13.html`
- **Panel médico**: `doctor_dashboard_14.html`

---

## API de usuario (`app.py`)

Base URL: `http://localhost:5000`

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/verify` | Registra o verifica al usuario por teléfono |
| `POST` | `/api/start` | Inicia una nueva sesión de conversación |
| `POST` | `/api/message` | Procesa un mensaje del usuario y devuelve la respuesta del bot |
| `POST` | `/api/reset` | Cierra la sesión activa y guarda el resumen |
| `GET` | `/api/circle` | Obtiene los datos del círculo de apoyo del usuario |
| `POST` | `/api/circle` | Guarda o actualiza el círculo de apoyo |
| `GET` | `/api/notifications` | Devuelve notificaciones no leídas para un familiar |
| `POST` | `/api/notifications/read` | Marca las notificaciones como leídas |
| `GET` | `/api/medical-centers` | Lista todos los países con centros médicos disponibles |
| `GET` | `/api/medical-centers/<code>` | Centros de un país específico (filtrado opcional con `?q=`) |

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

Cuando `emergency_112: true`, el frontend debe mostrar el aviso de llamada al 112. Cuando `emergency_024: true`, se muestra el aviso de la línea de atención a la conducta suicida (024).

---

## API de especialistas (`app_sp.py`)

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
| `GET` | `/api/doctor/countries` | No | Países disponibles |
| `GET` | `/api/medical-centers/<code>` | No | Centros de un país |

---

## Modelo de datos (MongoDB)

Base de datos: `CHATBOT_mhGAP`

### Colección `users`

```json
{
  "telephone": "+34612345678",
  "name": "María",
  "age (years)": 34,
  "USER_TERMS": { "status": "accepted", "timestamp": "..." },
  "PROFILE": {},
  "CIRCLE": {
    "contacts": [...],
    "medicalCenter": { "name": "CAP Florida", "city": "L'Hospitalet" },
    "privacy": { "shareWithHospital": true }
  },
  "DEP_EVAL": {},
  "SUI_EVAL": { "1_self_harm": false, "2_A_active_ideation": "none" },
  "SCREENING": {},
  "EMERGENCY": [],
  "FOLLOWUP": { "history": [], "last_check": "" },
  "checkpoint": { "phase": "DEP_PROTOCOLS", "state": "3" },
  "ctx": { "phase": "...", "state": "...", "bot_output": "...", "session_path": "..." },
  "2024-06-01 10:30:00_session": {
    "summary": "El usuario...",
    "valoration": "BUENA",
    "risk_level": "BAJO",
    "conversation_history": {
      "bot_output_0": "...",
      "user_input_0": "..."
    }
  },
  "doctorNotes": {
    "123456": { "note": "...", "updatedAt": "..." }
  }
}
```

### Colección `specialists`

```json
{
  "collegiateNumber": "123456",
  "email": "medico@hospital.es",
  "passwordHash": "...",
  "firstName": "Joan",
  "lastName": "García",
  "centerName": "CAP Florida",
  "centerCity": "L'Hospitalet de Llobregat",
  "countryCode": "ES",
  "profile": {}
}
```

### Colección `medicalCenters`

```json
{
  "countryCode": "ES",
  "countryName": "España",
  "centers": [
    { "name": "CAP Florida", "city": "L'Hospitalet de Llobregat" },
    ...
  ]
}
```

### Colección `notifications`

Notificaciones push para familiares cuando se activa un protocolo de emergencia.

---

## Flujo de conversación

```
Inicio
  │
  ├─ Usuario nuevo → PRESENTATION (aceptación de términos)
  │                      │
  │                      └─ acepta → recoge nombre, edad... → DETERMINA CASO DE USO
  │
  ├─ Usuario existente → RESUMING → DETERMINA CASO DE USO
  │                                     │
  │                        ┌────────────┼─────────────┬────────────┐
  │                        ▼            ▼             ▼            ▼
  │                    EMERGENCY   ASSISTANCE       TALK       MISENSE
  │                        │            │             │
  │                  Protocolo SUI  Protocolo DEP  Modo libre
  │                  (112 / 024)    (evaluación    (acompañamiento
  │                                 depresión)      empático)
  │                                      │
  │                                  FAREWELL
  │                               (resumen + valoración)
  │
  ├─ Usuario existente → RESUMING → Continuar DEP_EVAL
  │
  └─ Usuario existente (EMERGENCY activado previamente) → SEGUIMIENTO
                                 
```

La máquina de estados (`state_machine.py`) gestiona cada fase con sus preguntas extraídas del diccionario clínico (`phrase_dictionary.py`). El LLM se usa para generar conectores naturales que envuelven las preguntas fijas, manteniendo el rigor clínico con un tono conversacional.

---

## Panel de especialistas

El dashboard (`doctor_dashboard_14.html`) ofrece:

- **Registro / Login** con número de colegiado y contraseña.
- **Lista de pacientes** del mismo centro médico que han dado consentimiento (`shareWithHospital: true`).
- **Historial de sesiones** por paciente: resumen, valoración (BUENA / REGULAR / MALA) y nivel de riesgo (ESTABLE / BAJO / MODERADO / ALTO).
- **Notas clínicas**: el médico puede añadir y editar anotaciones privadas por paciente.
- **Informe PDF**: descarga un informe completo basado en la guía mhGAP.

---

## Generación de informes PDF

El módulo `reportPDF.py` genera informes estructurados que incluyen:

- Datos identificativos del paciente.
- Resultados de la evaluación de suicidio (SUI_EVAL).
- Resultados de la evaluación de depresión (DEP_EVAL).
- Historial de sesiones con resúmenes y valoraciones.
- Notas clínicas del especialista.
- Emergencias registradas.

Los informes se pueden descargar directamente desde el panel médico o generarse en local con el script auxiliar:

```bash
python create_inform.py  # editar el ID_USUARIO en el script
```

---

## Notas de seguridad y privacidad

- Las contraseñas de especialistas se almacenan **hasheadas** (bcrypt).
- Los datos de pacientes solo son visibles para especialistas del **mismo centro médico**.
- El compartir datos con el hospital requiere **consentimiento explícito** del usuario (`shareWithHospital: true`).
- Los protocolos de emergencia siguen las directrices de la **Guía mhGAP v2.0 de la OMS**.

---

## Países disponibles

El sistema incluye centros médicos para: 🇪🇸 España · 🇦🇷 Argentina · 🇨🇷 Costa Rica · 🇲🇽 México · 🇨🇴 Colombia · 🇨🇱 Chile · 🇵🇪 Perú

Para añadir nuevos países o centros, edita `seed_medical_centers.py` y ejecuta:

```bash
python seed_medical_centers.py --drop
```