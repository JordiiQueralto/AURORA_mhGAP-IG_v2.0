# Arquitectura Conceptual del Sistema

Aquí presento el diagrama de bloques de la arquitectura:

```mermaid
graph TB
    %% Definición de la Capa de Entrada y Enrutamiento
    subgraph Capa_Entrada ["Capa de Entrada y Gestión de Flujo"]
        M1["1. User Onboarding & Informed Consent<br>(Captura demográfica y consentimiento legal)"]
        M2{"2. Use Case Classification &<br>Session Routing Module<br>(Router Central Contextual)"}
    end

    %% Definición de la Capa de Lógica Clínica y Evaluación Crítica
    subgraph Capa_Clinica ["Capa de Lógica Clínica y Evaluación Crítica"]
        M4["4. Conversational Logic &<br>Clinical Screening Module<br>(FSM basada en mhGAP-IG v2.0)"]
        M5["5. Pattern Monitoring &<br>Emergency Referral Module<br>(Transversal: REGEX Engine)"]
        M7["7. Active Follow-up<br>Protocol Module<br>(Verificación post-emergencia)"]
    end

    %% Definición de la Capa de Soporte y Conversación Abierta
    subgraph Capa_Soporte ["Capa de Soporte y Psicoeducación (Level 0)"]
        M3["3. Free Conversation Module<br>(Caso TALK: Escucha Activa LLM)"]
        M6["6. Preventive Support &<br>Psychoeducation Module<br>(Herramientas y guías dinámicas)"]
    end

    %% Definición de la Capa de Persistencia y Analítica
    subgraph Capa_Datos ["Capa de Persistencia y Cuadro de Mando"]
        M8[("(DB & Clinical Report Generation)<br>Instancia MongoDB Core"]
        Dashboard["Panel del Especialista Médico<br>(Dashboard Clínico)"]
    end

    %% Nodos de Salida del Sistema Externos
    Emergencia["PANTALLA DE EMERGENCIA<br>(Derivación asistida 112 / 024)"]

    %% --- FLUJOS DE INTERACCIÓN Y DATOS (LÍNEAS DE CONEXIÓN) ---

    %% Flujo de entrada
    M1 -->|Usuario acepta términos y provee edad/datos| M2

    %% Decisiones del Router Central (M2)
    M2 -->|Caso: TALK o MISENSE<br>(Sin riesgo aparente inicial)| M3
    M2 -->|Caso: ASSISTANCE<br>(Evaluación requerida)| M4
    M2 -->|Caso: EMERGENCY<br>(Usuario regresa tras crisis)| M7

    %% Dinámica del Módulo de Conversación Libre (M3)
    M3 -->|Entrada de texto continua| M5
    M3 -.->|Desviación emocional detectada| M2

    %% Interacción Crítica Inter-Módulo (M4 y M5)
    M4 -->|Streaming de texto en tiempo real| M5
    M5 -->|¿Riesgo Inminente Detectado?<br>SÍ: Interrupción Forzada de FSM| M4
    M5 -->|Invocación del protocolo de crisis| Emergencia

    %% Transición a Soporte y Psicoeducación
    M4 -->|Cribado finalizado / Bajo riesgo| M6
    M7 -->|Seguimiento cerrado con éxito| M6

    %% Flujos de Persistencia hacia el Módulo de Datos (M8)
    M2 --->|Registro de sesión y metadatos| M8
    M4 --->|Historial de estados y scores mhGAP| M8
    M5 --->|Inyección de Flags de Alerta Crítica| M8
    M7 --->|Estatus de la derivación humana| M8

    %% Generación del Reporte Final
    M8 -->|Compilación de logs y generación de PDF| Dashboard

    %% --- ESTILOS VISUALES ASIGNADOS (Sintaxis Mermaid) ---
    %% Estilos Capa de Entrada (Azul / Neutro)
    style M1 fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    style M2 fill:#e0f2f1,stroke:#004d40,stroke-width:2px;

    %% Estilos Capa Clínica (Naranja / Rojo para el Core de Riesgo Vital)
    style M4 fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    style M5 fill:#ffebee,stroke:#c62828,stroke-width:3px,stroke-dasharray: 5 5;
    style M7 fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    style Emergencia fill:#ffb74d,stroke:#b71c1c,stroke-width:3px;

    %% Estilos Capa de Soporte (Verde / Relajante)
    style M3 fill:#f1f8e9,stroke:#558b2f,stroke-width:2px;
    style M6 fill:#f1f8e9,stroke:#33691e,stroke-width:2px;

    %% Estilos Capa de Persistencia (Púrpura / Estructura)
    style M8 fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px;
    style Dashboard fill:#eceff1,stroke:#37474f,stroke-width:2px;
