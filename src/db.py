from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import datetime

# ──────────────────────────────────────────────────────────────────────────────
# CONNECTION
# ──────────────────────────────────────────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017/")
db = client["CHATBOT_mhGAP"]

users       = db["users"]
specialists = db["specialists"]


# ══════════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════════

def is_new(telephone: str) -> bool:
    """Returns True if the user does not exist yet."""
    user = users.find_one({"telephone": telephone})
    if user:
        print("\n[Usuario encontrado en la base de datos.]\n")
        return False
    print("\n[Usuario no encontrado. Es un nuevo usuario.]\n")
    return True


def create_user(telephone, is_new_user):
    """Creates a new user document in the database if is_new_user is True. Silently ignores duplicate key errors."""
    users.create_index("telephone", unique=True)
    try:
        if is_new_user:
            users.insert_one({"telephone": telephone})
            print("\n[Usuario creado correctamente.]\n")
    except DuplicateKeyError:
        print("\n[Error: El usuario ya existe.]\n")


def add_user_info(telephone, key, value):
    """Sets or updates a field in the user's document using dot-notation keys."""
    users.update_one({"telephone": telephone}, {"$set": {key: value}})


def get_user_name(telephone, key="name"):
    """Returns the user's name field, or None if the user does not exist."""
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    return user.get("name") if user else None


def get_user_info(telephone, key1, key2=None):
    """Returns a top-level or nested field from the user's document. Pass key2 to retrieve a sub-key of a dict field."""
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    if not user: return None
    
    data = user.get(key1)
    
    # Si pedimos un segundo nivel y el primero es un diccionario
    if key2 and isinstance(data, dict):
        return data.get(key2)
    
    return data


def user_status(telephone: str) -> str:
    """Returns the user's terms-of-service acceptance status ('accepted' or 'rejected')."""
    user = users.find_one({"telephone": telephone})
    return user.get("USER_TERMS", {}).get("status")


def conversation_history(telephone):
    """Returns all session conversation histories for a user, grouped by session key."""
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    if not user:
        return {}
    history_dictionary = {}
    for key, session_data in user.items():
        if key.endswith("_session") and isinstance(session_data, dict):
            conv_inner = session_data.get("conversation_history", {})
            session_messages = {
                k: v for k, v in conv_inner.items()
                if k.startswith("user_input_") or k.startswith("bot_output_")
            }
            if session_messages:
                history_dictionary[key] = session_messages
    return history_dictionary


def save_flow(telephone, phase, state):
    """Persists the current phase and state as a checkpoint for session resumption."""
    add_user_info(telephone, "checkpoint.phase", phase)
    add_user_info(telephone, "checkpoint.state", state)


def resume_conversation(telephone):
    """Returns (phase, state) from the user's last saved checkpoint."""
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    if not user:
        return (None, None)
    phase = user.get("checkpoint", {}).get("phase")
    state = user.get("checkpoint", {}).get("state")
    return (phase, state)


def user_keys(telephone):
    """Returns a list of all top-level keys in the user's document."""
    user = users.find_one({"telephone": telephone})
    if user:
        return list(user.keys())
    return f"No se encontró ningún usuario con el teléfono: {telephone}"


def last_session_key(telephone):
    """Returns the most recent session key (format 'YYYY-MM-DD HH:MM:SS_session'), or None if none exist."""
    key_list = user_keys(telephone)
    if isinstance(key_list, str):
        return None
    sessions = [k for k in key_list if k.endswith("_session")]
    return max(sessions) if sessions else None


def user_memory(telephone, keys_list=["name", "age", "PROFILE"]):
    """Returns a projected user document with name, age, PROFILE, and the latest session summary."""
    projection = {key: 1 for key in keys_list}
    last_session = last_session_key(telephone)
    if last_session:
        projection[f"{last_session}.summary"] = 1
    if "_id" not in keys_list:
        projection["_id"] = 0
    return users.find_one({"telephone": telephone}, projection)


def add_emergency_instance(telephone, session_path, protocol, referal):
    """Appends a new emergency record to the user's EMERGENCY array in the database."""
    hora_activacion = datetime.datetime.now().strftime("%H:%M:%S")
    new_emergency = {
        "session_id":        session_path,
        "trigger_hour":      hora_activacion,
        "protocol_applied":  protocol,
        "referal":           referal,
    }
    users.update_one(
        {"telephone": telephone},
        {"$push": {"EMERGENCY": new_emergency}}
    )
    print(f"\n[CASO DE EMERGENCIA DETECTADA (SUI PROTOCOLO {protocol})]\n")


def save_notification(to_telephone, from_telephone, from_name, image_path_family):
    """Inserts a new unread notification into the notifications collection."""
    notification = {
        "to_telephone":      to_telephone,
        "from_telephone":    from_telephone,
        "from_name":         from_name,
        "image_path_family": image_path_family,
        "timestamp":         datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read":              False,
    }
    db["notifications"].insert_one(notification)


