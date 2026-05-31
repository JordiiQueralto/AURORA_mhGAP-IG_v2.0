import generate_output
import state_machine
import phrase_dictionary
import db
import datetime
import time

# ── Claves de contexto que guardamos entre peticiones ────────────────────────
_CTX_J             = "j"
_CTX_K             = "K" 
_CTX_VARIANT       = "variant"         
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
# init_user  –  llamado al verificar el código SMS, antes de start_conversation
# ─────────────────────────────────────────────────────────────────────────────
def init_user(telephone):
    """
    Registra o verifica al usuario en la BD en el momento del login.
    Garantiza que el documento existe antes de cualquier otra operación.
    Devuelve True si es usuario nuevo, False si ya existía.
    """
    telephone = str(telephone).replace(" ", "")
    is_new = db.is_new(telephone)
    db.create_user(telephone, is_new)

    if is_new:
        db.add_user_info(telephone, "name", "")
        db.add_user_info(telephone, "age (years)", "")
        db.add_user_info(telephone, "USER_TERMS.status", "rejected")
        db.add_user_info(telephone, "CIRCLE", {})
        db.add_user_info(telephone, "PROFILE", {})
        db.add_user_info(telephone, "DEP_EVAL", {})
        db.add_user_info(telephone, "SUI_EVAL", {})
        db.add_user_info(telephone, "SCREENING", {})
        db.add_user_info(telephone, "EMERGENCY", [])
        db.add_user_info(telephone, "FOLLOWUP.history", [])
        db.add_user_info(telephone, "FOLLOWUP.last_check", "")
        db.add_user_info(telephone, "checkpoint.phase", "")
        db.add_user_info(telephone, "checkpoint.state", "")
        db.add_user_info(telephone, "ctx", {})

    return is_new

# ─────────────────────────────────────────────────────────────────────────────
# start_conversation  –  llamado UNA vez al abrir el chat
# ─────────────────────────────────────────────────────────────────────────────
def start_conversation(telephone):
    telephone = str(telephone).replace(" ", "")
    memory = db.user_memory(telephone)
    status = db.user_status(telephone)

    # Preparar sesión
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_path = f"{current_time}_session"
    
    db.add_user_info(telephone, f"{session_path}.summary", "")
    db.add_user_info(telephone, f"{session_path}.valoration", "")
    db.add_user_info(telephone, f"{session_path}.risk_level", "")
    db.add_user_info(telephone, f"{session_path}.conversation_history", {})

    time.sleep(4)
    bot_output = generate_output.welcome(status, memory)

    # Identificamos dónde estamos para la siguiente iteración
    if status == "rejected":
        phase = "PRESENTATION"
    else:
        phase = "RESUMING" # Flag para retomar al usuario ya registrado

    # Persistir contexto inicial
    _ctx_set(telephone, _CTX_SESSION_PATH, session_path)
    _ctx_set(telephone, _CTX_J, 0)
    _ctx_set(telephone, _CTX_K, 0)
    _ctx_set(telephone, _CTX_BOT_OUT, bot_output)
    _ctx_set(telephone, _CTX_PHASE, phase)
    _ctx_set(telephone, _CTX_STATE, "")
    _ctx_set(telephone, _CTX_VARIANT, 0)

    return bot_output, None     # None correponds to `image_path`

