import generate_output
import state_machine
import phrase_dictionary
import db
import datetime

def start_conversation(telephone):
    """Se ejecuta cuando el usuario mete su número en la pantalla inicial."""
    is_new = db.is_new(telephone)
    db.create_user(telephone, is_new)
    
    if is_new:
        db.add_user_info(telephone, "USER_TERMS.status", "rejected")
        db.add_user_info(telephone, "checkpoint.phase", "PRESENTATION")
        db.add_user_info(telephone, "checkpoint.state", "start")
        # Inicializa todo lo demás...
        memory = ""
        status = "rejected"
    else:
        memory = db.user_info(telephone)
        status = db.user_status(telephone)
        
    # Guardamos el inicio de sesión
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.add_user_info(telephone, f"{current_time}_session.conversation_history", {})
    
    bot_output = generate_output.welcome(status, memory)
    return bot_output

def process_message(telephone, user_input):
    """Se ejecuta cada vez que el usuario pulsa 'Enviar'."""
    is_ended = False
    n_user_input = state_machine.normalize_text(user_input)
    
    if n_user_input == "salir":
        return generate_output.farewell("normal"), True
    
    # 1. Recuperar el estado actual del usuario desde la BD
    phase, state = db.resume_conversation(telephone)
    memory = db.user_info(telephone)
    status = db.user_status(telephone)
    
    bot_output = ""

    # 2. Máquina de estados (SIN bucles while, solo condicionales)
    if phase == "PRESENTATION":
        if status == "rejected":
            if n_user_input != "si acepto":
                bot_output = "Lo siento, no podemos continuar sin tu aceptación."
                is_ended = True
            else:
                db.add_user_info(telephone, "USER_TERMS", {"status": "accepted"})
                bot_output = "Gracias por aceptar. ¿Cómo podría ayudarte a explorar como te has sentido?"
                db.save_flow(telephone, "PROFILE", "name") # Actualizamos checkpoint
                
    elif phase == "PROFILE":
        # Evaluar la entrada y actualizar estado
        new_phase, new_state, variant = state_machine.StateMachine(telephone, phase, state, user_input)
        
        # Generar salida
        nucleo = phrase_dictionary.bot_output_info(new_phase, new_state)
        bot_output = generate_output.bot_output("", user_input, nucleo, memory)
        
        # Guardar el nuevo checkpoint
        db.save_flow(telephone, new_phase, new_state)

    # Añade aquí el resto de tus `elif` (DEP_EVAL, SUI_EVAL, etc.)
    # ...
    
    # 3. Retornar el mensaje del bot y si la sesión ha terminado
    return bot_output, is_ended