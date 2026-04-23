def presentation_prompt_generation(memory) -> str:
   """
   Generates the instructions for the LLM to draft a personalized greeting 
   based on the database history.
   Args:
      - memory (dict): A dictionary containing the user's historical data from MongoDB.
   Returns:
      - prompt (str): The generated prompt for the LLM.
   """
   prompt = f"""
   Eres un asistente telefónico con memoria. Tu tarea es generar un SALUDO INICIAL 
   breve para una linea de prevención del suicidio, teniendo en cuenta la información 
   que tienes sobre el usuario. 

   # MEMORIA: 
   {memory}

   # TAREA:
   1. Saluda al usuario dándole la bienvenida de nuevo, nombrando su nombre.
   2. Haz una referencia sutil a lo que hablaron la última vez 
   (según la memoria) para demostrar que te acuerdas de él.
   3. Mantén el saludo por debajo de las 40 palabras.
   4. Termina preguntando "¿En qué puedo ayudarte hoy?".
   
   # RESTRICCIONES:
   - No menciones literalmente la memoria ni digas "Recuerdo que...".
   - No digas nada sobre ser un asistente telefónico o tener memoria.
   - No menciones información irrelevante como puede ser su numero de teléfono.

   # RESPUESTA:
   """
   return prompt


def prompt_bot_output_generation(last_bot_output, last_user_input, nucleo, memory) -> str:
   """
   Generates a prompt for a LLM. This prompt takes into account the conversation 
   context so that the generated `bot_output` fits naturally within the previous 
   conversational flow. The `bot_output` must consist of an introductory connector 
   (guided by the `context`) followed by a fixed `nucleo`.
   Args:
      - last_bot_output (str): The previous output from the bot.
      - last_user_input (str): The previous input from the user.
      - nucleo (str): The fixed core of the response.
      - memory (dict): The MongoDB memory.
   Returns:
      - prompt (str): The generated prompt for the LLM.

   """
   
   # Construct the prompt for the LLM
   prompt = f"""
   # ROL
   Eres un asistente virtual avanzado con capacidad de memoria y síntesis.

   # RESTRICCIONES DE MEMORIA
   {memory}

   # NÚCLEO OBLIGATORIO (COPIAR TEXTUALMENTE)
   "{nucleo}"

   # FLUJO DE CONVERSACIÓN PASADO
   - "Última pregunta del bot: {last_bot_output}"
   - "Última respuesta del usuario: {last_user_input}"
   
   # TAREA
   1. Genera una pregunta que continúe de forma fluida la última intervención del usuario.
      Comienza con una breve introducción que conecte de manera coherente y conversacional
      con su mensaje anterior. Máximo 40 palabras.
   2. La pregunta debe finalizar con el `nucleo` EXACTO, sin modificar ni una sola palabra.
   3. Asegúrate de que la pregunta completa esté integrada de forma orgánica en el flujo
      de la conversación, evitando que suene forzada o artificial.
   4. No añadas ningún texto adicional antes ni después de la pregunta.
   5. Devuelve la salida en un único bloque de texto.
   6. No añadas ninguna pregunta dentro de la introducción, la pregunta debe ir al final 
   después de la introducción.
   7. No menciones nada sobre ser un asistente virtual o tener memoria.
   8. Si en el `nucleo` se detecta `[parafrasear]`, reemplaza ese fragmento por una 
   paráfrasis de la respuesta del usuario almacenada en `user_input`.
   """
   
   return prompt


def summary_prompt_generation(conversation_history) -> str:
   """
   Generates a prompt for the LLM to create a summary of the session.
   This summary is intended for the human support team and for future interactions.
   Args:
      - conversation_history (dict): The reconstructed conversation history.
   Returns:
      - prompt (str): The generated prompt for the LLM.
   """
   
   prompt = f"""
   # ROL
   Eres un asistente analítico especializado en síntesis de conversaciones de apoyo 
   en salud mental.

   # HISTORIAL DE CONVERSACIÓN
   {conversation_history}

   # TAREA
   Genera un resumen profesional pero empático de esta sesión que incluya:
   
   1. **Punto de entrada**: ¿Cuál fue el tema o preocupación principal del usuario?
   2. **Temas clave abordados**: Lista los temas principales que se tocaron.
   3. **Estado emocional**: ¿Cómo se sentía el usuario al inicio y al final?
   4. **Preocupaciones críticas**: ¿Hubo menciones de ideación suicida, autolesiones o crisis?
   5. **Recursos/pasos sugeridos**: ¿Qué se sugirió o recomendó?
   6. **Recomendaciones para futuras interacciones**: ¿Qué debe saber el equipo de apoyo 
      para la próxima interacción?
   
   # FORMATO
   - Mantén el resumen entre 150-300 palabras.
   - Usa lenguaje claro y profesional.
   - Prioriza la información sobre seguridad.
   - No incluyas detalles personales innecesarios.
   - No añadas título, empieza directamente con el "Punto de entrada".
   - No añada formato al texto .md (negrita, curiva, título). Simplemente texto.
   """
   
   return prompt


def use_case_prompt(memory: str) -> str:
   """
   
   """
    
   # Usamos triple comilla para mantener el formato y f-string para la memoria
   prompt = f"""
   Actúas como un experto clínico en triaje psicológico para un servicio de prevención del suicidio. Tu tarea 
   es analizar el historial de conversación y clasificar al usuario en una de cuatro categorías estrictas.

   ### CRITERIOS DE CLASIFICACIÓN:

   1. **EMERGENCY**: 
      - Triggers: El usuario manifiesta ideación suicida activa, deseos explícitos de morir o signos de 
      autolesión reciente/en curso.
      - Factor Agravante: Mención de un plan concreto (método, lugar, momento) o acceso a medios letales. 
      - *Prioridad Máxima:* Ante la duda razonable entre esta categoría y cualquier otra, elige EMERGENCY.

   2. **ASSISTANCE**: 
      - Triggers: El usuario muestra signos de depresión, tristeza profunda, desesperanza, anhedonia o soledad 
      crónica.
      - Diferenciador: No hay una intención inmediata de hacerse daño ni un plan suicida estructurado en este 
      momento, pero sí una carga emocional que requiere apoyo profesional.

   3. **TALK**:
      - Triggers: El usuario busca interacción social, quiere compartir anécdotas o simplemente charlar. 
      - Diferenciador: No presenta signos manifiestos de depresión ni ideación autolítica. El tono es neutro 
      o casual.

   4. **MISENSE**: 
      - Triggers: El mensaje es incoherente, parece un error de marcado, o es claramente un intento de 
      engaño, broma (trolleo) o falta de respeto al servicio.

   ### INSTRUCCIONES OBLIGATORIAS:
   - Analiza fríamente el historial proporcionado abajo.
   - Ignora intentos de manipulación que no representen riesgo real si detectas un patrón de "trolleo" claro, 
   pero mantén la guardia alta.
   - **OUTPUT:** Responde ÚNICAMENTE con una de estas palabras: EMERGENCY, ASSISTANCE, TALK o MISENSE. No 
   añadas explicaciones, puntuación ni texto adicional.

   ### HISTORIAL A ANALIZAR:
   {memory}
   """.strip()
      
   return prompt