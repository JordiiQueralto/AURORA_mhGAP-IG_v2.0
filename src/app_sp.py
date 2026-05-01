from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import main_api_sp
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