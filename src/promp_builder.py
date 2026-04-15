def presentation_prompt_generation(memory):
   """
   Genera las instrucciones para que el LLM redacte un saludo 
   personalizado basado en el historial de la base de datos.
   """
   prompt = f"""
   Eres un asistente telefónico con memoria. Tu tarea es generar un 
   SALUDO INICIAL breve.

   REGLA DE MEMORIA: 
   {memory}

   TAREA:
   1. Saluda al usuario dándole la bienvenida de nuevo.
   2. Haz una referencia sutil a lo que hablaron la última vez 
   (según la memoria) para demostrar que te acuerdas de él.
   3. Mantén el saludo por debajo de las 40 palabras.
   4. Termina preguntando "¿En qué puedo ayudarte hoy?".

   RESPUESTA:
   """
   return prompt



def prompt_generation(user_input, context_guide, nucleo, memory):
   """
   Ensambla todas las piezas: entrada del usuario, guía de estilo de la 
   máquina de estados, el núcleo fijo y la memoria de MongoDB.
   """
   # Construcción del prompt con delimitadores claros para la IA
   prompt = f"""
   ### ROL
   Eres un asistente virtual avanzado con capacidad de memoria y síntesis.

   ### RESTRICCIONES DE MEMORIA
   {memory}

   ### CONTEXTO Y ESTILO
   Debes seguir esta guía de estilo para la introducción: "{context_guide}"

   ### NÚCLEO OBLIGATORIO (COPIAR TEXTUALMENTE)
   "{nucleo}"

   ### ENTRADA DEL USUARIO
   "{user_input}"
       
   ### TAREA
   1. Redacta un INICIO empático que conecte la entrada del usuario con la guía 
   de estilo y la memoria. Esta no debe tener mas de 40 palabras. La guia de estilo
   no tiene porque ser mencionada literalmente, es solo para que el LLM sepa el tono 
   y enfoque a usar.
   2. Pega a continuación el NÚCLEO OBLIGATORIO sin modificar ni una sola palabra.
   3. No añadas despedidas ni texto adicional después del núcleo.
    """
   
   return prompt

####################################################################################
# Ejemplo
memory = {
   "name": "Juan",
   "edad": 30,
   "ultima_conversacion": "Tristeza por la pérdida de su mascota"
}

user_input = "He estado teniendo malos pensamientos últimamente."
context_guide = """Para poder entender mejor cómo te encuentras tengo que hacerte 
una pregunta.""" 
nucleo = """En este momento, o recientemente, ¿te has hecho daño físico de alguna 
forma, como heridas, haber tomado algo que te pudiera hacer mal, o algo similar?"""

prompt = prompt_generation(user_input, context_guide, nucleo, memory)
print("Prompt generado para Gemini:")
print(prompt)