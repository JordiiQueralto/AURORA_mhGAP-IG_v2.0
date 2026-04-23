import llm
import prompt_builder
import db
from datetime import datetime

def session_summary(telephone: int) -> str:
    """
    Generate a summary of the user's session for the human support team
    and for future interactions.

    Args:
        telephone (int): Phone number of the user whose session will be summarized.

    Returns:
        str: Generated summary of the session.
    """
    summary_dictionary = db.conversation_history(telephone)
    prompt = prompt_builder.summary_prompt_generation(summary_dictionary)
    summary = str(llm.send_prompt(prompt))

    return summary


def memory_summary(telephone: int) -> dict:
    memory = db.user_info(telephone)
    
    if not memory:
        filtered_memory = {}
        return filtered_memory

    # Filter keys that contain "_session_summary"
    summary_keys = [k for k in memory if "_session" in k]
    
    # Find the latest summary key based on the timestamp in the key
    latest_key = None
    if summary_keys:
        latest_key = max(
            summary_keys,
            key=lambda k: datetime.strptime(
                k.split("_session")[0],
                "%Y-%m-%d %H:%M:%S"))

    # Build filtered memory with only the desired keys
    filtered_memory = {k: memory[k] for k in ("name", "PROFILE") if k in memory}
    
    if latest_key:
        latest_summary = db.user_latest_summary(telephone, latest_key)
        filtered_memory["last_session_summary"] = latest_summary

    return filtered_memory


# Example
#.telephone = 666

#.memory = db.user_info(telephone)
#.print(memory)
#.print()

#.memory = memory_summary(telephone)
#.print(memory)