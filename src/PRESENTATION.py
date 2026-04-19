import db
import summarize
import generate_output
import datetime
import state_machine

def Init(telephone):
    print(f"\n[Procesando llamada de: {telephone}...]")
    
    is_new = db.is_new(telephone)
    db.create_user(telephone, is_new)
    
    phase = "PRESENTATION"
    state = ""
    memory = ""
    
    if is_new:
        status = "rejected"   
    else:
        status = db.user_status(telephone)
        if status is None:
            status = "rejected"

    bot_output = generate_output.welcome(status, memory)
    print(f"\nBOT: {bot_output}")

    # Si había rechazado les términos préviamente o es nuevo
    if status == "rejected":
        
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        key = "USER_TERMS"
        n_user_input = state_machine.normalize_text(user_input)

        if n_user_input != "si acepto":
            value = {
                "status": "rejected",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            db.add_user_info(telephone, key, value)
            
            bot_output = "Lo siento, no podemos continuar sin tu aceptación."
            print(f"\nBOT: {bot_output}")
        
            phase = "FAREWELL"
            state = "exit"

            return (bot_output, user_input, phase, state, memory)
        
        elif n_user_input == "salir":
            
            phase = "FAREWELL"
            state = "exit"
            
            return (bot_output, user_input, phase, state, memory)

        else:
            value = {
                "status": "accepted",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            db.add_user_info(telephone, key, value)
            
            bot_output = "Gracias por aceptar. ¿En qué puedo ayudarte?"
            print(f"\nBOT: {bot_output}")

            user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
           
            phase = "PROFILE"
            state = "name"

            return (bot_output, user_input, phase, state, memory)

    else:
        memory = summarize.memory_summary(telephone)
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        return (bot_output, user_input, phase, state, memory)