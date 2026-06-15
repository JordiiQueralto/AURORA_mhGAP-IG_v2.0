"""
services_specialist.py
Lógica de negocio para el panel de especialistas (médicos).
Usado exclusivamente por app_specialist.py.
"""
import datetime
import hashlib
import os
import secrets
import re
import db
import reportPDF

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNOS
# ──────────────────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Simple SHA-256 hash. Use bcrypt or argon2 in production."""
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    """Generates a random session token (64 hex characters)."""
    return secrets.token_hex(32)


def _validate_email(email: str) -> bool:
    """Returns True if the email matches a basic RFC-like pattern."""
    pattern = r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _specialist_to_session(doc: dict) -> dict:
    """
    Converts a MongoDB document into the SESSION object used by the frontend.
    The frontend expects: token, specialist_id, nombre, apellidos, fechaNacimiento,
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
    Verifies credentials and returns the session object.
    Raises ValueError if the credentials are incorrect.
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
    """Saves the specialist's editable profile fields."""
    coll_number = str(coll_number).strip()
    db.update_specialist_profile(coll_number, profile_data)


# ──────────────────────────────────────────────────────────────────────────────
# PATIENTS
# ──────────────────────────────────────────────────────────────────────────────


def _normalize_risk(risk_raw: str) -> str:
    """
    Normalizes the risk_level value stored by the LLM in the database.
    Accepts uppercase, lowercase, accented/unaccented, and English variants.
    """
    v = (risk_raw or "").lower().strip()
    # Eliminar tildes para comparacion robusta
    v = v.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    if v in ("alto", "alta", "high", "elevado", "elevada", "muy alto", "muy alta"):
        return "alto"
    if v in ("medio", "media", "moderate", "moderado", "moderada", "intermedio", "intermedia"):
        return "medio"
    if v in ("bajo", "baja", "low", "reducido", "reducida", "leve"):
        return "bajo"
    if v in ("estable", "stable", "sin riesgo", "normal", "nulo", "nula", "ninguno"):
        return "estable"
    # Valor desconocido → estable por defecto (conservador)
    return "estable"


