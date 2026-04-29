from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import llm
import prompt_builder

# Connection to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["CHATBOT_mhGAP"]
users = db["users"]  # collection


def is_new(telephone:str) -> bool:
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
    
    
def get_user_info(telephone, key_part_1, key_part_2):
    
    # Get the user information
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    
    if not user:
        print("\n[Error: Usuario no encontrado.]")
        return {}
    
    # Obtain last phase and state registered
    else:
        result = user.get(f"{key_part_1}", {}).get(f"{key_part_2}")
        return result


def user_status(telephone: str) -> str:
    user = users.find_one({"telephone": telephone})
    status = user.get("USER_TERMS", {}).get("status")
    return status
    
    
def conversation_history(telephone):
    """
    Devuelve un diccionario donde cada clave es una sesión y su valor es 
    el historial de inputs/outputs de esa sesión.
    """
    # 1. Buscamos el usuario
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    
    if not user:
        print("\n[Error: Usuario no encontrado.]")
        return {}
    
    history_dictionary = {}
    
    # 2. Iteramos por las claves que terminan en '_session'
    for key, session_data in user.items():
        if key.endswith("_session") and isinstance(session_data, dict):
            
            # Accedemos al sub-objeto donde están los mensajes
            conv_inner = session_data.get("conversation_history", {})
            
            # Filtramos solo las claves de mensajes (user_input y bot_output)
            session_messages = {
                k: v for k, v in conv_inner.items() 
                if k.startswith("user_input_") or k.startswith("bot_output_")
            }
            
            # Si la sesión tiene mensajes, la añadimos al resultado final
            if session_messages:
                history_dictionary[key] = session_messages
    
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


def user_keys(telefono):
    """
    Busca un usuario por su teléfono y devuelve una lista con los nombres
    de todos sus campos registrados.
    """
    # Buscamos el documento que coincida con el teléfono
    # Nota: Si en tu BD el teléfono es un número, pásalo como int. 
    # Si es texto, asegúrate de pasarlo como string.
    user = users.find_one({"telephone": telefono})

    if user:
        # Convertimos las llaves del diccionario a una lista
        key_list = list(user.keys())
        return key_list
    else:
        return f"No se encontró ningún usuario con el teléfono: {telefono}"


def last_session_key(telephone):
    """
    Filtra las llaves que corresponden a sesiones y devuelve la más reciente.
    """
    # Obtain key list of the user
    key_list = user_keys(telephone)
    
    # Filter keys the end swith: '_session'
    sesiones = [k for k in key_list if k.endswith("_session")]
    
    if not sesiones:
        return None
    
    # Obtain the latest registered key session
    last_session = max(sesiones)
    
    return last_session


def user_memory(telephone, keys_list=["name", "age", "PROFILE"]):
    """
    Retrieves specific fields for a user identified by their telephone number.
    
    :param telephone: The user's phone number (int or str depending on your DB).
    :param keys_list: A list of strings representing the keys to retrieve.
    :return: A dictionary with the requested data or None if the user is not found.
    """
    # Create the projection dictionary: { "key_name": 1 }
    # This tells MongoDB to only return these specific fields.
    projection = {key: 1 for key in keys_list}
    
    # Obtain last session key and add it to the projection dict
    last_session = last_session_key(telephone)
    projection[f"{last_session}.summary"] = 1
    
    # We usually exclude the '_id' unless it's explicitly requested in keys_list
    if "_id" not in keys_list:
        projection["_id"] = 0

    # Perform the query
    user_data = users.find_one({"telephone": telephone}, projection)
    
    return user_data


def session_summary(telephone, current_time) -> str:
    
    # Get the user information
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    
    if not user:
        print("\n[Error: Usuario no encontrado.]")
        return {}
    
    # Obtain last summary
    else:
        
        path = f"{current_time}_session"
        conversation_history = user.get(path, {}).get("conversation_history")
        prompt = prompt_builder.summary_prompt_generation(conversation_history)
        summary = str(llm.send_prompt(prompt))
        
        return summary
    