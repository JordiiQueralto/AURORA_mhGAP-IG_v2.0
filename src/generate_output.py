import prompt_builder
import llm
import db
import textwrap

def welcome(status, memory) -> str:
    """Generates the welcome message for the user, depending on whether they 
    are new (new users or have not accepted the terms of usage previously) or 
    existing, and using memory if available.
    Args:        
        - status (str): Indicates if the user has accepted the terms of use.
        - memory (dict): The user's memory retrieved from the database.
    Returns:    
        - welcome(str): The welcome message to be presented to the user.
    """
    
    if status == "rejected":
        bot_output = """
        Hola! Me llamo Aurora y soy un asistente virtual de apoyo en salud mental basado en inteligencia artificial. No soy una persona ni un profesional sanitario: soy un sistema conversacional automatizado desarrollado como prototipo de investigación.

        Antes de empezar, necesito que entiendas bien cómo funciono y qué implica usar este servicio:

        Qué puedo hacer por ti: Escucharte, ayudarte a entender cómo te sientes y, si lo necesitas, orientarte hacia recursos profesionales de ayuda. Mi lógica se basa en la guía clínica mhGAP de la Organización Mundial de la Salud, pero mis respuestas no sustituyen en ningún caso un diagnóstico médico ni una valoración profesional.

        Cómo detecto situaciones de riesgo: Utilizo patrones de lenguaje para identificar posibles señales de alerta. Si en algún momento detecto que puedes estar en peligro, te proporcionaré los recursos de emergencia adecuados (como el 112 o el 024) directamente en pantalla. La decisión de contactar con ellos será siempre tuya.

        Tus datos: Todo lo que me cuentes se almacenará de forma segura para poder ofrecerte un mejor seguimiento. Estos datos incluyen información relativa a tu salud emocional, que solo se utilizarán con la finalidad de este servicio y nunca se compartirán con terceros sin tu consentimiento explícito. Más adelante, en la sección "Mi Círculo", podrás decidir de forma independiente si deseas activar las notificaciones a familiares de confianza o compartir información con tu centro sanitario de referencia.

        Tu derecho a retirarte: Puedes eliminar tu cuenta en cualquier momento, lo que borrará de forma inmediata y definitiva toda la información almacenada.

        Requisito de edad: Este servicio está dirigido exclusivamente a mayores de 18 años.

        Si lo has entendido y estás de acuerdo, escribe: "Sí, acepto"."""
        
        # Fix the format
        bot_output = textwrap.dedent(bot_output).strip()
        
    else:
        # Existing user
        # Generate a specific prompt for LLM to use the memory in the welcome message
        prompt = prompt_builder.presentation_prompt(memory)
        bot_output = llm.send_prompt(prompt)
        
    # Return the generated welcome message
    return bot_output
        

def use_case_class(conversation_history) -> str:
    """Classifies the conversation into EMERGENCY, ASSISTANCE, TALK, or MISENSE. Defaults to ASSISTANCE if the LLM response is unrecognized."""
    prompt = prompt_builder.use_case_prompt(conversation_history)
    use_case = llm.send_prompt(prompt, 0.0)
    
    if use_case in ["EMERGENCY", "ASSISTANCE", "TALK", "MISENSE"]:
        return use_case 
    
    else:
        use_case = "ASSISTANCE"
        return use_case
    
     
def bot_output(last_bot_output, last_user_input, nucleo, memory) -> str:
    """
    Generates a response based on the user's input and the conversation context.
    Args:
        - last_bot_output (str): The previous question from the bot.
        - last_user_input (str): The previous response from the user.
        - nucleo (str): The core question for the conversation.
        - memory (dict): The user's memory retrieved from the database.
    Returns:
        - bot_output(str): The generated response."""
        
    # Create a prompt for the LLM including the memory from the DB
    prompt = prompt_builder.prompt_bot_output(
        last_bot_output,
        last_user_input, 
        nucleo, 
        memory,
    )

    # Generate the response using the LLM
    bot_output = llm.send_prompt(prompt)
    return bot_output


def talk_mode(conversation: dict, n: int=8) -> str:
    """
    Keep up to the last n messages (including bot_output_{i} and user_input_{i}) and 
    send them to the LLM.

    Args:
       - conversation (dict): Chat history with keys like 'user_input_0', 'bot_output_0'
       - n (int): Number of turns to keep (up to n if fewer are available)

    Returns:
       - bot_output(str): LLM response
    """

    # Filter only the last n messages to avoid LLM token waste
    sorted_items = sorted(conversation.items(), key=lambda x: int(x[0].split('_')[-1])) 
    last_items = sorted_items[-n:] 
    conversation_filtered = dict(last_items)

    # Generate prompt and get response
    prompt = prompt_builder.prompt_talk_mode(conversation_filtered)
    bot_output = llm.send_prompt(prompt)

    return bot_output


def farewell(state) -> str:
    """
    Generates a farewell message for the user.
    Returns:
        - farewell(str): The farewell message.
    """
    
    if state == "normal":
        farewell_message = """Gracias por confiar en mí hoy. Espero haber podido ayudarte. 
        Recuerda que siempre puedes llamar cuando lo necesites. Cuídate mucho."""
    
    elif state == "exit":
        farewell_message = """Si cambias de opinión aquí estaré. Recuerda que siempre puedes 
        llamar cuando lo necesites. Cuídate mucho."""
        
    elif state == "age":
        farewell_message = """Lo siento, para poder continuar debes tener al menos 18 años. 
        Cuídate mucho."""
        
    # Fix the format
    farewell_message = " ".join(farewell_message.split())
    
    return farewell_message


def session_summary(telephone, session_path) -> str:
    """
    Generates a summary of the session based on the conversation history.
    Args:
        - memory (dict): The session conversation history.
    Returns:
        - summary (str): The summary of the session.
    """
    # Obtain the conversation history of the actual session
    conversation = db.get_user_info(telephone, session_path, "conversation_history")
    
    # Create a prompt for the LLM to summarize the session
    prompt = prompt_builder.session_summary_prompt(conversation)
    summary = llm.send_prompt(prompt)
    return summary


def session_valoration(telephone, session_path) -> str:
    """
    Generates a valoration of the session based on the conversation history.
    Args:
        - memory (dict): The session conversation history.
    Returns:
        - valoration (str): The valoration of the session.
    """
    # Obtain the conversation history of the actual session
    conversation = db.get_user_info(telephone, session_path, "conversation_history")
    
    # Create a prompt for the LLM to valorate the session
    prompt = prompt_builder.session_valoration_prompt(conversation)
    valoration = llm.send_prompt(prompt, 0.0)
    return valoration


def session_risk(telephone, session_path) -> str:
    """
    Generate a risk assessment of the session based on the conversation history, 
    classifying it as "BUENA", "REGULAR" or "MALA".
    Args:
        - telephone (str): The user's telephone number.
        - session_path (str): The path to the session data.

    Returns:
        str: The risk assessment of the session.
    """
    # Obtain the conversation history of the actual session
    conversation = db.get_user_info(telephone, session_path, "conversation_history")
    
    # Create a prompt for the LLM to detrmine risk of crisis
    prompt = prompt_builder.risk_level_prompt(conversation)
    risk_level = llm.send_prompt(prompt, 0.0)
    return risk_level