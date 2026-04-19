def bot_output_info(phase, state):
    
    dict = {
        
        "PROFILE": {
            "name": {
                "nucleo": """¿Cómo te llamas?"""
                },
            "age": {
                "nucleo": """¿Qué edad tienes?"""
                },
            "reason": {
                "nucleo": """¿Cuál es el motivo de la llamada?"""
                },
            "expectation": {
                "nucleo": """¿Qué aspectativas tienes sobre mis capacidades?"""
                },
            },
        
        "DEP_EVAL": {
            "1A.1": {
                "nucleo": """Durante mínimo un periodo de dos semanas, ¿te has sentido triste, 
                vacío o sin ánimo la mayor parte del día, casi todos los días?”"""
            },
            "1A.2": {
                "nucleo": """Durante ese mismo periodo, ¿has perdido el interés o el placer en 
                actividades que antes disfrutaba, como hobbies, relaciones o trabajo?"""
            },
            "1B.1": {
                "nucleo": """¿Has notado cambios persistentes durante al menos dos semanas en aspectos 
                como pueden ser la dificultad para conciliar el sueño o por el contrario dormir demasiado?"""
            },
            "1B.2": {
                "nucleo": """¿Qué me dices pero sobre cambios significativos del apetito o del peso?"""
            },
            "1B.3": {
                "nucleo": """¿Has notado fatiga o pérdida de energía durante al menos dos semanas?"""
            },
            "1B.4": {
                "nucleo": """¿Has notado  problemas para concentrarte o tomar decisiones?"""
            },
            "1B.5": {
                "nucleo": """¿En este tiempo has sentido que no estás a la altura de las cosas 
                o que a veces te cuesta ver tus propios méritos?"""
            },
            "1B.6": {
                "nucleo": """"En estas últimas semanas, ¿has sentido que ya no hay salida o que la 
                vida se te hace demasiado pesada como para seguir adelante?" """
            },
            "1C": {
                "nucleo": """¿Hay algo de esto que está afectando tu capacidad de llevar tu vida 
                del día a día, como trabajar, estudiar, relacionarte con otros o cuidarte?"""
            },
            "2A.1": {
                "nucleo": """"""
            },
            "2A.2": {
                "nucleo": """"""
            },
            "2B.1": {
                "nucleo": """"""
            },
            "2B.2": {
                "nucleo": """"""
            },
            "2B.3": {
                "nucleo": """"""
            },
            "2B.4": {
                "nucleo": """"""
            },
            "2B.5": {
                "nucleo": """"""
            },
            "2C": {
                "nucleo": """"""
            },
            "2D.1": {
                "nucleo": """"""
            },
            "2D.2": {
                "nucleo": """"""
            },
            "2D.3": {
                "nucleo": """"""
            },
            "2D.3.1": {
                "nucleo": """"""
            },
            "3": {
                "nucleo": """"""
            },
        },
        
        "SUI_EVAL": {
            "1": {
                "nucleo": """En este momento, o recientemente, ¿te has hecho daño físico de alguna 
                forma, como heridas, haber tomado algo que te pudiera hacer mal, o algo similar?"""},
            "2A": {
                "nucleo": """¿Tienes planes o pensamientos de hacerte daño o de quitarte la 
                vida actualmente?"""},
            "2B.1": {
                "nucleo": """¿Has tenido pensamientos o un plan de autolesión el último mes?
                """},
            "2B.2": {
                "nucleo": """En el último año, ¿has llegado a autolesionarte físicamente con la 
                intención de hacerte daño o de quitarte la vida?"""},
            "3": {
                "nucleo": """“¿Has estado recibiendo tratamiento o atención por algún problema 
                de salud mental, como depresión, ansiedad, o algo relacionado con el consumo de 
                alcohol u otras sustancias?
                """},
            "4": {
                "nucleo": """¿Tienes algún dolor físico que lleve semanas o meses sin 
                mejorar y que afecte tu día a día?
                """},
            "5": {
                "nucleo": """¿Sientes que tus emociones o tu estado de ánimo están afectando tu 
                capacidad de hacer las cosas del día a día, como trabajar, estudiar, 
                relacionarte con otros, o cuidarte?”
                """}
        }    
    }
    
    # First we get the data for the phase and state 
    phase_data = dict.get(phase, {})
    state_data = phase_data.get(state, {})
    
    # Then we extract the context and nucleo
    raw_nucleo = state_data.get("nucleo", "Sin núcleo disponible")
    
    # Clean up the context and nucleo by removing extra whitespace
    nucleo = " ".join(raw_nucleo.split())
    
    return nucleo


