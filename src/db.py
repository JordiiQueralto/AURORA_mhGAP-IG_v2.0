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
# USERS (sin cambios respecto al original)
# ══════════════════════════════════════════════════════════════════════════════

def is_new(telephone: str) -> bool:
    """True si el usuario NO existe todavía."""
    user = users.find_one({"telephone": telephone})
    if user:
        print("\n[Usuario encontrado en la base de datos.]\n")
        return False
    print("\n[Usuario no encontrado. Es un nuevo usuario.]\n")
    return True


def create_user(telephone, is_new_user):
    users.create_index("telephone", unique=True)
    try:
        if is_new_user:
            users.insert_one({"telephone": telephone})
            print("\n[Usuario creado correctamente.]\n")
    except DuplicateKeyError:
        print("\n[Error: El usuario ya existe.]\n")


def add_user_info(telephone, key, value):
    users.update_one({"telephone": telephone}, {"$set": {key: value}})


def get_user_name(telephone, key="name"):
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    return user.get("name") if user else None


def get_user_info(telephone, key1, key2=None):
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    if not user: return None
    
    data = user.get(key1)
    
    # Si pedimos un segundo nivel y el primero es un diccionario
    if key2 and isinstance(data, dict):
        return data.get(key2)
    
    return data


def user_status(telephone: str) -> str:
    user = users.find_one({"telephone": telephone})
    return user.get("USER_TERMS", {}).get("status")


def conversation_history(telephone):
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
    add_user_info(telephone, "checkpoint.phase", phase)
    add_user_info(telephone, "checkpoint.state", state)


def resume_conversation(telephone):
    user = users.find_one({"telephone": telephone}, {"_id": 0})
    if not user:
        return (None, None)
    phase = user.get("checkpoint", {}).get("phase")
    state = user.get("checkpoint", {}).get("state")
    return (phase, state)


def user_keys(telephone):
    user = users.find_one({"telephone": telephone})
    if user:
        return list(user.keys())
    return f"No se encontró ningún usuario con el teléfono: {telephone}"


def last_session_key(telephone):
    key_list = user_keys(telephone)
    if isinstance(key_list, str):
        return None
    sessions = [k for k in key_list if k.endswith("_session")]
    return max(sessions) if sessions else None


def user_memory(telephone, keys_list=["name", "age", "PROFILE"]):
    projection = {key: 1 for key in keys_list}
    last_session = last_session_key(telephone)
    if last_session:
        projection[f"{last_session}.summary"] = 1
    if "_id" not in keys_list:
        projection["_id"] = 0
    return users.find_one({"telephone": telephone}, projection)


def add_emergency_instance(telephone, session_path, protocol, referal):
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
    docs = db["notifications"].find(
        {"to_telephone": telephone, "read": False},
        {"_id": 0}
    )
    return list(docs)


def mark_notifications_read(telephone):
    db["notifications"].update_many(
        {"to_telephone": telephone, "read": False},
        {"$set": {"read": True}}
    )


def add_to_list(telephone, key, list_item):
    # $push añade el objeto al final del array
    users.update_one({"telephone": telephone}, {"$push": {key: list_item}})
    return

def delete_user_info(telephone, key):
    """Elimina físicamente una clave del documento del usuario."""
    # $unset elimina el campo por completo
    users.update_one({"telephone": telephone}, {"$unset": {key: ""}})
    return

# ══════════════════════════════════════════════════════════════════════════════
# SPECIALISTS
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_specialist_indexes():
    """Crea índices únicos la primera vez (idempotente)."""
    specialists.create_index("collegiateNumber", unique=True)
    specialists.create_index("email", unique=True)


def is_registered(coll_number: str) -> bool:
    """True si el especialista YA existe en la BD."""
    specialist = specialists.find_one({"collegiateNumber": coll_number})
    if specialist:
        print("\n[Especialista encontrado en la base de datos.]\n")
        return True
    print("\n[Especialista no encontrado.]\n")
    return False


def email_exists(email: str) -> bool:
    """Comprueba si el email ya está registrado."""
    return specialists.find_one({"email": email.lower()}) is not None


def register_specialist(register_data: dict) -> None:
    """
    Inserta un nuevo especialista.
    register_data debe incluir al menos: collegiateNumber, email, passwordHash,
    firstName, lastName, birthDate, countryCode, centerName, centerCity.
    Lanza DuplicateKeyError si el número o email ya existen.
    """
    _ensure_specialist_indexes()
    register_data.setdefault("createdAt", datetime.datetime.utcnow())
    register_data.setdefault("profile", {})
    specialists.insert_one(register_data)
    print("\n[Perfil de especialista registrado correctamente]\n")


def get_specialist_by_email(email: str) -> dict | None:
    """Devuelve el documento completo del especialista por email."""
    return specialists.find_one({"email": email.lower()})


def get_specialist_by_id(specialist_id: str) -> dict | None:
    """Devuelve el documento completo por _id (str)."""
    from bson import ObjectId
    try:
        return specialists.find_one({"_id": ObjectId(specialist_id)})
    except Exception:
        return None


def update_specialist_profile(coll_number: str, profile_data: dict) -> None:
    """
    Actualiza los campos de perfil del especialista.
    Usa $set con el prefijo 'profile.' para no machacar otros campos.
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
    Guarda/actualiza una nota clínica del especialista sobre un usuario.
    Se almacena dentro del documento del usuario bajo 'doctorNotes'.
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
    Devuelve usuarios que pertenecen al mismo centro que el médico.
    Solo incluye usuarios que han dado consentimiento (shareWithHospital=True).
    El nombre viene de la misma coleccion medicalCenters, garantizando coincidencia exacta.
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