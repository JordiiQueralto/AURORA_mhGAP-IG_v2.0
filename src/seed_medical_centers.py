"""
seed_medical_centers.py
───────────────────────
Crea (o reemplaza) la colección `medicalCenters` en MongoDB.
Cada documento representa un país con sus centros médicos.

Uso:
    python seed_medical_centers.py
    python seed_medical_centers.py --uri mongodb+srv://user:pass@cluster/db
    python seed_medical_centers.py --drop   # vacía la colección antes de insertar
"""

import argparse
from pymongo import MongoClient, ASCENDING

# ──────────────────────────────────────────────────────────────────────────────
# DATOS
# ──────────────────────────────────────────────────────────────────────────────
MEDICAL_CENTERS_DATA = [

  # ── ESPAÑA ────────────────────────────────────────────────────────────────
  {
    "countryCode": "ES",
    "countryName": "España",
    "centers": [
      # Barcelona
      {"name": "CAP Les Corts",           "city": "Barcelona"},
      {"name": "CAP Eixample Esquerra",   "city": "Barcelona"},
      {"name": "CAP Gràcia",              "city": "Barcelona"},
      {"name": "CAP Sants",               "city": "Barcelona"},
      {"name": "CAP Sarrià",              "city": "Barcelona"},
      {"name": "CAP Poblenou",            "city": "Barcelona"},
      {"name": "CAP Barceloneta",         "city": "Barcelona"},
      {"name": "CAP Sant Andreu",         "city": "Barcelona"},
      {"name": "CAP Horta",               "city": "Barcelona"},
      {"name": "CAP Nou Barris",          "city": "Barcelona"},
      {"name": "CAP Guinardó",            "city": "Barcelona"},
      {"name": "CAP Sant Gervasi",        "city": "Barcelona"},
      # L'Hospitalet de Llobregat
      {"name": "CAP Florida",             "city": "L'Hospitalet de Llobregat"},
      {"name": "CAP Bellvitge",           "city": "L'Hospitalet de Llobregat"},
      {"name": "CAP Collblanc",           "city": "L'Hospitalet de Llobregat"},
      {"name": "CAP Pubilla Cases",       "city": "L'Hospitalet de Llobregat"},
      {"name": "CAP Centre",              "city": "L'Hospitalet de Llobregat"},
      # Resto de Catalunya
      {"name": "CAP La Mina",            "city": "Sant Adrià de Besòs"},
      {"name": "CAP Badalona Centre",    "city": "Badalona"},
      {"name": "CAP Llefià",             "city": "Badalona"},
      {"name": "CAP Cornellà",           "city": "Cornellà de Llobregat"},
      {"name": "CAP Sant Boi",           "city": "Sant Boi de Llobregat"},
      {"name": "CAP Gavà",               "city": "Gavà"},
      {"name": "CAP Viladecans",         "city": "Viladecans"},
      {"name": "CAP Castelldefels",      "city": "Castelldefels"},
      {"name": "CAP Sabadell Nord",      "city": "Sabadell"},
      {"name": "CAP Sabadell Sud",       "city": "Sabadell"},
      {"name": "CAP Terrassa Est",       "city": "Terrassa"},
      {"name": "CAP Terrassa Oest",      "city": "Terrassa"},
      {"name": "CAP Manresa",            "city": "Manresa"},
      {"name": "CAP Girona Centre",      "city": "Girona"},
      {"name": "CAP Tarragona",          "city": "Tarragona"},
      {"name": "CAP Lleida",             "city": "Lleida"},
      # Madrid
      {"name": "Centro de Salud Arganzuela",    "city": "Madrid"},
      {"name": "Centro de Salud Vallecas",       "city": "Madrid"},
      {"name": "Centro de Salud Chamberí",       "city": "Madrid"},
      {"name": "Centro de Salud Tetuán",         "city": "Madrid"},
      {"name": "Centro de Salud Retiro",         "city": "Madrid"},
      {"name": "Centro de Salud Carabanchel",    "city": "Madrid"},
      {"name": "Centro de Salud Fuencarral",     "city": "Madrid"},
      {"name": "Centro de Salud Hortaleza",      "city": "Madrid"},
      # Valencia
      {"name": "Centro de Salud Valencia Centro",  "city": "Valencia"},
      {"name": "Centro de Salud Patraix",          "city": "Valencia"},
      {"name": "Centro de Salud La Fe",            "city": "Valencia"},
      # Otras ciudades
      {"name": "Centro de Salud Nervión",    "city": "Sevilla"},
      {"name": "Centro de Salud Alameda",    "city": "Málaga"},
      {"name": "Centro de Salud Zaidín",     "city": "Granada"},
      {"name": "Centro de Salud San Pablo",  "city": "Zaragoza"},
      {"name": "Centro de Salud Casco Viejo","city": "Bilbao"},
      {"name": "Centro de Salud Amara",      "city": "San Sebastián"},
      {"name": "Centro de Salud A Coruña",   "city": "A Coruña"},
      {"name": "Centro de Salud Murcia Centro","city":"Murcia"},
      {"name": "Otro / No aparece en la lista","city": ""},
    ]
  },

  # ── ARGENTINA ─────────────────────────────────────────────────────────────
  {
    "countryCode": "AR",
    "countryName": "Argentina",
    "centers": [
      {"name": "Hospital Pirovano",               "city": "Buenos Aires"},
      {"name": "Hospital Fernández",              "city": "Buenos Aires"},
      {"name": "Hospital Rivadavia",              "city": "Buenos Aires"},
      {"name": "Hospital Ramos Mejía",            "city": "Buenos Aires"},
      {"name": "Hospital Italiano",               "city": "Buenos Aires"},
      {"name": "Hospital Álvarez",                "city": "Buenos Aires"},
      {"name": "Hospital Santojanni",             "city": "Buenos Aires"},
      {"name": "Centro de Salud Malvinas",        "city": "Rosario"},
      {"name": "Hospital Provincial Córdoba",     "city": "Córdoba"},
      {"name": "Hospital Central Mendoza",        "city": "Mendoza"},
      {"name": "Otro / No aparece en la lista",   "city": ""},
    ]
  },

  # ── COSTA RICA ────────────────────────────────────────────────────────────
  {
    "countryCode": "CR",
    "countryName": "Costa Rica",
    "centers": [
      # CCSS — Áreas de Salud San José
      {"name": "Área de Salud Zapote-Catedral",     "city": "San José"},
      {"name": "Área de Salud Desamparados 1",      "city": "Desamparados"},
      {"name": "Área de Salud Desamparados 2",      "city": "Desamparados"},
      {"name": "Área de Salud Pavas",               "city": "San José"},
      {"name": "Área de Salud Hatillo",             "city": "San José"},
      {"name": "Área de Salud Curridabat",          "city": "Curridabat"},
      {"name": "Área de Salud Tibás-Merced",        "city": "Tibás"},
      # Alajuela
      {"name": "Área de Salud Alajuela Central",    "city": "Alajuela"},
      {"name": "Área de Salud San Ramón",           "city": "San Ramón"},
      {"name": "Área de Salud Grecia",              "city": "Grecia"},
      # Cartago
      {"name": "Área de Salud Cartago",             "city": "Cartago"},
      {"name": "Área de Salud Turrialba",           "city": "Turrialba"},
      # Heredia
      {"name": "Área de Salud Heredia Central",     "city": "Heredia"},
      {"name": "Área de Salud San Pablo de Heredia","city": "San Pablo"},
      # Guanacaste
      {"name": "Área de Salud Liberia",             "city": "Liberia"},
      {"name": "Área de Salud Nicoya",              "city": "Nicoya"},
      # Puntarenas
      {"name": "Área de Salud Puntarenas",          "city": "Puntarenas"},
      {"name": "Área de Salud Quepos",              "city": "Quepos"},
      # Limón
      {"name": "Área de Salud Limón Central",       "city": "Limón"},
      {"name": "Área de Salud Siquirres",           "city": "Siquirres"},
      # Hospitales de referencia
      {"name": "Hospital San Juan de Dios",         "city": "San José"},
      {"name": "Hospital México",                   "city": "San José"},
      {"name": "Hospital Calderón Guardia",         "city": "San José"},
      {"name": "Hospital Nacional Psiquiátrico",    "city": "San José"},
      {"name": "Hospital de las Mujeres",           "city": "San José"},
      {"name": "Hospital Tony Facio Castro",        "city": "Limón"},
      {"name": "Hospital Monseñor Sanabria",        "city": "Puntarenas"},
      {"name": "Hospital Dr. Enrique Baltodano",    "city": "Liberia"},
      {"name": "Otro / No aparece en la lista",     "city": ""},
    ]
  },

  # ── MÉXICO ────────────────────────────────────────────────────────────────
  {
    "countryCode": "MX",
    "countryName": "México",
    "centers": [
      {"name": "Centro de Salud T-III Portales",          "city": "Ciudad de México"},
      {"name": "Centro de Salud T-III Coyoacán",          "city": "Ciudad de México"},
      {"name": "Centro de Salud T-III Iztapalapa",        "city": "Ciudad de México"},
      {"name": "Centro de Salud Guerrero",                "city": "Ciudad de México"},
      {"name": "Unidad Médica IMSS Monterrey Norte",      "city": "Monterrey"},
      {"name": "Unidad Médica IMSS Guadalajara",          "city": "Guadalajara"},
      {"name": "Centro de Salud Urbano Puebla",           "city": "Puebla"},
      {"name": "Clínica ISSSTE Tijuana",                  "city": "Tijuana"},
      {"name": "Otro / No aparece en la lista",           "city": ""},
    ]
  },

  # ── COLOMBIA ──────────────────────────────────────────────────────────────
  {
    "countryCode": "CO",
    "countryName": "Colombia",
    "centers": [
      {"name": "Hospital de Usaquén",           "city": "Bogotá"},
      {"name": "Hospital de Chapinero",         "city": "Bogotá"},
      {"name": "Hospital de Kennedy",           "city": "Bogotá"},
      {"name": "Hospital Universitario Medellín","city": "Medellín"},
      {"name": "Hospital del Valle",            "city": "Cali"},
      {"name": "Hospital Regional Barranquilla","city": "Barranquilla"},
      {"name": "Otro / No aparece en la lista", "city": ""},
    ]
  },

  # ── CHILE ─────────────────────────────────────────────────────────────────
  {
    "countryCode": "CL",
    "countryName": "Chile",
    "centers": [
      {"name": "CESFAM Juanita Aguirre",        "city": "Santiago"},
      {"name": "CESFAM San Gregorio",           "city": "Santiago"},
      {"name": "CESFAM Pudahuel",               "city": "Pudahuel"},
      {"name": "CESFAM Valparaíso",             "city": "Valparaíso"},
      {"name": "CESFAM Concepción Norte",       "city": "Concepción"},
      {"name": "Otro / No aparece en la lista", "city": ""},
    ]
  },

  # ── PERÚ ──────────────────────────────────────────────────────────────────
  {
    "countryCode": "PE",
    "countryName": "Perú",
    "centers": [
      {"name": "Centro de Salud Surquillo",          "city": "Lima"},
      {"name": "Centro de Salud Chorrillos",         "city": "Lima"},
      {"name": "Centro de Salud San Juan de Lurigancho","city":"Lima"},
      {"name": "Hospital Regional Arequipa",         "city": "Arequipa"},
      {"name": "Hospital Regional Cusco",            "city": "Cusco"},
      {"name": "Otro / No aparece en la lista",      "city": ""},
    ]
  },

]

# ──────────────────────────────────────────────────────────────────────────────
# SEED
# ──────────────────────────────────────────────────────────────────────────────
def seed(uri: str, db_name: str, drop: bool):
    client = MongoClient(uri)
    db = client[db_name]
    col = db["medicalCenters"]

    if drop:
        col.drop()
        print("⚠️  Colección 'medicalCenters' vaciada.")

    # Índices
    col.create_index([("countryCode", ASCENDING)], unique=True)
    col.create_index([("centers.name", ASCENDING)])

    inserted = 0
    updated  = 0
    for doc in MEDICAL_CENTERS_DATA:
        result = col.update_one(
            {"countryCode": doc["countryCode"]},
            {"$set": doc},
            upsert=True
        )
        if result.upserted_id:
            inserted += 1
        else:
            updated += 1

    print(f"✅ Seed completado — {inserted} insertados, {updated} actualizados.")
    print(f"   Total países: {col.count_documents({})}")
    client.close()

# Introducimos datos en nuestra DB
uri = "mongodb://localhost:27017/"
db_name = "CHATBOT_mhGAP"
seed(uri, db_name, drop=True)