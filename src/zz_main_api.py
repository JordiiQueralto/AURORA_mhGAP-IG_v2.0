import generate_output
import state_machine
import phrase_dictionary
import db
import datetime

# ── Claves de contexto que guardamos entre peticiones ────────────────────────
_CTX_J             = "j"               
_CTX_VARIANT       = "variant"         
_CTX_LAST_BOT_OUT  = "last_bot_output"
_CTX_BOT_OUT       = "bot_output"
_CTX_SESSION_PATH  = "session_path"    
_CTX_PHASE         = "phase"
_CTX_STATE         = "state"

def _ctx_get(telephone, key, default=None):
    """Lee un valor de contexto de la BD."""
    try:
        info = db.get_user_info(telephone, "ctx", key)
        return info if info is not None else default
    except Exception:
        return default

def _ctx_set(telephone, key, value):
    """Escribe un valor de contexto en la BD dentro del objeto ctx."""
    db.add_user_info(telephone, f"ctx.{key}", value)


# ─────────────────────────────────────────────────────────────────────────────
# start_conversation  –  llamado UNA vez al abrir el chat
# ─────────────────────────────────────────────────────────────────────────────
def start_conversation(telephone):
    telephone = int(telephone)  # Castear a int para consistencia con BD
    is_new = db.is_new(telephone)
    db.create_user(telephone, is_new)

    if is_new:
        db.add_user_info(telephone, "name", "")
        db.add_user_info(telephone, "age (years)", "")
        db.add_user_info(telephone, "USER_TERMS.status", "rejected")
        db.add_user_info(telephone, "PROFILE", {})
        db.add_user_info(telephone, "DEP_EVAL", {})
        db.add_user_info(telephone, "SUI_EVAL", {})
        db.add_user_info(telephone, "checkpoint.phase", "")
        db.add_user_info(telephone, "checkpoint.state", "")
        memory = ""
        status = "rejected"
    else:
        memory = db.user_memory(telephone)
        status = db.user_status(telephone) or "rejected"

    # Preparar sesión
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_path = f"{current_time}_session"
    
    db.add_user_info(telephone, f"{session_path}.summary", "")
    db.add_user_info(telephone, f"{session_path}.valoration", "")
    db.add_user_info(telephone, f"{session_path}.conversation_history", {})

    bot_output = generate_output.welcome(status, memory)

    # Identificamos dónde estamos para la siguiente iteración
    if status == "rejected":
        phase = "PRESENTATION"
    else:
        phase = "RESUMING" # Flag para retomar al usuario antiguo correctamente

    # Persistir contexto inicial
    _ctx_set(telephone, _CTX_SESSION_PATH, session_path)
    _ctx_set(telephone, _CTX_J, 0)
    _ctx_set(telephone, _CTX_BOT_OUT, bot_output)
    _ctx_set(telephone, _CTX_PHASE, phase)
    _ctx_set(telephone, _CTX_STATE, "")
    _ctx_set(telephone, _CTX_VARIANT, 0)

    return bot_output


