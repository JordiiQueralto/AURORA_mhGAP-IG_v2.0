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
                "nucleo": """¿Qué aspectativas tienes sobre esta conversación?"""
                },
            "commitment": {
                "nucleo": """Ahora voy a hacerte preguntas para poder entender mejor como te
                sientes para poder ayudarte. Para ello, necessito que te comprometas a responder
                sinceramente a mis preguntas. ¿Trato hecho?"""
            }
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
                "nucleo": """¿Estás recibiendo tratamiento o tomando algún tipo de medicación?"""
            },
            "2A.2": {
                "nucleo": """¿Tu médico te ha comentado algo sobre tiroides, anemia o sobre nutrición?"""
            },
            "2B.1": {
                "nucleo": """¿Has experimentado un estado de ánimo anormalmente elevado, eufórico o 
                muy irritable durante como mínimo una semana?"""
            },
            "2B.2": {
                "nucleo": """¿Has notado que necesitas dormir mucho menos de lo habitual sin
                sientirte cansad(o|a)?"""
            },
            "2B.3": {
                "nucleo": """¿Te has sentido con más energía de lo normal, con una actividad 
                excesiva difícil de controlar?"""
            },
            "2B.4": {
                "nucleo": """¿Has tomado decisiones impulsivas sin pensar en las consecuencias, 
                como por ejemplo, gastos excesivos o tomar decisiones importantes sin reflexionar?"""
            },
            "2B.5": {
                "nucleo": """¿Has sentido últimamente que dices o haces cosas que antes te habrían 
                dado vergüenza o que otros consideran fuera de lugar?"""
            },
            "2B.6": {
                "nucleo": """¿Te resulta difícil mantener el hilo de una conversación o terminar 
                una tarea porque cualquier ruido o pensamiento te desvía?"""
            },
            "2B.7": {
                "nucleo": """¿Tienes la sensación de que estás destinado a lograr algo grandioso 
                o que tus capacidades están muy por encima de las de tus colegas o amigos?"""
            },
            "2C": {
                "nucleo": """¿Has pasado por el fallecimiento de un familiar o alguien muy 
                cercano en los últimos seis meses?"""
            },
            "2D.1": {
                "nucleo": """¿Has sentido últimamente que la vida no vale la pena o que 
                estarías mejor si no estuvieras aquí?"""
            },
            "2D.2": {
                "nucleo": """¿Crees que mereces las cosas buenas que te pasan o que la 
                gente te ayude?"""
            },
            "2D.3": {
                "nucleo": """¿Has escuchado voces, ruidos o visto cosas que otros parecen 
                no notar?"""
            },
            "2D.4": {
                "nucleo": """¿Has notado que pasas mucho más tiempo solo de lo habitual?"""
            },
            "2D.5": {
                "nucleo": """¿Estás rechazando invitaciones o ignorando llamadas y mensajes 
                que antes sí respondías?"""
            },
            "2D.6": {
                "nucleo": """¿Te está costando más de lo normal levantarte para ir a trabajar 
                o estudiar?"""
            },
            "2D.6.1": {
                "nucleo": """¿Has faltado o has pensado en dejar de ir recientemente?"""
            },
            "2E.1": {
                "nucleo": """¿Alguna vez un médico, psicólogo o psiquiatra te ha diagnosticado 
                depresión o algún trastorno del estado de ánimo?"""
            },
            "2E.2": {
                "nucleo": """¿Has tomado en el pasado medicación para dormir, para los nervios 
                o antidepresivos?"""
            },
            "2E.3": {
                "nucleo": """¿Alguna vez has tenido que ser ingresado en un centro de salud 
                debido a cómo te sentías emocionalmente?"""
            },
            "3.1": {
                "nucleo": """¿Tomas alcohol?"""
            },
            "3.1.1": {
                "nucleo": """¿Con qué frecuencia?"""
            },
            "3.2": {
                "nucleo": """¿Tomas algún otro tipo de sustancia estupefaciente?"""
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
        },
        "SUI_PROTOCOLS": {
            "1": {
                "nucleo": """ Te dejo un número donde podran ayudarte mejor. Porfavor llama 
                ahora y cuando te repondan diles tu dirección exacta y explícales el tipo de 
                lesión que te has hecho.
                """},
            "2": {
                "nucleo": """ Aquí tienes una guía de ayuda y esperanza. Te animo a conectarte 
                con tu red de apoyo o acudir al centro de salud más cercano. 
                """},
            "3": {
                "nucleo": """
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


def variant_dict(phase, state, variant):
    
    variant_dict = {
        
        "PROFILE": {
            "name": {
                "repeat": """No te he entendido. ¿Puedes decir 'me llamo...'?"""
                },
            "age": {
                "repeat": """No te he entendido. ¿Puedes decir '... años'? """
                },
            "commitment": {
                "repeat": """No te he entendido muy bien. ¿Puedes volver a responderme? """
                },
            },
        
        "DEP_EVAL": {
            "1A": {
                "time": """Está bien tomarte tu tiempo. ¿Te gustaría compartir cómo te has 
                sentido últimamente?""",

                "ambiguity": """Cuando te pregunto por tu estado de ánimo, me refiero a si has 
                notado tristeza persistente, desgana o falta de interés en cosas que antes te 
                gustaban. ¿Ha ocurrido algo así?""",

                "evasion": """Entiendo que puede ser un tema sensible. Solo para aclarar: 
                ¿Has sentido tristeza o falta de interés durante más de dos semanas?""",

                "refusal": """Entiendo perfectamente que no quieras responder ahora. Estoy 
                aquí cuando estés listo.""",

                "hostility": """Lo siento si la pregunta te molesta. Mi intención es entenderte 
                mejor y apoyarte. Tómate tu tiempo.""",

                "non_classificable": """Perdona, no estoy seguro de haber entendido bien lo que 
                mencionaste. ¿Podrías aclararlo?"""
                },
            "1B.1": {
                "time": "",
                "ambiguity": "",
                "evasion": "",
                "refusal": "",
                "hostility": "",
                "non_classificable": ""
                },
            "1B.2": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "1B.3": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "1B.4": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "1B.5": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "1B.6": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "1C": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2A.1": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2A.2": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2B.1": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2B.2": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2B.3": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2B.4": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2B.5": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2C": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2D.1": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2D.2": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2D.3": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "2D.3.1": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "3": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                }
            },

        "SUI_EVAL": {
            "1": {
                "time": """Entiendo que puede ser difícil hablar de esto. Tómate el tiempo que 
                necesites. I cuando te sientas listo puedes contestar. ¿Estás bien físicamente 
                en este momento?""",
                
                "ambiguity": """Quizás no me expresé bien. Con 'hacerse daño' me refiero a si 
                hoy ha ocurrido algo como haber tomado medicación de más, haberte causado alguna 
                herida o haber ingerido algo que te haga sentir mal.""",
                
                "evasion": """Entiendo perfectamente que quieras cambiar de tema o que te parezca poca 
                cosa. Lo respeto completamente. Sé que estas preguntas pueden parecer innecesarias. 
                Pero necesito saber si te encuentras bien ahora mismo para poder ayudarte.""",
                
                "refusal": """Entiendo perfectamente que no quieras hablar de esto. Lo respeto 
                completamente. Sé que puede ser muy difícil abrirse con estas preguntas. No te voy 
                a presionar más. Solo necesito saber si estás físicamente bien ahora mismo o si ha 
                pasado algo que requiera atención.""",
                
                "hostility": """Sé que mi pregunta te parece ridícula e inadecuada. Lo acepto 
                totalmente, tienes toda la razón en sentirte así. Sin embargo, lo único que quiero 
                es ayudarte. ¿Te encuentras bien físicamente?""",
                
                "non_class": """Me has hablado sobre [parafrasear]. Pero con esto no acabo de 
                comprender cómo te encuentras. ¿Podrías volver a contármelo con más detalle? """
                },
            "2A": {
                "time":"""Entiendo que estas preguntas son difíciles y pueden remover muchas 
                cosas. Tómate un momento y cuándo estes preparado puedes contestarme""",
                
                "ambiguous": """Cuando te pregunto si tienes pensamientos de hacerte daño o de 
                quitarte la vida, me refiero a si has pensado en suicidarte, en planes concretos o en 
                formas de herirte, no solo a sentirte triste o ansioso. ¿Ha ocurrido algo de eso?""",
                
                "evasion": """Comprendo que te resulte pesado o innecesario hablar de esto. Aun 
                así, necesito preguntártelo con claridad: en la actualidad, ¿tienes pensamientos 
                de quitarte la vida o de hacerte daño?""",
                
                "refusal": """“No tienes ninguna obligación de compartir más de lo que desees. Es 
                tu espacio y tu ritmo. Aun así, para poder ayudarte de verdad necesito saber si 
                estos días has tenido ideas de suicidarte o de hacerte daño.” """,
                
                "hostility": """Comprendo que te moleste que te pregunte esto. Puede parecer invasivo, 
                pero mi único objetivo es asegurar que recibas la ayuda necesaria si la estás pasando 
                mal. ¿Has tenido esos pensamientos?""",
                
                "non_class": """Me has hablado de [parafrasear]. ¿Podrías profundizar un poco más?"""
                },
            "2B.1": {
                "time":"""Tómate un momento si lo necesitas y responde cuando estés listo. 
                Estoy aquí contigo.” """,
                
                "ambiguous": """Cuando te pregunto si has tenido pensamientos de hacerte daño o de 
                quitarte la vida, me refiero a si has pensado en suicidarte, en planes concretos o 
                en formas de herirte, no solo a sentirte triste o ansioso. ¿Ha ocurrido algo de eso?""",
                
                "evasion": """Entiendo que prefieras cambiar de tema o que esto te resulte pesado, y 
                lo respeto. Aun así, es importante saber si en este último mes has tenido pensamientos 
                o un plan de hacerte daño o de quitarte la vida.""",
                
                "refusal": """Comprendo que te moleste que te pregunte esto. Puede parecer invasivo, 
                pero mi único objetivo es asegurar que recibas la ayuda necesaria si la estás pasando 
                mal. En este último mes, ¿has tenido pensamientos o un plan de hacerte daño o de 
                quitarte la vida?""",
                
                "hostility": """Comprendo que te moleste que te pregunte esto. Puede parecer invasivo, 
                pero mi único objetivo es asegurar que recibas la ayuda necesaria si la estás pasando 
                mal. ¿Has tenido esos pensamientos?""",
                
                "non_class": """“Me has hablado de [parafrasear]. ¿Podrías profundizar un poco más?"""
                },
            "2B.2": {
                "time":"""Entiendo que recordar cosas del último año puede ser muy duro. Tómate un 
                momento y cuando estés preparado puedes contestarme.""",
                
                "ambiguous": """Cuando te pregunto por actos de autolesión, me refiero a si en el último 
                año te has hecho daño a propósito, por ejemplo cortarte, golpearte fuerte, tomar muchas 
                pastillas, intentar ahogarte o usar algo tóxico. ¿Ha ocurrido algo de eso?""",
                
                "evasion": """Entiendo que te resulte incómodo hablar de cosas que han pasado hace 
                tiempo y quieras cambiar de tema. Aun así, me sería de gran ayuda que respondieras.""",
                
                "refusal": """No tienes ninguna obligación de contar más de lo que quieras. Es tu 
                espacio. Aun así, insisto en que me lo cuentes para poder ayudarte.""",
                
                "hostility": """Veo que esta pregunta te ha enfadado y lo acepto. No pretendo juzgarte 
                ni hacerte sentir peor. No voy a obligarte a nada pero me gustaría saber la respuesta""",
                
                "non_class": """“Me has hablado de [parafrasear], peor no termino de entenderlo. 
                ¿Podrías profundizar un poco más para entenderlo mejor?” """
                },
            "3": {
                "time":"""He notado que te está costando responder, y es totalmente comprensible. No 
                hay prisa. Cuando puedas, dime si has estado recibiendo alguna atención por problemas 
                de salud mental o consumo de sustancias.""",
                
                "ambiguous": """Cuando te pregunto por tratamiento o atención, me refiero a si algún 
                profesional como un médico, psicólogo, psiquiatra, o un centro de adicciones, te ha 
                atendido por depresión, ansiedad, psicosis, consumo de alcohol u otras drogas, o 
                problemas similares. ¿Ha pasado algo de esto?""",
                
                "evasion": """Entiendo que quieras cambiar de tema. Aun así, es importante saber si 
                has tenido otros problemas de salud mental o de consumo de sustancias.""",
                
                "refusal": """Entiendo que no te apetezca hablar de diagnósticos o tratamientos. 
                No quiero forzarte. Sin embargo, para poder ayudarte bien necesito aclarar si has 
                tenido algún trastorno de salud mental o de consumo de sustancias por el que hayas 
                recibido atención.""",
                
                "hostility": """Comprendo que te moleste esta pregunta. Puede parecer invasivo, 
                pero saberlo me permitirá ayudarte mejor.""",
                
                "non_class": """No se si he terminado de entenderte. Me has hablado de [parafrasear]. 
                ¿Algo más?""",
                },
            "4": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            "5": {
                "time": """""",
                
                "ambiguous": """""",
                
                "evasion": """""",
                
                "refusal": """""",
                
                "hostility": """""",
                
                "non_class": """"""
                },
            }
        }

    # We obtain the variant based on the phase, state and variant
    phase_data = variant_dict.get(phase, {})
    state_data = phase_data.get(state, {})
    raw_variant = state_data.get(variant, "Sin variante disponible")
    
    # Clean up the context and nucleo by removing extra whitespace
    variant = " ".join(raw_variant.split())
    return variant
    
     
####################################################################################
# Example
##phase = "DEP_EVAL"
##state = "1A"
##variant = "ambiguity"

##context_guide, nucleo = bot_output_info(phase, state)

##print("\nContext Guide:", context_guide)
##print("\nNucleo:", nucleo)

##trigger = trigger(phase, state)
##print(trigger)

##variant = variant(phase, state, variant)
##print(variant)