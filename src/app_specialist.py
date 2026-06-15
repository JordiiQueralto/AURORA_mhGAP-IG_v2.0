"""
app_specialist.py
Flask backend exclusivo para el panel de especialistas (médicos).
Corre en el puerto 5001 para no colisionar con app_user.py (puerto 5000).

Endpoints expuestos:
  POST  /api/doctor/register          → Registro de nuevo especialista
  POST  /api/doctor/login             → Login
  PUT   /api/doctor/profile           → Actualizar perfil  [Auth]
  GET   /api/doctor/patients          → Usuarios del centro [Auth]
  PUT   /api/doctor/patients/<id>/notes   → Guardar nota clínica [Auth]
  GET   /api/doctor/patients/<id>/sessions → Historial de sesiones [Auth]
  GET   /api/doctor/patients/<id>/report   → Generar informe PDF [Auth]

  GET   /api/doctor/countries         → Lista de países con centros (reutiliza medicalCenters)
  GET   /api/medical-centers/<code>   → Centros de un país (igual que app_user.py)
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
from pymongo import MongoClient
import re
import services_specialist

# ──────────────────────────────────────────────────────────────────────────────
# APP & DB
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db     = client["CHATBOT_mhGAP"]

# CORS: permite peticiones desde archivo local (file://) y localhost en cualquier puerto
CORS(app, resources={r"/api/*": {"origins": [
    "null",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:5001",
    "http://127.0.0.1:5001",
]}}, supports_credentials=False)


# ──────────────────────────────────────────────────────────────────────────────
# AUTH DECORATOR
# ──────────────────────────────────────────────────────────────────────────────

def require_auth(f):
    """Decorator that validates the Bearer token in the Authorization header. If valid, injects the specialist document as the 'specialist' kwarg."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        specialist = services_specialist.validate_token(token)
        if not specialist:
            return jsonify({"error": "No autorizado. Token inválido o expirado."}), 401
        return f(*args, specialist=specialist, **kwargs)
    return decorated


# ──────────────────────────────────────────────────────────────────────────────
# AUTH ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/doctor/register", methods=["POST"])
def register():
    """
    Registers a new specialist.

    Expected JSON body:
    {
      "collegiateNumber": "28-5678",
      "firstName":        "María",
      "lastName":         "García López",
      "birthDate":        "1985-04-12",
      "email":            "maria@hospital.es",
      "password":         "MiClave123",
      "countryCode":      "ES",
      "centerName":       "CAP Les Corts",
      "centerCity":       "Barcelona"
    }
    """
    data = request.json or {}

    # Normalizar: el HTML envía 'nombre'/'apellidos', lo mapeamos al modelo interno
    data.setdefault("firstName", data.pop("nombre",    data.get("firstName", "")))
    data.setdefault("lastName",  data.pop("apellidos", data.get("lastName",  "")))

    try:
        session = services_specialist.handle_registration(data)
        return jsonify(session), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409      # Conflict: ya existe
    except Exception as e:
        print(f"[ERROR /register] {e}")
        return jsonify({"error": "Error interno del servidor."}), 500


@app.route("/api/doctor/login", methods=["POST"])
def login():
    """
    Specialist login.

    Body JSON: { "email": "...", "password": "..." }
    Returns the SESSION object that the frontend stores in the SESSION variable.
    """
    data     = request.json or {}
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email y contraseña son obligatorios."}), 400

    try:
        session = services_specialist.handle_login(email, password)
        return jsonify(session), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"[ERROR /login] {e}")
        return jsonify({"error": "Error interno del servidor."}), 500


