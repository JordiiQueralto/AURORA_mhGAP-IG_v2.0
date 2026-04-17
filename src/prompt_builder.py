def presentation_prompt_generation(memory):
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
   que tienes sobre el usuario

   # REGLA DE MEMORIA: 
   {memory}

   # TAREA:
   1. Saluda al usuario dándole la bienvenida de nuevo.
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


def prompt_generation(last_bot_output, last_user_input, nucleo, memory):
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
   """
   
   return prompt


def summary_prompt_generation(conversation_history):
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
   """
   
   return prompt


def prompt_response_classification(question, response, triggers):
   """
   Generates a prompt for the LLM to classify a response based on predefined triggers.
   Args:
      - question (str): The original question (bot output).
      - response (str): The user's response to classify (user input).
      - triggers (dict): A dictionary of predefined triggers for classification.
   Returns:
      - prompt (str): The generated prompt for the LLM.
   """
   prompt = f"""
   # ROL
   Eres un asistente de clasificación de respuestas para una línea de prevención del suicidio.
   
   # ENTRADA
   - Pregunta original del bot: "{question}"
   - Respuesta del usuario: "{response}"
   
   # TRIGGERS DE CLASIFICACIÓN
   {triggers}
   - `trigger_ambiguity` hace referencia a que el usuario no ha entendido la pregunta.
   - `trigger_evasion` hace referencia a que el usuario evade la pregunta.
   - `trigger_negative` hace referencia a que el usuario se niega explicitamenta a responder.
   - `trigger_hostility` hace referencia a que el usuario se muestra hostil hacia el bot.
   - `trigger_yes` respuesta afirmativa clara.
   - `trigger_no`: respuesta negativa clara.
   - `trigger_non_classificable`: la respuesta no encaja en ninguna de las categorías anteriores.
   
   # TAREA
   1. Analiza la respuesta del usuario y clasifícala según los triggers proporcionados:
      - En caso de pertenecer a `trigger_ambiguity` devuelve "ambiguity".
      - En caso de pertenecer a `trigger_evasion` devuelve "evasion".
      - En caso de pertenecer a `trigger_negative` devuelve "negative".
      - En caso de pertenecer a `trigger_hostility` devuelve "hostility".
      - En caso de pertenecer a `trigger_yes` devuelve "yes".
      - En caso de pertenecer a `trigger_no` devuelve "no".
      - En caso de pertenecer a `trigger_non_classificable` devuelve "non_classificable".
   2. Aunque no aparezca ninguna palabra de la `response` explicitamente en los triggers, 
   clasifícala según el sentido general de la respuesta.
   3. Devuelve solo la clasificación sin explicaciones adicionales.
   """
   return prompt