from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Connection to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["CHATBOT_mhGAP"]
users = db["users"]  # collection


def is_new(telephone:int) -> bool:
    """
    Verifies if a user with the given phone number exists in the database.
    Args:
        - telephone (int): The phone number to check.
    Returns:
        - bool: False if the user exists, True otherwise.
    """
    user = users.find_one({"telephone": telephone})
    
    if user:
        print("\n[Usuario encontrado en la base de datos.]")
        return False
    else:
        print("\n[Usuario no encontrado. Es un nuevo usuario.]")
        return True


def create_user(telephone, is_new):
    """
    Creates a new user in the database if they do not already exist.
    Args:
        - telephone (int): The phone number of the user to create.
    Returns:
        - None
    """
    users.create_index("telephone", unique=True)

    try:
        if is_new == True:
            users.insert_one({"telephone": telephone})
            print("\n[Usuario creado correctamente.]")
            return
        else:
            return
    except DuplicateKeyError:
        print("\n[Error: El usuario ya existe.]")
        return


def add_user_info(telephone, key, value):
    """
    Adds information to an existing user in the database.
    Args:
        - telephone (int): The phone number of the user.
        - key (str): The field to update.
        - value (Any): The value to set for the field.
    Returns:
        - None
    """
    users.update_one({"telephone": telephone}, {"$set": {key: value}})


def user_status(telephone: int) -> str:
    user = users.find_one({"telephone": telephone})
    status = user.get("USER_TERMS", {}).get("status")
    return status


def user_info(telephone):
    """
    Retrieves user information (excluding the ID) based on the provided phone number.
    Args:
        - telephone (int): The phone number of the user to retrieve.
    Returns:
        - user(dict): The user information if found, None otherwise.
    """
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    if user:
        return user
    else:
        print("\n[Usuario no encontrado.]")
        return None
    
    
def conversation_history(telephone):
    """
    Creates a dictionary with all interaction history fields (user_input_i and bot_output_i)
    existing in the conversation history of the user with the given phone number.
    Args:
        - telephone (int): The phone number of the user.
    Returns:
        - history_dictionary (dict): A dictionary containing all interaction history fields.
    """
    # Get the user information
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    
    if not user:
        print("\n[Error: Usuario no encontrado.]")
        return {}
    
    # Create a dictionary to store the history
    history_dictionary = {}
    
    # Search for all interaction keys
    for key in sorted(user.keys()):
        if key.startswith("user_input_") or key.startswith("bot_output_"):
            history_dictionary[key] = user[key]
    
    return history_dictionary


def save_flow(telephone, phase, state):
    """"""
    add_user_info(telephone, "checkpoint.phase", phase)
    add_user_info(telephone, "checkpoint.state", state)
    return


def resume_conversation(telephone):
    """"""
    
    # Get the user information
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    
    if not user:
        print("\n[Error: Usuario no encontrado.]")
        return {}
    
    # Obtain last phase and state registered
    else:
        phase = user.get("checkpoint", {}).get("phase")
        state = user.get("checkpoint", {}).get("state")
        return (phase, state)
    
    
def user_latest_summary(telephone, latest_key):
    """"""

    # Get the user information
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    
    if not user:
        print("\n[Error: Usuario no encontrado.]")
        return {}
    
    # Obtain last summary
    else:
        latest_summary = user.get(f"{latest_key}", {}).get("summary")
        return latest_summary


def session_keys(telephone: int):
    pipeline = [
        # 1. Buscamos al usuario
        {"$match": {"telephone": telephone}},
        # 2. Convertimos el documento en un array de llaves/valores
        {"$project": {"all_keys": {"$objectToArray": "$$ROOT"}}},
        # 3. Nos quedamos solo con los nombres de las llaves (k) 
        # que contienen "_session"
        {"$project": {
            "session_keys": {
                "$filter": {
                    "input": "$all_keys.k",
                    "as": "key",
                    "cond": {"$regexMatch": {"input": "$$key", "regex": "_session"}}
                }
            },
            "name": 1,      # Aprovechamos para traer el nombre
            "PROFILE": 1    # y el perfil, que son ligeros
        }}
    ]
    
    result = list(users.aggregate(pipeline))
    return result if result else None


