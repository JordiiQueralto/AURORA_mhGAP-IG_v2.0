from flask import Flask, request, jsonify
from flask_cors import CORS
import main_api

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

@app.route('/api/start', methods=['POST'])
def start_chat():
    data = request.json
    telephone = data.get('telephone')
    if not telephone:
        return jsonify({"error": "telephone requerido"}), 400

    bot_message = main_api.start_conversation(telephone)

    return jsonify({
        "bot_message": bot_message,
        "ended": False
    })

@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.json
    telephone = data.get('telephone')
    user_message = data.get('message')
    if not telephone or user_message is None:
        return jsonify({"error": "telephone y message requeridos"}), 400

    bot_message, is_ended = main_api.process_message(telephone, user_message)

    return jsonify({
        "bot_message": bot_message,
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