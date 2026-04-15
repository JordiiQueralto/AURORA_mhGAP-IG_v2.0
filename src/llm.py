from google import genai
from google.genai import types

# Configuración del cliente con tu API Key
# Puedes pasar la llave directamente o usar la variable de entorno GOOGLE_API_KEY
client = genai.Client(api_key="TU_API_KEY_AQUI")

def enviar_mensaje_gemini(prompt: str) -> str:
    """
    Envía un mensaje usando el cliente moderno de Gemini y retorna el texto.
    """
    try:
        # Usamos el modelo solicitado o el más reciente disponible
        response = client.models.generate_content(
            model="gemini-2.0-flash", # O gemini-1.5-flash según disponibilidad
            contents=prompt
        )
        
        # Retornamos el texto de la respuesta
        return response.text

    except Exception as e:
        return f"Ocurrió un error en la solicitud: {str(e)}"


####################################################################################
# Ejemplo
mi_prompt = """
### ROL
   Eres un asistente virtual avanzado con capacidad de memoria y síntesis.

### RESTRICCIONES DE MEMORIA
   {
       'name': 'Juan', 
       'edad': 30, 
       'ultima_conversacion': 'Tristeza por la pérdida de su mascota'
   }

### CONTEXTO Y ESTILO
   Debes seguir esta guía de estilo para la introducción: "Para poder entender 
   mejor cómo te encuentras tengo que hacerte una pregunta."

### NÚCLEO OBLIGATORIO (COPIAR TEXTUALMENTE)
   "En este momento, o recientemente, ¿te has hecho daño físico de alguna forma, 
   como heridas, haber tomado algo que te pudiera hacer mal, o algo similar?"

### ENTRADA DEL USUARIO
   "He estado teniendo malos pensamientos últimamente."
       
### TAREA
   1. Redacta un INICIO empático que conecte la entrada del usuario con la guía 
   de estilo y la memoria. Esta no debe tener mas de 40 palabras. La guia de estilo
   no tiene porque ser mencionada literalmente, es solo para que el LLM sepa el tono 
   y enfoque a usar.
   2. Pega a continuación el NÚCLEO OBLIGATORIO sin modificar ni una sola palabra.
   3. No añadas despedidas ni texto adicional después del núcleo."""
   
resultado = enviar_mensaje_gemini(mi_prompt)
    
print("Respuesta de Gemini:")
print(resultado)