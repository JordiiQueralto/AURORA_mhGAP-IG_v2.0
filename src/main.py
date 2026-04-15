import voice_service
import state_machine
import promp_builder
import llm
import db

def presentation(numero_telefono):
    # 1. Consulta de Memoria en MongoDB
    datos_usuario, is_new = db.obtener_historial_usuario(numero_telefono)
    memory = datos_usuario.get("resumen_memoria", "")
    
    # 2. Crear prompt en caso de llamada recurrente
    if is_new:
        saludo = """Hola. Soy un asistente de apoyo en salud mental. Estoy aquí 
        para escucharte y acompañarte, pero quiero que sepas desde el principio 
        que no soy un profesional médico. No puedo darte diagnósticos ni recetarte 
        nada. Lo que sí puedo hacer es estar contigo, ayudarte a entender cómo te 
        sientes, y si lo necesitas, conectarte con alguien que pueda ayudarte mejor. 
        Guardaré las cosas más importantes y si en algún momento creo que puedes 
        estar en riesgo, te lo diré y buscaremos ayuda juntos. ¿Estás de acuerdo?"""
    else:
        # Generamos un prompt específico para que Gemini use la memoria de 
        # forma natural
        prompt = promp_builder.presentation_prompt_generation(memory)
        saludo = llm.generar_saludo(prompt)
        
    # 3. Salida: Texto a Voz
    print(f"Bot (Saludo): {saludo}")
    voice_service.text_to_speech(saludo)

   
def iniciar_conversacion(numero_telefono):
    # 1. Consulta de Memoria en MongoDB
    datos_usuario, es_nuevo = db.obtener_historial_usuario(numero_telefono)
    memoria = datos_usuario.get("resumen_memoria", "")

    # 2. Entrada: Voz a Texto
    print(f"Procesando llamada de: {numero_telefono}...")
    user_input = voice_service.speech_to_text("user_input.mp3")
    print(f"Usuario: {user_input}")

    # 3. Lógica: Determinar Estado
    context_guide, nucleo = state_machine.determinar_estado(user_input)
    
    # 4. Construcción: Crear el Prompt incluyendo la memoria de la BD
    prompt = promp_builder.prompt_generation(
        user_input, 
        context_guide, 
        nucleo, 
        memoria, 
        es_nuevo
    )

    # 5. Inteligencia: Generar Respuesta con Gemini
    respuesta_texto = llm.generar_respuesta(prompt)
    print(f"IA: {respuesta_texto}")

    # 6. Salida: Texto a Voz
    voice_service.text_to_speech(respuesta_texto)
    
    # 7. Persistencia: Guardar la nueva interacción
    db.guardar_interaccion(numero_telefono, user_input, respuesta_texto)
    print("Conversación guardada en BD.")

if __name__ == "__main__":
    # Ejemplo con un número ficticio
    NUMERO_ENTRANTE = "+34600000000"
    
    presentation(NUMERO_ENTRANTE)
    
    while True:
        iniciar_conversacion(NUMERO_ENTRANTE) 