def get_notifications(telephone):
    """Returns all unread notifications addressed to the given telephone number."""
    docs = db["notifications"].find(
        {"to_telephone": telephone, "read": False},
        {"_id": 0}
    )
    return list(docs)


def mark_notifications_read(telephone):
    """Marks all unread notifications for the given telephone number as read."""
    db["notifications"].update_many(
        {"to_telephone": telephone, "read": False},
        {"$set": {"read": True}}
    )


def add_to_list(telephone, key, list_item):
    """Appends an item to an array field in the user's document."""
    # $push añade el objeto al final del array
    users.update_one({"telephone": telephone}, {"$push": {key: list_item}})
    return


def delete_user_info(telephone, key):
    """Permanently removes a key from the user's document."""
    # $unset elimina el campo por completo
    users.update_one({"telephone": telephone}, {"$unset": {key: ""}})
    return


def delete_user(telephone: str) -> bool:
    """Permanently deletes a user's document from the users collection. Returns True if deleted, False if not found."""
    result = users.delete_one({"telephone": telephone})
    if result.deleted_count:
        print(f"\n[Usuario {telephone} eliminado correctamente.]\n")
        return True
    print(f"\n[No se encontró ningún usuario con el teléfono: {telephone}]\n")
    return False


# ══════════════════════════════════════════════════════════════════════════════
# SPECIALISTS
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_specialist_indexes():
    """Creates unique indexes on the specialists collection (idempotent)."""
    specialists.create_index("collegiateNumber", unique=True)
    specialists.create_index("email", unique=True)


def is_registered(coll_number: str) -> bool:
    """Returns True if the specialist already exists in the database."""
    specialist = specialists.find_one({"collegiateNumber": coll_number})
    if specialist:
        print("\n[Especialista encontrado en la base de datos.]\n")
        return True
    print("\n[Especialista no encontrado.]\n")
    return False


def email_exists(email: str) -> bool:
    """Returns True if the email is already registered."""
    return specialists.find_one({"email": email.lower()}) is not None


def register_specialist(register_data: dict) -> None:
    """
    Inserts a new specialist.
    register_data must include at least: collegiateNumber, email, passwordHash,
    firstName, lastName, birthDate, countryCode, centerName, centerCity.
    Raises DuplicateKeyError if the collegiate number or email already exist.
    """
    _ensure_specialist_indexes()
    register_data.setdefault("createdAt", datetime.datetime.utcnow())
    register_data.setdefault("profile", {})
    specialists.insert_one(register_data)
    print("\n[Perfil de especialista registrado correctamente]\n")


def get_specialist_by_email(email: str) -> dict | None:
    """Returns the full specialist document by email."""
    return specialists.find_one({"email": email.lower()})


def get_specialist_by_id(specialist_id: str) -> dict | None:
    """Returns the full specialist document by _id (str)."""
    from bson import ObjectId
    try:
        return specialists.find_one({"_id": ObjectId(specialist_id)})
    except Exception:
        return None


def update_specialist_profile(coll_number: str, profile_data: dict) -> None:
    """
    Updates the specialist's profile fields.
    Uses $set with the 'profile.' prefix to avoid overwriting other fields.
    """
    update_fields = {f"profile.{k}": v for k, v in profile_data.items()}
    # También actualiza los campos raíz editables directamente
    root_fields = ["firstName", "lastName", "birthDate", "email",
                   "telefono", "especialidad", "genero"]
    for field in root_fields:
        if field in profile_data:
            update_fields[field] = profile_data[field]

    specialists.update_one(
        {"collegiateNumber": coll_number},
        {"$set": update_fields}
    )


def save_doctor_note(user_telephone: str, specialist_coll: str, note: str) -> None:
    """
    Saves or updates a specialist's clinical note for a user.
    Stored inside the user's document under 'doctorNotes'.
    """
    users.update_one(
        {"telephone": user_telephone},
        {"$set": {
            f"doctorNotes.{specialist_coll}": {
                "note":      note,
                "updatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        }}
    )


def get_users_by_center(center_name: str) -> list:
    """
    Returns users belonging to the same center as the doctor.
    Only includes users who have given consent (shareWithHospital=True).
    The name comes from the medicalCenters collection, ensuring an exact match.
    """
    # Sin proyeccion: necesitamos las claves "_session" que son dinamicas
    # (formato "YYYY-MM-DD HH:MM:SS_session") y no se pueden listar de antemano.
    # MongoDB solo devuelve los campos del documento que existen, por lo que
    # el rendimiento es aceptable para el volumen de datos de un centro medico.
    cursor = users.find(
        {
            "CIRCLE.medicalCenter.name":        center_name,
            "CIRCLE.privacy.shareWithHospital": True,
        }
    )
    return list(cursor)