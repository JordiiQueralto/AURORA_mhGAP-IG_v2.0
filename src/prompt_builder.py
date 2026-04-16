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



def prompt_generation(user_input, context_guide, nucleo, memory):
   """
   Generates a prompt for the LLM by combining user input, a style guide, 
   a fixed core question, and memory from MongoDB.
   Args:
      - user_input (str): The current user input.
      - context_guide (str): The style guide for the introduction.
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

   # CONTEXTO Y ESTILO
   Debes seguir esta guía de estilo para la introducción: "{context_guide}"

   # NÚCLEO OBLIGATORIO (COPIAR TEXTUALMENTE)
   "{nucleo}"

   # ENTRADA DEL USUARIO
   "{user_input}"
       
   # TAREA
   1. Redacta un INICIO empático que conecte la entrada del usuario con la guía 
   de estilo y la memoria. Esta no debe tener mas de 40 palabras. La guia de estilo
   no tiene porque ser mencionada literalmente, es solo para que el LLM sepa el tono 
   y enfoque a usar.
   2. Pega a continuación el NÚCLEO OBLIGATORIO sin modificar ni una sola palabra.
   3. No añadas despedidas ni texto adicional después del núcleo.
   4. Devuelve la respuesta en un solo bloque de texto.
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