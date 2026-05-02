"""
main_api_sp.py
Lógica de negocio para el panel de especialistas (médicos).
Usado exclusivamente por app_sp.py.
"""
import datetime
import hashlib
import os
import secrets
import re

import db

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNOS
# ──────────────────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """SHA-256 simple. Para producción usa bcrypt o argon2."""
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    """Token de sesión aleatorio (64 hex chars)."""
    return secrets.token_hex(32)


def _validate_email(email: str) -> bool:
    pattern = r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _specialist_to_session(doc: dict) -> dict:
    """
    Convierte un documento de MongoDB en el objeto SESSION que usa el frontend.
    El frontend espera: token, specialist_id, nombre, apellidos, fechaNacimiento,
    numeroColegiado, email, telefono, countryCode, centerName, centerCity.
    """
    return {
        "token":           doc.get("sessionToken", ""),
        "specialist_id":   str(doc["_id"]),
        "nombre":          doc.get("firstName", ""),
        "apellidos":       doc.get("lastName", ""),
        "fechaNacimiento": doc.get("birthDate", ""),
        "numeroColegiado": doc.get("collegiateNumber", ""),
        "email":           doc.get("email", ""),
        "telefono":        doc.get("profile", {}).get("telefono", ""),
        "especialidad":    doc.get("profile", {}).get("especialidad", ""),
        "genero":          doc.get("profile", {}).get("genero", ""),
        "countryCode":     doc.get("countryCode", ""),
        "centerName":      doc.get("centerName", ""),
        "centerCity":      doc.get("centerCity", ""),
    }


# ──────────────────────────────────────────────────────────────────────────────
# AUTH: REGISTRO
# ──────────────────────────────────────────────────────────────────────────────

def handle_registration(data: dict) -> dict:
    """
    Registra un nuevo especialista.

    Parámetros esperados en `data`:
      - collegiateNumber (str)  *obligatorio*
      - firstName        (str)  *obligatorio*
      - lastName         (str)  *obligatorio*
      - birthDate        (str)  *obligatorio*  formato YYYY-MM-DD
      - email            (str)  *obligatorio*
      - password         (str)  *obligatorio*  ≥ 8 chars
      - countryCode      (str)  *obligatorio*
      - centerName       (str)  *obligatorio*
      - centerCity       (str)

    Retorna:
      - dict con la sesión si todo va bien
      - Lanza ValueError con mensaje si hay error de validación
      - Lanza RuntimeError si ya existe el colegiado o email
    """
    # ── Validaciones ──────────────────────────────────────────────────────────
    required = ["collegiateNumber", "firstName", "lastName",
                "birthDate", "email", "password", "countryCode", "centerName"]
    for field in required:
        if not data.get(field, "").strip():
            raise ValueError(f"El campo '{field}' es obligatorio.")

    coll_number = str(data["collegiateNumber"]).strip()
    email       = data["email"].strip().lower()
    password    = data["password"]

    if not _validate_email(email):
        raise ValueError("El formato del correo electrónico no es válido.")

    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")

    # ── Unicidad ──────────────────────────────────────────────────────────────
    if db.is_registered(coll_number):
        raise RuntimeError("El número de colegiado ya está registrado.")

    if db.email_exists(email):
        raise RuntimeError("Este correo electrónico ya está registrado.")

    # ── Inserción ─────────────────────────────────────────────────────────────
    token = _generate_token()
    register_data = {
        "collegiateNumber": coll_number,
        "firstName":        data["firstName"].strip(),
        "lastName":         data["lastName"].strip(),
        "birthDate":        data.get("birthDate", "").strip(),
        "email":            email,
        "passwordHash":     _hash_password(password),
        "countryCode":      data["countryCode"].upper().strip(),
        "centerName":       data["centerName"].strip(),
        "centerCity":       data.get("centerCity", "").strip(),
        "sessionToken":     token,
        "profile":          {},
        "createdAt":        datetime.datetime.utcnow(),
    }
    db.register_specialist(register_data)

    # Recuperamos el doc recién insertado para obtener el _id
    doc = db.get_specialist_by_email(email)
    return _specialist_to_session(doc)


# ──────────────────────────────────────────────────────────────────────────────
# AUTH: LOGIN
# ──────────────────────────────────────────────────────────────────────────────

def handle_login(email: str, password: str) -> dict:
    """
    Verifica credenciales y devuelve el objeto de sesión.
    Lanza ValueError si las credenciales son incorrectas.
    """
    email = email.strip().lower()
    doc   = db.get_specialist_by_email(email)

    if not doc:
        raise ValueError("No existe ninguna cuenta con ese correo electrónico.")

    if doc.get("passwordHash") != _hash_password(password):
        raise ValueError("Contraseña incorrecta.")

    # Renovar token en cada login
    token = _generate_token()
    from pymongo import MongoClient
    from bson import ObjectId
    db.specialists.update_one(
        {"_id": doc["_id"]},
        {"$set": {"sessionToken": token}}
    )
    doc["sessionToken"] = token
    return _specialist_to_session(doc)


# ──────────────────────────────────────────────────────────────────────────────
# PROFILE UPDATE
# ──────────────────────────────────────────────────────────────────────────────

