from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Connection to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["CHATBOT_mhGAP"]
users = db["users"]  # collection


def is_new(telephone):
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


def user_status(telephone):
    doc = users.find_one({"telephone": telephone})
    status = doc["USER_TERMS"].get("status")
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
        print("\nUsuario no encontrado.")
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


def delete_interaction_history(telephone):
    """
    Deletes all interaction history fields (user_input_i and bot_output_i)
    from a user after the session summary has been generated.
    Args:
        - telephone (int): The phone number of the user.
    Returns:
        - None
    """
    # Get the user data
    user = users.find_one({"telephone": telephone})
    
    if not user:
        print("\n[Error: Usuario no encontrado.]")
        return
    
    # Find all keys that match the pattern
    keys_to_delete = []
    for key in user.keys():
        if key.startswith("user_input_") or key.startswith("bot_output_"):
            keys_to_delete.append(key)
    
    # Delete all matching keys
    if keys_to_delete:
        delete_update = {"$unset": {key: "" for key in keys_to_delete}}
        users.update_one({"telephone": telephone}, delete_update)
        print(f"\n[Se eliminaron {len(keys_to_delete)} campos de historial de interacción.]")
    else:
        print("\n[No se encontraron campos de historial para eliminar.]")


#################################################################################################
# Example
##create_user(123456)
    
##print(f"\n¿Es nuevo el usuario? {is_new(12345)}")
    
##info = user_info(12345)
##print(f"\nInformación del usuario: {info}")

##add_user_info(123456, "name", "Jordi")
##add_user_info(123456, "bot_output_1", "Hola, ¿cómo estás?")
##add_user_info(123456, "user_input_1", "Estoy triste")
##add_user_info(123456, "bot_output_2", 
##              "Lo siento mucho. ¿Quieres contarme más sobre lo que te está pasando?")
##add_user_info(123456, "user_input_2", 
##              "No sé, me siento solo y no tengo ganas de hacer nada.")
##add_user_info(123456, "bot_output_3", 
##              """Entiendo que te sientas así. A veces, cuando estamos pasando por momentos
##              difíciles, es normal sentirse solo y sin ganas de hacer cosas. ¿Hay algo que    
##              te haya ayudado a sentirte mejor en el pasado?""")
##add_user_info(123456, "user_input_3", 
##              """No lo sé, a veces me gusta salir a caminar, pero últimamente ni eso me apetece.""")   

##info = user_info(123456)
##print(f"\nInformación del usuario: {info}")

#delete_interaction_history(123456)
##info = user_info(123456)
##print(f"\nInformación del usuario: {info}")