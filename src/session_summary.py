import llm
import prompt_builder
import db

def summarize(telephone):
    """
    Generates a summary of the session for the human support team and future interactions.
    Args:
        - telephone (int): The phone number of the user whose session is to be summarized.
    Returns:
        - summary (str): The generated summary of the session.
    """
    # Retrieve the conversation history from the database
    summary_dictionary = db.conversation_history(telephone)
    
    # Create a prompt for the LLM to summarize the session
    prompt = prompt_builder.summary_prompt_generation(summary_dictionary)
    
    # Generate the summary using the LLM
    summary = llm.send_prompt(prompt)
    
    return summary