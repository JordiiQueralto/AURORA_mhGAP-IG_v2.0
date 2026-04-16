import db
import generate_responses

def main_prova(telephone):
    ### 1. Verificar si el usuario es nuevo o existente
    print(f"\n[Procesando llamada de: {telephone}...]")

    is_new = db.is_new(telephone)
    memory = db.user_info(telephone)

    context_guide = """Para poder entender mejor cómo te encuentras tengo que 
    hacerte una pregunta."""

    nucleo = """¿En este momento, o recientemente, te has hecho daño físico de alguna 
    forma, como heridas, haber tomado algo que te pudiera hacer mal, o algo similar?"""

    ### 2. Presentación del asistente y aceptación de términos (primera vez)
    ###    Retomar conversación (si no es la primera vez)
    welcome = generate_responses.presentation(is_new, memory)
    print(f"\nBOT: {welcome}")

    # Aceptacion terminos y condiciones
    if is_new == True:
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        if user_input.strip().lower() not in ("sí, acepto", "si, acepto"):
            print("\nBOT: Lo siento, no podemos continuar sin tu aceptación. Finalizando sesión.")
            exit()
        else:
            print("\nBOT: Gracias por aceptar. Estoy aquí para ayudarte.")
        
    #### 3. Bucle de conversación por consola
    while True:
        # Capturamos la entrada del usuario directamente desde la terminal
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
            
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n[Finalizando sesión de apoyo...]")
            break
                
        bot_output = generate_responses.response(user_input, context_guide, nucleo, memory)
        print(f"\nBOT: {bot_output}")

#######################################################################################################
# Example
telephone = 123456

main_prova(telephone)