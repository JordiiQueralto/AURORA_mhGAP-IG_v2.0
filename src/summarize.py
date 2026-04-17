import llm
import prompt_builder
import db
from datetime import datetime

def session_summary(telephone):
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


def memory_summary(telephone):
    """
    
    """
    
    memory = db.user_info(telephone)
    
    if not memory:
        return None

    # Filter keys that contain "_session_summary"
    summary_keys = [k for k in memory if "_session_summary" in k]
    
    if not summary_keys:
        return memory

    # Find the latest summary key based on the timestamp in the key
    latest_key = max(
    summary_keys,
    key=lambda k: datetime.strptime(
        k.split("_session_summary")[0],
        "%Y-%m-%d %H:%M:%S"))

    # Remove all summary keys except the latest one from the memory
    for key in summary_keys:
        if key != latest_key:
            del memory[key]

    return memory

####################################################################
# Example

##telephone = 123456

##memory = db.user_info(telephone)
##print(memory)
##print()

#memory = memory_summary(telephone)
##print(memory)