def trigger_dict(phase, state):
    trigger_phase_state = {
        "DEP": {
            "1A": {
                "trigger_yes":  [ # Afirmaciones directa
                                  "sí", "sí he notado", "claro", "exacto", "por supuesto", 
                                  "definitivamente", "cierto",
                                  
                                  # Síntomas de estado de ánimo bajo/triste/vacío
                                  "triste", "me siento triste", "muy triste", "triste todo el tiempo", 
                                  "estado de ánimo bajo", "bajo de ánimo", "vacío", "me siento vacío", 
                                  "siento un vacío", "deprimido", "deprimida", "depresión", 
                                  "me siento deprimido", "persistentemente triste", "no estoy contento", 
                                  "no estoy feliz",

                                  # Pérdida de interés/placer
                                  "perdí el interés", "sin ganas", "desganado", "desganada", 
                                  "nada me gusta", "no disfruto nada", "perdí el placer", "no me motiva nada", 
                                  "sin interés", "pérdida de interés", "no tengo ganas de nada", 
                                  "cosas que antes disfrutaba", "ya no disfruto", "no me apetece nada"],

                "trigger_no": [ # Negaciones directa
                                "no", "no he notado", "nunca", "jamás", "nada de eso", "para nada", 
                                "en absoluto", "de ninguna manera",

                                # Ausencia de síntomas de ánimo bajo
                                "no estoy triste", "no me siento vacío", "no estoy deprimido", 
                                "no tengo depresión", "mi ánimo está bien", "estado de ánimo normal",

                                # Interés/placer intacto
                                "sigo disfrutando", "me gusta lo mismo", "tengo interés", "disfruto las cosas", 
                                "me motivan", "tengo ganas", "estoy motivado", "sigo con ganas"]
                },
            "1B.1": {
                "trigger_yes": [],
                "trigger_no": []
                },
        },
        
        "SUI": {
        }
    }
    
    triggers = {
        "trigger_ambiguity": [ "no sé", "no se", "no estoy seguro", "no estoy segura", 
                               "no tengo claro", "no recuerdo", "depende", "quizás", 
                               "tal vez", "podría ser", "no lo sé exactamente", "no entiendo", 
                               "qué quieres decir", "explica mejor", "repite porfa", 
                               "repite por favor", "repite", "aclárame", "no capté" ],
        "trigger_evasion": [  "cuéntame un chiste", "que tiempo hace", 
                             "dime la hora", "qué tal tú", "pasemos página", "olvídalo", "olvídate", 
                             "no es nada", "no es grave", "son tonterías", "no pasa nada", 
                             "no vale la pena", "poca cosa", "es poco", "tengo miedo de decirlo",
                             "es complicado", "me duele hablar de eso", "muy difícil explicarlo" ],
        "trigger_negation": [ "cambia de tema", "canvia de tema", "otro tema", "habla de otra cosa", 
                             "hablemos de otra cosa", "no quiero hablar de eso", "prefiero no contestar", 
                             "no voy a responder", "eso no te importa", "no es asunto tuyo", 
                            "déjame en paz", "no insistas", "pasa de eso", "no me apetece" ],
        "trigger_hostility": [ "eres inútil", "robot inútil", "qué pregunta tonta", "no me jodas", 
                               "esto es ridículo", "para de preguntar", "no me fío de ti", 
                               "pregunta estúpida", "qué tontería", "no confío en ti", "cállate"]
        
        
    }
    
    phase_data = trigger_phase_state.get(phase, {})
    state_data = phase_data.get(state, {})

    triggers["trigger_yes"] = state_data.get("trigger_yes", [])
    triggers["trigger_no"] = state_data.get("trigger_no", [])
    
    return triggers
    

def variant(phase, state, classification):
    
    variant_dict = {
        "DEP": {
            "1A": {
                "time": """Está bien tomarte tu tiempo. ¿Te gustaría compartir cómo te has 
                sentido últimamente?""",

                "ambiguity": """Cuando te pregunto por tu estado de ánimo, me refiero a si has 
                notado tristeza persistente, desgana o falta de interés en cosas que antes te 
                gustaban. ¿Ha ocurrido algo así?""",

                "evasion": """Entiendo que puede ser un tema sensible. Solo para aclarar: 
                ¿Has sentido tristeza o falta de interés durante más de dos semanas?""",

                "negation": """Entiendo perfectamente que no quieras responder ahora. Estoy 
                aquí cuando estés listo.""",

                "hostility": """Lo siento si la pregunta te molesta. Mi intención es entenderte 
                mejor y apoyarte. Tómate tu tiempo.""",

                "non_classificable": """Perdona, no estoy seguro de haber entendido bien lo que 
                mencionaste. ¿Podrías aclararlo?"""
            },
            "1B1": {
                "time": "",
                "ambiguity": "",
                "evasion": "",
                "negation": "",
                "hostility": "",
                "non_classificable": ""
            }
        },

        "SUI": {
            "1": {
                "time": "",
                "ambiguity": "",
                "evasion": "",
                "negation": "",
                "hostility": "",
                "non_classificable": ""
            }
        }
    }

    # We obtain the variant based on the phase, state and classification
    phase_data = variant_dict.get(phase, {})
    state_data = phase_data.get(state, {})
    raw_variant = state_data.get(classification, "Sin variante disponible")
    
    # Clean up the context and nucleo by removing extra whitespace
    variant = " ".join(raw_variant.split())
    return variant
    
     
####################################################################################
# Example
##phase = "DEP"
##state = "1A"
##classification = "ambiguity"

##context_guide, nucleo = bot_output_info(phase, state)

##print("\nContext Guide:", context_guide)
##print("\nNucleo:", nucleo)

##trigger = trigger(phase, state)
##print(trigger)

##variant = variant(phase, state, classification)
##print(variant)