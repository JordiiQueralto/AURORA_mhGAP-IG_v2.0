from flask import Flask, request, jsonify
from flask_cors import CORS
import main_api

app = Flask(__name__)
# Permite que chat.html (en el navegador) hable con el servidor
CORS(app) 

@app.route('/api/start', methods=['POST'])
def start_chat():
    data = request.json
    telephone = data.get('telephone')
    
    # Lógica para iniciar la conversación
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
    
    # Lógica para procesar el mensaje según el estado actual
    bot_message, is_ended = main_api.process_message(telephone, user_message)
    
    return jsonify({
        "bot_message": bot_message,
        "ended": is_ended
    })

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    # Opcional: Lógica para borrar historial temporal o cache
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    # Ejecuta el servidor en el puerto 5000
    app.run(debug=True, port=5000)