import generate_output
import state_machine
import phrase_dictionary
import db
import datetime
import time


def main_prova(telephone):
    
    #---------------------------------------------------------------------------------------------------#
    ### 1. PRESENTATION
    #---------------------------------------------------------------------------------------------------#
    phase = "PRESENTATION"
    state = ""
    j = 0
    memory = ""
    status = "rejected"
    
    print(f"\n[Procesando llamada de: {telephone}...]")
    
    # Miramos si el paciente está registrado en la BD y en caso de que no lo esté lo añadimos
    is_new = db.is_new(telephone)
    db.create_user(telephone, is_new)
    
    if is_new:
        # si el usuario es nuevo, creamos objetos y variables para guardar datos del perfil, aceptación 
        # o rechazo de los términos de uso, evaluación DEP, evaluación SUI y checkpoint de la última 
        # `phase` y `state` para llamadas futuras
        db.add_user_info(telephone, "name", "")
        db.add_user_info(telephone, "age (years)", "")
        db.add_user_info(telephone, "USER_TERMS.status", status)    # inicializamos el estado de 
                                                                    # aceptación de términos de uso
                                                                    # en "rejected" provisionalmente
        db.add_user_info(telephone, "PROFILE", {})
        db.add_user_info(telephone, "DEP_EVAL", {})
        db.add_user_info(telephone, "SUI_EVAL", {})
        db.add_user_info(telephone, "checkpoint.phase", "")
        db.add_user_info(telephone, "checkpoint.state", "")
        
    else:
        # en caso de no ser nuevo, obtenemos un resumen del registro 
        # de la BD del usuario y el estado de aceptación de términos
        memory = db.user_info(telephone)
        status = db.user_status(telephone)
    
    
    # Obtenemos fecha y hora actuales
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Creamos un objeto, que empieza con la fecha y hora del inicio de la llamada, para guardar el historial 
    # de la conversación, un resumen y una valoración de la conversación (éxito/regular/fracaso)
    summary_path = f"{current_time}_session.summary"
    valoration_path = f"{current_time}_session.valoration"
    conversation_history_path = f"{current_time}_session.conversation_history"
    db.add_user_info(telephone, summary_path, "")
    db.add_user_info(telephone, valoration_path, "")
    db.add_user_info(telephone, conversation_history_path, {})

    
    # Saludo del bot según el `status` y el historial del usuario registrados
    bot_output = generate_output.welcome(status, memory)
    print(f"\nBOT: {bot_output}")
    time.sleep(1)
    
    # Si había rechazado les términos préviamente o es nuevo
    if status == "rejected":
        
        # Guardamos saludo del bot y respuesta del usuario en la BD
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        db.add_user_info(telephone, f"{conversation_history_path}.bot_output_{j}", bot_output)
        db.add_user_info(telephone, f"{conversation_history_path}.user_input_{j}", user_input)
        j += 1
        time.sleep(2)   # añadimos un sleep para simular que el bot piensa antes de responder
        
        # Creamos el objeto `USER_TERMS` para guardar estado de aceptación de términos por parte del usuario
        key = "USER_TERMS"
        n_user_input = state_machine.normalize_text(user_input)

        if n_user_input != "si acepto":     # si no acepta términos
            value = {
                "status": "rejected",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            db.add_user_info(telephone, key, value)
            
            bot_output = "Lo siento, no podemos continuar sin tu aceptación."
            time.sleep(1.5)
            print(f"\nBOT: {bot_output}")
            
            db.add_user_info(telephone, f"{conversation_history_path}.bot_output_{j}", bot_output)
            j += 1
        
            # terminamos llamada
            phase = "FAREWELL"
            state = "exit"


        else:       # si acepta términos
            value = {
                "status": "accepted",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            db.add_user_info(telephone, key, value)
            
            bot_output = "Gracias por aceptar. ¿Cómo podria ayudarte a explorar como te has sentido?"
            print(f"\nBOT: {bot_output}")
            time.sleep(1) 

            user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
            n_user_input = state_machine.normalize_text(user_input)
            
            db.add_user_info(telephone, f"{conversation_history_path}.bot_output_{j}", bot_output)
            db.add_user_info(telephone, f"{conversation_history_path}.user_input_{j}", user_input)
            last_bot_output = bot_output
            last_user_input = user_input
            j += 1
            
            
            if n_user_input == "salir":     # si el usuario quiere terminar la llamada
                phase = "FAREWELL"
                state = "normal"
                
                 
            else:   # en caso contrario continuamos con la obtención de su PERFIL
                phase = "PROFILE"
                state = "name"
                db.save_flow(telephone, phase, state)   # guardamos `phase` y `state` actuales en la BD
                                                        # es una especie de checkpoint para si el usuario
                                                        # termina la llamada
    
                
    # Si ya habia aceptado los términos anteriormente
    else:
        
        # Guardamos saludo del bot y respuesta del usuario en la BD
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        db.add_user_info(telephone, f"{conversation_history_path}.bot_output_{j}", bot_output)
        db.add_user_info(telephone, f"{conversation_history_path}.user_input_{j}", user_input)
        last_bot_output = bot_output
        last_user_input = user_input
        j += 1
        
        n_user_input = state_machine.normalize_text(user_input)
        
        if n_user_input != "salir":     # si la respuesta del usuario no es terminar la llamada 
            
            # Obtenemos el punto donde nos quedamos en la anterior conversación
            phase, state = db.resume_conversation(telephone)
        
        else:   # usuario quiere terminar la llamada
            
            phase = "FAREWELL"
            state = "normal"
     
     
    #---------------------------------------------------------------------------------------------------# 
    ### 2. PROFILE
    #---------------------------------------------------------------------------------------------------#
    if phase == "PROFILE":  
        variant = 0
        while True:
            
            # Obtenemos el nucleo de la `bot_output` dependiendo de la `phase` y `state` actuales
            if variant != 0:    # si en el loop anterior se activo alguna variante
                nucleo = phrase_dictionary.variant_dict(phase, state, variant)
            
            else:
                nucleo = phrase_dictionary.bot_output_info(phase, state)      
            
            # Creamos la `bot_output`   
            bot_output = generate_output.bot_output(last_bot_output, 
                                                    last_user_input, nucleo, memory)
            print(f"\nBOT: {bot_output}")
                
            # Esperamos la respuesta del usuario
            user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
            n_user_input = state_machine.normalize_text(user_input)
                
            # Salimos del bucle en caso de que el usuario lo desee
            if n_user_input == "salir":
                phase = "FAREWELL"
                state = "normal"
                break 
                
            else:
                # En caso contrario, actualizamos `phase` i `state`
                phase, state, variant = state_machine.StateMachine(telephone, phase, 
                                                                    state, user_input)
                    
                # Actualizar variables
                last_bot_output = bot_output
                last_user_input = user_input
                    
                # Actualizar memoria: Guardar la nueva información relevante en la BD
                db.add_user_info(telephone, f"{conversation_history_path}.bot_output_{j}", bot_output)
                db.add_user_info(telephone, f"{conversation_history_path}.user_input_{j}", user_input)
                j += 1
                    
                # Rompemos el bucle si llegamos a phase `USE_CASE_EVAL`
                if phase == "USE_CASE_EVAL":
                    break
     
                
    #---------------------------------------------------------------------------------------------------#            
    ### 3. USE CASE DETERMINATION
    #---------------------------------------------------------------------------------------------------#
    elif phase == "USE_CASE_EVAL":
        
        conversation_history = db.conversation_history(telephone)
        use_case = generate_output.use_case_class(conversation_history)
            
        # Potencial caso de emergencia (riesgo imminente)
        if use_case == "EMERGENCY":
            phase = "SUI_EVAL"
            state = "1"
            db.save_flow(telephone, phase, state)
        # Potencial caso de depresion (MAIN CASE)
        elif use_case == "ASSISTANCE":
            phase = "DEP_EVAL"
            state = "1A.1"
            db.save_flow(telephone, phase, state)
        # El usuario solo quiere charlar  
        elif use_case == "TALK":
            phase = "CHAT"
            state = "error"
            db.save_flow(telephone, phase, state)
        # Llamada por equivocacion / intento de engaño
        else:   # use_case == "MISUSE"
            phase = "FAREWELL"
            state = "misuse"
   
        
    #---------------------------------------------------------------------------------------------------#            
    ### 4. DEP EVALUATION
    #---------------------------------------------------------------------------------------------------#
    elif phase == "DEP_EVAL": 
        variant = 0
        while True:
            
            # Obtenemos el nucleo de la `bot_output` dependiendo de la `phase` y `state` actuales
            if variant != 0:    # si en el loop anterior se activo alguna variante
                nucleo = phrase_dictionary.variant_dict(phase, state, variant)
            
            else:
                nucleo = phrase_dictionary.bot_output_info(phase, state)      
            
            # Creamos la `bot_output`   
            bot_output = generate_output.bot_output(last_bot_output, 
                                                    last_user_input, nucleo, memory)
            print(f"\nBOT: {bot_output}")
                
            # Esperamos la respuesta del usuario
            user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
            n_user_input = state_machine.normalize_text(user_input)
                
            # Salimos del bucle en caso de que el usuario lo desee
            if n_user_input == "salir":
                phase = "FAREWELL"
                state = "normal"
                break 
                
            else:
                # En caso contrario, actualizamos `phase` i `state`
                phase, state, variant = state_machine.StateMachine(telephone, phase, 
                                                                    state, user_input)
                
                # Añadimos control de seguridad para si en cualquier momento hace falta cambiar a
                # SUI_EVAL (emergencia por crisis)
                phase, state, variant = state_machine.security_control(phase, state, 
                                                                                   variant, user_input)
                    
                # Actualizar variables
                last_bot_output = bot_output
                last_user_input = user_input
                    
                # Actualizar memoria: Guardar la nueva información relevante en la BD
                db.add_user_info(telephone, f"{conversation_history_path}.bot_output_{j}", bot_output)
                db.add_user_info(telephone, f"{conversation_history_path}.user_input_{j}", user_input)
                j += 1
                    
                # Rompemos el bucle si llegamos a phase `FAREWELL`    
                if phase == "FAREWELL":
                    break
    
    #---------------------------------------------------------------------------------------------------#            
    ### 5. SUI EVALUATION
    #---------------------------------------------------------------------------------------------------#
    elif phase == "SUI_EVAL": 
        variant = 0
        while True:
            
            # Obtenemos el nucleo de la `bot_output` dependiendo de la `phase` y `state` actuales
            if variant != 0:    # si en el loop anterior se activo alguna variante
                nucleo = phrase_dictionary.variant_dict(phase, state, variant)
            
            else:
                nucleo = phrase_dictionary.bot_output_info(phase, state)      
            
            # Creamos la `bot_output`   
            bot_output = generate_output.bot_output(last_bot_output, 
                                                    last_user_input, nucleo, memory)
            print(f"\nBOT: {bot_output}")
                
            # Esperamos la respuesta del usuario
            user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
            n_user_input = state_machine.normalize_text(user_input)
                
            # Salimos del bucle en caso de que el usuario lo desee
            if n_user_input == "salir":
                phase = "FAREWELL"
                state = "normal"
                break 
                
            else:
                # En caso contrario, actualizamos `phase` i `state`
                phase, state, variant = state_machine.StateMachine(telephone, phase, 
                                                                    state, user_input)
                    
                # Actualizar variables
                last_bot_output = bot_output
                last_user_input = user_input
                    
                # Actualizar memoria: Guardar la nueva información relevante en la BD
                db.add_user_info(telephone, f"{conversation_history_path}.bot_output_{j}", bot_output)
                db.add_user_info(telephone, f"{conversation_history_path}.user_input_{j}", user_input)
                j += 1
                    
                # Rompemos el bucle si llegamos a phase `FAREWELL`    
                if phase == "FAREWELL":
                    break
    
    
    #---------------------------------------------------------------------------------------------------#        
    ### 6. FAREWELL
    #---------------------------------------------------------------------------------------------------#
    elif phase == "FAREWELL":
        farewell = generate_output.farewell(state)
        time.sleep(1.5)
        print(f"\nBOT: {farewell}")
        print("\n[Finalizando sesión de apoyo...]")
        
        # Obtenemos un resumen de la sessión y la añadimos a la BD
        conversation_history = db.conversation_history(telephone)
        summary = db.session_summary(telephone)
        db.add_user_info(telephone, f"{current_time}_session.summary", summary)
        
        return
    
    
    ### ERROR OR OTR
    else:
        return
    

#######################################################################################################
# Example
telephone = 1234

main_prova(telephone)