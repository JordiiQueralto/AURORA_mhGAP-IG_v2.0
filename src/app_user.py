from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import services_user
import os
from pymongo import MongoClient
import re

app = Flask(__name__)
# Connect to mongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["CHATBOT_mhGAP"]

# Permite peticiones desde el HTML abierto como fichero local (file://)
# y desde cualquier localhost independientemente del puerto.
CORS(app, resources={r"/api/*": {"origins": ["null", "http://localhost", "http://127.0.0.1",
                                              "http://localhost:5000", "http://127.0.0.1:5000"]}},
     supports_credentials=False)

@app.route('/api/verify', methods=['POST'])
def verify_user():
    """Registra al usuario en BD al verificar el SMS. 
    Llamar antes de /api/start y antes de cargar el círculo."""
    data = request.json or {}
    telephone = data.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    is_new = services_user.init_user(telephone)
    return jsonify({"status": "ok", "is_new": is_new})

# ─────────────────────────────────────────────────────────────────────────────
# GET /api/medical-centers
# Devuelve: lista de { countryCode, countryName }
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/medical-centers", methods=["GET"])
def list_countries():
    countries = db.medicalCenters.find(
        {},
        {"_id": 0, "countryCode": 1, "countryName": 1}
    ).sort("countryName", 1)
    return jsonify(list(countries))


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/medical-centers/<countryCode>?q=<búsqueda>
# Devuelve: { countryCode, countryName, centers: [...] }
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/medical-centers/<country_code>", methods=["GET"])
def get_centers(country_code):
    doc = db.medicalCenters.find_one(
        {"countryCode": country_code.upper()},
        {"_id": 0}
    )
    if not doc:
        return jsonify({"error": f"País '{country_code}' no encontrado"}), 404

    # Filtro de búsqueda opcional (?q=texto)
    q = request.args.get("q", "").strip()
    if q:
        pattern = re.compile(re.escape(q), re.IGNORECASE)
        doc["centers"] = [
            c for c in doc["centers"]
            if pattern.search(c.get("name", "")) or pattern.search(c.get("city", ""))
        ]

    return jsonify(doc)

@app.route('/api/circle', methods=['GET'])
def get_circle():
    telephone = request.args.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    circle_data = services_user.get_circle_data(telephone)
    return jsonify({"circle_data": circle_data})

@app.route('/images/<path:filename>')
def serve_image(filename):
    # Usar ruta absoluta garantizada, subiendo un nivel si images/ está fuera de backend/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, '..', 'images')
    return send_from_directory(images_dir, filename)

@app.route('/api/start', methods=['POST'])
def start_chat():
    data = request.json
    telephone = data.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    bot_message, image_path = services_user.start_conversation(telephone)
    
    # Convertir ruta relativa en URL absoluta del servidor
    image_url = f"http://localhost:5000/{image_path}" if image_path else None

    return jsonify({
        "bot_message": bot_message,
        "image_url": image_url,
        "ended": False
    })

@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.json
    telephone = data.get('telephone')
    user_message = data.get('message')
    if not telephone or user_message is None:
        return jsonify({"error": "telephone y message requeridos"}), 400

    bot_message, image_path, is_ended, is_emergency, is_support = services_user.process_message(telephone, user_message)
    
    # Convertir ruta relativa en URL absoluta del servidor
    image_url = f"http://localhost:5000/{image_path}" if image_path else None

    return jsonify({
        "bot_message": bot_message,
        "image_url": image_url,
        "ended": is_ended,
        "emergency_112": is_emergency,
        "emergency_024": is_support
    })

@app.route('/api/circle', methods=['POST'])
def save_circle():
    data = request.json
    telephone = data.get('telephone')
    circle_data = data.get('circle_data') # Objeto con contactos, centro médico, etc.

    if not telephone or circle_data is None:
        return jsonify({"error": "telephone y circle_data requeridos"}), 400

    # Procesar el guardado
    services_user.save_circle_data(telephone, circle_data)

    return jsonify({"status": "ok", "message": "Datos del círculo guardados correctamente"})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """El familiar consulta sus notificaciones al abrir la app."""
    telephone = request.args.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    notifications = services_user.get_notifications(telephone)
    return jsonify({"notifications": notifications})

@app.route('/api/notifications/read', methods=['POST'])
def mark_read():
    """Marca las notificaciones como leídas cuando el familiar abre la pestaña."""
    data = request.json or {}
    telephone = data.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    services_user.mark_notifications_read(telephone)
    return jsonify({"status": "ok"})

@app.route('/api/user/delete', methods=['POST'])
def delete_user():
    """Elimina permanentemente el documento del usuario de la BD."""
    data = request.json or {}
    telephone = data.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    deleted = services_user.delete_user(telephone)
    if deleted:
        return jsonify({"status": "ok"})
    return jsonify({"error": "Usuario no encontrado"}), 404

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    """Ejecuta _run_farewell (guarda resumen de sesión) y limpia el contexto
    de sesión en BD. Se llama al hacer logout desde el front."""
    data = request.json or {}
    telephone = data.get('telephone')
    if telephone:
        try:
            services_user.reset_session(str(telephone))
        except Exception:
            pass
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("\n╔══════════════════════════════════════════════════╗")
    print("║   Chatbot de Prevención — Servidor Flask         ║")
    print("║   API disponible en: http://localhost:5000       ║")
    print("╚══════════════════════════════════════════════════╝\n")
    app.run(debug=True, port=5000)