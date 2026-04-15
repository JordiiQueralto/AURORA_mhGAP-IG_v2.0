import promp_builder
import llm

def presentation(is_new, memory):
    # 1. Saludo inicial
    if is_new:
        saludo = """Hola. Soy un asistente de apoyo en salud mental. Estoy aquí 
        para escucharte y acompañarte, pero quiero que sepas desde el principio 
        que no soy un profesional médico. No puedo darte diagnósticos ni recetarte 
        nada. Lo que sí puedo hacer es estar contigo, ayudarte a entender cómo te 
         sientes, y si lo necesitas, conectarte con alguien que pueda ayudarte mejor. 
        Guardaré las cosas más importantes y si en algún momento creo que puedes 
        estar en riesgo, te lo diré y buscaremos ayuda juntos. ¿Estás de acuerdo?"""
    else:
        # Generamos un prompt específico para que Gemini use la memoria de forma natural
        prompt = promp_builder.presentation_prompt_generation(memory)
        saludo = llm.generar_saludo(prompt)
        
    # 2. Salida
    print(f"BOT: {saludo}")

   
def iniciar_conversacion(numero_telefono, user_input, context_guide, nucleo, memory, is_new):
    # 1. Visualización de la entrada
    print(f"\n[Procesando llamada de: {numero_telefono}...]")
    print(f"USER: {user_input}")
    
    # 2. Construcción: Crear el Prompt incluyendo la memoria de la BD
    prompt = promp_builder.prompt_generation(
        user_input, 
        context_guide, 
        nucleo, 
        memory, 
        is_new
    )

    # 3. Inteligencia: Generar Respuesta con Gemini
    respuesta_texto = llm.generar_respuesta(prompt)
    print(f"IA: {respuesta_texto}")


if __name__ == "__main__": # Cambiado a __main__ para que ejecute directamente
    # Ejemplo con un número ficticio y datos de prueba
    NUMERO_ENTRANTE = "+34600000000"
    is_new = True
    memory = {
        'name': 'Juan', 
        'edad': 30, 
        'ultima_conversacion': 'Tristeza por la pérdida de su mascota'
        }
    context_guide = """Para poder entender mejor cómo te encuentras tengo que hacerte 
    una pregunta."""
    nucleo = """En este momento, o recientemente, ¿te has hecho daño físico de alguna 
    forma, como heridas, haber tomado algo que te pudiera hacer mal, o algo similar?"""
    
    # Presentación inicial
    presentation(is_new, memory)
    
    # Bucle de conversación por consola
    while True:
        # Capturamos la entrada del usuario directamente desde la terminal
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("Finalizando sesión de apoyo...")
            break
            
        iniciar_conversacion(NUMERO_ENTRANTE, user_input, context_guide, nucleo, memory, is_new)