# ──────────────────────────────────────────────────────────────────────────────
# PROFILE ENDPOINT
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/doctor/profile", methods=["PUT"])
@require_auth
def update_profile(specialist):
    """
    Updates the specialist's editable profile fields.
    Requires Authorization: Bearer <token>

    Body JSON (all optional, only provided fields are updated):
    {
      "nombre":          "María",
      "apellidos":       "García López",
      "fechaNacimiento": "1985-04-12",
      "numeroColegiado": "28-5678",
      "email":           "maria@hospital.es",
      "telefono":        "+34 600 000 000",
      "especialidad":    "Psiquiatría",
      "genero":          "dra"
    }
    """
    data        = request.json or {}
    coll_number = specialist.get("collegiateNumber", "")

    # Mapear campos del frontend al modelo interno
    profile_data = {}
    mapping = {
        "nombre":          "firstName",
        "apellidos":       "lastName",
        "fechaNacimiento": "birthDate",
        "numeroColegiado": "collegiateNumber",
        "email":           "email",
        "telefono":        "telefono",
        "especialidad":    "especialidad",
        "genero":          "genero",
    }
    for front_key, db_key in mapping.items():
        if front_key in data:
            profile_data[db_key] = data[front_key]

    try:
        services_specialist.save_profile_update(coll_number, profile_data)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"[ERROR /profile] {e}")
        return jsonify({"error": "Error al guardar el perfil."}), 500


# ──────────────────────────────────────────────────────────────────────────────
# PATIENTS ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/doctor/patients", methods=["GET"])
@require_auth
def get_patients(specialist):
    """
    Returns users belonging to the same medical center as the specialist.
    Requires Authorization: Bearer <token>
    """
    center_name = specialist.get("centerName", "")

    if not center_name:
        return jsonify({"patients": []}), 200

    try:
        patients = services_specialist.get_patients_for_specialist(center_name)
        return jsonify({"patients": patients}), 200
    except Exception as e:
        print(f"[ERROR /patients] {e}")
        return jsonify({"error": "Error al recuperar usuarios."}), 500


