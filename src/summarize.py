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
    memory = db.user_info(telephone)
    
    if not memory:
        return None

    # Filter keys that contain "_session_summary"
    summary_keys = [k for k in memory if "_session_summary" in k]
    
    # Find the latest summary key based on the timestamp in the key
    latest_key = None
    if summary_keys:
        latest_key = max(
            summary_keys,
            key=lambda k: datetime.strptime(
                k.split("_session_summary")[0],
                "%Y-%m-%d %H:%M:%S"))

    # Build filtered memory with only the desired keys
    filtered_memory = {k: memory[k] for k in ("name", "age", "call_reason") if k in memory}
    
    if latest_key:
        filtered_memory[latest_key] = memory[latest_key]

    return filtered_memory


# Example

##telephone = 1234

##memory = db.user_info(telephone)
##print(memory)
##print()

##memory = memory_summary(telephone)
##print(memory)