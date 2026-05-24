import os
import pymongo
import datetime
from fpdf import FPDF
from bson.objectid import ObjectId

# 1. Definición de la estructura del PDF
class ReportPDF(FPDF):
    def header(self):
        # Logo o Título
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "Informe de Evaluación: Guía de Intervención mhGAP v2.0", 0, 1, "C")
        # Fecha de generación
        self.set_font("Arial", "", 10)
        self.cell(0, 10, f"Fecha de generación: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1, "C")
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
        pdf.section_title("Resultados evaluación riesgo de suicidio (SUI p.133)")
        
        if not sui_eval:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, "No hay datos registrados en la evaluación de suicidio.", 0, 1)
            pdf.ln(2)
        else:
            # --- 1. Autolesión actual ---
            self_harm_val = sui_eval.get("1_self_harm")
            if self_harm_val is not None:
                self_harm_text = "Sí" if self_harm_val else "No"
            else:
                self_harm_text = "No evaluado"
            pdf.data_row("¿Presenta autolesiones actuales?", self_harm_text)
            
            # --- 2A. Ideación activa ---
            # Diccionario para mapear los resultados del bot a lenguaje natural
            map_ideacion_activa = {
                "no": "No presenta",
                "ideation": "Presenta ideación suicida",
                "concrete_plan": "Tiene un plan concreto"
            }
            ideacion_activa_val = sui_eval.get("2_A_active_ideation")
            ideacion_activa_text = map_ideacion_activa.get(ideacion_activa_val, "No evaluado")
            pdf.data_row("Nivel de ideación activa", ideacion_activa_text)

            # --- 2B.1 Ideación en el último mes ---
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

            # --- 2B.2 Autolesión en el último año ---
            self_harm_year_val = sui_eval.get("2_B2_last_year_self_harm")
            if self_harm_year_val is not None:
                self_harm_year_text = "Sí" if self_harm_year_val else "No"
                pdf.data_row("¿Autolesión presente en el último año?", self_harm_year_text)
                
            # --- 3 Transtornos MNS recurrentes ---
            mns_disorder = sui_eval.get("3_MNS_disorder", {})
            existence = mns_disorder.get("existence")
            if existence is not None:
                if existence:
                    # Mapear categorías a nombres legibles
                    category_names = {
                        "depresion": "Depresión",
                        "ansiedad": "Ansiedad",
                        "psicosis": "Psicosis",
                        "bipolar": "Trastorno Bipolar",
                        "tca": "Trastornos de la Conducta Alimentaria",
                        "tdah": "TDAH",
                        "personalidad": "Trastorno de Personalidad",
                        "sueno": "Trastornos del Sueño",
                        "alcohol": "Dependencia al Alcohol",
                        "drogas": "Abuso de Drogas"
                    }
                    # Recopilar categorías presentes
                    present_categories = [
                        category_names[cat] for cat in category_names.keys()
                        if mns_disorder.get(cat, False)
                    ]
                    if present_categories:
                        disorders_text = ", ".join(present_categories)
                    else:
                        disorders_text = "Sí (sin especificar categorías)"
                    pdf.data_row("¿Presenta trastornos mentales no suicidas recurrentes?", disorders_text)
                else:
                    pdf.data_row("¿Presenta trastornos mentales no suicidas recurrentes?", "No")
            else:
                pdf.data_row("¿Presenta trastornos mentales no suicidas recurrentes?", "No evaluado")
            
              
            # --- 4 Dolor crónico ---
            chronic_pain = sui_eval.get("4_chronic_pain")
            if chronic_pain is not None:
                chronic_pain_text = "Sí" if chronic_pain else "No"
                pdf.data_row("¿Sufre dolor crónico?", chronic_pain_text)
            
            # --- 5 ¿Está justificado el tratamiento clínico¿ ---
            justified_treatment = sui_eval.get("5_functional_impact")
            if justified_treatment is not None:
                justified_treatment_text = "Sí" if justified_treatment else "No"
                pdf.data_row("¿Tiene un impedimiento funcional como para justificar el tratamiento clínico?", 
                             justified_treatment_text)


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
        pdf.section_title("Resultados evaluación de depressión (DEP p.21)")
        
        if not dep_eval:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, "No hay datos registrados en la evaluación de depresión.", 0, 1)
            pdf.ln(2)
        else:
            # --- 1A.1 Ánimo deprimido persistente ---
            mood_val = dep_eval.get("1_A1_depressed_mood")
            if mood_val is not None:
                mood_text = "Sí" if mood_val else "No"
                pdf.data_row("¿Ánimo deprimido persistente?", mood_text)
            
            # --- 1A.2 Anhedonia (pérdida de interés/placer) ---
            anhedonia_val = dep_eval.get("1_A2_anhedonia")
            if anhedonia_val is not None:
                anhedonia_text = "Sí" if anhedonia_val else "No"
                pdf.data_row("¿Pérdida de interés o placer (anhedonia)?", anhedonia_text)
            
            # --- 1B.1 Alteraciones del sueño ---
            sleep_val = dep_eval.get("1B_1_sleep_alteration")
            if sleep_val is not None:
                sleep_text = "Sí" if sleep_val else "No"
                pdf.data_row("¿Alteraciones del sueño?", sleep_text)
            
            # --- 1B.2 Cambios en apetito o peso ---
            appetite_val = dep_eval.get("1B_2_appetite_weight_change")
            if appetite_val is not None:
                appetite_text = "Sí" if appetite_val else "No"
                pdf.data_row("¿Cambios en apetito o peso?", appetite_text)
            
            # --- 1B.3 Fatiga o pérdida de energía ---
            fatigue_val = dep_eval.get("1B_3_fatigue_energy_loss")
            if fatigue_val is not None:
                fatigue_text = "Sí" if fatigue_val else "No"
                pdf.data_row("¿Fatiga o pérdida de energía?", fatigue_text)
            
            # --- 1B.4 Dificultad de concentración o decisión ---
            concentration_val = dep_eval.get("1B_4_concentration_decision")
            if concentration_val is not None:
                concentration_text = "Sí" if concentration_val else "No"
                pdf.data_row("¿Dificultad para concentrarse o tomar decisiones?", concentration_text)
            
            # --- 1B.5 Baja autoestima o culpa ---
            selfworth_val = dep_eval.get("1B_5_low_selfworth_guilt")
            if selfworth_val is not None:
                selfworth_text = "Sí" if selfworth_val else "No"
                pdf.data_row("¿Baja autoestima o sentimientos de culpa?", selfworth_text)
            
            # --- 1B.6 Desesperanza o ideación suicida ---
            hopelessness_val = dep_eval.get("1B_6_hopelessness_suicidal_ideation")
            if hopelessness_val is not None:
                hopelessness_text = "Sí" if hopelessness_val else "No"
                pdf.data_row("¿Desesperanza o ideación suicida?", hopelessness_text)
            
            # --- 1C Impacto funcional ---
            functional_val = dep_eval.get("1C_functional_impairment")
            if functional_val is not None:
                functional_text = "Sí" if functional_val else "No"
                pdf.data_row("¿Impacto funcional en actividades diarias?", functional_text)
                
            # --- 2A.1 En tratamiento/medicación ---
            med_val = dep_eval.get("2A_1_on_medication")
            if med_val is not None:
                med_text = "Sí" if med_val else "No"
                pdf.data_row("¿Actualmente en tratamiento o medicación?", med_text)
            
            # --- 2A.2 Condiciones físicas ---
            phys_cond_val = dep_eval.get("2A_2_physical_conditions")
            if phys_cond_val is not None:
                phys_cond_text = "Sí" if phys_cond_val else "No"
                pdf.data_row("¿Condiciones físicas relevantes (tiroides, anemia, etc.)?", phys_cond_text)
            
            # --- 2B.1 Episodio maníaco/hipomaníaco ---
            mania_val = dep_eval.get("2B_1_mania_episode")
            if mania_val is not None:
                mania_text = "Sí" if mania_val else "No"
                pdf.data_row("¿Episodios de euforia o irritabilidad exagerada?", mania_text)
            
            # --- 2B.2 Menor necesidad de sueño ---
            sleep_need_val = dep_eval.get("2B_2_decreased_sleep_need")
            if sleep_need_val is not None:
                sleep_need_text = "Sí" if sleep_need_val else "No"
                pdf.data_row("¿Menor necesidad de sueño sin cansancio?", sleep_need_text)
            
            # --- 2B.3 Actividad excesiva ---
            excess_activity_val = dep_eval.get("2B_3_excessive_activity")
            if excess_activity_val is not None:
                excess_activity_text = "Sí" if excess_activity_val else "No"
                pdf.data_row("¿Actividad o energía excesiva?", excess_activity_text)
            
            # --- 2B.4 Decisiones impulsivas ---
            impulsive_val = dep_eval.get("2B_4_impulsive_decisions")
            if impulsive_val is not None:
                impulsive_text = "Sí" if impulsive_val else "No"
                pdf.data_row("¿Decisiones impulsivas o gastos excesivos?", impulsive_text)
            
            # --- 2B.5 Desinhibición social ---
            disinhibition_val = dep_eval.get("2B_5_social_disinhibition")
            if disinhibition_val is not None:
                disinhibition_text = "Sí" if disinhibition_val else "No"
                pdf.data_row("¿Comportamiento más desinhibido o sin filtro?", disinhibition_text)
            
            # --- 2B.6 Distractibilidad ---
            distract_val = dep_eval.get("2B_6_distractibility")
            if distract_val is not None:
                distract_text = "Sí" if distract_val else "No"
                pdf.data_row("¿Fácil distracción o dificultad de concentración?", distract_text)
            
            # --- 2B.7 Grandiosidad ---
            grandios_val = dep_eval.get("2B_7_grandiosity")
            if grandios_val is not None:
                grandios_text = "Sí" if grandios_val else "No"
                pdf.data_row("¿Sentimientos de grandiosidad o destino especial?", grandios_text)
            
            # --- 2C Duelo reciente ---
            bereavement_val = dep_eval.get("2C_recent_bereavement")
            if bereavement_val is not None:
                bereavement_text = "Sí" if bereavement_val else "No"
                pdf.data_row("¿Duelo reciente (fallecimiento de persona cercana)?", bereavement_text)
            
            # --- 2D.1 Ideación suicida en último mes ---
            suicidal_val = dep_eval.get("2D_1_suicidal_ideation")
            if suicidal_val is not None:
                suicidal_text = "Sí" if suicidal_val else "No"
                pdf.data_row("¿Ideación suicida en el último mes?", suicidal_text)
            
            # --- 2D.2 Sentimientos de indignidad ---
            unworthiness_val = dep_eval.get("2D_2_unworthiness")
            if unworthiness_val is not None:
                unworthiness_text = "Sí" if unworthiness_val else "No"
                pdf.data_row("¿Sentimientos de indignidad o ser una carga?", unworthiness_text)
            
            # --- 2D.3 Síntomas psicóticos ---
            psychotic_val = dep_eval.get("2D_3_psychotic_symptoms")
            if psychotic_val is not None:
                psychotic_text = "Sí" if psychotic_val else "No"
                pdf.data_row("¿Síntomas psicóticos (alucinaciones, delirios)?", psychotic_text)
            
            # --- 2D.4 Aislamiento social ---
            withdrawal_val = dep_eval.get("2D_4_social_withdrawal")
            if withdrawal_val is not None:
                withdrawal_text = "Sí" if withdrawal_val else "No"
                pdf.data_row("¿Retirada social o aislamiento?", withdrawal_text)
            
            # --- 2D.5 Impacto funcional severo ---
            func_impair_val = dep_eval.get("2D_5_functional_impairment")
            if func_impair_val is not None:
                func_impair_text = "Sí" if func_impair_val else "No"
                pdf.data_row("¿Impacto funcional severo?", func_impair_text)
            
            # --- 2E.1 Diagnóstico previo de depresión ---
            prior_diag_val = dep_eval.get("2E_1_prior_diagnosis")
            if prior_diag_val is not None:
                prior_diag_text = "Sí" if prior_diag_val else "No"
                pdf.data_row("¿Diagnóstico previo de depresión?", prior_diag_text)
            
            # --- 2E.2 Medicación previa para depresión ---
            prior_med_val = dep_eval.get("2E_2_prior_medication")
            if prior_med_val is not None:
                prior_med_text = "Sí" if prior_med_val else "No"
                pdf.data_row("¿Ha recibido medicación previa para depresión?", prior_med_text)
            
            # --- 2E.3 Hospitalización previa ---
            prior_hosp_val = dep_eval.get("2E_3_prior_hospitalization")
            if prior_hosp_val is not None:
                prior_hosp_text = "Sí" if prior_hosp_val else "No"
                pdf.data_row("¿Hospitalización previa por problemas de salud mental?", prior_hosp_text)
            
            # --- 3A Consumo concurrente de alcohol ---
            alcohol_val = dep_eval.get("3A_concurrent_alcohol")
            if alcohol_val is not None:
                alcohol_text = "Sí" if alcohol_val else "No"
                pdf.data_row("¿Consumo concurrente de alcohol?", alcohol_text)
            
            # --- 3B Consumo concurrente de sustancias ---
            substances_val = dep_eval.get("3B_concurrent_substances")
            if substances_val is not None:
                substances_text = "Sí" if substances_val else "No"
                pdf.data_row("¿Consumo concurrente de otras sustancias?", substances_text)
            
            pdf.ln(5)
        
                # --- Disclaimer / Descargo de responsabilidad ---
        pdf.ln(10)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(100, 100, 100)

        disclaimer = (
            "Este informe ha sido generado automáticamente a partir de información "
            "recopilada mediante un sistema conversacional automatizado (chatbot). "
            "Los resultados presentados son únicamente orientativos y no constituyen "
            "un diagnóstico clínico ni sustituyen la valoración, evaluación o criterio "
            "de un profesional sanitario cualificado. La información contenida puede "
            "presentar errores, omisiones o interpretaciones inexactas. "
            "Este documento no debe utilizarse como única base para la toma de "
            "decisiones clínicas o terapéuticas."
        )

        pdf.multi_cell(0, 5, disclaimer)

        # Restaurar formato por defecto
        pdf.set_text_color(0, 0, 0)

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