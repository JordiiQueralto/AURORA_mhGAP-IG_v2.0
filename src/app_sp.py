"""
app_sp.py
Flask backend exclusivo para el panel de especialistas (médicos).
Corre en el puerto 5001 para no colisionar con app.py (puerto 5000).

Endpoints expuestos:
  POST  /api/doctor/register          → Registro de nuevo especialista
  POST  /api/doctor/login             → Login
  PUT   /api/doctor/profile           → Actualizar perfil  [Auth]
  GET   /api/doctor/patients          → Usuarios del centro [Auth]
  PUT   /api/doctor/patients/<id>/notes   → Guardar nota clínica [Auth]
  GET   /api/doctor/patients/<id>/sessions → Historial de sesiones [Auth]
  GET   /api/doctor/patients/<id>/report   → Generar informe PDF [Auth]

  GET   /api/doctor/countries         → Lista de países con centros (reutiliza medicalCenters)
  GET   /api/medical-centers/<code>   → Centros de un país (igual que app.py)
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
from pymongo import MongoClient
import re
import main_api_sp

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
    """
    Decorador que valida el token Bearer en la cabecera Authorization.
    Si es válido, inyecta el documento del especialista como kwarg 'specialist'.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        specialist = main_api_sp.validate_token(token)
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
    Registra un nuevo especialista.

    Body JSON esperado:
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
        session = main_api_sp.handle_registration(data)
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
    Login de especialista.

    Body JSON: { "email": "...", "password": "..." }
    Devuelve el objeto SESSION que el frontend almacena en la variable SESSION.
    """
    data     = request.json or {}
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email y contraseña son obligatorios."}), 400

    try:
        session = main_api_sp.handle_login(email, password)
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
    Actualiza los campos de perfil editables del especialista.
    Requiere Authorization: Bearer <token>

    Body JSON (todos opcionales, se actualiza lo que llegue):
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
        main_api_sp.save_profile_update(coll_number, profile_data)
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
    Devuelve los usuarios que pertenecen al mismo centro que el especialista.
    Requiere Authorization: Bearer <token>
    """
    center_name = specialist.get("centerName", "")

    if not center_name:
        return jsonify({"patients": []}), 200

    try:
        patients = main_api_sp.get_patients_for_specialist(center_name)
        return jsonify({"patients": patients}), 200
    except Exception as e:
        print(f"[ERROR /patients] {e}")
        return jsonify({"error": "Error al recuperar usuarios."}), 500


@app.route("/api/doctor/patients/<user_id>/notes", methods=["PUT"])
@require_auth
def save_note(specialist, user_id):
    """
    Guarda una nota clínica del especialista sobre un usuario.
    Requiere Authorization: Bearer <token>

    Body JSON: { "notes": "Texto de la nota clínica..." }
    """
    data = request.json or {}
    note = data.get("notes", "").strip()
    coll_number = specialist.get("collegiateNumber", "")

    try:
        main_api_sp.save_patient_note(user_id, coll_number, note)
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
    Devuelve el historial completo de sesiones de un usuario concreto.
    Requiere Authorization: Bearer <token>

    Devuelve lista de sesiones con: date, datetime, summary, valoration, status
    ordenadas de más reciente a más antigua.
    """
    try:
        sessions = main_api_sp.get_patient_sessions(user_id)
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
    Genera el informe PDF del paciente y lo devuelve como descarga directa.
    Requiere Authorization: Bearer <token>

    El PDF se genera en memoria con un fichero temporal y se elimina tras el envío,
    por lo que no queda nada escrito en disco del servidor.
    """
    import tempfile, os

    try:
        # Creamos un fichero temporal con extensión .pdf
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp_path = tmp.name
        tmp.close()

        # Generamos el PDF en esa ruta temporal (en vez de en Descargas)
        main_api_sp.generate_patient_report(user_id, output_path=tmp_path)

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


# ──────────────────────────────────────────────────────────────────────────────
# MEDICAL CENTERS (reutilizando la misma colección de app.py)
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/doctor/countries", methods=["GET"])
def list_countries():
    """
    Devuelve la lista de países disponibles en la colección medicalCenters.
    El frontend usa este endpoint al abrir la pestaña de registro.
    """
    countries = db.medicalCenters.find(
        {},
        {"_id": 0, "countryCode": 1, "countryName": 1}
    ).sort("countryName", 1)
    return jsonify(list(countries))


@app.route("/api/medical-centers/<country_code>", methods=["GET"])
def get_centers(country_code):
    """
    Devuelve los centros de un país concreto.
    Soporta filtro opcional: ?q=<texto>
    Idéntico al endpoint en app.py — el HTML apunta a este servidor (puerto 5001).
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