# ─────────────────────────────────────────────────────────────────────────────
# process_message  –  llamado en cada mensaje del usuario
# ─────────────────────────────────────────────────────────────────────────────
def process_message(telephone, user_input):
    telephone = str(telephone).replace(" ", "")
    n_user_input = state_machine._normalize_text(user_input)

    # 1. Recuperar el contexto íntegro de la BD
    memory = db.user_memory(telephone)
    status = db.user_status(telephone)

    session_path    = _ctx_get(telephone, _CTX_SESSION_PATH, "")
    j               = int(_ctx_get(telephone, _CTX_J, 0))
    k               = int(_ctx_get(telephone, _CTX_K, 0))
    last_bot_output = _ctx_get(telephone, _CTX_BOT_OUT, "")
    phase           = _ctx_get(telephone, _CTX_PHASE, "")
    state           = _ctx_get(telephone, _CTX_STATE, "")
    variant         = _ctx_get(telephone, _CTX_VARIANT, 0)

    conv_path = f"{session_path}.conversation_history"

    # 2. Guardar el input del usuario emparejado con la salida previa del bot
    db.add_user_info(telephone, f"{conv_path}.bot_output_{j}", last_bot_output)
    db.add_user_info(telephone, f"{conv_path}.user_input_{j}", user_input)
    j += 1

    # Variables que modificaremos
    image_path = None
    is_ended = False
    emergency_112 = False
    emergency_024 = False
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
                time.sleep(1.5)
                bot_output = "Lo siento, no podemos continuar sin tu aceptación."
                is_ended = True
                new_phase = "FAREWELL"
            else:
                db.add_user_info(telephone, "USER_TERMS", {
                    "status": "accepted",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                time.sleep(2)
                bot_output = "Gracias por aceptar. ¿Cómo podría ayudarte a explorar como te has sentido?"
                new_phase = "PRESENTATION_ASKED"
                new_state = ""

    elif phase == "PRESENTATION_ASKED":
        # Ahora el usuario ha respondido a "¿Cómo podría ayudarte?". Pasamos a PROFILE/name
        new_phase, new_state = "PROFILE", "name"
        new_variant = 0
        db.save_flow(telephone, new_phase, new_state)
        bot_output, image_path, is_ended, new_phase, new_state, new_variant, k = _generate_response(
            telephone, new_phase, new_state, new_variant, user_input, last_bot_output, memory, session_path, k
        )

    elif phase == "RESUMING":
        # El usuario ha respondido al mensaje de Bienvenida personalizado.
        new_phase, new_state = db.resume_conversation(telephone)
        new_variant = 0
        bot_output, image_path, is_ended, new_phase, new_state, new_variant, k = _generate_response(
            telephone, new_phase, new_state, new_variant, user_input, last_bot_output, memory, session_path, k
        )
        

    # ── B. FLUJO NORMAL Y MÁQUINA DE ESTADOS ─────────────────────────────────
    else:
        # Avanzamos la máquina de estados en base a la respuesta del usuario
        new_phase, new_state, new_variant = state_machine.StateMachine(
            telephone, phase, state, user_input
        )

        # Control de seguridad (Emergencia)
        if phase == "DEP_EVAL" or phase == "CHAT":
            new_phase, new_state, new_variant = state_machine.security_control(
                new_phase, new_state, new_variant, user_input
            )
            
        # Casos especiales (PROTOCOLOS)
        if new_phase == "SUI_PROTOCOLS":
            if new_state == "1":
                # Obtenemos el bot_output directamente de la libreria de frases
                bot_output = phrase_dictionary.bot_output_info(new_phase, new_state)
                
                # Obtener imagen para esta fase/estado
                image_path_user, image_path_family = state_machine.bot_output_image(new_phase, new_state)
                image_path = image_path_user
                
                # En caso de existir `image_path_family` se les envia notificación
                if image_path_family:
                    consent = db.get_user_info(telephone, "CIRCLE", "privacy")
                    
                    # Si 'consent' es None o no tiene la clave, family_consent será False por defecto.
                    family_consent = consent.get("allowContactFamily",
                                                 False) if isinstance(consent, dict) else False
                    
                    # Si existe consentimiento de compartir datos con familia, le enviamos notificación
                    # a los familiares/gente cercana guardada en a DB
                    if family_consent:
                        contacts = db.get_user_info(telephone, "CIRCLE", "contacts")
                        for contact in contacts:
                            fam_phone = contact.get("phone")
                            if fam_phone and (db.is_new(fam_phone) == False):
                                user_name = db.get_user_name(telephone)
                                db.save_notification(
                                    to_telephone=fam_phone,
                                    from_telephone=telephone,
                                    from_name=user_name,
                                    image_path_family=image_path_family
                                    )
                
                # Registramos la emergencia en la BD
                referal = "112"
                emergency_112 = True
                db.add_emergency_instance(telephone, session_path, new_state, referal)
                
            elif new_state == "2":
                # Obtenemos el bot_output directamente de la libreria de frases
                bot_output = phrase_dictionary.bot_output_info(new_phase, new_state)
                
                # Obtener imagen para esta fase/estado
                image_path_user, image_path_family = state_machine.bot_output_image(new_phase, new_state)
                image_path = image_path_user
                
                # En caso de existir `image_path_family` se les envia notificación
                if image_path_family:
                    consent = db.get_user_info(telephone, "CIRCLE", "privacy")
                    
                    # Si 'consent' es None o no tiene la clave, family_consent será False por defecto.
                    family_consent = consent.get("allowContactFamily",
                                                 False) if isinstance(consent, dict) else False
                    
                    # Si existe consentimiento de compartir datos con familia, le enviamos notificación
                    # a los familiares/gente cercana guardada en a DB
                    if family_consent:
                        contacts = db.get_user_info(telephone, "CIRCLE", "contacts")
                        for contact in contacts:
                            fam_phone = contact.get("phone")
                            if fam_phone and (db.is_new(fam_phone) == False):
                                user_name = db.get_user_name(telephone)
                                db.save_notification(
                                    to_telephone=fam_phone,
                                    from_telephone=telephone,
                                    from_name=user_name,
                                    image_path_family=image_path_family
                                    )
                            
                # Registramos la emergencia en la BD
                referal = "024"
                emergency_024 = True
                db.add_emergency_instance(telephone, session_path, new_state, referal)
                
            else:   # new_state = "3"
                # Obtenemos el bot_output directamente de la libreria de frases
                bot_output = phrase_dictionary.bot_output_info(new_phase, new_state)
                
                # Obtener imagen para esta fase/estado
                image_path_user, image_path_family = state_machine.bot_output_image(new_phase, new_state)
                image_path = image_path_user
                
                # En caso de existir `image_path_family` se les envia notificación
                if image_path_family:
                    consent = db.get_user_info(telephone, "CIRCLE", "privacy")
                    
                    # Si 'consent' es None o no tiene la clave, family_consent será False por defecto.
                    family_consent = consent.get("allowContactFamily",
                                                 False) if isinstance(consent, dict) else False
                    
                    # Si existe consentimiento de compartir datos con familia, le enviamos notificación
                    # a los familiares/gente cercana guardada en a DB
                    if family_consent:
                        contacts = db.get_user_info(telephone, "CIRCLE", "contacts")
                        for contact in contacts:
                            fam_phone = contact.get("phone")
                            if fam_phone and (db.is_new(fam_phone) == False):
                                user_name = db.get_user_name(telephone)
                                db.save_notification(
                                    to_telephone=fam_phone,
                                    from_telephone=telephone,
                                    from_name=user_name,
                                    image_path_family=image_path_family
                                    )
                            
                # Registramos la emergencia en la BD
                referal = "024"
                emergency_024 = True
                db.add_emergency_instance(telephone, session_path, new_state, referal)
                
            db.save_flow(telephone, "FOLLOWUP", "emergency_followup")
            return bot_output, image_path, True, emergency_112, emergency_024
                

        # Generar la pregunta del BOT para el NUEVO estado
        bot_output, image_path, is_ended, new_phase, new_state, new_variant, k = _generate_response(
            telephone, new_phase, new_state, new_variant, user_input, last_bot_output, memory, session_path, k
        )

    # 3. Actualizar estado de vuelta a la BD
    _ctx_set(telephone, _CTX_J, j)
    _ctx_set(telephone, _CTX_K, k)
    _ctx_set(telephone, _CTX_BOT_OUT, bot_output)
    _ctx_set(telephone, _CTX_PHASE, new_phase)
    _ctx_set(telephone, _CTX_STATE, new_state)
    _ctx_set(telephone, _CTX_VARIANT, new_variant)

    return bot_output, image_path, is_ended, emergency_112, emergency_024

# ─────────────────────────────────────────────────────────────────────────────
# _generate_response  –  Maneja lógicad e transición compleja y Prompt del LLM
# ─────────────────────────────────────────────────────────────────────────────
def _generate_response(telephone, new_phase, new_state, new_variant, user_input, 
                       last_bot, memory, session_path, k):
    is_ended = False
    image_path = None

    # Determinar el caso de uso del usuario
    if new_phase == "USE_CASE_EVAL":
        conversation_history = db.conversation_history(telephone)
        use_case = generate_output.use_case_class(conversation_history)
        
        print (f"\n[USE CASE DETECTED : {use_case}]\n")
        
        if use_case == "EMERGENCY":
            new_phase, new_state = "SUI_EVAL", "1"
        elif use_case == "ASSISTANCE":
            new_phase, new_state = "DEP_EVAL", "1A.1"
            db.save_flow(telephone, new_phase, new_state)
        elif use_case == "TALK":
            new_phase, new_state = "CHAT", ""
        else:
            new_phase, new_state = "FAREWELL", "misuse"
    
    if new_phase == "CHAT":
        # Modo libre de conversación. No hay máquina de estados, solo respuesta abierta del LLM.
        # Obtain the conversation history of the actual session
        conversation = db.get_user_info(telephone, session_path, "conversation_history")
        
        # Every 5 messages reevaluate if use case change is needed
        if (k % 5 == 0) and (k != 0):
            
            use_case = generate_output.use_case_class(conversation)
            print (f"\n[REEVALUATION USE CASE: {use_case}]\n")
                
            if use_case == "EMERGENCY":
                new_phase, new_state = "SUI_EVAL", "1"
                    
            elif use_case == "ASSISTANCE":
                new_phase, new_state = "DEP_EVAL", "1A.1"
                    
            elif use_case == "TALK":
                new_phase, new_state = "CHAT", ""
                    
            else:
                new_phase, new_state = "FAREWELL", "misuse"

        # Comprobamos que el phase sigue igual y que no ha cambiado debido a reevaluación
        if new_phase == "CHAT":
            # Output generado por LLM
            bot_output = generate_output.talk_mode(conversation)
            k += 1
            return bot_output, image_path, is_ended, new_phase, new_state, new_variant, k
    
    # Revisar si cerramos llamada
    if new_phase == "FAREWELL":
        time.sleep(2)
        bot_output = generate_output.farewell(new_state)
        return bot_output, None, True, new_phase, new_state, new_variant, k
    
    else:
        # Si todo sigue, preparamos el nuevo output
        if new_variant != 0:
            nucleo = phrase_dictionary.variant_dict(new_phase, new_state, new_variant)
        else:
            nucleo = phrase_dictionary.bot_output_info(new_phase, new_state)

        # Llamada al LLM
        bot_output = generate_output.bot_output(last_bot, user_input, nucleo, memory)

        return bot_output, image_path, is_ended, new_phase, new_state, new_variant, k

# ─────────────────────────────────────────────────────────────────────────────
# save_circle_data  –  Guardar info de contactos en la DB
# ─────────────────────────────────────────────────────────────────────────────
def save_circle_data(telephone, circle_data):
    """
    Guarda la información de 'Mi círculo' en el perfil del usuario en la BD.
    """
    telephone = str(telephone).replace(" ", "")
    
    # Extraemos las distintas partes
    contacts = circle_data.get("contacts", [])
    medicalCenter = circle_data.get("medicalCenter", {})
    privacy = circle_data.get("privacy", {})
    
    # Limpiamos los números de teléfono
    for contact in contacts:
            if "phone" in contact:
                contact["phone"] = str(contact["phone"]).replace(" ", "")
                
    # Volvemos a reconstruir los datos de 'Mi círculo'
    filtered_circle_data ={
        "contacts": contacts,
        "medicalCenter": medicalCenter,
        "privacy": privacy
    }
    
    # Guardamos todo el objeto bajo la clave 'CIRCLE' en el perfil del usuario
    db.add_user_info(telephone, "CIRCLE", filtered_circle_data)
    
# ─────────────────────────────────────────────────────────────────────────────
# get_circle_data  –  Recuperar la info de contactos guardada en la DB
# ─────────────────────────────────────────────────────────────────────────────
def get_circle_data(telephone):
    """
    Recupera la información de 'Mi círculo' del perfil del usuario en la BD.
    """
    telephone = str(telephone).replace(" ", "")
    contacts = db.get_user_info(telephone, "CIRCLE", "contacts") or {}
    medicalCenter = db.get_user_info(telephone, "CIRCLE", "medicalCenter") or {}
    privacy = db.get_user_info(telephone, "CIRCLE", "privacy") or {}
    
    circle_data = {
            "contacts": contacts,
            "medicalCenter": medicalCenter,
            "privacy": privacy
            }
    
    return circle_data

# ─────────────────────────────────────────────────────────────────────────────
# _run_farewell  –  Tareas de cierre de sesión
# ─────────────────────────────────────────────────────────────────────────────
def _run_farewell(telephone):
    """Guarda resumen, valoración y nivel de riesgo de crisis de la sesión en 
    MongoDB al terminar."""
    try:
        session_path = _ctx_get(telephone, _CTX_SESSION_PATH, "")
        if session_path:
            summary = generate_output.session_summary(telephone, session_path)
            valoration = generate_output.session_valoration(telephone, session_path)
            risk_level = generate_output.session_risk(telephone, session_path)
            
            db.add_user_info(telephone, f"{session_path}.summary", summary)
            db.add_user_info(telephone, f"{session_path}.valoration", valoration)
            db.add_user_info(telephone, f"{session_path}.risk_level", risk_level)
            
            # Revisar si existe ctx.emergency_followup
            ctx = db.get_user_info(telephone, "ctx")

            if ctx and isinstance(ctx, dict) and "emergency_followup" in ctx:
                # 1. Preparamos los datos base que siempre existen
                # Obtenemos el array de emergencias
                emergencies = db.get_user_info(telephone, "EMERGENCY")

                if emergencies and isinstance(emergencies, list) and len(emergencies) > 0:
                    # Accedemos al último elemento del array (-1)
                    last_emergency = emergencies[-1]
                    
                    # Extraemos el session_id (que contiene la fecha)
                    raw_session = last_emergency.get("session_id", "")
                    
                    # Limpiamos el formato
                    emergency_date = raw_session.replace("_session", "")
                else:
                    emergency_date = None
                    
                followup_date = ctx["session_path"].replace("_session", "")
                new_instance = {
                    "emergency_date": emergency_date,
                    "followup_date": followup_date, 
                    "outcome": ctx["emergency_followup"]
                }

                # 2. Añadimos la razón solo si existe (no llamó a emergencias)
                if "non_contact_reason" in ctx:
                    new_instance["reason"] = ctx["non_contact_reason"]

                # 3. Guardamos
                db.add_to_list(telephone, "FOLLOWUP.history", new_instance)
                db.add_user_info(telephone, "FOLLOWUP.last_check", followup_date)
                
                # 4. Borramos info ya usada
                db.delete_user_info(telephone, "ctx.emergency_followup")
                db.delete_user_info(telephone, "ctx.non_contact_reason")
            
    except Exception as e:
        print(f"\n[Error guardando resumen (Farewell): {e}]\n")
        
# ─────────────────────────────────────────────────────────────────────────────
# get_notifications  –  Recupera las notificaciones para un usuario
# ─────────────────────────────────────────────────────────────────────────────
def get_notifications(telephone):
    telephone = str(telephone).replace(" ", "")
    return db.get_notifications(telephone)

# ─────────────────────────────────────────────────────────────────────────────
# mark_notifications_read  –  Marca las notificaciones como leídas para un usuario
# ─────────────────────────────────────────────────────────────────────────────
def mark_notifications_read(telephone):
    telephone = str(telephone).replace(" ", "")
    db.mark_notifications_read(telephone)

# ─────────────────────────────────────────────────────────────────────────────
# reset_session  –  Borra el contexto de sesión activa para un usuario
# ─────────────────────────────────────────────────────────────────────────────
def reset_session(telephone):
    """Resetea el contexto ctx en la BD para que la próxima llamada a
    start_conversation arranque limpia (útil al hacer logout desde el front).
    Antes de limpiar el contexto, ejecuta _run_farewell para guardar el
    resumen y valoración de la sesión."""
    telephone = str(telephone).replace(" ", "")
    # Guardar resumen de sesión antes de borrar el contexto
    _run_farewell(telephone)
    for key in [_CTX_J, _CTX_VARIANT,_CTX_BOT_OUT, _CTX_SESSION_PATH, 
                _CTX_PHASE, _CTX_STATE, _CTX_K]:
        try:
            _ctx_set(telephone, key, None)
        except Exception:
            pass