@app.route("/api/doctor/patients/<user_id>/notes", methods=["PUT"])
@require_auth
def save_note(specialist, user_id):
    """
    Saves a specialist's clinical note for a user.
    Requires Authorization: Bearer <token>

    Body JSON: { "notes": "Clinical note text..." }
    """
    data = request.json or {}
    note = data.get("notes", "").strip()
    coll_number = specialist.get("collegiateNumber", "")

    try:
        services_specialist.save_patient_note(user_id, coll_number, note)
        return jsonify({"status": "ok"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[ERROR /notes] {e}")
        return jsonify({"error": "Error al guardar la nota."}), 500



@app.route("/api/doctor/patients/<user_id>/sessions", methods=["GET"])
@require_auth
def get_patient_sessions(specialist, user_id):
    """
    Returns the full session history for a specific user.
    Requires Authorization: Bearer <token>

    Returns a list of sessions with: date, datetime, summary, valoration, status
    ordered from most recent to oldest.
    """
    try:
        sessions = services_specialist.get_patient_sessions(user_id)
        return jsonify({"sessions": sessions}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[ERROR /sessions] {e}")
        return jsonify({"error": "Error al recuperar sesiones."}), 500


@app.route("/api/doctor/patients/<user_id>/report", methods=["GET"])
@require_auth
def generate_report(specialist, user_id):
    """
    Generates the patient's PDF report and returns it as a direct download.
    Requires Authorization: Bearer <token>

    The PDF is generated via a temporary file that is deleted after the response is sent,
    so nothing is left on the server's disk.
    """
    import tempfile, os

    try:
        # Creamos un fichero temporal con extensión .pdf
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp_path = tmp.name
        tmp.close()

        # Generamos el PDF en esa ruta temporal (en vez de en Descargas)
        services_specialist.generate_patient_report(user_id, output_path=tmp_path)

        # Nombre de descarga legible para el médico
        filename = f"Informe_{user_id}.pdf"

        return send_file(
            tmp_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[ERROR /report] {e}")
        return jsonify({"error": "Error al generar el informe."}), 500
    finally:
        # Limpieza del fichero temporal aunque haya error
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass



@app.route("/api/doctor/stats", methods=["GET"])
@require_auth
def get_stats(specialist):
    """
    Returns real statistics for the center to populate dashboard charts:
      - riskDistribution:    { estable, bajo, medio, alto }
      - sessionsByDay:       { "YYYY-MM-DD": count } last 30 days
      - valorationDist:      { buena, regular, mala, sin_valorar }
      - suiDist:             { self_harm, concrete_plan, ideation, improbable, others }
      - depDist:             { depression, bipolar, others }
      - emergencyStats:      { total_emergencies, total_followups, outcome_no_help, outcome_help }
    Requires Authorization: Bearer <token>
    """
    center_name = specialist.get("centerName", "")
    try:
        risk_dist    = services_specialist.get_risk_distribution(center_name)
        sessions_day = services_specialist.get_sessions_by_day(center_name, days=30)
        valoration   = services_specialist.get_valoration_distribution(center_name)
        screening    = services_specialist.get_screening_distribution(center_name)
        emergency_stats = services_specialist.get_emergency_followup_stats(center_name)
        return jsonify({
            "riskDistribution": risk_dist,
            "sessionsByDay":    sessions_day,
            "valorationDist":   valoration,
            "suiDist":          screening["sui"],
            "depDist":          screening["dep"],
            "emergencyStats":   emergency_stats,
        }), 200
    except Exception as e:
        print(f"[ERROR /stats] {e}")
        return jsonify({"error": "Error al recuperar estadísticas."}), 500


@app.route("/api/doctor/stats/debug", methods=["GET"])
@require_auth
def debug_screening(specialist):
    """
    Debug endpoint: returns the SCREENING field of each center user as stored in the database,
    to help diagnose data issues.
    """
    center_name = specialist.get("centerName", "")
    raw_users = services_specialist.db.get_users_by_center(center_name)
    result = []
    for u in raw_users:
        result.append({
            "name":      u.get("name", "?"),
            "telephone": str(u.get("telephone", "?")),
            "SCREENING": u.get("SCREENING") or u.get("screening"),
            "has_circle_share": u.get("CIRCLE", {}).get("privacy", {}).get("shareWithHospital"),
        })
    return jsonify({"users": result, "count": len(result)}), 200

# ──────────────────────────────────────────────────────────────────────────────
# MEDICAL CENTERS (reutilizando la misma colección de app_user.py)
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/doctor/countries", methods=["GET"])
def list_countries():
    """
    Returns the list of available countries from the medicalCenters collection.
    Used by the frontend when opening the registration tab.
    """
    countries = db.medicalCenters.find(
        {},
        {"_id": 0, "countryCode": 1, "countryName": 1}
    ).sort("countryName", 1)
    return jsonify(list(countries))


@app.route("/api/medical-centers/<country_code>", methods=["GET"])
def get_centers(country_code):
    """
    Returns medical centers for a given country.
    Supports optional text filter: ?q=<text>
    Mirrors the endpoint in app_user.py — the HTML points to this server (port 5001).
    """
    doc = db.medicalCenters.find_one(
        {"countryCode": country_code.upper()},
        {"_id": 0}
    )
    if not doc:
        return jsonify({"error": f"País '{country_code}' no encontrado"}), 404

    q = request.args.get("q", "").strip()
    if q:
        pattern = re.compile(re.escape(q), re.IGNORECASE)
        doc["centers"] = [
            c for c in doc["centers"]
            if pattern.search(c.get("name", "")) or pattern.search(c.get("city", ""))
        ]

    return jsonify(doc)


# ──────────────────────────────────────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════════════╗")
    print("║   Panel Médico mhGAP — Servidor Flask            ║")
    print("║   API disponible en: http://localhost:5001       ║")
    print("╚══════════════════════════════════════════════════╝\n")
    app.run(debug=True, port=5001)