def save_profile_update(coll_number: str, profile_data: dict) -> None:
    """Guarda los campos de perfil editables del especialista."""
    coll_number = str(coll_number).strip()
    db.update_specialist_profile(coll_number, profile_data)


# ──────────────────────────────────────────────────────────────────────────────
# PATIENTS
# ──────────────────────────────────────────────────────────────────────────────

def get_patients_for_specialist(center_name: str) -> list:
    """
    Devuelve la lista de usuarios del mismo centro medico que el especialista,
    formateada para el frontend. Solo incluye usuarios con shareWithHospital=True.

    Estructura real del documento usuario en MongoDB (segun main_api.py):
      - telephone                          str
      - name                               str
      - CIRCLE.medicalCenter.name          str  ← usado para filtrar
      - CIRCLE.privacy.shareWithHospital   bool ← usado para filtrar
      - EMERGENCY                          list de objetos de emergencia
      - checkpoint.phase / .state          str
      - "<YYYY-MM-DD HH:MM:SS>_session"   dict con .summary, .valoration,
                                           .conversation_history
    """
    raw_users = db.get_users_by_center(center_name)
    patients  = []

    for u in raw_users:
        telephone = u.get("telephone", "")
        masked    = _mask_phone(str(telephone))

        # ── Emergencias ───────────────────────────────────────────────────────
        emergency_list = u.get("EMERGENCY", [])
        has_emergency  = len(emergency_list) > 0

        # ── Sesiones: las claves de sesion tienen formato "YYYY-MM-DD HH:MM:SS_session"
        session_keys  = sorted([k for k in u.keys() if k.endswith("_session")])
        session_count = len(session_keys)
        session_log   = []
        last_date     = None

        for key in session_keys:
            session_data = u.get(key, {})

            # La fecha esta embebida en la clave: "2025-07-18 10:30:00_session"
            raw_date = key.replace("_session", "")
            date_str = raw_date[:10]          # "YYYY-MM-DD"
            last_date = date_str              # la ultima del sorted es la mas reciente

            summary = session_data.get("summary", "") or ""
            # Marcar como emergencia si el checkpoint de esa sesion lo indica
            # o si hay entradas de emergencia cuyo session_id coincide con la clave
            is_emergency_session = any(
                e.get("session_id", "") == key for e in emergency_list
            )
            session_log.append({
                "date":   date_str,
                "topic":  (summary[:80] if summary else "Sesion registrada"),
                "status": "emergencia" if is_emergency_session else "completada",
            })

        # ── Nivel de riesgo desde PROFILE ─────────────────────────────────────
        profile  = u.get("PROFILE", {})
        risk_raw = profile.get("riskLevel", "").lower() if isinstance(profile, dict) else ""
        risk     = risk_raw if risk_raw in ("alto", "medio", "bajo", "estable") else "estable"

        # ── Estado activo/inactivo: si la ultima sesion fue hace menos de 30 dias
        status = "inactivo"
        if last_date:
            try:
                import datetime as _dt
                days_since = (_dt.date.today() - _dt.date.fromisoformat(last_date)).days
                status = "activo" if days_since <= 30 else "inactivo"
            except Exception:
                status = "activo" if session_count > 0 else "inactivo"

        patients.append({
            "id":         str(u["_id"]),
            "name":       _anonymize_name(u.get("name", "Usuario")),
            "phone":      masked,
            "last":       last_date or "",
            "sessions":   session_count,
            "risk":       risk,
            "status":     status,
            "emergency":  has_emergency,
            "reg":        "",          # no se guarda createdAt en users
            "notes":      "",          # las notas se cargan por separado si se necesitan
            "sessionLog": session_log[-5:],   # max 5 mas recientes
        })

    return patients


def save_patient_note(user_id: str, specialist_coll: str, note: str) -> None:
    """Guarda una nota clínica del especialista sobre un usuario por su _id."""
    from bson import ObjectId
    # Buscamos el teléfono a partir del _id
    user = db.users.find_one({"_id": ObjectId(user_id)}, {"telephone": 1})
    if not user:
        raise ValueError("Usuario no encontrado.")
    db.save_doctor_note(user["telephone"], specialist_coll, note)


# ──────────────────────────────────────────────────────────────────────────────
# TOKEN VALIDATION
# ──────────────────────────────────────────────────────────────────────────────

def validate_token(token: str) -> dict | None:
    """
    Valida el token de sesión.
    Devuelve el documento del especialista o None si no es válido.
    """
    if not token:
        return None
    return db.specialists.find_one({"sessionToken": token})


# ──────────────────────────────────────────────────────────────────────────────
# UTILS
# ──────────────────────────────────────────────────────────────────────────────

def _mask_phone(phone: str) -> str:
    """Enmascara el número dejando solo los primeros 3 y último dígito."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) >= 7:
        return f"+{digits[:2]} {digits[2]}** ***-{digits[-1]}"
    return "*** *** ***"


def _anonymize_name(name: str) -> str:
    """
    Muestra solo la inicial del nombre + apellido para privacidad.
    ej: 'María García López' → 'M. García'
    """
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0].upper()}. {parts[1]}"
    return name[:20] if name else "Usuario"
