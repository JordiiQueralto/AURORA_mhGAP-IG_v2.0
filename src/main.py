import voice_service
import state_machine
import db
import generate_responses
import phrase_dictionary
import summarize
import datetime

def main(telephone):
    ### 1. Verificar si el usuario es nuevo o existente
    print(f"\n[Procesando llamada de: {telephone}...]")

    is_new = db.is_new(telephone)
    memory = summarize.memory_summary(telephone)


    ### 2. Presentación del asistente y aceptación de términos (primera vez)
    ###    Retomar conversación (si no es la primera vez)
    welcome = generate_responses.presentation(is_new, memory)
    print(f"\nBOT: {welcome}")
    voice_service.text_to_speech(welcome)
    
    
    ### 3. En caso de ser usuario nuevo, espera la respuesta del usuario para 
    ### aceptar términos y condiciones 
      
    if is_new == True:
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        user_input = voice_service.STT("user_input.mp3")
        if user_input.strip().lower() not in ("sí, acepto", "si, acepto"):
            print("\nBOT: Lo siento, no podemos continuar sin tu aceptación. Finalizando sesión.")
            voice_service.TTS("Lo siento, no podemos continuar sin tu aceptación. Finalizando sesión.")
            exit()
        else:
            print("\nBOT: Gracias por aceptar. Estoy aquí para ayudarte.")
            voice_service.TTS("""Gracias por aceptar. Estoy aquí para ayudarte. 
                              Qué te gustaría compartir conmigo hoy?""")
        
    ### 4. Bucle de conversación
    while True:
        
        # Esperamos la respuesta del ususario
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        user_input = voice_service.STT("user_input.mp3")
        
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n[Finalizando sesión de apoyo...]")
            break
        
        # Lógica: Determinar estado y información para formar la pregunta
        state = state_machine.determine_state(user_input)
        context_guide, nucleo = phrase_dictionary.bot_output_info(state)
        
        # Generar respuesta con Gemini usando la memoria de la BD
        bot_output = generate_responses.bot_output(user_input, context_guide, nucleo, memory)
        
        # Salida: Pregunta generada por Gemini
        print(f"\nBOT: {bot_output}")
        voice_service.TTS(bot_output)
        
        # Actualizar memoria: Guardar la nueva información relevante en la BD
        db.add_user_info(telephone, f"user_input_{i}", user_input)
        db.add_user_info(telephone, f"bot_output_{i}", bot_output)
        i += 1
        
    ### 5. Finalizar sesión:
    # Despedida
    farewell = generate_responses.farewell()
    print(f"\nBOT: {farewell}")
    voice_service.TTS(farewell)
    
    # Toma la informacion guardada en la sesión y hace un resumen para el equipo de apoyo
    # humano y para futuras interacciones con el usuario. Luego, borra el historial de 
    # interacciones individuales.
    datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = summarize.session_summary(telephone)
    db.add_user_info(telephone, f"{datetime}_session_summary", summary)
    db.delete_interaction_history(telephone)



if __name__ == "__main__":
    # Example
    NUMERO_ENTRANTE = "1234"
    
    main(NUMERO_ENTRANTE)