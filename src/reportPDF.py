import os
import pymongo
from fpdf import FPDF
from bson.objectid import ObjectId

# 1. Definición de la estructura del PDF
class ReportPDF(FPDF):
    def header(self):
        # Logo o Título
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "Informe de Evaluación Psicológica", 0, 1, "C")
        self.ln(5)

    def footer(self):
        # Pie de página con número de página
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

    def section_title(self, label):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, label, 0, 1, "L", 1)
        self.ln(4)

    def data_row(self, label, value):
        self.set_font("Arial", "B", 10)
        self.write(10, f"{label}: ")
        self.set_font("Arial", "", 10)
        self.write(10, f"{str(value)}\n")

# 2. Función principal
def generate_report(user_id_str, output_path=None):
    try:
        # Configuración de MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["CHATBOT_mhGAP"] 
        collection = db["users"]

        user_doc = collection.find_one({"_id": ObjectId(user_id_str)})
        
        if not user_doc:
            print(f"\n[Error: No se encontró el usuario con ID {user_id_str}]\n")
            return

        # Creación del objeto PDF
        pdf = ReportPDF()
        pdf.add_page()
        
        # Sección: Datos Personales
        pdf.section_title("Datos Identificativos")
        pdf.data_row("ID de Usuario", user_doc.get("_id"))
        pdf.data_row("Nombre", user_doc.get("name", "No consta"))
        pdf.data_row("Teléfono", user_doc.get("telephone", "No consta"))
        pdf.data_row("Edad", user_doc.get("age (years)", "No consta"))
        pdf.ln(5)

        # Sección: Evaluación de Suicidio (SUI_EVAL)
        sui_eval = user_doc.get("SUI_EVAL", {})
        pdf.section_title("Resultados evaluación riesgo de suicidio (SUI mhGAP)")
        
        if not sui_eval:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, "No hay datos registrados en la evaluación de suicidio.", 0, 1)
            pdf.ln(2)
        else:
            # --- 1. Autolesión actual (Estado 1) ---
            self_harm_val = sui_eval.get("1_self_harm")
            if self_harm_val is not None:
                self_harm_text = "Sí" if self_harm_val else "No"
            else:
                self_harm_text = "No evaluado"
            pdf.data_row("¿Presenta autolesiones actuales?", self_harm_text)
            
            # --- 2A. Ideación activa (Estado 2A) ---
            # Diccionario para mapear los resultados del bot a lenguaje natural
            map_ideacion_activa = {
                "no": "No presenta",
                "ideation": "Presenta ideación suicida",
                "concrete_plan": "Tiene un plan concreto"
            }
            ideacion_activa_val = sui_eval.get("2_A_active_ideation")
            ideacion_activa_text = map_ideacion_activa.get(ideacion_activa_val, "No evaluado")
            pdf.data_row("Nivel de ideación activa", ideacion_activa_text)

            # --- 2B.1 Ideación en el último mes (Estado 2B.1) ---
            # Se usa un texto en pasado ya que evalúa el último mes
            map_ideacion_mes = {
                "no": "No presentó",
                "ideation": "Presentó ideación suicida",
                "concrete_plan": "Tuvo un plan concreto"
            }
            ideacion_mes_val = sui_eval.get("2_B1_last_month_ideation")
            # Solo mostramos esto si el bot llegó a evaluarlo
            if ideacion_mes_val: 
                ideacion_mes_text = map_ideacion_mes.get(ideacion_mes_val, "No evaluado")
                pdf.data_row("Ideación en el último mes", ideacion_mes_text)

            # --- 2B.2 Autolesión en el último año (Estado 2B.2) ---
            self_harm_year_val = sui_eval.get("2_B2_last_year_self_harm")
            if self_harm_year_val is not None:
                self_harm_year_text = "Sí" if self_harm_year_val else "No"
                pdf.data_row("¿Autolesión en el último año?", self_harm_year_text)

            pdf.ln(5)
            
            # --- 3. Antecedentes y Medicación (Estado 3) ---
            # Este estado suele guardar una lista de hallazgos o un booleano 
            # indicando si hay síntomas de depresión o uso de psicofármacos.
            mental_health_val = sui_eval.get("3_mental_health_history")
            
            # Si guardas los hallazgos específicos (ej. "depresión, sertralina")
            if isinstance(mental_health_val, str) and mental_health_val != "no":
                # Limpiamos el texto para que la primera letra sea mayúscula
                mental_health_text = mental_health_val.capitalize()
            elif mental_health_val is True:
                mental_health_text = "Sí (Reporta antecedentes o medicación)"
            elif mental_health_val is False or mental_health_val == "no":
                mental_health_text = "No reporta antecedentes ni medicación actual"
            else:
                mental_health_text = "No evaluado"

            pdf.data_row("Antecedentes de salud mental / Medicación", mental_health_text)

            # --- Resumen de Riesgo (Opcional pero recomendado) ---
            # Una pequeña lógica para añadir una nota visual si hay riesgo alto
            if self_harm_val or ideacion_activa_val == "concrete_plan":
                pdf.ln(2)
                pdf.set_text_color(200, 0, 0) # Color rojo para alerta
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 10, "ALERTA: Se requiere intervención inmediata según protocolo mhGAP.", 0, 1)
                pdf.set_text_color(0, 0, 0) # Volver a negro

        # Sección: Evaluación de Depresión (DEP_EVAL)
        dep_eval = user_doc.get("DEP_EVAL", {})
        pdf.section_title("Resultados evaluación de depressión (DEP mhGAP)")
        if dep_eval:
            # Aquí puedes iterar si DEP_EVAL tiene muchos campos
            for clave, valor in dep_eval.items():
                pdf.data_row(clave, valor)
        else:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, "No hay datos registrados en la evaluación de depresión.", 0, 1)

        # --- Lógica de guardado ---
        # Si se pasa output_path (p.ej. fichero temporal desde Flask),
        # se guarda ahí para que send_file lo devuelva al navegador.
        # Si no, comportamiento original: carpeta Descargas del sistema.
        if output_path:
            ruta_final = output_path
        else:
            home = os.path.expanduser("~")
            nombre_archivo = f"Informe_{user_doc.get('name', 'Usuario')}_{user_id_str}.pdf"
            ruta_final = os.path.join(home, "Downloads", nombre_archivo)

        pdf.output(ruta_final)
        print(f"\n[¡Éxito! El informe se ha guardado en: {ruta_final}]\n")

    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")