# ─────────────────────────────────────────────────────────────────────────────
# process_message  –  llamado en cada mensaje del usuario
# ─────────────────────────────────────────────────────────────────────────────
def process_message(telephone, user_input):
    telephone = int(telephone)
    n_user_input = state_machine.normalize_text(user_input)

    # 1. Salida rápida global
    if n_user_input == "salir":
        _run_farewell(telephone, "normal")
        return generate_output.farewell("normal"), True

    # 2. Recuperar el contexto íntegro de la BD
    memory = db.user_memory(telephone)
    status = db.user_status(telephone) or "rejected"

    session_path = _ctx_get(telephone, _CTX_SESSION_PATH, "")
    j            = int(_ctx_get(telephone, _CTX_J, 0))
    bot_output_prev = _ctx_get(telephone, _CTX_BOT_OUT, "")
    phase        = _ctx_get(telephone, _CTX_PHASE, "")
    state        = _ctx_get(telephone, _CTX_STATE, "")
    variant      = _ctx_get(telephone, _CTX_VARIANT, 0)

    conv_path = f"{session_path}.conversation_history"

    # 3. Guardar el input del usuario emparejado con la salida previa del bot
    db.add_user_info(telephone, f"{conv_path}.bot_output_{j}", bot_output_prev)
    db.add_user_info(telephone, f"{conv_path}.user_input_{j}", user_input)
    j += 1

    # Variables que modificaremos
    is_ended = False
    bot_output = ""
    new_phase = phase
    new_state = state
    new_variant = variant

    # ── A. FLUJOS DE INICIO/PRESENTACIÓN ─────────────────────────────────────
    if phase == "PRESENTATION":
        if status == "rejected":
            if n_user_input != "si acepto":
                db.add_user_info(telephone, "USER_TERMS", {
                    "status": "rejected",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                bot_output = "Lo siento, no podemos continuar sin tu aceptación."
                _run_farewell(telephone, "exit")
                is_ended = True
                new_phase = "FAREWELL"
            else:
                db.add_user_info(telephone, "USER_TERMS", {
                    "status": "accepted",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                bot_output = "Gracias por aceptar. ¿Cómo podría ayudarte a explorar como te has sentido?"
                new_phase = "PRESENTATION_ASKED"
                new_state = ""

    elif phase == "PRESENTATION_ASKED":
        # Ahora el usuario ha respondido a "¿Cómo podría ayudarte?". Pasamos a PROFILE/name
        new_phase, new_state = "PROFILE", "name"
        new_variant = 0
        bot_output, is_ended, new_phase, new_state, new_variant = _generate_response(
            telephone, new_phase, new_state, new_variant, user_input, bot_output_prev, memory
        )

    elif phase == "RESUMING":
        # El usuario ha respondido al mensaje de Bienvenida personalizado.
        new_phase, new_state = db.resume_conversation(telephone)
        new_variant = 0
        bot_output, is_ended, new_phase, new_state, new_variant = _generate_response(
            telephone, new_phase, new_state, new_variant, user_input, bot_output_prev, memory
        )

    # ── B. FLUJO NORMAL Y MÁQUINA DE ESTADOS ─────────────────────────────────
    else:
        # Avanzamos la máquina de estados en base a la respuesta del usuario
        new_phase, new_state, new_variant = state_machine.StateMachine(
            telephone, phase, state, user_input
        )

        # Control de seguridad (Emergencia)
        if phase == "DEP_EVAL":
            new_phase, new_state, new_variant = state_machine.security_control(
                new_phase, new_state, new_variant, user_input
            )

        # Generar la pregunta del BOT para el NUEVO estado
        bot_output, is_ended, new_phase, new_state, new_variant = _generate_response(
            telephone, new_phase, new_state, new_variant, user_input, bot_output_prev, memory
        )

    # 4. Actualizar estado de vuelta a la BD
    _ctx_set(telephone, _CTX_J, j)
    _ctx_set(telephone, _CTX_BOT_OUT, bot_output)
    _ctx_set(telephone, _CTX_PHASE, new_phase)
    _ctx_set(telephone, _CTX_STATE, new_state)
    _ctx_set(telephone, _CTX_VARIANT, new_variant)

    return bot_output, is_ended


# ─────────────────────────────────────────────────────────────────────────────
# _generate_response  –  Maneja lógicad e transición compleja y Prompt del LLM
# ─────────────────────────────────────────────────────────────────────────────
def _generate_response(telephone, new_phase, new_state, new_variant, user_input, last_bot, memory):
    is_ended = False

    # Revisar si se debe hacer clasificación automática
    if new_phase == "USE_CASE_EVAL":
        use_case = generate_output.use_case_class(db.conversation_history(telephone))
        
        if use_case == "EMERGENCY":
            new_phase, new_state = "SUI_EVAL", "1"
        elif use_case == "ASSISTANCE":
            new_phase, new_state = "DEP_EVAL", "1A.1"
        elif use_case == "TALK":
            new_phase, new_state = "CHAT", "error"
        else:
            new_phase, new_state = "FAREWELL", "misuse"

    # Revisar si cerramos llamada
    if new_phase == "FAREWELL":
        bot_output = generate_output.farewell(new_state)
        _run_farewell(telephone, new_state)
        db.save_flow(telephone, new_phase, new_state)
        return bot_output, True, new_phase, new_state, new_variant

    # Si todo sigue, preparamos el nuevo output
    if new_variant != 0:
        nucleo = phrase_dictionary.variant_dict(new_phase, new_state, new_variant)
    else:
        nucleo = phrase_dictionary.bot_output_info(new_phase, new_state)

    # Llamada al LLM
    bot_output = generate_output.bot_output(last_bot, user_input, nucleo, memory)
    
    # Guardamos checkpoint seguro
    db.save_flow(telephone, new_phase, new_state)

    return bot_output, is_ended, new_phase, new_state, new_variant


# ─────────────────────────────────────────────────────────────────────────────
# _run_farewell  –  Tareas de cierre de sesión
# ─────────────────────────────────────────────────────────────────────────────
def _run_farewell(telephone, state):
    """Guarda resumen y valoración de la sesión en MongoDB al terminar."""
    try:
        session_path = _ctx_get(telephone, _CTX_SESSION_PATH, "")
        if session_path:
            # Obtener `current_time` removiendo "_session" del final
            current_time = session_path.replace("_session", "")
            summary = db.session_summary(telephone, current_time)
            
            db.add_user_info(telephone, f"{session_path}.summary", summary)
            db.add_user_info(telephone, f"{session_path}.valoration", state)
    except Exception as e:
        print(f"\n[Error guardando resumen (Farewell)]: {e}")