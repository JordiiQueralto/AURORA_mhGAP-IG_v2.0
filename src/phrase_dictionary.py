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
                "nucleo": """¿Qué expectativas tienes sobre esta conversación?"""
                },
            "commitment": {
                "nucleo": """Ahora voy a hacerte preguntas para poder entender mejor como te
                sientes para poder ayudarte. Para ello, necessito que te comprometas a responder
                sinceramente a mis preguntas. ¿Trato hecho?"""
            }
            },
        
        "DEP_EVAL": {
            "1A.1": {
                "nucleo": """Durante un periodo mínimo de dos semanas, ¿te has sentido triste, 
                vacío o sin ánimo la mayor parte del día, casi todos los días?"""
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
                una tarea porque cualquier ruido o pensamiento te desconcentra?"""
            },
            "2B.7": {
                "nucleo": """¿Tienes la sensación de que estás destinado a lograr algo grandioso 
                o que tus capacidades están muy por encima de las de tus conocidos o amigos?"""
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
                "nucleo": """¿Has notado que pasas mucho más tiempo solo de lo habitual o 
                que estas ignorando invitaciones o mensajes que antes sí respondías?"""
            },
            "2D.5": {
                "nucleo": """¿Te está costando más de lo normal levantarte para ir a trabajar 
                o estudiar?"""
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
            "3A": {
                "nucleo": """¿Tomas alcohol de forma habitual?"""
            },
            "3B": {
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
        },
        
        "FOLLOWUP": {
        "emergency_followup": {
            "nucleo": """¿Lograste contactar con el número que te proporcioné anteriormente o 
            has buscado algún tipo de ayuda?"""
        },
        "non_contact_reason": {
            "nucleo": """¿Tuviste alguna dificultad para comunicarte con ellos o simplemente 
            decidiste no hacerlo?"""
        },
        "second_try": {
            "nucleo": """De verdad te recomiendo llamar. ¿Qué crees que te está frenando para 
            dar el paso de hablar con ellos?"""
            },
        "post_help": {
            "nucleo": """Después de hablar con el servicio de ayuda, ¿te sientes un poco mejor?"""
        },
        "family": {
            "nucleo": """¿Hay alguien contigo en este momento o tienes a alguien a quien puedas 
            llamar para que te acompañe mientras te sientes mejor?"""
        },
        "continuity_plan": {
            "nucleo": """¿Te proporcionaron algún paso a seguir o cita de seguimiento? Es 
            muy importante seguir esas indicaciones."""
        }
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
                "repeat": """No te he entendido. ¿Puedes decir '... años'?"""
                },
            "commitment": {
                "repeat": """No te he entendido muy bien. ¿Puedes volver a responderme?"""
                },
            },
        
        "DEP_EVAL": {
            "1A.1": {
                "time": """Está bien tomarte tu tiempo. ¿Te gustaría compartir cómo te has 
                sentido últimamente?""",

                "ambiguity": """Cuando menciono 'sentirse sin ánimo', me refiero a una sensación 
                que persiste casi todo el tiempo, no solo en momentos puntuales. ¿Ha ocurrido esa 
                sensación de vacío o tristeza te ha acompañado la mayor parte del día?""",

                "evasion": """Entiendo que prefieras hablar de otras cosas, pero para entender 
                bien lo que te pasa, necesito saber si ese sentimiento de tristeza o vacío ha 
                estado presente de forma continua.""",

                "refusal": """Entiendo perfectamente que no quieras responder ahora. Estoy 
                aquí cuando estés listo.""",

                "hostility": """Lo siento si la pregunta te molesta. Mi intención es entenderte 
                mejor y apoyarte. Tómate tu tiempo.""",

                "non_classificable": """Perdona, no estoy seguro de haber entendido bien lo que 
                mencionaste. ¿Podrías aclararlo?"""
                },
            "1A.2": {
                "time": """¿Has notado si cosas que antes te hacían ilusión ahora te dan un poco 
                igual o te cuesta mucho ponerte con ellas?""",
                
                "ambiguity": """Me refiero a si has dejado de sentir esa satisfacción al hacer cosas que 
                normalmente te gustan. ¿Te sientes indiferente ante actividades que antes te apasionaban?""",
                
                "evasion": """Entiendo que haya otros temas en tu mente ahora mismo. Aun así, para poder entenderte, 
                ¿podrías decirme si has sentido ese desinterés por tus actividades habituales en las últimas semanas?""",
                
                "refusal": """Respeto que no quieras entrar en detalles. Solo trato de entender si has experimentado 
                una falta de ganas o disfrute generalizada.""",
                
                "hostility": """Siento si parezco insistente. Mi intención no es incomodarte, sino comprenderte. 
                ¿Crees que te ha pasado esto recientemente?”""",
                
                "non_classificable": """Perdona, no estoy seguro de haber entendido bien lo que mencionaste sobre 
                [parafrasear]. ¿Podrías aclarármelo?"""
                },
            "1B.1": {
                "time": """“¿Estás aquí? ¿Has notado algún cambio en tu sueño últimamente?""",
                
                "ambiguous": """Cuando te pregunto por tu sueño, me refiero a si has tenido dificultades 
                para dormir o, por el contrario, si has dormido más de lo habitual durante al menos dos 
                semanas. ¿Ha sido así?""",
                
                "evasion": """Entiendo que puede ser personal. Solo para aclarar, ¿has tenido cambios en 
                tu sueño durante más de dos semanas?""",
                
                "refusal": """Puedes contármelo, tranquilo. ¿Quieres responder o cambiamos de tema?""",
                
                "hostility": """“Lo siente, mi intención no era molestarte.""",
                
                "non_class": """Cuando me has contado [parafrasear] no me ha terminado de quedar claro. 
                ¿Podrías volver a explicarmelo?"""
                },
            "1B.2": {
                "time": """Si lo necesitas, te dejo más tiempo para pensarlo...""",
                
                "ambiguous": """Cuando hablo de apetito o peso, me refiero a si has comido mucho más 
                o menos de lo normal, o si has ganado o perdido peso sin motivo. ¿Ha pasado eso?""",
                
                "evasion": """Para ser más concreto, ¿has tenido cambios notables en cuánto comes o 
                en tu peso?""",
                
                "refusal": """Entiendo perfectamente. Podemos seguir cuando estés listo.""",
                
                "hostility": """Disculpa si te incomoda la pregunta. Solo quiero conocerte mejor.""",
                
                "non_class": """Cuando mencionaste [parafrasear], no me quedó claro si eso se relaciona 
                con cambios en apetito o peso. ¿Podrías explicármelo?” """
                },
            "1B.3": {
                "time": """¿Sientes que tu cuerpo se ha quedado sin energia o que cualquier tarea te 
                exige un esfuerzo enorme? Me refiero a ese tipo de agotamiento constante que dura al 
                menos dos semanas.""",
                
                "ambiguous": """A lo que me refiero es a si has sentido una falta de fuerzas real, de 
                esas que no se pasan solo con descansar un poco, y si eso te ha acompañado durante un 
                periodo de dos semanas. ¿Logras identificar un periodo así?""",
                
                "evasion": """Volviendo al tema, ¿has notado ese senación de fatiga o pesadez en el 
                cuerpo de forma persistente durante dos semanas?""",
                
                "refusal": """“Si quieres te puedo dejar más tiempo. Solo intento entender si en algún 
                momento ese cansancio se volvió tan pesado que sentiste una pérdida constante de energía.""",
                
                "hostility": """Siento si la pregunta es incómoda. Mi intención es solo entender si has 
                experimentado ese agotamiento profundo durante dos semanas, para saber cómo ayudarte mejor.""",
                
                "non_class": """Cuando me hablas sobre [parafrasear] no termino de entenderlo. 
                ¿Puedes volver a explicármelo?” """
                },
            "1B.4": {
                "time": """He notado que te has tomado un tiempo para responder; no hay prisa. ¿En estas últimas 
                dos semanas has sentido que tu mente o tu cuerpo funcionan a un ritmo distinto?" """,
                
                "ambiguous": """A lo que me refiero es a si has sentido que dudar de ti mismo o el no poder 
                concentrarte se ha vuelto algo constante, de esas sensaciones que no se van en un par de días, 
                sino que te han acompañado durante dos semanas. ¿Identificas algo así?""",
                
                "evasion": """Entiendo que prefieras hablar de otros temas, pero es importante saber si estas 
                sensaciones, como la indecisión, desorientación o falta de concentración, han estado ahí de 
                forma persistente.""",
                
                "refusal": """Te entiendo. Si prefieres podemos ir más despacio. Solo trato de saber si en algún 
                momento  esa falta de concentración se volvió tan seguida que sentiste que no podías pensar con 
                claridad durante dos semanas.""",
                
                "hostility": """Siento si estas preguntas parecen un poco repetitivas o molestas. Mi única 
                intención es comprender bien el alcance de tu malestar para saber cómo acompañarte mejor. 
                ¿Podemos intentarlo de nuevo?""",
                
                "non_class": """Cuando me hablas sobre [parafrasear] no termino de entenderlo. 
                ¿Puedes volver a explicármelo?"""
                },
            "1B.5": {
                "time": """A veces es difícil ponerlo en palabras... me refiero a si has tenido esa sensación de 
                no estar a la altura o de ser demasiado exigente contigo mismo/a""",
                
                "ambiguous": """A lo que me refiero es a si has notado una tendencia a pensar mal de ti mismo 
                o a ponerte demasiada responsabilidad encima.""",
                
                "evasion": """Sé que estas cosas no son fáciles de contar. Te lo pregunto porque, cuando uno está 
                así, a veces empieza a pensar que no hace nada bien o a cargarse con culpas que no le tocan. 
                ¿Te ha pasado algo parecido?""",
                
                "refusal": """A veces puede ser difícil hablar sobre estos temas. 
                ¿Estás segura que no quieres contármelo?""",
                
                "hostility": """Siento si la pregunta suena algo personal, no es mi intención incomodarte. 
                Solo intento entenderte mejor.""",
                
                "non_class": """Cuando me hablas de [parafrasear] no termino de entenderlo del todo. 
                ¿Podrías explicármelo otra vez?” """
                },
            "1B.6": {
                "time": """Entiendo que esta pregunta puede ser difícil de responder. Tómate el tiempo que 
                necesites, estoy aquí contigo. Cuándo estés listo estoy aquí para escucharte.""",
                
                "ambiguous": """Tal vez no me expresé bien. Me refiero a si, en las últimas semanas, has 
                tenido sentimientos persistentes de tristeza, cansancio extremo o falta de ganas de vivir.""",
                
                "evasion": """Entiendo perfectamente que quieras evitar hablar de esto o que te incomode. 
                Lo respeto totalmente. Mi única intención es acompañarte y cuidar de tu bienestar. 
                ¿Podrías contarme si has tenido alguno de esos sentimientos últimamente?""",
                
                "refusal": """No tienes ninguna obligación de responder si no quieres, lo respeto plenamente. 
                Pero me gustaría saberlo para poder ayudarte.""",
                
                "hostility": """Sé que puede parecer una pregunta inadecuada y entiendo tu enfado. 
                Pero lo único que busco es que estés bién""",
                
                "non_class": """Cuando me hablas de [parafrasear] no termino de entenderlo del todo. 
                ¿Podrías explicármelo otra vez?"""
                },
            "1C": {
                "time": """Entiendo que puede ser difícil de explicar. Solo quería saber si sientes que estos 
                sentimientos te están complicando cumplir con tus cosas del día a día, como el trabajo o tus 
                relaciones. ¿Te sientes así? """,
                
                "ambiguous": """Me refiero a si estos sentimientos te están dificultando trabajar, estudiar, 
                relacionarte o cuidarte como antes. ¿Te está pasando eso?""",
                
                "evasion": """Entiendo lo que mencionas, pero me ayudaría mucho saber si esto que estás viviendo 
                te impide llevar tu vida con normalidad o si sientes que te sobrepasa en tus tareas diarias.""",
                
                "refusal": """Solo quiero entender cómo te está afectando todo esto para ver de qué manera 
                puedo serte más útil.""",
                
                "hostility": """Siento si la pregunta no ha sido adecuada o te ha incomodado. Mi única intención 
                es entender si hay áreas de tu vida que se están volviendo más pesadas debido a cómo te sientes.""",
                
                "non_class": """Me dices que [parafrasear]. Con eso que me cuentas, ¿sientes que te resulta más 
                difícil de lo normal ocuparte de tus responsabilidades o de tu cuidado personal?"""
                },
            "2A.1": {
                "time": """¿Estás pensando? ¿Se te ocurre algún medicamento o suplemento que estés tomando?""",
                
                "ambiguous": """Entiendo que es complejo. Me refiero a si tomas algo para el dolor, para dormir, 
                o cualquier suplemento o medicamento. ¿Te suena algo de eso?""",
                
                "evasion": """Comprendo que prefieras hablar de otros temas pero está información podría ser 
                importante a valorar. ¿Se te ocurre alguno?""",
                
                "refusal": """Comprendo que prefieras no entrar en detalles médicos. Solo lo pregunto porque 
                podría ser importante a valorar. ¿Se te ocurre alguno?""",
                
                "hostility": """Entiendo que mi pregunta pueda parecer fuera de lugar o poco relevante, 
                lo respeto. Solo intento saber si hay algún factor físico que esté afectando tu bienestar.""",
                
                "non_class": """Mencionaste [parafrasear]. ¿Podrías volvérmelo a explicar?"""
                },
            "2A.2": {
                "time": """No hay prisa. Te preguntaba esto porque a veces el cuerpo influye mucho en cómo nos 
                sentimos emocionalmente. ¿Sabes si tu salud física está bien últimamente?""",
                
                "ambiguous": """A lo mejor no me he explicado bien. Me refiero a si tu médico ha mencionado 
                algún problema con la tiroides, con los niveles de hierro, o con tu nutrición general. 
                ¿Recuerdas algo de eso?""",
                
                "evasion": """Céntrate en la pregunta. ¿Recuerdas si en alguna revisión te dijeron algo sobre 
                anemia, tiroides o nutrición?""",
                
                "refusal": """Tienes derecho a no responder, pero si me lo cuentas podré ayudarte mejor. 
                ¿Puedes responderme porfavor?""",
                
                "hostility": """Entiendo que mi pregunta pueda parecer innecesaria, lo respeto totalmente. 
                Solo intento descartar si hay algo físico que esté influyendo en cómo te sientes. 
                ¿Podrías responderme?""",
                
                "non_class": """Cuándo has hablado sobre [parafrasear], no te he entendido bien. 
                ¿Podrías volvérmelo a explicar?"""
                },
            "2B.1": {
                "time": """Entiendo que estas preguntas pueden ser un poco raras o difíciles de recordar. 
                Tómate un momento y, cuando estés preparado, puedes responderme.""",
                
                "ambiguous": """Cuando te pregunto por un estado de ánimo anormalmente elevado o muy irritable, 
                me refiero a épocas en las que te sentías 'pasado de vueltas': con excesiva energia… 
                ¿Has tenido algo así?""",
                
                "evasion": """Entiendo que te resulte raro hablar de estas épocas de estar eufórico y 
                prefieras cambiar de tema.  Aun así, es importante saber si has tenido periodos así.""",
                
                "refusal": """No tienes obligación de contar nada que no quieras. Aun así, te pediría que, 
                si puedes, me digas con sinceridad si alguna vez has tenido una época en la que estabas 
                excesivamente animado, con mucha energía o muy irritable.""",
                
                "hostility": """Comprendo que esta pregunta pueda parecerte tonta o fuera de lugar. Pero es 
                importante ¿Crees que has tenido alguna etapa así?""",
                
                "non_class": """Me has hablado de [parafrasear]. ¿Podrías aclararlo un poco más?"""
                },
            "2B.2": {
                "time": """Entiendo que quizá es una pregunta un poco específica y cuesta encontrar las 
                palabras. No hay prisa. ¿Te ha pasado alguna vez eso de dormir poquísimo y aun así sentir 
                que tienes energía para todo el día?""",
                
                "ambiguous": """Para entenderte mejor: no me refiero a cuando quieres dormir y no puedes 
                (y acabas agotado). Hablo de esos momentos en los que duermes muy poco, pero te sientes con 
                las pilas cargadas, como si no te hiciera falta descansar. ¿Te suena de algo?""",
                
                "evasion": """Te escucho y entiendo que prefieras hablar de eso ahora. Solo te preguntaba lo 
                del sueño porque a veces los cambios en la energía nos dan pistas importantes sobre cómo estamos. 
                Si recuerdas haber tenido rachas así de estar muy activo sin apenas dormir, dímelo.""",
                
                "refusal": """No tienes por qué contarme nada que no quieras, respeto mucho tu espacio. Solo te 
                lo comentaba porque es algo que a veces pasa y es útil saberlo para entenderte mejor.""",
                
                "hostility": """Siento si la pregunta te ha incomodado, no era mi intención molestarte. Solo 
                trato de hacerme una idea clara de cómo te has sentido para ver cómo puedo apoyarte.""",
                
                "non_class": """Me dices que [parafrasear]. Podrías explicarme un poquito más cómo era 
                esa sensación?"""
                },
            "2B.3": {
                "time": """Entiendo que a veces es difícil ponerle palabras a estas sensaciones. No hay 
                ninguna prisa. ¿Has sentido en algún momento que tenías tanta energía que te costaba 
                incluso parar o quedarte quieto?""",
                
                "ambiguous": """A veces es fácil confundirlo con estar muy ocupado por el trabajo o las tareas. 
                Me refiero a una sensación de estar 'acelerado', como si tuvieras un motor interno que no 
                puedes apagar. ¿Te ha pasado algo parecido?""",
                
                "evasion": """Entiendo que prefieras hablar de otros temas ahora mismo. Te lo preguntaba porque 
                sentir ese exceso de energía a veces nos ayuda a entender mejor los cambios en el estado de ánimo. 
                Si en algún momento te sientes cómodo contándome, aquí estaré.""",
                
                "refusal": """No quiero que sientas que te estoy interrogando, respeto mucho lo que quieras 
                compartir. Solo intento comprender si has tenido esos momentos de mucha actividad para saber 
                cómo apoyarte mejor, pero vamos a tu ritmo.""",
                
                "hostility": """Siento si la pregunta te ha molestado o te parece fuera de lugar, no era mi 
                intención. Solo buscaba entender mejor tu situación. Podemos dejar este tema si prefieres y 
                centrarnos en lo que tú necesites.""",
                
                "non_class": """Te entiendo cuando dices que [parafrasear]. 
                Pero, ¿podrías profundizar un poco más?"""
                },
            "2B.4": {
                "time": """A veces cuesta reconocer estos momentos porque pueden ser confusos. No te preocupes, 
                tómate tu tiempo. ¿Recuerdas alguna vez haber actuado muy rápido, de forma que luego te 
                sorprendieras a ti mismo?""",
                
                "ambiguous": """Me refiero a situaciones que se salen de lo normal, como gastar dinero que 
                necesitabas para otra cosa o meterte en líos por no pararte a pensar un segundo. 
                ¿Te ha pasado algo así de forma recurrente?""",
                
                "evasion": """Te escucho. Entiendo que quizá prefieras no entrar en detalles sobre esto ahora. 
                Si en algún momento quieres comentarlo, aquí estoy.""",
                
                "refusal": """Está bien, no hace falta que me des detalles si no te sientes cómodo. Respeto 
                mucho tu espacio. Solo quería saber si habías notado ese tipo de impulsos para entender mejor 
                tu situación.""",
                
                "hostility": """Siento mucho si te has sentido juzgado con esta pregunta, no era mi intención. 
                Mi único objetivo es entender mejor tu situación.""",
                
                "non_class": """Me comentas que [parafrasear]. ¿Podrías profundizar un poco más?"""
                },
            "2B.5": {
                "time": """A veces es difícil admitir que nos hemos comportado de forma diferente a la habitual, 
                es normal que cueste responder. ¿Has notado que te haya pasado?""",
                
                "ambiguous": """Me refiero a si has estado mucho más lanzado o atrevido de lo normal o 
                comportarte con una confianza que no solías tener. ¿Te ha pasado algo así?""",
                
                "evasion": """Entiendo que prefieras pasar de largo esta pregunta, a veces recordar estos 
                momentos da un poco de reparo. Pero te pediría que me lo contaras.""",
                
                "refusal": """Respeto mucho que no quieras entrar en este tema ahora mismo. Pero no estoy 
                aquí para juzgarte, solo para entender cómo te sientes.""",
                
                "hostility": """Siento si la pregunta te ha parecido invasiva o fuera de lugar. No es mi 
                intención incomodarte, sino intentar comprender mejor tu situación.""",
                
                "non_class": """Me has hablado sobre [parafrasear]. ¿Podrías contarme más?"""
                },
            "2B.6": {
                "time": """Sé que a veces es difícil darse cuenta de estas cosas si no nos paramos a 
                pensarlo. No hay prisa. ¿Sientes que tu cabeza va tan rápido últimamente que te cuesta 
                centrarte en una sola cosa a la vez?""",
                
                "ambiguous": """Me refiero a si te distraes con mucha facilidad, incluso con cosas insignificantes 
                como un ruido fuera o una idea que se te cruza en la mente, haciendo que dejes a medias lo que 
                estabas haciendo. ¿Te ha pasado algo así?""",
                
                "evasion": """Entiendo que quizá este no sea el tema que más te preocupa ahora mismo. Solo te lo 
                preguntaba porque esa falta de concentración a veces es una señal importante. Si en algún momento 
                quieres comentarlo, aquí estaré.""",
                
                "refusal": """Está bien, no quiero que te sientas presionado a responder si no te apetece. 
                Solo intentaba ver si habías notado ese cambio en tu atención para entenderte mejor.""",
                
                "hostility": """Siento site he incomodado. Solo busco valorar tu situación de la forma más 
                completa posible para poder apoyarte.""",
                
                "non_class": """Me dices que [parafrasear], pero no me termina de quedar claro. 
                ¿Podrías profundizar un poco más?"""
                },
            "2B.7": {
                "time": """Entiendo que es una pregunta profunda y puede sonar un poco extraña. Solo trato de 
                saber si alguna vez has sentido una confianza en ti mismo mucho más fuerte de lo habitual.""",
                
                "ambiguous": """A veces todos nos sentimos seguros de nosotros mismos, pero me refiero a una 
                sensación fuera de lo común. ¿Has sentido en algún momento que tienes un poder, una inteligencia
                o una misión que nadie más entiende o posee?""",
                
                "evasion": """Respeto que prefieras no profundizar en esto ahora. Te lo preguntaba porque a 
                veces, cuando el ánimo sube mucho, nuestra percepción de lo que podemos lograr también cambia. 
                Si te apetece contarme si te has sentido así de especial, te escucho.""",
                
                "refusal": """No hace falta que me des detalles si te incomoda, de verdad. Solo quería saber 
                si habías notado ese sentimiento de superioridad o de destino especial.""",
                
                "hostility": """Siento si la pregunta te ha parecido arrogante o fuera de lugar. No es mi 
                intención juzgar tus metas ni tus capacidades. Solo intento entender si has tenido esos 
                momentos de extrema seguridad en ti mismo.""",
                
                "non_class": """Me has hablado sobre [parafrasear]. ¿Cuéntame más?"""
                },
            "2C": {
                "time": """Siento si la pregunta ha sido un poco brusca o difícil de responder. No tienes que 
                correr. Si ha habido alguna pérdida reciente en tu vida, dímelo cuando sientas que puedes hacerlo.""",
                
                "ambiguous": """A veces un evento así cambia mucho cómo nos sentimos por dentro. 
                ¿Te ha pasado algo así?""",
                
                "evasion": """Entiendo que es un tema muy personal y quizá prefieras no removerlo ahora. Te lo 
                preguntaba solo porque el duelo es un proceso muy intenso y me ayuda a entender mejor por lo que 
                estás pasando. ¿Te apetece comentar algo sobre esto?""",
                
                "refusal": """Respeto totalmente que prefieras no hablar de esto. Solo quería saber si había 
                ocurrido algo así para comprender mejor tu situación.""",
                
                "hostility": """Perdona si te ha parecido una pregunta demasiado directa o invasiva, 
                no era mi intención molestarte.""",
                
                "non_class": """Me has comentado que [parafrasear]. ¿Te apetece profundizar un poco más?"""
                },
            "2D.1": {
                "time": """Entiendo que esta es una pregunta muy fuerte y que puede costar responderla. 
                No pasa nada, tómate tu tiempo. Solo quiero saber si has tenido esos pensamientos en los 
                que todo parece perder el sentido.""",
                
                "ambiguous": """A veces uno no quiere hacerse daño, pero sí siente un cansancio muy grande de 
                todo. ¿Te has sentido así, como con ganas de 'desaparecer' o de que todo se detenga de una vez?""",
                
                "evasion": """A veces estos pensamientos son difíciles de compartir, aún así, saber si te sientes 
                así de desanimado es muy importante para mi. ¿Te ha pasado algo así últimamente?""",
                
                "refusal": """No tienes por qué responderme si no te sientes cómodo. Solo quería que supieras que 
                este es un espacio seguro para hablar de lo que sea, incluso de los sentimientos más oscuros.""",
                
                "hostility": """Siento si la pregunta te ha parecido muy directa o te ha molestado. Mi única 
                intención es entender qué tan pesado sientes todo ahora mismo para intentar ayudarte.""",
                
                "non_class": """¿Cuando hablas sobre [parafrasear], a que te refieres exactamente?"""
                },
            "2D.2": {
                "time": """A veces es difícil reconocer estos pensamientos. No te presiones. ¿Has sentido 
                últimamente que, por alguna razón, no deberías recibir el cariño o el apoyo de los demás?""",
                
                "ambiguous": """Me refiero a si sientes que 'no eres suficiente' o que eres una carga, y por 
                eso te cuesta aceptar que alguien se preocupe por ti o que te pasen cosas buenas. 
                ¿Te sientes identificado con eso?""",
                
                "evasion": """Te lo pregunto porque en ciertas situaciones podemos llegar a creer que no 
                valemos lo suficiente, y es importante saber si te está pasando. 
                ¿Has tenido esa sensación de no merecer nada bueno?""",
                
                "refusal": """Entiendo que no quieras profundizar en esto ahora. Solo quería saber si esa 
                sensación de 'no merecer' te está acompañando""",
                
                "hostility": """Siento si la pregunta te ha resultado molesta, no es mi intención juzgar 
                cómo te sientes. Si te apetece puedes compartirlo conmigo.""",
                
                "non_class": """No termino de comprender cuando hablas sobre [parafrasear]. 
                ¿Podrías profundizar un poco más?"""
                },
            "2D.3": {
                "time": """Entiendo que esta pregunta puede sonar extraña o incluso asustar un poco. 
                A algunas personas les pasa y no hay nada de que avergonzarse. ¿Te ha pasado?""",
                
                "ambiguous": """A veces, podemos tener sensaciones confusas, como sombras que pasan 
                rápido o ruidos que no sabemos de dónde vienen. ¿Has tenido alguna experiencia así?""",
                
                "evasion": """A veces da un poco de reparo hablar de estas sensaciones porque son 
                difíciles de explicar. Te lo preguntaba porque es algo que le ocurre a algunas personas. 
                ¿Recuerdas algo parecido?""",
                
                "refusal": """No quiero que te sientas presionado a contarme nada que te incomode. 
                Solo quería saber si estabas teniendo este tipo de sensaciones.""",
                
                "hostility": """Me disculpo si la pregunta ha podido incomodarte.  Solo intentaba 
                profundizar en como te sientes. Si cambais de opinión, te escucho.""",
                
                "non_class": """Me has hablado sobre [parafrasear]. ¿Podrías explicármelo un poquito más?"""
                },
            "2D.4": {
                "time": """A veces uno no se da cuenta de que se va alejando poco a poco de los demás. 
                No te preocupes por el silencio. ¿Sientes que últimamente has buscado refugiarte más en 
                la soledad de lo que solías hacer?""",
                
                "ambiguous": """No me refiero solo a estar solo por falta de planes, sino a esa sensación 
                de no tener ganas de ver a nadie o de preferir encerrarte aunque tengas gente cerca. 
                ¿Te has estado distanciando de tus amigos o familiares?""",
                
                "evasion": """Entiendo que es más cómodo hablar de otras cosas. Te preguntaba esto porque 
                cuando no estamos bien, solemos perder el contacto con los demás casi sin querer. 
                ¿Crees que te has estado aislando más estas últimas semanas?""",
                
                "refusal": """No quiero que sientas que te cuestiono. Solo me gustaría saber si notas 
                que te cuesta más que antes estar con gente.""",
                
                "hostility": """Lo siento, no pretendo controlar tu vida social, solo trato de 
                entender tu situación.""",
                
                "non_class": """Me comentas que [parafrasear]. Cuéntame un poco más…” """
                },
            "2D.5": {
                "time": """A veces, cuando uno está muy agotado, hasta pensar en la rutina cansa. 
                No hay prisa por responder. ¿Sientes que el cuerpo te pesa mucho más de lo habitual 
                al empezar el día?""",
                
                "ambiguous": """Más que a la pereza normal, me refiero a esa sensación de que no le 
                encuentras el sentido a levantarte o de que te falta la fuerza física para hacerlo. 
                ¿Te está pasando esto?""",
                
                "evasion": """Entiendo que hablar de responsabilidades puede ser agobiante ahora mismo. 
                Te lo pregunto porque ese bloqueo para empezar el día nos da mucha información. 
                ¿Lo has notado?""",
                
                "refusal": """No quiero que sientas que te estoy juzgando. Solo intento entender si 
                ese cansancio te está dificultando seguir con tus actividades normales.""",
                
                "hostility": """Lamento si la pregunta te ha sonado a presión o exigencia, no era mi 
                intención. Solo intento entender si te sientes con fuerzas para el día a día o no.""",
                
                "non_class": """Has comentado [parafrasear]. 
                Continua explicándome esto un poco más por favor."""
                },
            "2E.1": {
                "time": """Sé que echar la vista atrás y recordar consultas médicas a veces cuesta 
                un poco. No hay prisa. ¿Recuerdas si en el pasado algún profesional te hablo sobre 
                algo parecido?""",
                
                "ambiguous": """Me refiero a si alguna vez llegaste a ir a una consulta y te dieron un 
                diagnóstico oficial. A veces uno se siente muy mal pero no llega a ver a un profesional.
                En tu caso, ¿llegaron a visitarte y darte un diagnóstico?""",
                
                "evasion": """Entiendo que las etiquetas médicas a veces son incómodas y preferimos no 
                pensar en el pasado. Te lo preguntaba solo por saber si ya has recibido ayuda antes. 
                ¿Te suena haber tenido algún diagnóstico formal?""",
                
                "refusal": """No tienes por qué compartir tu historial médico si no te sientes cómodo, 
                respeto tu privacidad. Solo quería ver si esto es algo que ya te había pasado antes 
                para entenderte mejor.""",
                
                "hostility": """Siento si la pregunta te ha resultado molesta. Mi única intención es 
                saber si ya tienes experiencia lidiando con esto de forma profesional para poder 
                apoyarte mejor.""",
                
                "non_class": """Me comentas que [parafrasear]. Continua explicándome…"""
                },
            "2E.2": {
                "time": """Tómate tu tiempo…¿Te suena haber tenido que recurrir a alguna pastilla o 
                gotas para ayudarte con el ánimo o el descanso?""",
                
                "ambiguous": """Me refiero a cualquier apoyo médico que hayas recibido para sentirte 
                más tranquilo o para levantar el ánimo. No importa si fue por poco tiempo, ¿llegaste 
                a tomar algo recetado para los nervios o para dormir?""",
                
                "evasion": """Entiendo que hablar de medicación puede ser un tema personal. Te lo 
                pregunto porque saber qué te ha ayudado en el pasado podría ser de utilidad ahora. 
                ¿Recuerdas haber tomado algo así?""",
                
                "refusal": """Respeto totalmente si prefieres no entrar en detalles sobre tratamientos 
                anteriores. Solo quería saber si ya habías tenido esa ayuda médica antes.""",
                
                "hostility": """Siento si la pregunta te ha parecido demasiado directa o incómoda. 
                Solo trato de entender mejor tu pasado para serte de más ayuda.""",
                
                "non_class": """He entendido que [parafrasear]. ¿Podrías explicarme más detalles?"""
                },
            "2E.3": {
                "time": """Tómate un respiro si lo necesitas y, cuando estés listo/a, puedes responderme.""",
                
                "ambiguous": """Me refiero a si en algún momento llegaste a quedarte a dormir en un 
                hospital o clínica especializada porque tu ánimo estaba muy mal. ¿Te ha pasado algo así?""",
                
                "evasion": """Entiendo que es un tema muy íntimo y a veces preferimos no removerlo. Te lo 
                pregunto solo para entender si has pasado por episodios en el pasado y cómo saliste adelante. 
                ¿Llegaste a estar ingresado?""",
                
                "refusal": """Respeto totalmente si prefieres no hablar de tu pasado ahora mismo. 
                Solo quería saber si habías necesitado ese nivel de apoyo en el pasado.""",
                
                "hostility": """Lamento si la pregunta te ha parecido invasiva o te ha molestado. Mi única 
                intención es comprender la gravedad de lo que has vivido para acompañarte mejor hoy.""",
                
                "non_class": """Me comentas que [parafraseo], pero no me ha terminado de quedar claro. 
                ¿Puedes profundizar un poquito más?"""
                },
            "3A": {
                "time": """Tómate tu tiempo para pensar. Solo quiero saber si el consumo de alcohol es 
                algo frecuente en tu día a día.""",
                
                "ambiguous": """Más allá de si es mucho o poco, me interesa saber si el alcohol forma 
                parte de tu rutina, especialmente cuando te sientes mal. ¿Bebes con cierta frecuencia?""",
                
                "evasion": """Entiendo que es algo muy común y social, pero te lo pregunto porque a veces 
                el alcohol puede afectar mucho al ánimo o al sueño sin que nos demos cuenta. 
                ¿Sueles beber con frecuencia?""",
                
                "refusal": """Entiendo que no quieras entrar en este tema si te resulta incómodo. 
                Pero puedes contármelo, no te voy a juzgar.""",
                
                "hostility": """Siento si la pregunta te ha parecido fuera de lugar. No es un 
                interrogatorio, solo intento comprender tu situación sin juzgarte.""",
                
                "non_class": """No te he entendido bien. ¿Puedes volver a explicármelo?"""
                },
            "3B": {
                "time": """Tómate tu tiempo... Solo trato de saber si consumes alguna otra sustancia 
                que pueda estar influyendo en cómo te sientes.""",
                
                "ambiguous": """Me refiero a si utilizas alguna sustancia de forma recreativa o para 
                intentar aliviar el malestar, como fumar porros o usar algo más fuerte. 
                ¿Es algo que esté presente en tu vida?""",
                
                "evasion": """Sé que puede ser difícil hablar de esto. Te lo pregunto porque muchas 
                sustancias pueden imitar o empeorar los síntomas de la depresión. 
                ¿Ha habido algún consumo últimamente?""",
                
                "refusal": """Respeto si prefieres no tocar este tema. Sin embargo, me sería de 
                gran utilidad para comprender mejor tu situación, Si cambias de idea, te escucho.""",
                
                "hostility": """Lamento si la pregunta te ha molestado. Solo intento entender 
                tu situación para ayudarte mejor.""",
                
                "non_class": """Me has hablado sobre [parafrasear]. ¿Puedes explicarme un poco más?"""
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
                "time": """Entiendo que hablar de dolores físicos puede parecer secundario, pero para 
                mí es importante. Tómate un momento y, cuando estés preparado, puedes contarme si 
                tienes algún dolor que no mejora.""",
                
                "ambiguous": """Quiero ser más concreto: me refiero a un dolor constante que interfiere 
                con lo que haces a diario, aunque tomes medicación o intentes cuidarte. 
                ¿Tienes ese tipo de dolor?""",
                
                "evasion": """“Entiendo que quizá no parezca importante, pero el dolor físico puede 
                influir mucho en el estado emocional.""",
                
                "refusal": """Por favor, reconsidéralo. No quiero presionarte, pero saber si tienes 
                un dolor físico persistente que afecta a tu día a día es importante para entender 
                mejor cómo te encuentras y cómo puedo ayudarte""",
                
                "hostility": """Siento si mi pregunta te ha molestado, no era mi intención incomodarte. 
                Solo intento comprender todos los factores que podrían estar afectando tu bienestar para 
                ayudarte mejor. Si cambias de opinión te escucho""",
                
                "non_class": """No me ha quedado claro si tienes algún dolor persistente. 
                ¿Podrías explicármelo un poco más?"""
                },
            "5": {
                "time": """Entiendo que puede no ser una pregunta fácil. Te dejaré más tiempo para que lo pienses…""",
                
                "ambiguous": """Cuando digo 'afectar tu día a día', me refiero a si sientes que tus emociones son como 
                un obstáculo que te impide concentrarte, salir de casa o disfrutar de lo que antes te gustaba. 
                ¿Te ocurre algo así?""",
                
                "evasion": """Parece que quieres cambiar de tema. Pero para poder orientarte mejor, necesito saber 
                si sientes que estas emociones te están ganando la batalla en tu rutina diaria.""",
                
                "refusal": """Respeto que prefieras no profundizar en tus emociones ahora mismo. Pero esta información 
                me sería útil para entender mejor tu situación. Estoy aquí por si cambias de opinión.""",
                
                "hostility": """Lamento si suena como un interrogatorio. Mi única intención es ayudarte, pero para 
                hacerlo necesito que me respondas.""",
                
                "non_class": """No he terminado de entender a qué te refieres con [parafrasear]. ¿Podrías aclarármelo 
                un poco más?"""
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