import prompt_builder
import llm
import textwrap

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
        prompt = prompt_builder.presentation_prompt_generation(memory)
        bot_output = llm.send_prompt(prompt)
        
    # Return the generated welcome message
    return bot_output
        
     
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
    prompt = prompt_builder.prompt_generation(
        last_bot_output,
        last_user_input, 
        nucleo, 
        memory,
    )

    # Generate the response using the LLM
    bot_output = llm.send_prompt(prompt)
    return bot_output


def farewell():
    """
    Generates a farewell message for the user.
    Returns:
        - farewell(str): The farewell message.
    """
    farewell_message = """Gracias por confiar en mí hoy. Espero haber podido ayudarte. 
    Recuerda que siempre puedes llamar cuando lo necesites. Cuídate mucho."""
    return farewell_message


def session_summary(memory):
    """
    Generates a summary of the session based on the conversation history.
    Args:
        - memory (dict): The user's memory with all interactions.
    Returns:
        - summary (str): The summary of the session.
    """
    # Create a prompt for the LLM to summarize the session
    prompt = prompt_builder.summary_prompt_generation(memory)
    summary = llm.send_prompt(prompt)
    return summary


def response_classification(question, response, triggers):
    """
    Generates a classification for the user's response based on predefined triggers.
    Args:
        - question (str): The original question (bot output).
        - response (str): The user's response to classify (user input).
        - triggers (dict): A dictionary of predefined triggers for classification.
    Returns:
        - classification (str): The classification result based on the triggers.
    """
    prompt = prompt_builder.prompt_response_classification(question, response, triggers)
    classification = llm.send_prompt(prompt)
    
    return classification