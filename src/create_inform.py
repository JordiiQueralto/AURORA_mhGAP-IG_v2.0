import os
import pymongo
from fpdf import FPDF
from bson.objectid import ObjectId

# 1. Definición de la estructura del PDF
class InformePDF(FPDF):
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
def generar_informe_en_descargas(user_id_str):
    try:
        # --- Configuración de MongoDB ---
        # Cambia 'tu_base_de_datos' y 'tu_coleccion' por tus nombres reales
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["CHATBOT_mhGAP"] 
        collection = db["users"]

        # Buscar el documento por ID (basado en image_127121.png)
        user_doc = collection.find_one({"_id": ObjectId(user_id_str)})
        
        if not user_doc:
            print(f"\n[Error: No se encontró el usuario con ID {user_id_str}]\n")
            return

        # --- Creación del objeto PDF ---
        pdf = InformePDF()
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
        pdf.section_title("Resultados SUI_EVAL (Riesgo de Suicidio)")
        
        # Mapeo de autolesión (booleano a texto)
        self_harm = "Sí" if sui_eval.get("1_self_harm") else "No"
        pdf.data_row("¿Presenta autolesiones?", self_harm)
        
        # Ideación activa
        ideacion = sui_eval.get("2_A_active_ideation", "No evaluado")
        pdf.data_row("Nivel de ideación activa", ideacion)
        pdf.ln(5)

        # Sección: Evaluación de Depresión (DEP_EVAL)
        dep_eval = user_doc.get("DEP_EVAL", {})
        pdf.section_title("Resultados DEP_EVAL (Depresión)")
        if dep_eval:
            # Aquí puedes iterar si DEP_EVAL tiene muchos campos
            for clave, valor in dep_eval.items():
                pdf.data_row(clave, valor)
        else:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, "No hay datos registrados en la evaluación de depresión.", 0, 1)

        # --- Lógica de guardado en carpeta Descargas ---
        home = os.path.expanduser("~")
        # El archivo se llamará Informe_Nombre_ID.pdf
        nombre_archivo = f"Informe_{user_doc.get('name', 'Usuario')}_{user_id_str}.pdf"
        ruta_descargas = os.path.join(home, "Downloads", nombre_archivo)

        pdf.output(ruta_descargas)
        print(f"\n[¡Éxito! El informe se ha guardado en: {ruta_descargas}]\n")

    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

# 3. Ejecución del script
if __name__ == "__main__":
    # Usa el ID que aparece en tu imagen image_127121.png
    ID_USUARIO = "69f3826e4c90058b18ce627e"
    generar_informe_en_descargas(ID_USUARIO)