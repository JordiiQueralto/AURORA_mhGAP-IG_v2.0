import prompt_builder
import llm
import db

def welcome(status, memory):
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
        Hola. Soy un asistente de apoyo en salud mental. Estoy aquí 
        para escucharte y acompañarte, pero quiero que sepas desde el principio 
        que no soy un profesional médico. No puedo darte diagnósticos ni recetarte 
        nada. Lo que sí puedo hacer es estar contigo, ayudarte a entender cómo te 
        sientes, y si lo necesitas, conectarte con alguien que pueda ayudarte mejor. 
        Guardaré las cosas más importantes y si en algún momento creo que puedes 
        estar en riesgo, te lo diré y buscaremos ayuda juntos. ¿Estás de acuerdo?
        En caso afirmativo, di: "Sí, acepto"."""
        
        # Fix the format
        bot_output = " ".join(bot_output.split())
        
    else:
        # Existing user
        # Generate a specific prompt for LLM to use the memory in the welcome message
        prompt = prompt_builder.presentation_prompt(memory)
        bot_output = llm.send_prompt(prompt)
        
    # Return the generated welcome message
    return bot_output
        

def use_case_class(conversation_history):
    
    prompt = prompt_builder.use_case_prompt(conversation_history)
    use_case = llm.send_prompt(prompt, 0.0)
    
    if use_case in ["EMERGENCY", "ASSISTANCE", "TALK", "MISENSE"]:
        return use_case 
    
    else:
        use_case = "ASSISTANCE"
        return use_case
    
     
def bot_output(last_bot_output, last_user_input, nucleo, memory):
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


def bot_output_image(phase, state):
    image_path_user = None 
    image_path_family = None
    
    if phase == "DEP_PROTOCOLS":
        return image_path_user, image_path_family
    
    elif phase == "SUI_PROTOCOLS":
        if state == "1":
            image_path_user = None
            image_path_family = "images/SUI/Emergency/family_esp.png"
        elif state == "2":
            image_path_user = "images/SUI/Psicoeducation/user_esp.png"
            image_path_family = "images/SUI/Psicoeducation/family_esp.png"

    return image_path_user, image_path_family


def farewell(state):
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
    
    # Create a prompt for the LLM to summarize the session
    prompt = prompt_builder.session_valoration_prompt(conversation)
    valoration = llm.send_prompt(prompt)
    return valoration