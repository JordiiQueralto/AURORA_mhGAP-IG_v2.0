from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import main_api
import os

app = Flask(__name__)

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

    is_new = main_api.init_user(telephone)
    return jsonify({"status": "ok", "is_new": is_new})

@app.route('/api/circle', methods=['GET'])
def get_circle():
    telephone = request.args.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    circle_data = main_api.get_circle_data(telephone)
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

    bot_message, image_path = main_api.start_conversation(telephone)
    
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

    bot_message, image_path, is_ended = main_api.process_message(telephone, user_message)
    
    # Convertir ruta relativa en URL absoluta del servidor
    image_url = f"http://localhost:5000/{image_path}" if image_path else None

    return jsonify({
        "bot_message": bot_message,
        "image_url": image_url,
        "ended": is_ended
    })

@app.route('/api/circle', methods=['POST'])
def save_circle():
    data = request.json
    telephone = data.get('telephone')
    circle_data = data.get('circle_data') # Objeto con contactos, centro médico, etc.

    if not telephone or circle_data is None:
        return jsonify({"error": "telephone y circle_data requeridos"}), 400

    # Procesar el guardado
    main_api.save_circle_data(telephone, circle_data)

    return jsonify({"status": "ok", "message": "Datos del círculo guardados correctamente"})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """El familiar consulta sus notificaciones al abrir la app."""
    telephone = request.args.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    notifications = main_api.get_notifications(telephone)
    return jsonify({"notifications": notifications})

@app.route('/api/notifications/read', methods=['POST'])
def mark_read():
    """Marca las notificaciones como leídas cuando el familiar abre la pestaña."""
    data = request.json or {}
    telephone = data.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    main_api.mark_notifications_read(telephone)
    return jsonify({"status": "ok"})

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    """Limpia el contexto de sesión en BD para que la próxima llamada
    a /api/start arranque desde cero para este usuario."""
    data = request.json or {}
    telephone = data.get('telephone')
    if telephone:
        try:
            main_api.reset_session(int(telephone))
        except Exception:
            pass
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("\n╔══════════════════════════════════════════════════╗")
    print("║   Chatbot de Prevención — Servidor Flask         ║")
    print("║   API disponible en: http://localhost:5000       ║")
    print("╚══════════════════════════════════════════════════╝\n")
    app.run(debug=True, port=5000)