def get_patients_for_specialist(center_name: str) -> list:
    """
    Returns the list of users from the same medical center as the specialist,
    formatted for the frontend. Only includes users with shareWithHospital=True.

    Actual user document structure in MongoDB (per services_user.py):
      - telephone                          str
      - name                               str
      - CIRCLE.medicalCenter.name          str  ← used for filtering
      - CIRCLE.privacy.shareWithHospital   bool ← used for filtering
      - EMERGENCY                          list of emergency objects
      - checkpoint.phase / .state          str
      - "<YYYY-MM-DD HH:MM:SS>_session"   dict with .summary, .valoration,
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
            valoration = session_data.get("valoration", "") or ""
            session_log.append({
                "date":      date_str,
                "datetime":  raw_date,           # "YYYY-MM-DD HH:MM:SS" para ordenar
                "summary":   summary,            # texto completo del resumen
                "valoration": valoration,        # "BUENA" / "REGULAR" / "MALA" etc.
                "status":    "emergencia" if is_emergency_session else "completada",
            })

        # ── Nivel de riesgo: se lee de la ULTIMA sesion ({session_path}.risk_level)
        # generate_output.session_risk() lo guarda en _run_farewell de services_user.py
        risk = "estable"  # valor por defecto si no hay sesiones o no tiene risk_level
        if session_keys:
            last_session_key = session_keys[-1]   # sorted ASC → el ultimo es el mas reciente
            last_session_data = u.get(last_session_key, {})
            risk_raw = (last_session_data.get("risk_level", "") or "").lower().strip()
            # Normalizar distintas variantes que puede devolver el LLM
            risk = _normalize_risk(risk_raw)

        # ── Estado activo/inactivo: si la ultima sesion fue hace menos de 30 dias
        status = "inactivo"
        if last_date:
            try:
                import datetime as _dt
                days_since = (_dt.date.today() - _dt.date.fromisoformat(last_date)).days
                status = "activo" if days_since <= 30 else "inactivo"
            except Exception:
                status = "activo" if session_count > 0 else "inactivo"

        # ── Nº Seguridad Social (CIRCLE.privacy.socialSecurityNumber) ───────────
        ssn = (
            u.get("CIRCLE", {})
             .get("privacy", {})
             .get("socialSecurityNumber", "") or ""
        ).strip()

        patients.append({
            "id":         str(u["_id"]),
            "name":       _anonymize_name(u.get("name", "Usuario")),
            "phone":      masked,
            "last":       last_date or "",
            "sessions":   session_count,
            "risk":       risk,
            "status":     status,
            "emergency":  has_emergency,
            "reg":        "",
            "notes":      "",
            "ssn":        ssn,         # Nº Seguridad Social (vacío si no aportado)
            "sessionLog": session_log,
        })

    return patients



def get_patient_sessions(user_id: str) -> list:
    """
    Returns the full session history for a user by their _id.
    Each session includes: date, datetime, summary, valoration, status.
    Ordered from most recent to oldest.
    """
    from bson import ObjectId
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("Usuario no encontrado.")

    emergency_list = user.get("EMERGENCY", [])
    session_keys   = sorted([k for k in user.keys() if k.endswith("_session")])
    sessions       = []

    for key in session_keys:
        session_data = user.get(key, {})
        raw_date     = key.replace("_session", "")   # "YYYY-MM-DD HH:MM:SS"
        date_str     = raw_date[:10]                  # "YYYY-MM-DD"

        summary    = session_data.get("summary",    "") or ""
        valoration = session_data.get("valoration", "") or ""

        is_emergency = any(e.get("session_id", "") == key for e in emergency_list)

        risk_level = (session_data.get("risk_level", "") or "").lower().strip()
        sessions.append({
            "date":       date_str,
            "datetime":   raw_date,
            "summary":    summary,
            "valoration": valoration,
            "risk_level": risk_level,
            "status":     "emergencia" if is_emergency else "completada",
        })

    # Mas reciente primero
    sessions.reverse()
    return sessions

def generate_patient_report(user_id: str, output_path: str = None) -> None:
    """
    Generates a PDF report with the user's data.
    - output_path: path where the PDF will be saved.
      If None, reportPDF saves it to the system Downloads folder.
      If provided (e.g. a temporary file), that path is used so
      Flask can return it directly to the doctor's browser.
    """
    reportPDF.generate_report(user_id, output_path=output_path)
    return


def get_risk_distribution(center_name: str) -> dict:
    """
    Calculates the risk level distribution for all users in the center,
    reading the risk_level from each user's most recent session.
    Returns: { "estable": N, "bajo": N, "medio": N, "alto": N }
    """
    raw_users = db.get_users_by_center(center_name)
    distribution = {"estable": 0, "bajo": 0, "medio": 0, "alto": 0}

    for u in raw_users:
        session_keys = sorted([k for k in u.keys() if k.endswith("_session")])
        risk = "estable"
        if session_keys:
            last_data = u.get(session_keys[-1], {})
            risk_raw  = (last_data.get("risk_level", "") or "").lower().strip()
            risk = _normalize_risk(risk_raw)
        distribution[risk] += 1

    return distribution


def get_sessions_by_day(center_name: str, days: int = 30) -> dict:
    """
    Counts how many sessions occurred each day over the last `days` days,
    for all users in the center.
    A single user can contribute multiple sessions on the same day.
    Returns: { "YYYY-MM-DD": count, ... } sorted chronologically.
    """
    import datetime as _dt
    raw_users = db.get_users_by_center(center_name)
    cutoff    = _dt.date.today() - _dt.timedelta(days=days - 1)
    counts    = {}

    for u in raw_users:
        for key in u.keys():
            if not key.endswith("_session"):
                continue
            # La clave tiene formato "YYYY-MM-DD HH:MM:SS_session"
            date_str = key.replace("_session", "")[:10]   # "YYYY-MM-DD"
            try:
                day = _dt.date.fromisoformat(date_str)
            except ValueError:
                continue
            if day >= cutoff:
                counts[date_str] = counts.get(date_str, 0) + 1

    # Rellenar todos los dias del rango (incluso con 0)
    result = {}
    for i in range(days):
        d = (cutoff + _dt.timedelta(days=i)).isoformat()
        result[d] = counts.get(d, 0)

    return result   # dict ordenado (Python 3.7+ mantiene orden de insercion)


def get_valoration_distribution(center_name: str) -> dict:
    """
    Counts how many sessions have each valoration type, cumulatively
    (a single user can contribute multiple times).
    Returns: { "buena": N, "regular": N, "mala": N, "sin_valorar": N }
    """
    raw_users = db.get_users_by_center(center_name)
    dist = {"buena": 0, "regular": 0, "mala": 0, "sin_valorar": 0}

    for u in raw_users:
        for key in u.keys():
            if not key.endswith("_session"):
                continue
            session_data = u.get(key, {})
            val = (session_data.get("valoration", "") or "").lower().strip()
            # Normalizar tildes
            val = val.replace("á","a").replace("é","e").replace("ó","o")
            if val in ("buena", "bueno", "good", "bien"):
                dist["buena"]   += 1
            elif val in ("regular", "medio", "moderate"):
                dist["regular"] += 1
            elif val in ("mala", "malo", "bad", "mal"):
                dist["mala"]    += 1
            else:
                dist["sin_valorar"] += 1

    return dist



def get_screening_distribution(center_name: str) -> dict:
    """
    Reads the SCREENING field from each center user and counts how many
    have each result.

    Database structure:
      SCREENING: {
        SUI: "self_harm" | "concrete_plan" | "ideation" | "improbable" | "others"
        DEP: "depression" | "bipolar" | "others"
      }

    Returns:
      {
        "sui": { "self_harm":0, "concrete_plan":0, "ideation":0, "improbable":0, "others":0 },
        "dep": { "depression":0, "bipolar":0, "others":0 }
      }
    """
    raw_users = db.get_users_by_center(center_name)

    sui = {"self_harm": 0, "concrete_plan": 0, "ideation": 0, "improbable": 0, "others": 0}
    dep = {"depression": 0, "bipolar": 0, "others": 0}

    print(f"\n[SCREENING] Usuarios encontrados en centro '{center_name}': {len(raw_users)}")

    for u in raw_users:
        name = u.get("name", "?")
        # El campo puede estar en mayusculas SCREENING o en minusculas screening
        # Buscamos ambas variantes para ser robustos
        screening = u.get("SCREENING") or u.get("screening") or {}
        if not isinstance(screening, dict):
            print(f"  [{name}] SCREENING no es dict: {type(screening)} → {screening!r}")
            continue

        print(f"  [{name}] SCREENING: {screening}")

        # ── SUI — buscar clave en mayusculas y minusculas ─────────────────────
        sui_val = (screening.get("SUI") or screening.get("sui") or "").lower().strip()
        if sui_val in sui:
            sui[sui_val] += 1
        elif sui_val:
            print(f"  [{name}] SUI valor inesperado: {sui_val!r} → others")
            sui["others"] += 1

        # ── DEP — buscar clave en mayusculas y minusculas ─────────────────────
        dep_val = (screening.get("DEP") or screening.get("dep") or "").lower().strip()
        if dep_val in dep:
            dep[dep_val] += 1
        elif dep_val:
            print(f"  [{name}] DEP valor inesperado: {dep_val!r} → others")
            dep["others"] += 1

    print(f"  SUI result: {sui}")
    print(f"  DEP result: {dep}\n")
    return {"sui": sui, "dep": dep}


def get_emergency_followup_stats(center_name: str) -> dict:
    """
    Iterates over all center users and counts:
      - total_emergencies:  entries in the EMERGENCY array
      - total_followups:    entries in FOLLOWUP.history
      - outcome_no_help:    followups with outcome=True  ("did not seek help")
      - outcome_help:       followups with outcome=False ("did seek help")

    Database structure:
      EMERGENCY: [ { session_id, trigger_hour, protocol_applied, referal }, ... ]
      FOLLOWUP: {
        history: [ { emergency_date, followup_date, outcome: bool, reason }, ... ],
        last_check: "YYYY-MM-DD HH:MM:SS"
      }
    """
    raw_users = db.get_users_by_center(center_name)

    total_emergencies = 0
    total_followups   = 0
    outcome_no_help   = 0   # outcome: True  → no buscó ayuda
    outcome_help      = 0   # outcome: False → sí buscó ayuda

    for u in raw_users:
        # ── EMERGENCY ─────────────────────────────────────────────────────────
        emergency_list = u.get("EMERGENCY", [])
        if isinstance(emergency_list, list):
            total_emergencies += len(emergency_list)

        # ── FOLLOWUP ──────────────────────────────────────────────────────────
        followup = u.get("FOLLOWUP", {})
        if not isinstance(followup, dict):
            continue
        history = followup.get("history", [])
        if not isinstance(history, list):
            continue

        total_followups += len(history)
        for entry in history:
            outcome = entry.get("outcome")
            if outcome is True:
                outcome_no_help += 1
            elif outcome is False:
                outcome_help += 1

    return {
        "total_emergencies": total_emergencies,
        "total_followups":   total_followups,
        "outcome_no_help":   outcome_no_help,
        "outcome_help":      outcome_help,
    }

def save_patient_note(user_id: str, specialist_coll: str, note: str) -> None:
    """Saves a specialist's clinical note for a user identified by their _id."""
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
    Validates the session token.
    Returns the specialist document or None if the token is invalid.
    """
    if not token:
        return None
    return db.specialists.find_one({"sessionToken": token})


# ──────────────────────────────────────────────────────────────────────────────
# UTILS
# ──────────────────────────────────────────────────────────────────────────────

def _mask_phone(phone: str) -> str:
    """Masks the phone number, keeping only the first 3 and the last digit."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) >= 7:
        return f"+{digits[:2]} {digits[2]}** ***-{digits[-1]}"
    return "*** *** ***"


def _anonymize_name(name: str) -> str:
    """
    Shows only the first initial plus surname for privacy.
    e.g. 'María García López' → 'M. García'
    """
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0].upper()}. {parts[1]}"
    return name[:20] if name else "Usuario"