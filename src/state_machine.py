import db
import re
import unicodedata
import time

def _strip_accents(user_input: str) -> str:
    """Removes diacritics (accents) from a string using Unicode NFD decomposition."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', user_input)
        if unicodedata.category(c) != 'Mn'
    )


def _normalize_text(user_input: str) -> str:
    """Lowercases, strips accents, removes quotes and punctuation, and collapses whitespace."""
    user_input = user_input.lower().strip()
    user_input = _strip_accents(user_input)
    user_input = re.sub(r'[“”"\'`´]', '', user_input)
    user_input = re.sub(r'[\(\)\[\]\{\},;:¡!¿?\.\-_/]+', ' ', user_input)
    n_user_input = " ".join(user_input.split())
    return n_user_input

  
def _pattern_search(user_input: str, patterns: list[str]) -> list[str]:
    """Returns a list of patterns that match anywhere in user_input (case-insensitive)."""
    match = []
    for pattern in patterns:
        if re.search(pattern, user_input, flags=re.IGNORECASE):
            match.append(pattern)
    return match


def _variant_search(n_user_input: str) -> str:
    """Classifies normalized user input into a behavioral variant: 'ambiguity', 'evasion', 'refusal', 'hostility', or 'non_class'."""
    PATTERNS_AMBIGUITY: list[str] = [
        r"\bno se\b",
        r"\bno estoy segur[ao]\b",
        r"\bno tengo claro\b",
        r"\bno recuerdo\b",
        r"\bdepende\b",
        r"\bquizas\b",
        r"\btal vez\b",
        r"\bpodria ser\b",
        r"\bno lo se (exactamente)?\b",
        r"\bno entiendo\b",
        r"\bque quieres decir\b",
        r"\bexplica (mejor|mas)\b",
        r"\brepite( porfa| por favor)?\b",
        r"\baclarame\b",
        r"\bno capte\b",
    ]

    PATTERNS_EVASION: list[str] = [
        r"\bcambi[ao] de tema\b",
        r"\bcanvi[ao] de tema\b",
        r"\botro tema\b",
        r"\bhabla de otra cosa\b",
        r"\bhablemos de otra cosa\b",
        r"\bcuentame un chiste\b",
        r"\bque tiempo hace\b",
        r"\bdime la hora\b",
        r"\bque tal tu\b",
        r"\bpasemos pagina\b",
        r"\bolvida(lo|te)?\b",
        r"\bno es nada\b",
        r"\bno es grave\b",
        r"\bson tonteria(s)?\b",
        r"\bexageras\b",
        r"\bno pasa nada\b",
        r"\bno vale la pena\b",
        r"\bpoca cosa\b",
        r"\bes poco\b",
    ]

    PATTERNS_DIRECT_REFUSAL: list[str] = [
        r"\bno quiero hablar de (eso|esto)\b",
        r"\bprefiero no contestar\b",
        r"\bno voy a responder\b",
        r"\beso no te importa\b",
        r"\bno es asunto tuyo\b",
        r"\bcallate\b",
        r"\bdejame en paz\b",
        r"\bno insistas\b",
        r"\bpasa de eso\b",
        r"\bno me apetece\b",
    ]

    PATTERNS_HOSTILITY: list[str] = [
        r"\beres inutil\b",
        r"\brobot inutil\b",
        r"\brobot de\b"
        r"\bque pregunta tonta\b",
        r"\bno me jodas\b",
        r"\besto es ridiculo\b",
        r"\bpara de preguntar\b",
        r"\bno me fio de ti\b",
        r"\bpregunta estupida\b",
        r"\bque tonteria\b",
        r"\bno confio en ti\b",
    ]
    
    # 1 - Ambiguity
    match_ambiguity = _pattern_search(n_user_input, PATTERNS_AMBIGUITY)
    if match_ambiguity:
        variant = "ambiguity"
        
        return variant
    
    else:
        # 2 - Evasion
        match_evasion = _pattern_search(n_user_input, PATTERNS_EVASION)
        if match_evasion:
            variant = "evasion"
            
            return variant
        
        else:
            # 3 - Direct refusal
            match_refusal = _pattern_search(n_user_input, PATTERNS_DIRECT_REFUSAL)
            if match_refusal:
                variant = "refusal"
                
                return variant
            
            else:
                # 4 - Hostility
                match_hostility = _pattern_search(n_user_input, PATTERNS_HOSTILITY)
                if match_hostility:
                    variant = "hostility"
                    
                    return variant
                
                else:
                    # Non classificable
                    variant = "non_class"
                        
                    return variant
    

def StateMachine(telephone, phase, state, user_input):
    """Applies regex pattern banks to user input to advance the clinical conversation state. Returns (new_phase, new_state, variant)."""
    n_user_input = _normalize_text(user_input)
    variant = 0
    
    if phase == "PROFILE":
        if state == "name":
            name_match = re.search(
                r'(?:me llamo|soy|mi nombre es)\s+'
                r'([a-záéíóúñ]+(?:\s+(?:de|del|la|las|los|y|e)?\s*[a-záéíóúñ]+){0,2})',
                user_input,
                re.IGNORECASE
            )
            if name_match:
                raw_name = name_match.group(1).strip().lower()

                connectors = {"de", "del", "la", "las", "los", "y", "e"}

                words = raw_name.split()
                formatted_name = " ".join(
                    p if p in connectors else p.capitalize()
                    for p in words
                )

                key = "name"
                value = formatted_name
                db.add_user_info(telephone, key, value)
                
                phase, state = "PROFILE", "age"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                variant = "repeat"
                phase, state = "PROFILE", "name"
                return (phase, state, variant)

        elif state == "age":
            age_match = re.search(r'\b(\d{1,3})\s*años\b', user_input, re.IGNORECASE)
            if age_match:
                key = "age (years)"
                value = int(age_match.group(1))
                if 18 <= value < 120:  # Range of validation
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "PROFILE", "reason"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                elif value < 18:
                    
                    phase, state = "FAREWELL", "age"
                    return (phase, state, variant)
                
                else:
                    
                    phase, state = "PROFILE", "age"
                    return (phase, state, variant)
                
            else:
                variant = "repeat"
                phase, state = "PROFILE", "age"
                return (phase, state, variant)
            
        elif state == "reason":
            key = "PROFILE.call_reason"
            value = user_input
            db.add_user_info(telephone, key, value)
            
            phase, state = "PROFILE", "expectation"
            db.save_flow(telephone, phase, state)
            return (phase, state, variant)
        
        elif state == "expectation":
            key = "PROFILE.expectation"
            value = user_input
            db.add_user_info(telephone, key, value)
            
            phase, state = "PROFILE", "commitment"
            db.save_flow(telephone, phase, state)
            return (phase, state, variant)
        
        elif state == "commitment":
            # Regex patterns definition
            PATTERNS_YES = [
                r'\b(s[ií]|si+)\b',
                r'\b(claro|claro que s[ií])\b',
                r'\b(por supuesto)\b',
                r'\b(desde luego)\b',
                r'\b(vale|venga|va)\b',
                r'\b(ok|okay|okey)\b',
                r'\b(de acuerdo)\b',
                r'\b(trato hecho)\b',
                r'\b(perfecto|genial|estupendo|fenomenal)\b',
                r'\b(adelante|dale)\b',
                r'\b(me comprometo)\b',
                r'\b(obvio|obviam\w*)\b',
                r'\b(afirmativo)\b',
            ]
            
            PATTERNS_NO = [
                r'\b(nel|nop+e?|nah)\b',
                r'\b(para nada)\b',
                r'\b(en absoluto)\b',
                r'\b(ni hablar)\b',
                r'\b(negativo)\b',
                r'\b(no (quiero|me apetece|puedo))\b',
                r'\b(prefiero no)\b',
                r'\b(no\s+gracias)\b',
                r'\b(imposible)\b',
                r'\b(jamas)\b',
                r'\b(nunca)\b',
            ]
            
            PATTERNS_AMBIGUOUS = [
                # Incertidumbre
                r'\bno(?:\s+lo)?\s+se\b',                    
                r'\b(no\s+estoy\s+segur[oa])\b',             # no estoy seguro/a
                r'\b(tal vez|talvez)\b',                     # tal vez
                r'\b(quizas?)\b',                            # quizá, quizás, quiza
                r'\b(a lo mejor)\b',                         # a lo mejor
                r'\b(depende)\b',                            # depende
                r'\b(puede\s+(ser|que))\b',                  # puede ser, puede que
                r'\b(no\s+tengo\s+(claro|ni idea))\b',       # no tengo claro / ni idea

                # Aplazamiento / evasión
                r'\b(vamos\s+viendo)\b',                     # vamos viendo
                r'\b(ya\s+vere?mos)\b',                      # ya veremos, ya veré
                r'\b(lo\s+pienso)\b',                        # lo pienso
                r'\b(dejame\s+pensar)\b',                    # déjame pensar
                r'\b(ahora\s+mismo\s+no)\b',                 # ahora mismo no
                r'\b(mas\s+adelante)\b',                     # más adelante
                r'\b(en\s+otro\s+momento)\b',                # en otro momento
                r'\b(luego\s+te\s+digo)\b',                  # luego te digo
                r'\b(ya\s+te\s+(digo|dire))\b',              # ya te digo / diré

                # Condición / negociación
                r'\b(depende\s+de)\b',                       # depende de
                r'\b(segun)\b',                              # según
                r'\b(si\s+(me|puedo|puedes))\b',             # si me..., si puedo...
                r'\b(con\s+una\s+condicion)\b',              # con una condición

                # Respuestas vagas
                r'\b(bueno+)\b',                             # bueno, bueeno
                r'\b(eeh+|mmm+|hmm+|eh+)\b',                 # vacilaciones
                r'\b(supongo)\b',                            # supongo
                r'\b(imagino)\b',                            # imagino
                r'\b(espero\s+que\s+si)\b',                  # espero que sí
            ]
                     
            # 1 - Reject
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "PROFILE.commitment"
                value = "Non commited"
                db.add_user_info(telephone, key, value)
                
                phase, state = "USE_CASE_EVAL", ""
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
                
            else:
                # 2 - Accept
                match_yes = _pattern_search(n_user_input, PATTERNS_YES)
                if match_yes:
                    key = "PROFILE.commitment"
                    value = "Fully commited"
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "USE_CASE_EVAL", ""
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                    
                else:
                    # 3 - Ambiguous
                    match_ambiguous = _pattern_search(n_user_input, PATTERNS_AMBIGUOUS) 
                    if match_ambiguous:
                        key = "PROFILE.commitment"
                        value = "Partially commited"
                        db.add_user_info(telephone, key, value)
                        
                        phase, state = "USE_CASE_EVAL", ""
                        db.save_flow(telephone, phase, state)
                        return (phase, state, variant)
                        
                    else:
                        variant = "repeat"
                        phase, state = "PROFILE", "commitement"
                        return (phase, state, variant) 
    
    
    elif phase == "CHAT":
        return (phase, state, variant)                    
    
                            
    elif phase == "DEP_EVAL":
        if state == "1A.1":
            
            PATTERNS_YES = [

                # Afirmaciones directas
                r"\bsi[,\s]+he\s+notado\b",
                r"\bclaro\b",
                r"\bexacto\b",
                r"\bpor\s+supuesto\b",
                r"\bdefinitivamente\b",
                r"\bcierto\b",

                # Estado de ánimo bajo / triste / vacío
                r"\btriste\b",
                r"\bme\s+siento\s+triste\b",
                r"\bmuy\s+triste\b",
                r"\btriste\s+todo\s+el\s+tiempo\b",
                r"\bestado\s+de\s+ánimo\s+bajo\b",
                r"\bbajo\s+de\s+ánimo\b",
                r"\bvacio\b",
                r"\bme\s+siento\s+vacio\b",
                r"\bsiento\s+un\s+vacío\b",
                r"\bdeprimid[oa]\b",
                r"\bdepresion\b",
                r"\bme\s+siento\s+deprimid[oa]\b",
                r"\bpersistentemente\s+triste\b",
                r"\bno\s+estoy\s+content[oa]\b",
                r"\bno\s+estoy\s+feliz\b",

                # COMBINACIONES NATURALES
                r"\bsi?\s*(?:llevo\s+asi|me\s+pasa)\s+(?:desde\s+hace|mucho)\b",
                r"\bsi?\s*(?:la\s+verdad\s+es\s+que\s+)?(?:estoy\s+fatal|me\s+siento\s+vacio)\b",
            ]
            
            PATTERNS_NO = [

                # Negaciones directas
                r"\bno\b",
                r"\bno\s+he\s+notado\b",
                r"\bnunca\b",
                r"\bjamas\b",
                r"\bnada\s+de\s+eso\b",
                r"\bpara\s+nada\b",
                r"\ben\s+absoluto\b",
                r"\bde\s+ninguna\s+manera\b",

                # Ausencia de síntomas de ánimo bajo
                r"\bno\s+estoy\s+triste\b",
                r"\bno\s+me\s+siento\s+vacio\b",
                r"\bno\s+estoy\s+deprimid[oa]\b",
                r"\bno\s+tengo\s+depresion\b",
                r"\bmi\s+animo\s+está\s+bien\b",
                r"\bestado\s+de\s+animo\s+normal\b",
            ]
                        
            # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1_A1_depressed_mood"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "1A.2"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Confirmation
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1_A1_depressed_mood"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "1A.2"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1A.1"
                    return (phase, state, variant)
            
        elif state == "1A.2":
            
            PATTERNS_YES: list[str] = [
                # PÉRDIDA DE INTERÉS / MOTIVACIÓN
                r"\b(?:he\s+perdido\s+el\s+)?(?:interes|gusto|placer|ganas|ilusion)\b",
                r"\b(?:ya\s+)?no\s+(?:me\s+apetece|me\s+motiva|me\s+ilusiona|me\s+llama)\s+(?:nada|hacer\s+cosas)\b",
                r"\bnada\s+me\s+(?:hace\s+gracia|llena|anima|divierte)\b",
                r"\bme\s+da\s+(?:todo\s+)?igual\s+(?:todo|lo\s+que\s+hago|salir)\b",
                r"\bestoy\s+(?:muy\s+)?(?:apatico|desmotivado|sin\s+ganas)\b",

                # COMPARACIÓN "ANTES VS AHORA"
                r"\bantes\s+(?:me\s+gustaba|disfrutaba|hacia)\s+(?:mucho|mas)\s+y\s+ahora\s+(?:no|nada|ni\s+frio\s+ni\s+calor)\b",
                r"\bya\s+no\s+(?:disfruto|hago)\s+(?:con\s+)?(?:mis\s+hobbies|lo\s+que\s+me\s+gustaba)\b",
                r"\bhe\s+dejado\s+(?:de\s+lado\s+)?(?:mis\s+aficiones|mis\s+hobbies|de\s+salir|el\s+gimnasio)\b",

                # IMPACTO EN RELACIONES Y TRABAJO
                r"\bno\s+quiero\s+(?:ver\s+a|quedar\s+con)\s+nadie\b",
                r"\bel\s+trabajo\s+me\s+(?:da\s+asco|es\s+una\s+carga|no\s+me\s+interesa)\b",
                r"\bhe\s+perdido\s+la\s+conexion\s+con\s+(?:mi\s+pareja|mis\s+amigos)\b",
                
                # RESPUESTAS AFIRMATIVAS DIRECTAS
                r"^(si|totalmente|asi\s+es|exacto|la\s+verdad\s+es\s+que\s+si|bastante)$",
                r"\bsi[,.]?\s*(?:no\s+tengo\s+ganas\s+de\s+nada|me\s+pasa\s+eso)\b"
            ]
            
            PATTERNS_NO: list[str] = [
                # MANTIENE EL DISFRUTE
                r"\b(?:aun|todavia|si)\s+(?:disfruto|me\s+gusta|me\s+divierto)\b",
                r"\b(?:mis\s+hobbies|mis\s+amigos|mi\s+familia)\s+(?:me\s+ayudan|me\s+hacen\s+bien|me\s+distraen)\b",
                r"\bsigo\s+(?:haciendo|teniendo\s+ganas\s+de)\s+(?:mis\s+cosas|de\s+todo|hobbies)\b",
                r"\bno\s+he\s+dejado\s+de\s+(?:hacer|disfrutar)\s+nada\b",
                
                # NEGACIÓN DE LA PÉRDIDA
                r"\bno\s+he\s+perdido\s+(?:el\s+interes|la\s+ilusion|las\s+ganas)\b",
                r"\bme\s+sigo\s+sintiendo\s+(?:motivado|con\s+ganas)\b",
                r"\bme\s+gusta\s+hacer\s+las\s+mismas\s+cosas\s+(?:de\s+siempre|que\s+antes)\b",

                # ACLARACIONES
                r"\ba\s+veces\s+me\s+cuesta\s+pero\s+luego\s+disfruto\b",
                r"\bestoy\s+cansado\s+pero\s+no\s+he\s+perdido\s+el\s+interes\b",
                
                # RESPUESTAS NEGATIVAS DIRECTAS
                r"^(no|para\s+nada|que\s+va|en\s+absoluto|aun\s+disfruto)$",
                r"\bno\b"
            ]
                        
             # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1_A2_anhedonia"
                value = False
                db.add_user_info(telephone, key, value)
                
                previous = db.get_user_info(telephone, "DEP_EVAL", "1A.1")
                
                if previous:
                    phase, state = "DEP_EVAL", "1B.1"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    phase, state = "CHAT", ""   # seria OTR
                    key = "SCREENING.DEP"
                    value = "others"
                    db.add_user_info(telephone, key, value)
                    return (phase, state, variant)
            
            else:
                # 2 - Confirmation
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1_A2_anhedonia"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "1B.1"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1A.2"
                    return (phase, state, variant)
            
        elif state == "1B.1":
            
            PATTERNS_YES: list[str] = [
                # DIFICULTAD PARA DORMIR (INSOMNIO)
                r"\b(duermo|he dormido|estoy durmiendo) (mal|fatal|muy poco|peor|menos)\b",
                r"\b(me cuesta|tengo problemas para|no consigo) (mucho )?dormir\b",
                r"\bno (puedo|consigo|soy capaz de) (dormir|conciliar el sueno|pegar ojo)\b",
                r"\b(tengo|sufro de) (insomnio|mucho insomnio)\b",
                r"\bme despierto (mucho|varias veces|constantemente|por la noche)\b",
                r"\b(tengo|mi) sueno (es |es muy )?(ligero|inquieto|malo)\b",
                r"\bno (descanso|he descansado) (bien|nada|lo suficiente)\b",
                r"\bpaso las noches (en vela|despierto|sin dormir)\b",

                # DORMIR DEMASIADO (HIPERSOMNIA)
                r"\b(duermo|paso el dia) (demasiado|mucho|mas de lo normal|todo el dia|muchas horas)\b",
                r"\bme paso (el dia|las horas) durmiendo\b",
                r"\bno (puedo|tengo fuerzas para) (despertarme|levantarme|salir de la cama) por el sueno\b",
                r"\btengo (muchisimo|mucho) sueno (todo el dia|a todas horas)\b",

                # RESPUESTA AFIRMATIVA GENERAL / PERSISTENCIA
                r"\bsi[,.]?\s*(me pasa|he notado cambios|es verdad|me ocurre eso|asi es|correcto|exacto)\b",
                r"\bllevo (asi|con estos cambios) (al menos |mas de )?(dos semanas|quince dias|un tiempo)\b",
                r"^(si|correcto|exacto|asi es|efectivamente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(he notado nada|nada de eso|en absoluto|para nada|nunca|no me pasa)\b",
                r"\bno (tengo|he tenido) (cambios|problemas) (con el sueno|al dormir)\b",
                r"\bno[,.]?\s*(todo esta igual|sin cambios|no es mi caso)\b",

                # SUEÑO NORMAL / ESTABLE
                r"\b(duermo|descanso) (bien|normal|perfectamente|como siempre)\b",
                r"\bno (tengo problemas|me cuesta) (para |al )?dormir\b",
                r"\bestoy (bien|tranquilo) con el sueno\b",
                r"\b(sigo|mantengo) (mis habitos|mi rutina) de sueno\b",
                r"\b(todo igual|sin novedad) (en ese sentido|con el dormir)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|que va|ninguno|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Sueño sin alteraciones relevantes)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1B_1_sleep_alteration"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "1B.2"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Alteración detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1B_1_sleep_alteration"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "1B.2"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase = "DEP_EVAL"
                    state = "1B.1"
                    return (phase, state, variant)

        elif state == "1B.2":
            
            PATTERNS_YES: list[str] = [
                # AUMENTO DE APETITO / ANSIEDAD
                r"\b(como|comiendo) (mucho |mas |demasiado|peor|sin parar|compulsivamente)\b",
                r"\b(tengo|me ha entrado) (mucha |mas )?(hambre|ansiedad por comer)\b",
                r"\bno (paro|puedo parar) de comer\b",
                r"\bme (como|he comido) todo\b",
                r"\baumento de (apetito|hambre)\b",

                # DISMINUCIÓN DE APETITO
                r"\bno (tengo|tengo ganas de) (hambre|comer|apetito)\b",
                r"\b(he perdido|perdi|sin) (el )?apetito\b",
                r"\bno (me apetece|como) (nada|apetece|casi nada)\b",
                r"\bhe dejado de comer\b",
                r"\bcomo (muy poco|menos|poquisimo)\b",

                # CAMBIOS DE PESO (PÉRDIDA)
                r"\bhe (perdido|bajado) (mucho |bastante )?peso\b",
                r"\b(sin querer |estoy )?(mas delgado|adelgazado|he bajado de peso)\b",
                r"\bla ropa me (queda grande|baila)\b",

                # CAMBIOS DE PESO (AUMENTO)
                r"\bhe (ganado|subido|aumentado) (mucho |bastante )?peso\b",
                r"\b(he |estoy )?(engordado|mas gordo|subido de peso)\b",
                r"\bsubi de peso (rapido|mucho)\b",

                # RESPUESTA AFIRMATIVA GENERAL
                r"\bsi[,.]?\s*(me pasa|he notado cambios|es verdad|me ocurre eso|asi es|he cambiado)\b",
                r"^(si|correcto|exacto|asi es|bastante|mucho)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(he notado nada|nada de eso|en absoluto|para nada|nunca|no me pasa)\b",
                r"\bno (tengo|he tenido) (cambios|problemas) (con el peso|con la comida|con el apetito)\b",
                r"\bno[,.]?\s*(todo esta igual|sin cambios|no es mi caso|nada ha cambiado)\b",

                # APETITO Y PESO NORMAL / ESTABLE
                r"\b(como|peso) (bien|normal|perfectamente|como siempre|lo mismo)\b",
                r"\b(apetito|peso) (normal|estable|bien)\b",
                r"\bno (he subido ni bajado|he cambiado de peso)\b",
                r"\b(sigo|estoy) igual (de peso|con la comida)\b",
                r"\b(todo igual|sin novedad) (en ese sentido|con el apetito)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|que va|ninguno|todo normal)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Apetito/Peso estable)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1B_2_appetite_weight_change"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "1B.3"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Cambio detectado)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1B_2_appetite_weight_change"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "1B.3"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1B.2"
                    return (phase, state, variant)
                       
        elif state == "1B.3":
            
            PATTERNS_YES: list[str] = [
                # AFIRMACIONES DIRECTAS Y PERSISTENCIA
                r"\bsi[,.]?\s*(me pasa|he notado eso|me ocurre|exacto|tal cual|asi es)\b",
                r"\b(me pasa|estoy asi) (mucho|siempre|casi cada dia|todos los dias)\b",
                r"^(si|exacto|asi es|tal cual|efectivamente)$",

                # FATIGA INTENSA / CANSANCIO EXTREMO
                r"\bestoy (agotado|agotada|reventado|reventada|fundido|fundida|hecho polvo)\b",
                r"\b(tengo|siento) (un )?(cansancio extremo|agotamiento total)\b",
                r"\bno (tengo|me quedan) (fuerzas|energia|ganas de nada)\b",
                r"\b(me falta|sin) (energia|fuerzas)\b",
                r"\b(me pesa|no puedo con) (el cuerpo|mi cuerpo|la vida)\b",
                r"\bme siento (muy )?(pesado|pesada|lento|lenta)\b",
                r"\bno puedo mas\b",

                # FALTA DE ENERGÍA PESE A DESCANSAR
                r"\baun (durmiendo|descansando) sigo (cansado|cansada|igual)\b",
                r"\b(ni durmiendo|ni descansando) se me pasa\b",
                r"\bme levanto (ya )?(cansado|cansada|sin fuerzas|reventado)\b",
                r"\bel (descanso|sueno) no me (ayuda|recupera|sirve)\b",

                # ESFUERZO EXCESIVO PARA TAREAS PEQUEÑAS
                r"\b(cualquier cosa|todo) me (cuesta|supone) (un mundo|un esfuerzo|muchisimo)\b",
                r"\b(las tareas|hacer algo) se me (hacen enormes|hace cuesta arriba)\b",
                r"\bme cuesta (mucho )?(levantarme|ducharme|hacer las cosas|moverme)\b",
                r"\bno tengo fuerzas ni para (lo simple|las cosas basicas|cosas simples)\b"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(me pasa|he notado eso|nada de eso|en absoluto|para nada)\b",
                r"\bno estoy (tan |muy )?(cansado|cansada|agotado|agotada)\b",
                r"\bno (tengo|he notado) (esa fatiga|ese cansancio|falta de energia)\b",

                # CANSANCIO NORMAL / CIRCUNSTANCIAL
                r"\b(solo|es el) cansancio (normal|del dia a dia|de trabajar)\b",
                r"\bcansado pero (normal|lo justo|puedo con ello)\b",
                r"\bsolo (si duermo poco|cuando trabajo mucho|a veces)\b",
                r"\bno es (constante|algo de siempre|para tanto)\b",

                # ENERGÍA Y RENDIMIENTO
                r"\b(tengo|me siento con) (energia|fuerzas)\b",
                r"\b(aguanto|rindo) (bien|perfectamente) (el dia|todo el dia)\b",
                r"\bpuedo (hacer mis cosas|con todo)\b",
                r"\bno me falta (la )?energia\b",

                # DURACIÓN INSUFICIENTE
                r"\b(me paso|fue) (solo |tan solo )?(unos dias|un par de dias)\b",
                r"\bno (llego a|duro) (dos semanas|quince dias|tanto tiempo)\b",
                r"\bfue algo (puntual|pasajero)\b",

                # RESPUESTAS BREVES
                r"^(no|que va|estoy bien|ninguno)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Energía normal o cansancio puntual)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1B_3_fatigue_energy_loss"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "1B.4" 
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Fatiga detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1B_3_fatigue_energy_loss"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "1B.4"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1B.3"
                    return (phase, state, variant)
            
        elif state == "1B.4":
            
            PATTERNS_YES: list[str] = [
                # AFIRMACIONES DIRECTAS
                r"\bsi[,.]?\s*(me pasa|he notado eso|me ocurre|exacto|asi es|tal cual)\b",
                r"\b(me pasa|me ocurre|estoy asi) (mucho|siempre|constantemente)\b",
                r"^(si|exacto|asi es|efectivamente|totalmente)$",

                # DIFICULTAD PARA CONCENTRARSE
                r"\b(no (logro|puedo|consigo)|me cuesta) (mucho )?(concentrarme|enfocarme|mantener la atencion|centrarme)\b",
                r"\bpierdo el hilo( facilmente| enseguida| muy rapido)?\b",
                r"\bme (distraigo|desconcentro) (mucho|facilmente|enseguida|rapido)\b",
                r"\bme cuesta (leer|seguir una conversacion|atender|estudiar)\b",
                r"\bno (retengo|me quedo con) lo que (leo|escucho|me dicen)\b",
                r"\bmi mente se va (a otro lado|a otra parte|todo el rato)\b",

                # PROBLEMAS PARA TOMAR DECISIONES
                r"\b(me cuesta|no (logro|puedo|se)) (decidir|decidirme|elegir|tomar decisiones)\b",
                r"\bdudo (todo el tiempo|siempre|mucho|constantemente)\b",
                r"\bme (bloqueo|paralizo) (cuando tengo que elegir|ante las decisiones|para decidir|al decidir)\b",
                r"\bme cuesta tomar decisiones (simples|basicas|del dia a dia)\b"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIONES DIRECTAS
                r"\bno[,.]?\s*(me pasa|he notado eso|tengo ese problema|nada de eso|para nada)\b",
                r"\bno tengo (problemas|dificultad) (con eso|en ese sentido)\b",

                # CONCENTRACIÓN PRESERVADA
                r"\bme concentro (bien|normal|sin problema|como siempre)\b",
                r"\bno (tengo problemas|me cuesta) (para |al )?(concentrarme|enfocarme)\b",
                r"\b(puedo|consigo) seguir lo que (leo|escucho) (bien|sin problema)\b",
                r"\bmantengo la atencion( sin problema| bien)?\b",
                r"\bmi cabeza (funciona bien|esta bien)\b",

                # DECISIONES NORMALES
                r"\b(tomo decisiones|decido) (sin dificultad|bien|rapido|como siempre|normal)\b",
                r"\bno me cuesta (nada )?decidir(me)?\b",
                r"\bno dudo mas (de lo habitual|de lo normal)\b",

                # DURACIÓN INSUFICIENTE O PUNTUAL
                r"\bsolo me pasa (a veces|en momentos puntuales|algun dia)\b",
                r"\b(algun dia|algo) puntual\b",
                r"\b(fue|me paso) solo unos dias\b",
                r"\bno (ha durado tanto|es constante|es siempre)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|que va|en absoluto|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Concentración y toma de decisiones normales)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1B_4_concentration_decision_issues"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "1B.5"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Problemas cognitivos detectados)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1B_4_concentration_decision_issues"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "1B.5"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1B.4"
                    return (phase, state, variant)
        
        elif state == "1B.5":
            
            PATTERNS_YES: list[str] = [
                # AFIRMACIONES DIRECTAS
                r"\bsi[,.]?\s*(me pasa|he notado eso|me ocurre|exacto|asi es|tal cual)\b",
                r"\b(me pasa|me ocurre) (mucho|siempre|constantemente)\b",
                r"^(si|exacto|asi es|efectivamente|totalmente)$",

                # BAJA AUTOESTIMA / FALTA DE MÉRITOS
                r"\bno (valgo|sirvo)( para nada)?\b",
                r"\bme siento (inferior|menos)\b",
                r"\bno me veo capaz\b",
                r"\bno doy la talla\b",
                r"\bno estoy a la altura\b",
                r"\bme exijo demasiado\b",
                r"\bme veo mal\b",
                r"\bno veo mis meritos\b",
                r"\bno reconozco lo que hago bien\b",

                # CULPABILIDAD EXCESIVA
                r"\b(todo es|es) culpa mia\b",
                r"\bme culpo (por todo)?\b",
                r"\bme siento culpable (por todo)?\b",
                r"\bsiempre pienso que es por mi culpa\b",
                r"\bme responsabilizo de todo\b",
                r"\bme echo la culpa\b",
                r"\bme siento culpable aunque no (toque|sea necesario)\b"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIONES DIRECTAS
                r"\bno[,.]?\s*(me pasa|he notado eso|nada de eso|para nada|en absoluto)\b",
                r"^(no|para nada|en absoluto|que va)$",

                # AUTOEVALUACIÓN CONSERVADA
                r"\bme valoro (bien|normal)\b",
                r"\btengo confianza en mi\b",
                r"\bse reconocer lo que hago bien\b",
                r"\bno me culpo (por todo)?\b",
                r"\bno suelo pensar asi\b",

                # EXIGENCIA / CULPA NORMAL
                r"\bme exijo (como cualquiera|normal)\b",
                r"\ba veces me critico(,? pero nada mas)?\b",
                r"\balguna culpa puntual\b",
                r"\bsolo en momentos concretos\b",

                # DURACIÓN INSUFICIENTE
                r"\b(fue|me paso) solo unos dias\b",
                r"\bme paso puntual\b",
                r"\bno llego a (dos semanas|tanto tiempo)\b",
                r"\bno es constante\b"
            ]
            
            # 1 - Negación (Autoestima preservada)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1B_5_low_selfworth_guilt"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "1B.6"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Baja autoestima / culpa detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1B_5_low_selfworth_guilt"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "1B.6"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1B.5"
                    return (phase, state, variant)
            
        elif state == "1B.6":
            
            PATTERNS_YES: list[str] = [
                # AFIRMACIONES DIRECTAS
                r"\bsi[,.]?\s*(me pasa|he pensado eso|me ocurre|exacto|asi es|tal cual)\b",
                r"\b(me pasa|me ocurre|he pensado eso) (mucho|siempre|constantemente)\b",
                r"^(si|exacto|asi es|efectivamente|totalmente)$",

                # DESESPERANZA INTENSA
                r"\bno (hay|veo) salida\b",
                r"\bno merece la pena\b",
                r"\bnada va a mejorar\b",
                r"\bya no tengo esperanza\b",
                r"\bestoy desesperad[oa]\b",
                r"\btodo da igual\b",
                r"\bya no puedo mas\b",
                r"\bno aguanto mas\b",

                # IDEACIÓN SUICIDA PASIVA
                r"\bquisiera desaparecer\b",
                r"\bojala no despertar\b",
                r"\bpreferiria no estar aqui\b",
                r"\bseria mejor no existir\b",
                r"\bme gustaria dormir y no despertar\b",
                r"\bquisiera no seguir\b",

                # IDEACIÓN / CONDUCTA SUICIDA ACTIVA
                r"\bhe pensado en (suicidarme|matarme)\b",
                r"\bquiero quitarme la vida\b",
                r"\bhe intentado (hacerme dano|suicidarme)\b",
                r"\bhe pensado en hacerme dano\b",
                r"\bhe planificado (algo|mi muerte|suicidarme)\b"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIONES DIRECTAS
                r"\bno[,.]?\s*(me pasa|he pensado eso|nada de eso|para nada|en absoluto)\b",
                r"^(no|para nada|en absoluto|que va)$",

                # ESPERANZA CONSERVADA
                r"\btengo esperanza\b",
                r"\bcreo que esto va a mejorar\b",
                r"\baunque estoy mal, quiero seguir\b",
                r"\bno pienso en eso\b",

                # MALESTAR SIN IDEACIÓN SUICIDA
                r"\bestoy (triste|mal|agobiad[oa]) pero no (asi|tanto)\b",
                r"\bestoy (mal|agobiad[oa]) pero no me haria nada\b",
                r"\bestoy mal pero no quiero desaparecer\b"
            ]
            
            # 1 - Negación (Sin desesperanza grave ni ideación suicida)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1B_6_hopelessness_suicidal_ideation"
                value = False
                db.add_user_info(telephone, key, value)
                
                # Mirar las otras respuestas de 1B
                b1 = db.get_user_info(telephone, "DEP_EVAL", "1B.1")
                b2 = db.get_user_info(telephone, "DEP_EVAL", "1B.2")
                b3 = db.get_user_info(telephone, "DEP_EVAL", "1B.3")
                b4 = db.get_user_info(telephone, "DEP_EVAL", "1B.4")
                b5 = db.get_user_info(telephone, "DEP_EVAL", "1B.5")
                results = [b1, b2, b3, b4, b5]
                
                if sum(1 for x in results if x) >= 2:
                    phase, state = "DEP_EVAL", "1C"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    phase, state = "CHAT", ""   # seria OTR
                    key = "SCREENING.DEP"
                    value = "others"
                    db.add_user_info(telephone, key, value)
                    return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Desesperanza / ideación detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1B_6_hopelessness_suicidal_ideation"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    # Mirar las otras respuestas de 1B
                    b1 = db.get_user_info(telephone, "DEP_EVAL", "1B.1")
                    b2 = db.get_user_info(telephone, "DEP_EVAL", "1B.2")
                    b3 = db.get_user_info(telephone, "DEP_EVAL", "1B.3")
                    b4 = db.get_user_info(telephone, "DEP_EVAL", "1B.4")
                    b5 = db.get_user_info(telephone, "DEP_EVAL", "1B.5")
                    results = [b1, b2, b3, b4, b5]
                    
                    if sum(1 for x in results if x) >= 1:
                        phase, state = "DEP_EVAL", "1C"
                        db.save_flow(telephone, phase, state)
                        return (phase, state, variant)
                    
                    else:
                        phase, state = "CHAT", ""   # seria OTR
                        key = "SCREENING.DEP"
                        value = "others"
                        db.add_user_info(telephone, key, value)
                        return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1B.6"
                    return (phase, state, variant)
            
        elif state == "1C":
            
            PATTERNS_YES: list[str] = [
                # AFIRMACIONES DIRECTAS
                r"\bsi[,.]?\s*(me afecta|me pasa|me ocurre|exacto|asi es|tal cual)\b",
                r"\b(me afecta|me ocurre) (mucho|siempre|constantemente)\b",
                r"^(si|exacto|asi es|efectivamente|totalmente)$",

                # DIFICULTAD LABORAL
                r"\bno puedo trabajar\b",
                r"\bhe faltado al trabajo\b",
                r"\bno rindo en el trabajo\b",
                r"\bno puedo concentrarme en el trabajo\b",
                r"\bel trabajo se me hace imposible\b",

                # DIFICULTAD ACADÉMICA
                r"\bno puedo estudiar\b",
                r"\bhe bajado las notas\b",
                r"\bno me concentro estudiando\b",
                r"\bhe suspendido\b",
                r"\bno voy a clase\b",
                r"\bestoy reprobando\b",

                # DIFICULTAD SOCIAL / RELACIONAL
                r"\bno salgo con amigos\b",
                r"\bme he aislado\b",
                r"\bno quiero ver a nadie\b",
                r"\bhe discutido con (mi )?familia\b",
                r"\bme he distanciado\b",

                # IMPACTO GENERAL
                r"\bsi me afecta\b",
                r"\bme esta costando mucho\b",
                r"\bno funciono (normal|como antes)\b",
                r"\bmi vida esta parada\b",
                r"\btodo se me complica\b",
                r"\bno llevo mi rutina\b"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIONES DIRECTAS
                r"\bno[,.]?\s*(me afecta|me pasa|nada de eso|para nada|en absoluto)\b",
                r"^(no|para nada|en absoluto|que va)$",

                # FUNCIONAMIENTO NORMAL
                r"\btrabajo (normal|como siempre)\b",
                r"\bsigo estudiando\b",
                r"\bmi vida sigue igual\b",
                r"\bno ha cambiado nada\b",
                r"\bno me impide nada\b",
                r"\b(hago|mantengo) mi rutina (normal|como siempre)?\b"
            ]
            
            # 1 - Negación
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1C_functional_impairment"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "CHAT", ""   # seria OTR
                key = "SCREENING.DEP"
                value = "others"
                db.add_user_info(telephone, key, value)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Deterioro funcional detectado)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1C_functional_impairment"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2A.1"
                    db.save_flow(telephone, phase, state)
                    key = "SCREENING.DEP"
                    value = "depression"
                    db.add_user_info(telephone, key, value)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "1C"
                    return (phase, state, variant)
            
        elif state == "2A.1":
            
            PATTERNS_YES: list[str] = [
                # TOMA DE MEDICACIÓN O TRATAMIENTO
                r"\bsi[,.]?\s*(tomo|estoy tomando|sigo|me recetaron|uso)\b",
                r"\b(tomo|estoy tomando|uso) (medicacion|pastillas|medicinas|farmacos|algo)\b",
                r"\bme (dieron|recetaron|prescribieron) (algo|pastillas|medicinas)\b",
                r"\bsigo (un )?(tratamiento medico|tratamiento)\b",
                r"\buso (suplementos|vitaminas|remedios)\b",

                # AUTOMEDICACIÓN O CONSUMO NO CONTROLADO
                r"\b(tomo|uso) (algo |cosas )?por mi cuenta\b",
                r"\bme automedico\b",
                r"\buso (analgesicos|relajantes|pastillas para dormir)\b",
                r"\bconsumo (pastillas|medicacion) sin receta\b",
                r"\btomo algo para (dormir|los nervios|relajarme|el dolor)\b",

                # TRATAMIENTOS RECIENTES O CONTINUOS
                r"\bacabo de empezar (un |el )?tratamiento\b",
                r"\bsigo (el |un )?tratamiento desde hace (tiempo|mucho)\b",
                r"\bme (ajustaron|cambiaron) la (dosis|medicacion)\b",
                r"\bhe cambiado de (medicacion|pastillas)\b",

                # IMPACTO PERCIBIDO
                r"\bla medicacion me (afecta|hace sentir raro|sienta mal)\b",
                r"\b(tengo|noto) efectos secundarios\b",
                r"\bme cuesta seguir el tratamiento\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|correcto|asi es|exacto|efectivamente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(tomo nada|uso nada|me han recetado nada|estoy bajo tratamiento)\b",
                r"\bsin (medicacion|pastillas|tratamiento)\b",
                r"\bno (estoy siguiendo|tengo|uso) ningun tratamiento\b",
                r"\bno (uso|tomo) (suplementos|pastillas|nada)\b",

                # ESTADO SIN INTERVENCIÓN MÉDICA
                r"\bno me (recetaron|dieron) nada\b",
                r"\bno (necesito|tomo) (medicinas|medicacion)\b",
                r"\bno estoy bajo tratamiento\b",
                r"\bestoy limpio de (pastillas|medicacion)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|ninguno|que va|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (No toma medicación)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2A_1_on_medication"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2A.2"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Toma medicación/tratamiento)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2A_1_on_medication"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2A.2" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2A.1"
                    return (phase, state, variant)
        
        elif state == "2A.2":
            
            PATTERNS_YES: list[str] = [
                # PROBLEMAS DE TIROIDES
                r"\b(tengo|sufro de) (hipotiroidismo|hipertiroidismo|tiroides)\b",
                r"\b(tengo|mi) tiroides (alterada|mal|no funciona bien)\b",
                r"\btomo (algo|medicacion) para la tiroides\b",
                r"\bme dijeron lo de la tiroides\b",
                
                # ANEMIA O DÉFICIT DE HIERRO
                r"\b(tengo|sufro de) (anemia|falta de hierro|ferropenia)\b",
                r"\bme (falta|salio bajo el) hierro\b",
                r"\bme dijeron que tengo anemia\b",
                r"\btomo hierro\b",
                
                # PROBLEMAS NUTRICIONALES O METABÓLICOS
                r"\b(tengo|me dijeron de) (un |algun )?deficit (nutricional|de vitaminas)\b",
                r"\b(tengo la|me falta) vitamina d\b",
                r"\bme hablaron de (nutricion|mi alimentacion|las vitaminas)\b",
                r"\b(tengo|salio) bajo el (acido folico|b12)\b",

                # RESPUESTAS AFIRMATIVAS GENERALES
                r"\bsi[,.]?\s*(me han dicho algo|me lo comentaron|lo tengo|me pasa eso)\b",
                r"^(si|correcto|exacto|asi es)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(me han dicho nada|nunca me dijeron nada|nada de eso|no es mi caso)\b",
                r"\bno tengo (anemia|tiroides|nada de eso)\b",
                r"\bmis (analisis|pruebas|analiticas) salieron (bien|normal)\b",
                
                # FUNCIÓN Y BIENESTAR NORMAL
                r"\bmi (salud|medico) dice que (esta bien|estoy sano|todo normal)\b",
                r"\b(todo esta|me encuentro) (bien|perfectamente|normal)\b",
                r"\bno tengo problemas (fisicos|de salud)\b",
                r"\b(estoy|salio) todo (en orden|bien)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|que va|ninguno|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Sin patologías físicas detectadas)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2A_2_physical_conditions"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2B.1"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Condición física presente)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2A_2_physical_conditions"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2B.1"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2A.2"
                    return (phase, state, variant)
        
        elif state == "2B.1":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y EUFORIA
                r"\bsi[,.]?\s*(he tenido epocas|tuve una etapa|me paso eso|asi es)\b",
                r"\b(episodios?|etapas?|momentos?) de (euforia|estar euforic[oa])\b",
                r"\bme (sentia|siento) (invencible|en la gloria|dios|poderoso|poderosa)\b",
                r"\bestaba (exageradamente|demasiado|locamente) (feliz|alegre|animado|animada)\b",
                r"\btener (una )?energia (desbordante|ilimitada|brutal)\b",
                r"\bestaba (muy |super )?arriba\b",

                # IRRITABILIDAD MARCADA
                r"\b(he estado|estaba) (muy |super )?(irritable|agresiv[oa]|discutidor|discutidora)\b",
                r"\bsaltaba por (cualquier cosa|nada)\b",
                r"\bme (enfadaba|cabreaba) con (todo el mundo|todos) sin (razon|motivo)\b",
                r"\bestaba (insoportable|muy borde) durante dias\b",

                # AUMENTO DE ACTIVIDAD / HIPERPRODUCTIVIDAD
                r"\bme puse a (hacer muchos proyectos|crear cosas) a la vez\b",
                r"\bno (paraba quieto|podia parar)\b",
                r"\btenia demasiadas actividades\b",
                r"\btrabajaba sin parar y (luego seguia|no dormia)\b",
                r"\bestaba (muy |super )?acelerado\b",

                # REFERENCIAS TEMPORALES
                r"\bhace (anos|tiempo) tuve una etapa asi\b",
                r"\bme paso (una vez |varias veces )durante (semanas|meses)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|efectivamente|tal cual|asi es)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca he tenido algo asi|nunca he estado tan|no he tenido esas fases)\b",
                r"\bno me (reconozco|pasa eso)\b",
                r"\bno es mi caso\b",

                # DIFERENCIAR BUEN ÁNIMO NORMAL DE MANÍA
                r"\bepocas buenas pero (nada exagerado|normales)\b",
                r"\bhe estado (contento|animado) pero dentro de lo normal\b",
                r"\bsin perder el control\b",
                r"\bno (llegaba a tanto|eran semanas enteras)\b",
                r"\bdias buenos pero no (tanto tiempo|semanas)\b",

                # SOLO IRRITABILIDAD / NERVIOS PUNTUALES
                r"\b(me he puesto|estoy) (nervioso|irritable) a veces pero (no tanto|poco tiempo)\b",
                r"\bme enfado a veces pero no (seguido|una semana)\b",
                r"\bsolo han sido dias sueltos\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Ánimo estable o fluctuaciones normales)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2B_1_mania_episode"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2B.2"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Indicios de episodio maníaco/hipomaníaco)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2B_1_mania_episode"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2B.2" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2B.1"
                    return (phase, state, variant)
            
        elif state == "2B.2":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y SENSACIÓN DE DESCANSO
                r"\bsi[,.]?\s*(me ha pasado|he dormido poco sin cansarme|es verdad)\b",
                r"\b(no necesitaba|sin necesidad de) dormir\b",
                r"\bapenas dormia y (seguia con energia|estaba bien)\b",
                r"\bcon (muy |tan )?poco sueno me encontraba (perfecto|totalmente bien|genial)\b",
                
                # DISMINUCIÓN CLARA (HORAS ESPECÍFICAS)
                r"\bdormia (2|3|4|dos|tres|cuatro) horas y (estaba perfecto|me sobraba)\b",
                r"\bno sentia sueno (aunque|pese a que) hubiera dormido poco\b",
                r"\bme despertaba (descansado|descansada|a tope) con (muy )?poco sueno\b",
                
                # ACTIVIDAD Y ENERGÍA
                r"\bseguia (activo|activa) todo el dia sin (notar cansancio|cansarme)\b",
                r"\bpodia funcionar con (poquisimo|nada de) sueno\b",
                r"\bestaba (lleno|llena) de energia con solo un par de horas\b",

                # REFERENCIAS TEMPORALES
                r"\bhace una temporada me pasaba\b",
                r"\bdurante varios dias (seguidos )?dormia muy poco\b",
                r"\btuve una racha asi\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|correcto|exacto|asi es|totalmente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca me ha pasado|nada de eso|no es mi caso)\b",
                r"\bno recuerdo algo asi\b",
                r"\bno[,.]?\s*(siempre necesito dormir|duermo normal)\b",

                # DIFERENCIAR INSOMNIO DE MANÍA (CRUCIAL)
                r"\bhe dormido (mal|poco) pero (si me cansaba|estaba agotado|estaba muerto)\b",
                r"\bme costaba dormir pero (al dia siguiente )?estaba (agotado|fatal|reventado)\b",
                r"\b(tengo|he tenido) insomnio\b",
                r"\bno es (que no necesite|menos necesidad), es que no puedo\b",
                r"\bsi no duermo me (muero|siento fatal|agoto)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca)$",
                r"\bno\b"
            ]

            
            # 1 - Negación (O insomnio clásico donde sí hay cansancio)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2B_2_decreased_sleep_need"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2B.3"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Menos necesidad de sueño detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2B_2_decreased_sleep_need"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2B.3"
                    db.save_flow(telephone, phase, state) 
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2B.2"
                    return (phase, state, variant)
            
        elif state == "2B.3":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y ACELERACIÓN
                r"\bsi[,.]?\s*(he tenido epocas|me pasaba eso|he sentido|iba asi)\b",
                r"\b(iba|voy|estaba) (acelerado|acelerada|a mil|a mil por hora|a cien)\b",
                r"\bsenti que (iba|estaba) (muy )?acelerado\b",
                r"\b(tenia|con) (muchisima|demasiada) energia\b",
                
                # EXCESO DE ACTIVIDAD / DIFICULTAD DE CONTROL
                r"\bno (podia quedarme quieto|podia parar|podia frenar)\b",
                r"\bhacia (muchas|demasiadas) cosas (a la vez|al mismo tiempo) sin cansarme\b",
                r"\bme (costaba|era imposible) (frenarme|parar|quedarme tranquilo)\b",
                r"\bestaba (hiperactivo|hiperactiva|desbordado|desbordada)\b",
                r"\bun (exceso|chorro) de actividad\b",
                r"\bno paraba en casa\b",

                # REFERENCIAS TEMPORALES
                r"\bhace (anos|un tiempo) tuve una etapa asi\b",
                r"\bdurante varios dias (seguidos )?me paso\b",
                r"\bhe tenido (varios )?episodios de ese tipo\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|tal cual|efectivamente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca me ha pasado|nada de eso|no es mi caso)\b",
                r"\bno (he tenido|siento) (ese exceso|esa energia|esa actividad)\b",
                r"\bno me he sentido asi\b",

                # DIFERENCIAR ACTIVIDAD NORMAL DE MANÍA
                r"\bestaba (muy |bastante )?ocupado pero (era |todo )?normal\b",
                r"\btenia muchas cosas (que hacer|por hacer) pero no (iba acelerado|estaba descontrolado)\b",
                r"\btrabajaba mucho pero (bien|sin sentirme descontrolado|con calma)\b",
                r"\bcansado pero no hiperactivo\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|no recuerdo nada asi)\b",
                r"\bno\b"
            ]
            
            # 1 - Negación (Actividad normal o solo estar ocupado)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2B_3_excessive_activity"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2B.4"
                db.save_flow(telephone, phase, state)  
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Actividad excesiva detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2B_3_excessive_activity"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2B.4"
                    db.save_flow(telephone, phase, state)  
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2B.3"
                    return (phase, state, variant)
            
        elif state == "2B.4":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y GASTOS
                r"\bsi[,.]?\s*(he tomado decisiones impulsivas|he gastado sin pensar|me he lanzado)\b",
                r"\b(me gaste|me he gastado) (mucho|demasiado) (dinero|pasta)\b",
                r"\bsin control (con el dinero|comprando)\b",
                r"\b(compras|gastos) (compulsivas|compulsivos|sin sentido)\b",
                r"\bgaste mas de lo que (debia|tenia|pedia)\b",
                r"\btire la casa por la ventana\b",

                # DECISIONES IMPORTANTES SIN REFLEXIONAR
                r"\b(tome|hice) decisiones (grandes|importantes) sin (pensar|pensarlo)\b",
                r"\bme (cambie|deje|deje el) (trabajo|curro) (sin mas|de golpe|sin pensar)\b",
                r"\bme (meti|enrede) en (proyectos|deudas|líos) sin (reflexionar|pensar)\b",
                r"\bme lie la manta a la cabeza\b",
                
                # IMPULSIVIDAD / FALTA DE CONTROL
                r"\b(actue|hice las cosas) sin pensar\b",
                r"\bno (media|pense en) las consecuencias\b",
                r"\bme (dejaba llevar|lance) y luego me (arrepentia|arrepenti)\b",
                r"\biba por impulso\b",
                r"\bestaba (muy |super )?impulsiv[oa]\b",

                # REFERENCIAS TEMPORALES
                r"\bdurante (aquella|esa) racha\b",
                r"\bme paso en (varias ocasiones|una epoca)\b",
                r"\bfui muy impulsiv[oa] (en ese tiempo|entonces)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|tal cual|totalmente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca he hecho nada asi|no he tenido gastos|nada de eso)\b",
                r"\bno suelo (tomar decisiones impulsivas|ser impulsivo)\b",
                r"\bno me (identifico|reconozco) con eso\b",
                r"\bno es mi caso\b",

                # DIFERENCIAR IMPULSO NORMAL DE MANÍA
                r"\bcompro cosas pero (con control|normal|lo justo)\b",
                r"\b(tome decisiones|decidi) rapido pero (las pense|con cabeza)\b",
                r"\bhe sido impulsiv[oa] (alguna vez|un poco) pero no (exagerado|de esa forma)\b",
                r"\bsiempre (pienso|reflexiono) antes de actuar\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|no recuerdo algo asi)\b",
                r"\bno\b"
            ]

            
            # 1 - Negación (Conducta controlada)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2B_4_impulsive_decisions"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2B.5" 
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Impulsividad detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2B_4_impulsive_decisions"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2B.5" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2B.4"
                    return (phase, state, variant)
            
        elif state == "2B.5":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y VERGÜENZA
                r"\bsi[,.]?\s*(he hecho cosas fuera de lugar|me daban verguenza|estaba desinhibido)\b",
                r"\b(hice|he hecho) cosas que antes me (daban|habrian dado) verguenza\b",
                r"\bsi[,.]?\s*(perdia|perdi|sin) el filtro\b",
                r"\bdecir cosas que antes me (callaba|daban verguenza)\b",

                # DESINHIBICIÓN / CONDUCTA INAPROPIADA
                r"\bcomportarme (sin filtro|sin frenos)\b",
                r"\bdecir lo (primero|primero que se me pasaba) por la cabeza\b",
                r"\bestaba (demasiado |muy )?lanzado\b",
                r"\bme daba igual lo que (pensaran|dijeran) (los demas|el resto)\b",
                r"\bestaba (sobrado|muy crecido)\b",
                
                # CONFIANZA Y ATREVIMIENTO
                r"\bme (sentia|veia) capaz de todo\b",
                r"\bactuaba sin (reparo|miedo|pensar)\b",
                r"\bhacia cosas que (normalmente|antes) no haria\b",
                r"\bme sentia (demasiado |muy )?confiado\b",

                # CONDUCTA SOCIAL / FEEDBACK EXTERNO
                r"\b(otros|la gente) me (decian|decia) que estaba raro\b",
                r"\bme dijeron que (estaba pasando limites|me pasaba de la raya)\b",
                r"\bme comporte de forma (impropia|inadecuada)\b",
                r"\bllame la atencion por (como hablaba|mi conducta)\b",

                # REFERENCIAS TEMPORALES
                r"\ben una etapa me paso\b",
                r"\bdurante varios dias estaba asi\b",
                r"\bhe tenido epocas en las que (perdia|no tenia) el filtro\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|totalmente|efectivamente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca me ha pasado|nada de eso|no es mi caso)\b",
                r"\bno (me he sentido|he estado) (lanzado|raro|sin filtro)\b",
                r"\bno he hecho nada (asi|fuera de lugar)\b",

                # DIFERENCIAR CAMBIOS NORMALES
                r"\b(dicho|hice) alguna tonteria pero (nada fuera de lo normal|lo tipico)\b",
                r"\ba veces (he sido|soy) (mas abierto|suelto) pero sin (pasarme|exagerar)\b",
                r"\bsiempre tengo (el |mi )?filtro\b",
                r"\bsoy (timido|prudente) siempre\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|no recuerdo algo asi)\b",
                r"\bno\b"
            ]
            
            # 1 - Negación (Conducta social habitual o controlada)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2B_5_social_disinhibition"
                value = False
                db.add_user_info(telephone, key, value)
                
                # Final de la sub-fase 2B
                phase, state = "DEP_EVAL", "2B.6" 
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Desinhibición detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2B_5_social_disinhibition"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2B.6" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2B.5"
                    return (phase, state, variant)
        
        elif state == "2B.6":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y DISTRACCIÓN
                r"\bsi[,.]?\s*(me distraigo mucho|me cuesta seguir|me pasa eso)\b",
                r"\b(me cuesta|es dificil) (seguir|mantener) (el hilo|la conversacion)\b",
                r"\bse me va (la cabeza|la pinza|el santo al cielo)\b",
                r"\b(pierdo|he perdido) el hilo (enseguida|facilmente)\b",
                r"\bcualquier (cosa|ruido|pensamiento) me (distrae|desconcentra|saca)\b",

                # TAREAS INACABADAS / SALTO DE ACTIVIDAD
                r"\b(dejo|dejar) (las cosas|todo) a medias\b",
                r"\bvoy saltando de (una cosa a otra|tarea en tarea)\b",
                r"\bme pongo con algo y (enseguida cambio|no acabo)\b",
                r"\bno (consigo|puedo) terminar lo que (empiezo|comienzo)\b",
                r"\bno (consigo|puedo) mantener la atencion\b",
                
                # PENSAMIENTOS ACELERADOS / ESTÍMULOS
                r"\b(se me cruzan|tengo) mil (ideas|pensamientos)\b",
                r"\bcualquier ruido me (saca de foco|despista)\b",
                r"\bmi cabeza va (demasiado rapido|a mil) para centrarme\b",
                r"\bme interrumpe cualquier (cosa|tonteria)\b",

                # REFERENCIAS TEMPORALES
                r"\ben una temporada me paso\b",
                r"\bdurante varios dias estaba asi\b",
                r"\bhe tenido epocas en las que no podia concentrarme\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|totalmente|efectivamente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(no me pasa eso|suelo mantener bien el hilo|no me distraigo)\b",
                r"\bno me (distraigo|desconcentro) (tanto|asi)\b",
                r"\bpuedo (centrarme|concentrarme) bien\b",

                # DIFERENCIAR DISTRACCIÓN NORMAL DE MANÍA
                r"\ba veces (me distraigo|pierdo el hilo) pero (como cualquiera|lo normal)\b",
                r"\bde vez en cuando pero no (exagerado|siempre)\b",
                r"\bme desconcentro si (estoy cansado|tengo sueno) pero no (habitualmente|siempre)\b",
                r"\bpuedo terminar mis tareas\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|no recuerdo algo asi)\b",
                r"\bno\b"
            ]

            
            # 1 - Negación (Atención preservada o distracción normal)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2B_6_distractibility"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2B.7" 
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Distractibilidad detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2B_6_distractibility"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2B.7" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2B.6"
                    return (phase, state, variant)
        
        elif state == "2B.7":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y DESTINO
                r"\bsi[,.]?\s*(me he sentido asi|estoy destinado|soy especial|lo he sentido)\b",
                r"\b(siento|creo) que estoy destinado a (algo grande|algo grandioso|hacer historia)\b",
                r"\btengo una (mision importante|mision especial)\b",
                r"\bestoy aqui para (hacer algo extraordinario|cambiar el mundo)\b",
                r"\btengo un proposito (unico|especial)\b",

                # SUPERIORIDAD / CAPACIDADES
                r"\b(mis capacidades|mi inteligencia) (estan|esta) (muy )?por encima\b",
                r"\bsoy (mas capaz|mejor|superior) que (los demas|la gente|mis amigos)\b",
                r"\btengo (poderes|habilidades|talentos) que otros no (tienen|entienden)\b",
                r"\bveo cosas que (los demas|el resto) no (ven|entienden)\b",
                r"\bestoy en otro nivel\b",
                
                # CONFIANZA EXTREMA
                r"\bme (veo|siento) capaz de (cualquier cosa|todo)\b",
                r"\bpuedo conseguir lo que quiera (sin problema|facilmente)\b",
                r"\bnadie me iguala\b",
                r"\bsoy (un genio|alguien superior|especial)\b",

                # REFERENCIAS TEMPORALES
                r"\btuve una epoca en la que me sentia asi\b",
                r"\bme paso durante (un tiempo|aquella racha)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|totalmente|por supuesto)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca me he sentido asi|no creo tener|no me veo asi)\b",
                r"\bno me (creo|siento) (especial|superior)\b",
                r"\bno es mi caso\b",
                r"\bpara nada soy asi\b",

                # DIFERENCIAR CONFIANZA NORMAL DE GRANDIOSIDAD
                r"\btengo (metas|ambiciones) pero (no me siento especial|soy normal)\b",
                r"\bconfio en mi (mismo|misma) pero (dentro de lo normal|lo justo)\b",
                r"\baspiro a cosas pero sin (sentirme superior|creerme nada)\b",
                r"\bme considero capaz pero (como cualquiera|nada del otro mundo)\b",
                r"\bsoy una persona (normal|corriente|humilde)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|no recuerdo algo asi)\b",
                r"\bno\b"
            ]
            
            # 1 - Negación (Autoestima normal o metas realistas)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2B_7_grandiosity"
                value = False
                db.add_user_info(telephone, key, value)
                
                # Mirar las otras respuestas de 2B
                b1 = db.get_user_info(telephone, "DEP_EVAL", "2B.1")
                b2 = db.get_user_info(telephone, "DEP_EVAL", "2B.2")
                b3 = db.get_user_info(telephone, "DEP_EVAL", "2B.3")
                b4 = db.get_user_info(telephone, "DEP_EVAL", "2B.4")
                b5 = db.get_user_info(telephone, "DEP_EVAL", "2B.5")
                b6 = db.get_user_info(telephone, "DEP_EVAL", "2B.6")
                results = [b1, b2, b3, b4, b5, b6]
                
                if sum(1 for x in results if x) >= 2:
                    phase, state = "DEP_PROTOCOLS", "2"
                    db.save_flow(telephone, phase, state)
                    key = "SCREENING.DEP"
                    value = "bipolar"
                    db.add_user_info(telephone, key, value)
                    return (phase, state, variant)
                
                else:
                    phase, state = "DEP_EVAL", "2C"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Grandiosidad detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2B_7_grandiosity"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    # Mirar las otras respuestas de 2B
                    b1 = db.get_user_info(telephone, "DEP_EVAL", "2B.1")
                    b2 = db.get_user_info(telephone, "DEP_EVAL", "2B.2")
                    b3 = db.get_user_info(telephone, "DEP_EVAL", "2B.3")
                    b4 = db.get_user_info(telephone, "DEP_EVAL", "2B.4")
                    b5 = db.get_user_info(telephone, "DEP_EVAL", "2B.5")
                    b6 = db.get_user_info(telephone, "DEP_EVAL", "2B.6")
                    results = [b1, b2, b3, b4, b5, b6]
                    
                    if sum(1 for x in results if x) >= 1:
                        phase, state = "DEP_PROTOCOLS", "2"
                        db.save_flow(telephone, phase, state)
                        key = "SCREENING.DEP"
                        value = "bipolar"
                        db.add_user_info(telephone, key, value)
                        return (phase, state, variant)
                    
                    else:
                        phase, state = "DEP_EVAL", "2C"
                        db.save_flow(telephone, phase, state)
                        return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2B.7"
                    return (phase, state, variant)
            
        elif state == "2C":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO GENERAL
                r"\bsi[,.]?\s*(he perdido a alguien|fallecio alguien|ha muerto)\b",
                r"\b(fallecio|murio|perdi a) (alguien|una persona) (muy )?(cercano|cercana|importante|querido|querida)\b",
                
                # FALLECIMIENTO DE FAMILIAR O PAREJA
                r"\b(murio|fallecio|perdi a) (mi |un )?(padre|madre|papa|mama|hermano|hermana|abuelo|abuela|hijo|hija|tio|tia)\b",
                r"\b(murio|fallecio|perdi a) mi (pareja|novio|novia|esposo|esposa|marido|mujer)\b",
                r"\bha muerto un familiar( hace poco| recientemente)?\b",

                # FALLECIMIENTO DE AMIGO
                r"\b(murio|fallecio|perdi a) mi (mejor )?amigo\b",
                r"\b(murio|fallecio|perdi a) un amigo (muy )?(cercano|intimo)\b",

                # RESPUESTAS AFIRMATIVAS BREVES (Con contexto de dolor)
                r"^(si|asi es|lamentablemente si|tristemente si|por desgracia si)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(no he perdido a nadie|no ha fallecido nadie|nadie cercano)\b",
                r"\bno[,.]?\s*(no he tenido|ninguna) perdida\b",
                r"\btodos (estan bien|vivos)\b",

                # PÉRDIDA FUERA DEL PLAZO (MÁS DE 6 MESES) - MUY IMPORTANTE
                r"\b(fue|paso|murio|fallecio) hace (mas de un ano|anos|mucho|mucho tiempo|bastante)\b",
                r"\bhace (ya )?(tiempo|anos|mucho) que paso\b",
                r"\bya hace (anos|mucho) de eso\b",
                r"\b(fue|paso) en el ano (20[0-2][0-9]|19[0-9]{2})\b", # Filtra menciones a años anteriores como "en 2020"

                # RESPUESTAS BREVES
                r"^(no|nada de eso|en absoluto|afortunadamente no|que va|ninguno|nadie)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Nadie ha fallecido o la pérdida fue hace mucho tiempo)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2C_recent_bereavement"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_PROTOCOLS", "1" 
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Pérdida reciente detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2C_recent_bereavement"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2D.1" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2C"
                    return (phase, state, variant)
            
        elif state == "2D.1":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO GENERAL
                r"\bsi[,.]?\s*(he sentido eso|la vida no vale la pena|he pensado eso|me pasa)\b",
                r"\b(he pensado|pienso) (en |que )?estaria mejor (muerto|muerta|si no estuviera)\b",
                r"\bhe tenido (esos pensamientos|ideas de ese tipo)\b",
                
                # DESEO DE NO EXISTIR / DESAPARECER
                r"\b(preferiria|ojala) no (estar aqui|existir|despertar)\b",
                r"\b(me gustaria|quisiera|quiero) desaparecer\b",
                r"\bno (quiero|tengo ganas de) seguir (viviendo|adelante|con esto)\b",
                r"\btodo seria (mas facil|mejor) si no estuviera\b",
                
                # PÉRDIDA DE SENTIDO VITAL
                r"\bla vida no tiene (sentido|valor)\b",
                r"\bnada vale la pena\b",
                r"\btodo me da igual\b",
                r"\bpara que seguir\b",
                r"\bno (veo|tengo) (razon|motivos) para (continuar|seguir|vivir)\b",
                
                # CANSANCIO EXISTENCIAL / DESESPERACIÓN
                r"\bestoy (cansado|cansada|harto|harta) de todo\b",
                r"\bya no puedo mas (con esto|con mi vida)?\b",
                r"\bquiero que todo se (acabe|termine)\b",
                r"\bno quiero seguir viviendo asi\b",
                
                # EXPRESIONES DE CARGA (INDIRECTAS)
                r"\bestarian mejor sin mi\b",
                r"\bsoy una carga (para todos|para mi familia)\b",
                r"\bel mundo estaria mejor sin mi\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|asi es|exacto|efectivamente|totalmente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca he pensado eso|no siento eso|nada de eso)\b",
                r"\bno he tenido esos pensamientos\b",
                r"\bpara nada (pienso eso|me pasa)\b",
                
                # DIFERENCIAR CANSANCIO NORMAL DE IDEACIÓN
                r"\bestoy (cansado|cansada) pero no (quiero morir|pienso en eso)\b",
                r"\ba veces (me siento mal|estoy mal) pero no (pienso en no estar|quiero desaparecer)\b",
                r"\bme gustaria que las cosas (fueran diferentes|cambiaran) pero no (en desaparecer|morir)\b",
                r"\bamo la vida\b",
                r"\btengo (muchos |mis )?motivos para seguir\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Sin ideación detectada)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2D_1_suicidal_ideation"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2D.2" 
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Ideación detectada - ACTIVAR PROTOCOLO RIESGO)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2D_1_suicidal_ideation"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2D.2" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2D.1"
                    return (phase, state, variant)
            
        elif state == "2D.2":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO GENERAL
                r"\bsi[,.]?\s*(no creo merecer|no merezco|me siento asi|tienes razon)\b",
                r"\bno (merezco|merit) (nada bueno|que me pase nada bueno|el carino)\b",
                r"\bno (deberia|tendria que) recibir ayuda\b",
                r"\blas cosas buenas son para otros\b",
                
                # SENTIMIENTO DE SER UNA CARGA
                r"\bsoy una carga (para los demas|para mi familia|para todo el mundo)\b",
                r"\bmolesto a la gente (que me ayuda|que me quiere)\b",
                r"\bno (deberian|tendrian que) perder el tiempo conmigo\b",
                r"\bles hago la vida (mas dificil|imposible)\b",
                
                # BAJA AUTOESTIMA / INDIGNIDAD
                r"\bno valgo (lo suficiente|nada|un pimiento)\b",
                r"\bno soy suficiente\b",
                r"\bsoy (un inutil|una inutil|un desastre)\b",
                r"\bno sirvo para nada\b",
                
                # CULPA / AUTORREPROCHE
                r"\bhe hecho cosas que no merecen perdon\b",
                r"\bme siento culpable (por todo|de todo)\b",
                r"\bno merezco (ser feliz|estar bien)\b",
                r"\bmerezco sufrir\b",
                
                # DIFICULTAD PARA ACEPTAR AYUDA
                r"\bme cuesta (aceptar|creer) que alguien se preocupe\b",
                r"\bno entiendo por que me ayudan\b",
                r"\bno deberia aceptar su (apoyo|ayuda)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|totalmente|asi es|exacto|efectivamente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(no siento eso|creo que merezco|nada de eso)\b",
                r"\bno me siento (asi|de esa manera)\b",
                r"\bcreo que merezco (ayuda|ser feliz) como cualquiera\b",
                
                # DIFERENCIAR HUMILDAD DE INDIGNIDAD
                r"\b(soy humilde|me cuesta aceptar cumplidos) pero (no porque no lo merezca|estoy bien)\b",
                r"\bno me siento indigno\b",
                r"\bagradezco la ayuda (sin sentirme mal|bien)\b",
                r"\bse que la gente me quiere y lo acepto\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Siente que merece ayuda o bienestar)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2D_2_unworthiness"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2D.3"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Indignidad detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2D_2_unworthiness"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2D.3" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2D.2"
                    return (phase, state, variant)
            
        elif state == "2D.3":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO GENERAL
                r"\bsi[,.]?\s*(he escuchado voces|visto cosas|me pasa eso|las oigo)\b",
                r"\bsi[,.]?\s*(oigo|escucho|veo) (cosas|voces|ruidos) (raros|extranos)\b",
                
                # ALUCINACIONES AUDITIVAS
                r"\b(oigo|escucho) voces que me (hablan|dicen cosas)\b",
                r"\b(escucho|oigo) (ruidos|susurros) que nadie (mas oye|escucha)\b",
                r"\b(oigo|escucho) mi nombre (cuando no hay nadie|estando solo|estando sola)\b",
                r"\bvoces en mi cabeza que no son mías\b",
                
                # ALUCINACIONES VISUALES
                r"\bveo (sombras|figuras|personas) (que no estan|que se mueven|extranas)\b",
                r"\bveo cosas que (otros|los demas) no (ven|notan)\b",
                r"\bhe visto (apariciones|fantasmas|gente)\b",
                
                # PERCEPCIONES DISCORDANTES / PRESENCIAS
                r"\bnoto (presencias|que hay alguien) (aunque no haya nadie|estando solo)\b",
                r"\bpercibo cosas que los demas no (notan|perciben)\b",
                r"\bla gente me dice que (no es real|me lo invento|no hay nada)\b",
                r"\blos demas dicen que no hay nada pero yo lo (veo|oigo)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|efectivamente|totalmente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca he escuchado|no he visto nada|no me pasa)\b",
                r"\bno (oigo|veo) nada (raro|extraño)\b",
                r"\bpara nada (me pasa eso|tengo visiones)\b",
                
                # DIFERENCIAR EXPERIENCIAS NORMALES (SUEÑO O ILUSIÓN)
                r"\bsolo (al dormirme|al despertarme|entre suenos)\b",
                r"\b(fue|parecia) una ilusion optica\b",
                r"\ba veces (creo oir|me parece oir) algo pero (luego veo que es real|es el viento)\b",
                r"\bes mi imaginacion (cuando estoy cansado|por el cansancio)\b",
                r"\bno estoy (loco|loca) ni veo cosas\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Sin síntomas psicóticos)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2D_3_psychotic_symptoms"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2D.4"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Presencia de alucinaciones)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2D_3_psychotic_symptoms"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2D.4" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2D.3"
                    return (phase, state, variant)
            
        elif state == "2D.4":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y AISLAMIENTO
                r"\bsi[,.]?\s*(paso mas tiempo solo|me estoy aislando|evito a la gente)\b",
                r"\bme (estoy aislando|estoy encerrando)\b",
                r"\b(prefiero|quiero) estar sol[oa]\b",
                r"\bno me apetece (ver a nadie|quedar con nadie)\b",
                r"\bme (encierro|quedo) en casa\b",
                r"\bno salgo (como antes|casi nunca|a ningun lado)\b",

                # EVITACIÓN DE CONTACTO / COMUNICACIÓN
                r"\bignoro (mensajes|llamadas|invitaciones|a mis amigos)\b",
                r"\bno (respondo|contesto) (llamadas|mensajes|whatsapp|invitaciones)\b",
                r"\bdejo (los mensajes|las llamadas) sin (contestar|responder)\b",
                r"\bpongo excusas para no (quedar|salir)\b",
                r"\bno (quiero|tengo ganas de) hablar con nadie\b",
                
                # PÉRDIDA DE INTERÉS O AGOBIO
                r"\bya no me interesa (salir|quedar)\b",
                r"\bme da (pereza|fatiga) el contacto social\b",
                r"\bla gente me (agobia|estresa|agota)\b",
                
                # CAMBIO RESPECTO AL PASADO
                r"\bantes (respondia|salia) mas\b",
                r"\bantes era (mas social|mas activo|mas activa)\b",
                r"\bhe perdido el contacto\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|asi es|es verdad|exacto|totalmente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(sigo quedando|respondo normalmente|no me he aislado)\b",
                r"\bno me he (aislado|encerrado)\b",
                r"\bsigo (viendo|quedando) con gente\b",
                r"\b(contesto|respondo) a (todo|todos)\b",
                
                # DIFERENCIAR SOLEDAD SANA / TRABAJO
                r"\bestoy (sol[oa]) porque (estoy ocupad[oa]|tengo mucho trabajo)\b",
                r"\bno es que me aisle, es que no tengo tiempo\b",
                r"\bdisfruto (de mi tiempo|estar solo) sin evitar a nadie\b",
                r"\bsigo siendo (social|activo|activa)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|no es mi caso)\b",
                r"\bno\b"
            ]
            
            # 1 - Negación (Mantiene vida social o soledad no patológica)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2D_4_social_withdrawal"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2D.5"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Aislamiento detectado)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2D_4_social_withdrawal"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2D.5" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2D.4"
                    return (phase, state, variant)
        
        elif state == "2D.5":
            
            PATTERNS_YES: list[str] = [
                # DIFICULTAD PARA ARRANCAR / PESADEZ
                r"\bsi[,.]?\s*(no puedo moverme|me quedo en la cama|me cuesta un mundo|me cuesta mucho)\b",
                r"\b(el despertador|la alarma) suena y (no puedo|no tengo fuerzas)\b",
                r"\bme quedo (horas |mucho tiempo )?en la cama sin (poder levantarme|fuerzas)\b",
                r"\bsiento que el cuerpo (me pesa toneladas|no me responde)\b",
                r"\bme cuesta (horrores|muchisimo) empezar el dia\b",
                
                # ABANDONO DE OBLIGACIONES / RENDIMIENTO
                r"\bhe (faltado|dejado de ir) (al trabajo|a clase|al curro)\b",
                r"\bestoy (a punto de perder|por perder) el (empleo|trabajo|curro)\b",
                r"\bno (rindo|estoy rindiendo|puedo producir)\b",
                r"\bno soy capaz de concentrarme (en lo que estudio|en el trabajo)\b",
                r"\bhe descuidado mis obligaciones\b",
                
                # FALTA DE MOTIVACIÓN / MODO ROBOT
                r"\bme levanto porque (no me queda otra|tengo que) pero (no tengo ganas|sin energia)\b",
                r"\bvoy como un robot\b",
                r"\bhago lo minimo\b",
                r"\bno me da la vida (para mas|para trabajar)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|me pasa|totalmente)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # FUNCIONALIDAD PRESERVADA
                r"\bno[,.]?\s*(me levanto y voy bien|cumplo con todo|estoy bien en eso)\b",
                r"\bme cuesta lo normal (pero cumplo|para todo el mundo)\b",
                r"\bsigo con (mi ritmo|mis tareas) (de siempre|normal)\b",
                r"\btengo (energia|fuerzas) para (mis cosas|mis tareas|trabajar)\b",
                r"\bno he notado que me cueste mas de lo normal\b",
                
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(en ese aspecto|en eso) (estoy bien|no noto nada)\b",
                r"\bpara nada[,.]?\s*sigo activo\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|que va|todo normal|ninguno)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Funcionalidad preservada)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2D_5_functional_impairment"
                value = False
                db.add_user_info(telephone, key, value)
                
                # Mirar las otras respuestas de 2D
                d1 = db.get_user_info(telephone, "DEP_EVAL", "2D.1")
                d2 = db.get_user_info(telephone, "DEP_EVAL", "2D.2")
                d3 = db.get_user_info(telephone, "DEP_EVAL", "2D.3")
                d4 = db.get_user_info(telephone, "DEP_EVAL", "2D.4")
                results = [d1, d2, d3, d4]
                
                if sum(1 for x in results if x) >= 1:
                    phase, state = "DEP_EVAL", "3A"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    phase, state = "DEP_EVAL", "2E.1"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Afectación funcional detectada)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2D_5_functional_impairment"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "3A"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2D.5"
                    return (phase, state, variant)
        
        elif state == "2E.1":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y CONFIRMACIÓN
                r"\bsi[,.]?\s*(me han diagnosticado|tengo un diagnostico|me lo dijeron)\b",
                r"\bsi[,.]?\s*(el medico|el psiquiatra|el psicologo) me lo (confirmo|dijo)\b",
                
                # DIAGNÓSTICO FORMAL (DEPRESIÓN)
                r"\bme diagnosticaron (depresion|trastorno)\b",
                r"\b(tengo|padezco) depresion mayor\b",
                r"\bme dijeron que tenia (depresion|distimia|trastorno del animo)\b",
                r"\bhe tenido episodios (depresivos|de depresion) diagnosticados\b",
                
                # DIAGNÓSTICO DE OTROS TRASTORNOS DEL ÁNIMO
                r"\bme diagnosticaron (trastorno bipolar|bipolaridad)\b",
                r"\bme dijeron que (era|tengo) bipolar\b",
                r"\btrastorno del estado de animo\b",
                
                # TRATAMIENTO PREVIO (INDICADOR DE DIAGNÓSTICO)
                r"\bhe estado en tratamiento (por|de) depresion\b",
                r"\b(tome|estoy tomando) antidepresivos\b",
                r"\bhe ido al (psicologo|psiquiatra) por (depresion|esto)\b",
                r"\bme han (medicado|recetado algo) para la depresion\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|asi es|exacto|efectivamente|si me lo dijeron)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca me han diagnosticado|no tengo diagnostico|no me han dicho nada)\b",
                r"\bno[,.]?\s*(nunca he ido|no he visitado) al (psicologo|psiquiatra|medico)\b",
                r"\bnadie me ha (diagnosticado|dicho nada)\b",
                
                # DIFERENCIAR SENTIMIENTO DE DIAGNÓSTICO (FILTRO CLAVE)
                r"\bme (he sentido|siento) deprimido pero nunca (fui a un profesional|me diagnosticaron)\b",
                r"\bcreo que (he tenido|tengo) depresion pero (no es oficial|nadie me lo ha dicho)\b",
                r"\bnunca me lo (confirmaron|dijeron formalmente)\b",
                r"\bhe estado mal pero sin ir al medico\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca|no es mi caso)\b",
                r"\bno\b"
            ]
            # 1 - Negación (Sin antecedentes profesionales confirmados)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2E_1_prior_diagnosis"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2E.2"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Antecedentes confirmados)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2E_1_prior_diagnosis"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2E.2" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2E.1"
                    return (phase, state, variant)
        
        elif state == "2E.2":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO Y GENÉRICOS
                r"\bsi[,.]?\s*(he tomado medicacion|tome pastillas|me recetaron algo)\b",
                r"\bsi[,.]?\s*(tome|tomaba|he tomado) (antidepresivos|ansioliticos|somniferos|tranquilizantes)\b",
                r"\bme recetaron algo para (los nervios|dormir|el animo|descansar)\b",
                
                # ANTIDEPRESIVOS (Nombres comunes)
                r"\b(tome|estuve con) (prozac|sertralina|escitalopram|fluoxetina|paroxetina|venlafaxina)\b",
                r"\bpastillas para (la depresion|el animo)\b",
                
                # ANSIOLÍTICOS / NERVIOS (Nombres comunes)
                r"\b(tome|tomaba) (diazepam|lorazepam|alprazolam|trankimazin|lexatin|orfidal)\b",
                r"\bpastillas para (los nervios|la ansiedad)\b",
                
                # MEDICACIÓN PARA DORMIR
                r"\b(tome|me dieron) (zolpidem|lormetazepam|noctamid|somniferos)\b",
                r"\balgo para (el insomnio|poder dormir)\b",
                
                # REFERENCIAS PSIQUIÁTRICAS
                r"\bhe estado medicad[oa]\b",
                r"\btome algo que me receto el (psiquiatra|medico)\b",
                r"\btratamiento farmacologico\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|asi es|exacto|varias veces|durante un tiempo)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca he tomado nada|no he tomado medicacion|no me han recetado nada)\b",
                r"\bnunca me han dado pastillas (para eso|asi)\b",
                r"\bno tomo (psicofarmacos|medicamentos)\b",
                
                # DIFERENCIAR AUTOMEDICACIÓN O NATURAL
                r"\btome (cosas por mi cuenta|hierbas|valeriana) pero no (recetadas|medico)\b",
                r"\b(solo |tome )?melatonina\b",
                r"\bsolo medicacion para (el dolor|otras cosas|temas fisicos)\b",
                r"\bno es mi caso\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Sin antecedentes de medicación psiquiátrica)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2E_2_prior_medication"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "2E.3" 
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Antecedentes de medicación detectados)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2E_2_prior_medication"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "2E.3" 
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2E.2"
                    return (phase, state, variant)
        
        elif state == "2E.3":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO GENERAL
                r"\bsi[,.]?\s*(he estado ingresad[oa]|me ingresaron|estuve en un centro)\b",
                r"\bme tuvieron que ingresar\b",
                r"\bestuve ingresad[oa] (varios dias|semanas|un tiempo)\b",
                
                # INGRESO PSIQUIÁTRICO / SALUD MENTAL
                r"\bestuve en el (hospital psiquiatrico|psiquiatrico)\b",
                r"\bme ingresaron en (psiquiatria|salud mental)\b",
                r"\bpase tiempo en una (clinica mental|clinica psiquiatrica)\b",
                r"\bestuve hospitalizad[oa] por (mi estado de animo|depresion|ansiedad|salud mental)\b",
                
                # URGENCIAS Y UNIDADES ESPECÍFICAS
                r"\bestuve en urgencias y me (dejaron|quede) ingresad[oa]\b",
                r"\bestuve en la unidad de agudos\b",
                r"\bme ingresaron en una unidad de (salud mental|agudos)\b",
                r"\bcentro (especializado|de reposo)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|asi es|exacto|efectivamente|si estuve)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(nunca he estado ingresad[oa]|no he necesitado hospitalizacion|nunca me han ingresado)\b",
                r"\bno he pisado un psiquiatrico\b",
                r"\bnunca he llegado a ese (punto|extremo)\b",
                
                # DIFERENCIAR OTROS INGRESOS / URGENCIAS SIN INGRESO
                r"\bhe estado en el hospital pero (por otras cosas|por temas fisicos|no por mi estado)\b",
                r"\bestuve ingresad[oa] por una (operacion|enfermedad) pero no por salud mental\b",
                r"\bfui a urgencias pero no me ingresaron\b",
                r"\bme dieron el alta (el mismo dia|enseguida)\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca|no es mi caso)\b",
                r"\bno\b"
            ]
            
            # 1 - Negación (Sin antecedentes de ingreso psiquiátrico)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.2E_3_prior_hospitalization"
                value = False
                db.add_user_info(telephone, key, value)
                
                # Mirar las otras respuestas de 2E
                e1 = db.get_user_info(telephone, "DEP_EVAL", "2E.1")
                e2 = db.get_user_info(telephone, "DEP_EVAL", "2E.2")
                results = [e1, e2]
                
                if sum(1 for x in results if x) >= 1:
                    phase, state = "DEP_EVAL", "3A"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    phase, state = "CHAT", ""    # seria OTR
                    db.save_flow(telephone, phase, state)
                    key = "SCREENING.DEP"
                    value = "others"
                    db.add_user_info(telephone, key, value)
                    return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Antecedentes de ingreso detectados)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.2E_3_prior_hospitalization"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "3A"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "2E.3"
                    return (phase, state, variant)
        
        elif state == "3A":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO GENERAL Y FRECUENCIA
                r"\bsi[,.]?\s*(bebo|tomo|consumo) (alcohol|habitualmente|con frecuencia|bastante)\b",
                r"\b(bebo|tomo) (casi )?todos los dias\b",
                r"\btomo algo (todas las noches|a diario)\b",
                r"\bsuelo beber a menudo\b",
                r"\b(es parte de mi rutina|es mi costumbre)\b",
                
                # CANTIDAD / TIPO DE BEBIDA REGULAR
                r"\b(bebo|me tomo) varias (copas|cervezas|latas) al dia\b",
                r"\b(tomo|bebo) (cerveza|vino|licor|cubatas) con regularidad\b",
                
                # USO COMO ESTRATEGIA DE AFRONTAMIENTO (AUTOMEDICACIÓN)
                r"\b(necesito|tengo que) beber para (relajarme|dormir|calmarme|desconectar)\b",
                r"\bbebo cuando me siento mal\b",
                r"\bel alcohol me ayuda a (sobrellevar|aguantar|olvidar)\b",
                r"\bbebo para olvidarme de (los problemas|todo)\b",
                
                # DEPENDENCIA / PREOCUPACIÓN
                r"\bcreo que bebo demasiado\b",
                r"\bme preocupa cuanto bebo\b",
                r"\bno puedo (pasar|estar) sin beber\b",
                r"\bhe intentado dejarlo pero no puedo\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|asi es|exacto|bastante|a diario|todos los dias)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA Y ABSTINENCIA
                r"\bno[,.]?\s*(no bebo|no tomo alcohol|rara vez|casi nunca)\b",
                r"\bno bebo nada\b",
                r"\bdeje de beber\b",
                r"\bno consumo alcohol\b",
                r"\bsoy (abstemio|abstemia)\b",
                r"\bno me gusta el alcohol\b",
                
                # CONSUMO OCASIONAL / SOCIAL NO PROBLEMÁTICO
                r"\bbebo (de vez en cuando|muy de vez en cuando|poco)\b",
                r"\ben (ocasiones|eventos|fiestas) especiales\b",
                r"\bsolo (bebo )?(socialmente|los fines de semana|esporadicamente)\b",
                r"\btomo (una cerveza|algo) (de vez en cuando|a veces) pero no es habitual\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca|cero|nada)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (Abstemio o bebedor social ocasional)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.3A_concurrent_alcohol"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "DEP_EVAL", "3B"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Consumo de alcohol habitual o problemático)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.3A_concurrent_alcohol"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_EVAL", "3B"
                    db.save_flow(telephone, phase, state) 
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "3A"
                    return (phase, state, variant)
        
        elif state == "3B":
            
            PATTERNS_YES: list[str] = [
                # AUTO-RECONOCIMIENTO GENERAL
                r"\bsi[,.]?\s*(consumo|tomo|uso) (sustancias|drogas|estupefacientes)\b",
                r"\b(tomo|consumo) de vez en cuando\b",
                
                # CANNABIS (Muy común en contexto de ansiedad/insomnio)
                r"\b(fumo|consumo) (porros|marihuana|hachis|hierba|cannabis|weed)\b",
                r"\bme fumo (algo|un porro) para (relajarme|dormir)\b",
                
                # COCAÍNA Y ESTIMULANTES
                r"\b(consumo|tomo|uso) (cocaina|coca|rayas|nieve|farlopa)\b",
                r"\b(tomo|uso) (speed|anfetaminas|estimulantes|pastis|pastillas para activarme)\b",
                
                # OTRAS SUSTANCIAS (MDMA, Psicodélicos, Opiáceos)
                r"\b(consumo|tomo) (extasis|mdma|m|ketamina|keta|lsd|tripi|setas|alucinogenos)\b",
                r"\b(tomo|uso) (opiaceos|heroina|caballo)\b",
                
                # USO COMO AFRONTAMIENTO
                r"\b(consumo|tomo) para (sentirme mejor|aguantar|olvidar|evadirme)\b",
                r"\buso sustancias cuando (estoy mal|estoy bajo)\b",
                r"\bme ayuda a (sobrellevar|aguantar|pasar el dia)\b",
                
                # RECONOCIMIENTO DE DEPENDENCIA
                r"\bcreo que (consumo|tomo) demasiado\b",
                r"\bno puedo dejarlo\b",
                r"\bdependo de (ello|eso)\b",

                # RESPUESTAS AFIRMATIVAS BREVES
                r"^(si|exacto|asi es|algunas cosas|varias)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA Y ABSTINENCIA
                r"\bno[,.]?\s*(no consumo|no tomo|nada de eso|ni hablar)\b",
                r"\bno (tomo|consumo) (drogas|sustancias)\b",
                r"\bno (consumo|tomo) nada\b",
                r"\bsoy (limpio|limpia)\b",
                
                # CONSUMO PASADO (Importante para el protocolo actual)
                r"\blo (probe|use) (alguna vez|hace tiempo) pero ya no\b",
                r"\b(ya )?deje de (consumir|tomar)\b",
                r"\b(ya )?no (tomo|consumo) (sustancias|nada)\b",
                r"\bestoy rehabilitado\b",

                # RESPUESTAS BREVES
                r"^(no|para nada|en absoluto|que va|nunca|no es mi caso)$",
                r"\bno\b"
            ]
            
            # 1 - Negación (No consume o consumo pasado finalizado)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.3B_concurrent_substances"
                value = False
                db.add_user_info(telephone, key, value)

                phase, state = "DEP_PROTOCOLS", "1"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Consumo actual detectado)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.3B_concurrent_substances"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "DEP_PROTOCOLS", "1"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "DEP_EVAL", "3B"
                    return (phase, state, variant)
            
            
    elif phase == "SUI_EVAL":
        if state == "1":
            PATTERNS_YES: list[str] = [
                # PASTILLAS / SOBREDOSIS
                r"\btome (muchas )?pastillas\b",
                r"\btome (el bote( entero)?|toda la caja|todo el frasco)\b",
                r"\bme tome todo el frasco\b",
                r"\bpastillas de mas\b",
                r"\bmedicacion de mas\b",
                r"\btome demasiado\b",
                r"\bsobredosis\b",
                r"\bme pase con (las )?pastillas\b",
                r"\bacabo de tomar\b",
                r"\bhace un rato tome\b",

                # CORTES / HERIDAS
                r"\bme (he )?cort[eo]\b",
                r"\bme (he )?cortado\b",
                r"\bme cort[eo] (las )?venas\b",
                r"\bme hice cortes\b",
                r"\btengo cortes\b",
                r"\bvenas cortadas\b",
                r"\bme hice un corte\b",
                r"\bcorte profundo\b",
                r"\bsangro por cortes\b",
                r"\bme (he )?(herido?|lastimado?)\b",
                r"\bheridas?\b",
                r"\bme hice dano\b",
                r"\bhoy me cort[eo]\b",

                # SANGRADO
                r"\bestoy sangrando\b",
                r"\bsangro mucho\b",
                r"\bno para de sangrar\b",
                r"\bsangre por todos lados\b",
                r"\bestoy perdiendo sangre\b",
                r"\bsangro\b",

                # QUEMADURAS / VENENO
                r"\bme (he )?quem[eo]\b",
                r"\bquemaduras?\b",
                r"\bme puse fuego\b",
                r"\b(ingeri|trague|tome) (lejia|veneno|algo toxico|una sustancia quimica|producto (de )?limpieza|matarratas)\b",
                r"\btome algo (toxico|peligroso|que hace dano)\b",
            ]

            PATTERNS_NO: list[str] = [
                # Negación directa de daño
                r"\bno me he hecho (dano( todavia| aun)?|nada( fisico)?|danado|lastimado|lesionado)\b",
                r"\bno me he danado\b",
                r"\bno ha pasado nada( fisico)?\b",
                r"\bno se me\b"

                # Estado físico correcto
                r"\bestoy (bien fisicamente|fisicamente bien)\b",
                r"\bfisicamente estoy bien\b",
                r"\bmi cuerpo esta bien\b",
                r"\bno tengo (nada|ningun problema) fisico\b",
                r"\bno me pasa nada fisico\b",
                r"\bestoy bien\b",

                # No ha tomado nada
                r"\bno he tomado (nada|pastillas|medicacion de mas|nada raro|nada (que haga dano|peligroso))\b",

                # Solo pensamientos
                r"\b(no[,.]?\s*)?solo (son pensamientos|lo he pensado|lo pienso)\b",
                r"\bno he hecho nada[,.]?\s*solo lo pienso\b",
                r"\bno he llegado a hacerlo\b",
                r"\bno he hecho nada fisico\b",

                # Negaciones breves
                r"\bno me he hecho\b",
                r"\bno he hecho nada\b",
            ]
            
            # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.1_self_harm"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "SUI_EVAL", "2A"
                return (phase, state, variant)
            
            else:
                # 2 - Self harm detected
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "SUI_EVAL.1_self_harm"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "SUI_PROTOCOLS", "1"
                    key = "SCREENING.SUI"
                    value = "self_harm"
                    db.add_user_info(telephone, key, value)
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = _variant_search(n_user_input)
                    phase = "SUI_EVAL", "1"
                    return (phase, state, variant)
        
        elif state == "2A":
            
            PATTERNS_CONCRETE_PLANS: list[str] = [
                r"\btengo un plan\b",
                r"\bse como lo voy a hacer\b",
                r"\btengo todo planeado\b",
                r"\bya tengo mi plan\b",
                r"\bvoy a tomar (todas las |el bote entero de )?pastillas\b",
                r"\btengo pastillas guardadas\b",
                r"\bbote entero\b",
                r"\bvoy a saltar\b",
                r"\bvoy a tirarme del (puente|balcon|ventana)\b",
                r"\btengo una cuerda\b",
                r"\bvoy a colgarme\b",
                r"\bvoy a cortarme las venas\b",
                r"\btengo un cuchillo preparado\b",
                r"\bvoy a ingerir (veneno|lejia|algo toxico)\b",
                r"\btengo el método listo\b",
                r"\bvoy a hacerlo con pastillas y alcohol\b",
                r"\bmi plan es\b",
                r"\bya decidi como\b",
                r"\btengo las cosas preparadas\b",
                r"\blo voy a hacer (este fin de semana|manana|hoy)\b",
                r"\bme voy a matar ahora\b",
            ]
            
            PATTERNS_IDEATION: list[str] = [
                r"\bsi[,.]?\s*(he tenido|he pensado en ello|en los ultimos dias|ahora mismo)\b",
                r"\b(he tenido|he pensado en ello|en los ultimos dias|ahora mismo)\b",
                r"\bpienso en (quitarme la vida|suicidarme|hacerme dano|ello|(?:acabar|terminar) con todo)\b",
                r"\bestoy pensando en matarme\b",
                r"\bquiero morir\b",
                r"\btengo ganas de morir\b",
                r"\bno quiero seguir viviendo\b",
                r"\bojala me muriera?\b",
                r"\bmejor me muero\b",
                r"\bquiero desaparecer\b",
                r"\bno aguanto más esta vida\b",
                r"\btengo pensamientos suicidas\b",
                r"\bideacion suicida\b",
                r"\bpensamientos de (muerte|autolesion)\b",
                r"\bhe pensado en acabar con todo\b",
                r"\bno quiero vivir mas\b",
                r"\bla vida no vale la pena\b",
                r"\bestoy cansado de vivir\b",
                r"\bsolo pienso en morir\b",
                r"\bme paso el dia pensando en morirme\b",
                r"\b(si[,.]?\s*)?(ultimamente|en los ultimos dias|hace poco|recientemente)\s*si\b",
                r"\bvoy a hacerlo ahora\b",
                r"\blo voy a hacer hoy\b",
                r"\bya no puedo mas[,.]?\s*lo hago ya\b",
                r"\bestoy a punto de hacerlo\b",
                r"\ben este momento lo estoy pensando seriamente\b",
                r"\btengo la intención de hacerlo\b",
                r"\bestoy decidida?[,.]?\b",
                r"\bno voy a esperar mas\b",
                r"\besto se acaba hoy\b",
                r"\bya no aguanto[,.]?\s*me despido\b",
                r"\bojalsa (me durmiera? y no despertara?|no hubiera nacido|no existiera)\b",
                r"\bno le importaria a nadie (si me muriera?|que desapareciera?)\b",
                r"\btodo seria mejor sin mi\b",
                r"\bseria mejor desaparecer\b",
                r"\bno tiene sentido seguir (viviendo|adelante)\b",
            ]
            
            PATTERNS_NO: list[str] = [
                # Negaciones directas y breves
                r"^\s*no[,.]?\s*$",
                r"\bno[,.]?\s*he tenido\b",
                r"\bnunca\b",
                r"\bno ahora\b",
                r"\bno en este momento\b",
                r"\bno ultimamente\b",
                r"\bno en los ultimos dias\b",
                r"\bno recientemente\b",
                r"\bno me ha pasado por la cabeza\b",
                r"\bno pienso en eso\b",
                r"\bno se me ha ocurrido\b",
                r"\bnada de eso\b",
                r"\bno tengo pensamientos asi\b",
                r"\bno estoy pensando en nada parecido\b",
                r"\bno tengo nada parecido\b",
                
                # Negaciones explícitas
                r"\bno he pensado en suicidarme\b",
                r"\bnunca he pensado en quitarme la vida\b",
                r"\bno tengo pensamientos suicidas\b",
                r"\bno he tenido ideación suicida\b",
                r"\bno deseo morir\b",
                r"\bno quiero morir\b",
                r"\bno quiero acabar con mi vida\b",
                r"\bno me quiero suicidar\b",
                r"\bno tengo ganas de morir\b",
                r"\bno pienso en matarme\b",
                r"\bno he considerado hacerme dano\b",
                r"\bno he pensado en autolesionarme\b",
                r"\bno tengo ideas de muerte\b",
                r"\bno contemplo quitarme la vida\b",
                r"\bno está en mis pensamientos\b",
                
                # Emociones negativas sin ideación
                r"\bsolo estoy triste pero no quiero morir\b",
                r"\bestoy muy mal pero no pienso en suicidarme\b",
                r"\bme siento desesperado pero no quiero quitarme la vida\b",
                r"\btengo pensamientos negativos pero no de muerte\b",
                r"\bestoy harto de todo pero no al punto de suicidarme\b",
                r"\bme siento vacío pero no quiero morir\b",
                r"\bestoy sufriendo pero quiero vivir\b",
                r"\bquiero salir de esto[,.]?\s*no morir\b",
                r"\bestoy mal pero no hasta ese extremo\b",
                
                # Pensamientos antiguos
                r"\bsolo pensamientos muy antiguos\b",
                r"\bhace mucho tiempo (si|pense en eso)[,.]?\s*pero ahora no\b",
                r"\bantes si[,.]?\s*pero (ya no|ahora no)\b",
                r"\ben el pasado lejano\b",
                r"\bhace anos que no pienso en eso\b",
                r"\bsolo cuando era mas joven[,.]?\s*ahora no\b",
                r"\bnunca en los ultimos tiempos\b",
                r"\bhace meses que no pienso en eso\b",
                
                # Sin plan / intención
                r"\bno tengo (ningun )?plan(es)? (para eso)?\b",
                r"\bno tengo intención de hacerlo\b",
                r"\bno lo haria nunca\b",
                r"\baunque me sienta mal[,.]?\s*nunca lo haria\b",
                r"\bno me atreveria\b",
                r"\bme da miedo solo pensarlo\b",
                r"\bno tengo (medios ni ganas|nada preparado)\b",
                
                # Otras negaciones contextuales
                r"\bestoy bien en ese sentido\b",
                r"\bno estoy en ese punto\b",
                r"\bno es mi caso\b",
                r"\btengo (razones|familia|hijos|motivos) para (seguir|no hacerlo)\b",
                r"\bno gracias a dios no\b",
                r"\bpor suerte no he llegado a eso\b",
                r"\bno he llegado a esos pensamientos\b",
                r"\bno me ronda por la cabeza\b",
                r"\bestoy de bajón pero quiero seguir\b",
                r"\bnada relacionado con suicidarme\b",
            ]
            
            # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.2_A_active_ideation"
                value = "no"
                db.add_user_info(telephone, key, value)
                
                phase, state = "SUI_EVAL", "2B.1"
                return (phase, state, variant)
        
            else:
                # 2 - Concrete plans
                match_plan = _pattern_search(n_user_input, PATTERNS_CONCRETE_PLANS)
                if match_plan:
                    key = "SUI_EVAL.2_A_active_ideation"
                    value = "concrete_plan"
                    db.add_user_info(telephone, key, value)
                    key = "SCREENING.SUI"
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "SUI_PROTOCOLS", "2"
                    return (phase, state, variant) 
                
                else:
                    # 3 - Ideation
                    match_ideation = _pattern_search(n_user_input, PATTERNS_IDEATION)
                    if match_ideation:
                        key = "SUI_EVAL.2_A_active_ideation"
                        value = "ideation"
                        db.add_user_info(telephone, key, value)
                        key = "SCREENING.SUI"
                        db.add_user_info(telephone, key, value)
                        
                        phase, state = "SUI_PROTOCOLS", "2"
                        return (phase, state, variant)
                    
                    # 4 - Variant activation
                    else:
                        variant = _variant_search(n_user_input)
                        phase, state = "SUI_EVAL", "2A"
                        return (phase, state, variant)
                
        elif state == "2B.1":
            
            PATTERNS_IDEATION: list[str] = [
                # Afirmaciones directas
                r"\bsi\b",
                r"\bsi[,.]?\s*(he tenido|he pensado|tuve|pense)\b",
                r"\bhe tenido pensamientos\b",
                r"\bhe pensado en (ello|esto|morir|suicidarme|quitarme la vida|hacerme dano)\b",
                r"\bhe tenido ganas de morir\b",
                r"\bhe querido morir\b",
                r"\bhe pensado en desaparecer\b",
                r"\bhe tenido ideas de muerte\b",
                r"\bpensamientos suicidas\b",
                r"\bideacion suicida\b",
                r"\bme ha pasado por la cabeza\b",
                r"\blo he pensado\b",
                r"\bhe tenido esos pensamientos\b",
                r"\balgunas veces si\b",
                r"\bultimamente si\b",
                r"\beste mes si\b",
                r"\bsi el ultimo mes\b",
                r"\bsi recientemente\b",
                r"\bsi hace poco\b",
                r"\bsi en los ultimos dias\b",
                r"\bsi esta semana\b",
                r"\bhe pensado en acabar con todo\b",
                r"\bhe tenido pensamientos de autolesion\b",
                r"\bhe pensado en hacerme dano\b",
                r"\bhe querido hacerme dano\b",
                r"\bhe tenido deseos de morir\b",
                r"\bno queria seguir viviendo\b",
                r"\bqueria desaparecer\b",
                r"\bpense en matarme\b",
                r"\bpense en suicidarme\b",
                r"\bpense en quitarme la vida\b",
            ]

            PATTERNS_PLAN: list[str] = [
                # Plan concreto en el pasado reciente
                r"\btengo un plan\b",
                r"\btuve un plan\b",
                r"\bhe tenido un plan\b",
                r"\bpense en como hacerlo\b",
                r"\bpense en el metodo\b",
                r"\btenia pensado como\b",
                r"\bhabia pensado en (pastillas|cortarme|tirarme|colgarme|veneno|lejia|matarratas)\b",
                r"\bpense en tomar pastillas\b",
                r"\bpense en cortarme (las venas)?\b",
                r"\bpense en tirarme (del puente|del balcon|de la ventana|al tren|al metro)\b",
                r"\bpense en colgarme\b",
                r"\bpense en usar (una cuerda|un cuchillo|un arma)\b",
                r"\btenia las cosas (preparadas|listas)\b",
                r"\bhabia preparado (algo|todo|el metodo)\b",
                r"\btenia pastillas guardadas\b",
                r"\bguarde pastillas\b",
                r"\bya sabia como (lo iba a hacer|hacerlo)\b",
                r"\bestaba decidid[ao]\b",
                r"\btenia todo (pensado|planeado|preparado)\b",
                r"\bel plan era\b",
                r"\bmi plan era\b",
                r"\biba a hacerlo\b",
                r"\biba a (matarme|suicidarme|quitarme la vida|hacerme dano)\b",
                r"\bestuve a punto de hacerlo\b",
                r"\bllegu[eé] a intentarlo\b",
                r"\blo intente\b",
                r"\bintente (suicidarme|matarme|quitarme la vida|hacerme dano)\b",
            ]

            PATTERNS_NO: list[str] = [
                # Negaciones directas
                r"\bno\b",
                r"\bnunca\b",
                r"\bno he tenido\b",
                r"\bno he pensado (en eso|en ello|en nada de eso)\b",
                r"\bno me ha pasado por la cabeza\b",
                r"\bnada de eso\b",
                r"\bno he tenido pensamientos (asi|de ese tipo|suicidas|de muerte|de autolesion)\b",
                r"\bno he tenido nada de eso\b",
                r"\bno en el ultimo mes\b",
                r"\bno recientemente\b",
                r"\bno este mes\b",
                r"\bno en estos dias\b",
                r"\bno ultimamente\b",
                r"\bno en los ultimos tiempos\b",
                # Pensamientos muy lejanos
                r"\bfue hace mucho\b",
                r"\bhace mucho tiempo\b",
                r"\bfue hace (meses|anos|tiempo)\b",
                r"\bya no (pienso en eso|tengo esos pensamientos)\b",
                r"\beso fue antes\b",
                r"\ben otra epoca\b",
                r"\bno en este periodo\b",
                # Emociones sin ideación
                r"\bmal pero no al punto de\b",
                r"\btriste pero no pienso en (morir|suicidarme|hacerme dano)\b",
                r"\bno he querido (morir|hacerme dano|quitarme la vida)\b",
                r"\bno he deseado morir\b",
                r"\bquiero seguir viviendo\b",
                r"\btengo ganas de vivir\b",
            ]
            
            # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.2_B1_last_month_ideation"
                value = "no"
                db.add_user_info(telephone, key, value)
                               
                phase, state = "SUI_EVAL", "2B.2"
                return (phase, state, variant)
        
            else:
                # 2 - Concrete plans
                match_plan = _pattern_search(n_user_input, PATTERNS_PLAN)
                if match_plan:
                    key = "SUI_EVAL.2_B1_last_month_ideation"
                    value = "concrete_plan"
                    db.add_user_info(telephone, key, value)
                    key = "SCREENING.SUI"
                    value = "improbable"
                    db.add_user_info(telephone, key, value)
                                        
                    phase, state = "SUI_PROTOCOLS", "3"
                    return (phase, state, variant) 
                
                else:
                    # 3 - Ideation
                    match_ideation = _pattern_search(n_user_input, PATTERNS_IDEATION)
                    if match_ideation:
                        key = "SUI_EVAL.2_B1_last_month_ideation"
                        value = "ideation"
                        db.add_user_info(telephone, key, value)
                        key = "SCREENING.SUI"
                        value = "improbable"
                        db.add_user_info(telephone, key, value)
                                                
                        phase, state = "SUI_PROTOCOLS", "3"
                        return (phase, state, variant)
                    
                    # 4 - Variant activation
                    else:
                        variant = _variant_search(n_user_input)
                        phase, state = "SUI_EVAL", "2B.1"
                        return (phase, state, variant)
        
        elif state == "2B.2":
            
            PATTERNS_YES: list[str] = [
                # CONFIRMACIÓN GENERAL
                r"\bsi[,.]?\s*me (he hecho|hice) dano (a proposito|a posta|con intencion)\b",
                r"\bsi[,.]?\s*me (he )?autolesionado\b",
                r"\bsi[,.]?\s*(he tenido|tuve) un intento\b",
                r"\bsi[,.]?\s*intent[eo] suicidarme\b",
                r"\bsi[,.]?\s*tuve un intento de suicidio\b",
                r"\bsi[,.]?\s*lo intent[eo] hace poco\b",
                r"\bsi[,.]?\s*(el ano pasado|hace unos meses) lo intent[eo]\b",
                r"\bsi[,.]?\s*me hice dano a posta\b",
                r"\bfue a proposito\b",
                r"\bsi[,.]?\s*he (tenido|repetido) (episodios de )?autolesion(es)? este ano\b",

                # CORTES / HERIDAS
                r"\bme (hice|he hecho) cortes( a proposito| profundos| en (los brazos|las munecas|las venas))?\b",
                r"\bme (he )?cort[eo]( a proposito| las venas| las munecas)?\b",
                r"\bme (hice|he hecho) (muchos cortes|heridas)\b",
                r"\bme (heri|lesione) a proposito\b",
                r"\bme abri la piel con intencion\b",
                r"\bme raje los brazos\b",

                # QUEMADURAS
                r"\bme (he )?quem[eo]( a proposito)?\b",
                r"\bme (hice|he hecho) quemaduras\b",
                r"\bme apague cigarrillos en la piel\b",
                r"\bme (hice|he hecho) marcas con fuego\b",

                # GOLPES / TRAUMAS INTENCIONALES
                r"\bme golpe[eo] (fuerte|la cabeza|contra la pared)( a proposito)?\b",
                r"\bme di golpes contra la pared\b",
                r"\bme tire al suelo para hacerme dano\b",
                r"\bme pegue punetazos\b",

                # PASTILLAS / SOBREDOSIS
                r"\btome (muchas|un monton de) pastillas\b",
                r"\bme tome (todo el bote|toda la caja( de pastillas)?)\b",
                r"\bhice una sobredosis\b",
                r"\bme pase con las pastillas a proposito\b",
                r"\bmezclé pastillas y alcohol para hacerme dano\b",
                r"\bme intoxique a proposito\b",

                # VENENOS / SUSTANCIAS TOXICAS
                r"\b(bebi|tome|ingeri) (lejia|veneno|algo toxico|productos? de limpieza|matarratas|sustancias? quimicas?)\b",
                r"\b(bebi|tome|ingeri) (algo|una sustancia) (toxico|peligroso|para hacerme dano)\b",

                # MÉTODOS LETALES
                r"\bintent[eo] (ahogarme|colgarme|ahorcarme)\b",
                r"\bme ate una cuerda al cuello\b",
                r"\bintent[eo] tirarme (a las vias|del balcon|por la ventana|de un sitio alto)\b",
                r"\bme subi a un sitio alto para tirarme\b",

                # PLAN EJECUTADO
                r"\bllegue a hacerlo\b",
                r"\blleve a cabo (mi )?plan\b",
                r"\bejecute el plan\b",
                r"\bpase de pensarlo a hacerlo\b",
                r"\bno solo lo pense[,.]?\s*(lo llegue a hacer|lo hice)\b",

                # CONSECUENCIAS MÉDICAS
                r"\bacabe en urgencias (por hacerme dano|por autolesion|por un intento)\b",
                r"\bme ingresaron por (un intento|autolesion)\b",
                r"\bestuve hospitalizado por (autolesion|un intento)\b",
                r"\bme tuvieron que curar (los cortes|las heridas) en urgencias\b",

                # MARCO TEMPORAL CLARO
                r"\bhace (poco|unas semanas|unos meses) me (hice dano|autolesione|hice cortes)\b",
                r"\b(en este ultimo ano|dentro de este ano|este ano) (si )?(me he hecho dano|tuve un intento|paso)\b",

                # AUTOLESIÓN SIN INTENCIÓN DE MORIR
                r"\bme autolesiono cuando estoy mal\b",
                r"\bcuando exploto me hago dano\b",
                r"\bhe tenido (varios )?episodios (de autolesion )?este ano\b",
                r"\baunque no queria morir[,.]?\s*me lesione (queriendo hacerme dano|a proposito)\b",
            ]

            PATTERNS_NO: list[str] = [
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(no me he hecho dano|no me he autolesionado)\b",
                r"\bno he tenido ningun intento\b",
                r"\bno he intentado (suicidarme|hacerme dano)\b",
                r"\bno ha habido (autolesiones|actos|ningun intento) (este ano|reciente(s)?)\b",
                r"\bno ha pasado nada (este ano|fisico)\b",
                r"\b(en este ultimo ano|dentro de este ano|en los ultimos doce meses) no\b",
                r"\bno he llegado a (hacer nada|pasar de pensarlo a hacerlo)\b",
                r"\bno he hecho nada(?: (fisico|contra mi cuerpo))?\b",
                r"\bno ha habido actos[,.]?\s*solo pensamientos\b",

                # AUTOLESIÓN MUY ANTIGUA
                r"\bsolo fue hace (muchos anos|mucho tiempo)\b",
                r"\bhace anos (si[,.]?\s*)?pero (ahora|en este ultimo ano) no\b",
                r"\bcuando era mas joven (si[,.]?\s*)?pero (en este ultimo ano|ahora) no\b",
                r"\bantes (tuve intentos|me autolesione)[,.]?\s*pero hace mucho\b",
                r"\ben otra epoca (de mi vida)?(si[,.]?\s*)?pero no en este ano\b",
                r"\bhace (muchisimo|mas de un ano) (que no me hago dano|del ultimo intento)\b",

                # ACCIDENTES SIN INTENCIONALIDAD
                r"\b(tuve un accidente|me hice dano|me cai|me golpee)[,.]?\s*(pero )?no fue a proposito\b",
                r"\bme (corte|hice dano) sin querer[,.]?\s*no fue autolesion\b",
                r"\bfue un accidente (laboral)?[,.]?\s*no (tenia )?intencion de hacerme dano\b",
                r"\bno porque quisiera dañarme\b",

                # MALESTAR SIN CONDUCTA
                r"\b(estoy|he estado) (muy )?mal pero no me he hecho dano\b",
                r"\bhe tenido pensamientos pero no he hecho nada\b",
                r"\blo pense pero no llegue a hacerlo\b",
                r"\bhe estado fatal pero no he pasado a los actos\b",
                r"\bno he hecho nada contra mi\b",
                r"\bno he llevado a cabo ningun intento\b",

                # TRANQUILIZACIÓN EXPLÍCITA
                r"\bno he llegado a (hacerme nada|autolesionarme)\b",
                r"\bno he tenido episodios de autolesion este ano\b",
                r"\bno tengo ninguna herida hecha por mi\b",
                r"\bno ha habido ningun intento reciente\b",
                r"\bno (soy de hacerme dano|me hago dano de esa manera|me autolesiono)\b",
                r"\bnunca me he hecho dano a proposito\b",

                # RESPUESTAS BREVES
                r"\bno[,.]?\s*(nada de eso|para nada|nunca|cero|en absoluto)\b",
                r"\bno (ha|me ha) pasado( eso)?\b",
                r"\bno me he hecho nada (este ano|fisico)?\b",
            ]
            
            # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.2_B2_last_year_self_harm"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "SUI_EVAL", "3"
                return (phase, state, variant)
            
            else:
                # 2 - Self harm detected
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "SUI_EVAL.2_B2_last_year_self_harm"
                    value = True
                    db.add_user_info(telephone, key, value)
                    key = "SCREENING.SUI"
                    value = "improbable"
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "SUI_PROTOCOLS", "3"
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = _variant_search(n_user_input)
                    phase, state = "SUI_EVAL", "2B.2"
                    return (phase, state, variant)
    
        elif state == "3":
            PATTERNS_MENTAL_HEALTH_DEPRESSION: list[str] = [
                r"\bdepresion\b", r"\bdepresivo\b", r"\bdepresiva\b", r"\bantidepresivos?\b",
                r"\bfluoxetina\b", r"\bsertralina\b", r"\bescitalopram\b", r"\bparoxetina\b",
                r"\bvenlafaxina\b", r"\bduolexetina\b", r"\bduloxetina\b", r"\bmirtazapina\b",
                r"\bbupropion\b", r"\btrazodona\b", r"\bamitriptilina\b", r"\bclomipramina\b",
                r"\bprozac\b", r"\bzoloft\b", r"\blexapro\b", r"\beffexor\b", r"\bcymbalta\b",
                r"\bremeron\b", r"\btristeza profunda\b", r"\banhedonia\b",
            ]

            PATTERNS_MENTAL_HEALTH_ANXIETY: list[str] = [
                r"\bansiedad\b", r"\bansioso\b", r"\bansiolitic[ao]\b", r"\battaques? de panico\b",
                r"\bfobia(s)?\b", r"\btoc\b", r"\bobsesivo\b", r"\bcompulsivo\b",
                r"\bestrés (cronico|postraumatico)?\b", r"\bptsd\b", r"\btrauma\b",
                r"\balprazolam\b", r"\bdiazepam\b", r"\blorazepam\b", r"\bclonazepam\b",
                r"\bbuspiron\b", r"\bhydroxizina\b", r"\bhidroxizina\b",
                r"\bxanax\b", r"\bvalium\b", r"\brivotril\b", r"\batarax\b",
                r"\bnerviosa?\b", r"\bpalpitaciones\b", r"\btension nerviosa\b",
            ]

            PATTERNS_MENTAL_HEALTH_PSYCHOSIS: list[str] = [
                r"\bpsicosis\b", r"\bpsicotico\b", r"\besquizofrenia\b", r"\besquizofrenico\b",
                r"\balucinaciones?\b", r"\bdelirios?\b", r"\bparanoico\b", r"\bparanoia\b",
                r"\bbrote (psicotico)?\b", r"\bvoces (en mi cabeza)?\b", r"\boigo voces\b",
                r"\brisperidona\b", r"\bolanzapina\b", r"\bquetiapina\b", r"\baripiprazol\b",
                r"\bhaloperidol\b", r"\bclorpromazina\b", r"\bamisulprida\b", r"\bpaliperidona\b",
                r"\bresperdal\b", r"\bzyprexa\b", r"\bseroquel\b", r"\babilify\b",
            ]

            PATTERNS_MENTAL_HEALTH_BIPOLAR: list[str] = [
                r"\bbipolar\b", r"\btrastorno bipolar\b", r"\bmania\b", r"\bmanico\b",
                r"\bepisodio (maniaco|depresivo|mixto)\b", r"\bhipomani[ao]\b",
                r"\blitio\b", r"\bcarbonato de litio\b", r"\bvalproato\b", r"\bacido valproico\b",
                r"\blamotrigina\b", r"\bcarbamazepina\b", r"\boxcarbazepina\b",
                r"\bdepakote\b", r"\blamictal\b", r"\btegretol\b",
            ]

            PATTERNS_MENTAL_HEALTH_EATING: list[str] = [
                r"\banorexia\b", r"\bbulimia\b", r"\btrastorno (de la )?conducta alimentaria\b",
                r"\btca\b", r"\bbing(e)? eating\b", r"\bpurgas?\b", r"\bvomitos? (inducidos?|a proposito)\b",
                r"\brestriccion (alimentaria|calorica)\b", r"\bobsesion con (el peso|la comida|las calorias)\b",
            ]

            PATTERNS_MENTAL_HEALTH_ADHD: list[str] = [
                r"\btdah\b", r"\badhd\b", r"\bhiperactividad\b", r"\bdeficit de atencion\b",
                r"\bmetilfenidato\b", r"\batomoxetina\b", r"\blisdexanfetamina\b",
                r"\britalin\b", r"\bconcerta\b", r"\bstrattera\b", r"\bvyvanse\b",
            ]

            PATTERNS_MENTAL_HEALTH_PERSONALITY: list[str] = [
                r"\btrastorno de personalidad\b", r"\blimite\b", r"\bborderline\b",
                r"\bnarcisista\b", r"\bantisocial\b", r"\btp[bl]\b",
            ]

            PATTERNS_MENTAL_HEALTH_SLEEP: list[str] = [
                r"\binsomnio\b", r"\btrastorno del sueno\b", r"\bno puedo dormir\b",
                r"\bzolpidem\b", r"\blormetazepam\b", r"\bmelatonina\b",
                r"\bdormir mal\b", r"\bno duermo\b",
            ]

            # ---------------------------------------------------------------------------
            # ALCOHOL Y SUSTANCIAS
            # ---------------------------------------------------------------------------

            PATTERNS_SUBSTANCE_ALCOHOL: list[str] = [
                r"\balcohol\b", r"\balcoholismo\b", r"\balcoholico\b", r"\bbebo (mucho|demasiado)\b",
                r"\bdependencia (al|del) alcohol\b", r"\babuso de alcohol\b",
                r"\bnaltrexona\b", r"\bacamprosato\b", r"\bdisulfiram\b", r"\bantabuse\b",
                r"\bantabus\b", r"\b(estoy|he estado) tomando\b", r"\btomo (cada dia|habitualmente)\b",
                r"\bbebo para (calmarme|olvidar|dormir)\b",
            ]

            PATTERNS_SUBSTANCE_DRUGS: list[str] = [
                # Cannabis
                r"\bcannabis\b", r"\bmarihuana\b", r"\bporros?\b", r"\bhachis\b",
                r"\bfumo (cannabis|marihuana|porros?)\b",
                # Cocaína
                r"\bcocaina\b", r"\bcocaina\b", r"\bsnort\b",
                # Opioides
                r"\bheroin[ao]\b", r"\bopioides?\b", r"\bmetadona\b", r"\bbuprenorfina\b",
                r"\boxicodona\b", r"\btramadol\b", r"\bsuboxone\b",
                # Benzos / hipnoticos de abuso
                r"\babuso de (benzodiacepinas?|pastillas|medicacion)\b",
                r"\bdependencia (a las|de las) (pastillas|benzodiacepinas?)\b",
                # Estimulantes
                r"\banfetaminas?\b", r"\bmetanfetaminas?\b", r"\bspeed\b", r"\bmdma\b",
                r"\bextasis\b", r"\bcoca\b",
                # Genérico
                r"\bconsumo de (drogas|sustancias)\b", r"\bdrogadicto\b", r"\bdrogodependencia\b",
                r"\bdesintoxicacion\b", r"\bdeshabituacion\b",
            ]

            # ---------------------------------------------------------------------------
            # TRATAMIENTO (confirma que está recibiendo atención)
            # ---------------------------------------------------------------------------

            PATTERNS_TREATMENT_YES: list[str] = [
                r"\bsi[,.]?\b",
                r"\bsi[,.]?\s*(estoy|he estado|estaba) (en tratamiento|recibiendo (ayuda|atencion|tratamiento))\b",
                r"\bvoy al (psicologo|psiquiatra|terapeuta|medico)\b",
                r"\btengo (psicologo|psiquiatra|terapeuta)\b",
                r"\bme (atiende|trata|lleva|sigue) (un |el )?(psicologo|psiquiatra|medico|terapeuta)\b",
                r"\bme han (recetado|dado|puesto) (medicacion|pastillas|tratamiento)\b",
                r"\bestoy (medicado|tomando medicacion|con medicacion)\b",
                r"\btomo (pastillas|medicacion|medicamentos?) para\b",
                r"\bestoy (en terapia|haciendo terapia|en seguimiento)\b",
                r"\btengo (citas?|consultas?) (con el |con la )?(psicologo|psiquiatra|medico)\b",
                r"\bme diagnosticaron\b", r"\btengo diagnostico de\b", r"\bme han diagnosticado\b",
                r"\bfui diagnosticado\b", r"\btengo (depresion|ansiedad|bipolar|esquizofrenia)\b",
                r"\bingrese en (un |el )?(hospital|centro|psiquiatrico|clinica)\b",
                r"\bestuve (ingresado|hospitalizado|internado)\b",
                r"\bestoy en (un |el )?(centro de salud mental|csm|unidad de salud mental|usm)\b",
                r"\bme dieron el alta (hace|recientemente)\b",
                r"\bme han (dado|dado de) alta (psiquiatrica)?\b",
            ]

            PATTERNS_TREATMENT_NO: list[str] = [
                r"\bno[,.]?\s*(estoy|he estado|he recibido|he tenido) (en tratamiento|ayuda|atencion|seguimiento|tratamiento)\b",
                r"\bno tengo (psicologo|psiquiatra|terapeuta|medico)\b",
                r"\bno voy a (ningun|el) (psicologo|psiquiatra|medico|profesional)\b",
                r"\bno tomo (nada|ninguna medicacion|pastillas)\b",
                r"\bno estoy (medicado|en terapia|con tratamiento)\b",
                r"\bnunca he (ido al psicologo|ido al psiquiatra|tenido tratamiento|estado en terapia)\b",
                r"\bno he pedido (ayuda|atencion)\b",
                r"\bno he consultado (a nadie|con nadie|ningun profesional)\b",
                r"\bno tengo diagnostico\b",
                r"\bno me han diagnosticado nada\b",
                r"\bno[,.]?\s*(para nada|nunca|en absoluto|nada de eso)\b",
                r"\bno[,.]?\s*nunca\b",
            ]
            
            CATEGORY_PATTERNS: dict[str, list[str]] = {
                "depresion":      PATTERNS_MENTAL_HEALTH_DEPRESSION,
                "ansiedad":       PATTERNS_MENTAL_HEALTH_ANXIETY,
                "psicosis":       PATTERNS_MENTAL_HEALTH_PSYCHOSIS,
                "bipolar":        PATTERNS_MENTAL_HEALTH_BIPOLAR,
                "tca":            PATTERNS_MENTAL_HEALTH_EATING,
                "tdah":           PATTERNS_MENTAL_HEALTH_ADHD,
                "personalidad":   PATTERNS_MENTAL_HEALTH_PERSONALITY,
                "sueno":          PATTERNS_MENTAL_HEALTH_SLEEP,
                "alcohol":        PATTERNS_SUBSTANCE_ALCOHOL,
                "drogas":         PATTERNS_SUBSTANCE_DRUGS,
            }
    
            # 1 - Negation (prioridad máxima, como en tu ejemplo)
            match_no = _pattern_search(n_user_input, PATTERNS_TREATMENT_NO)
            if match_no and not any([
                _pattern_search(n_user_input, p) 
                for p in CATEGORY_PATTERNS.values()
            ]):
                key = "SUI_EVAL.3_MNS_disorder.existence"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "SUI_EVAL", "4"
                return (phase, state, variant)

            else:
                # 2 - YES + extraer categorías
                match_yes = _pattern_search(n_user_input, PATTERNS_TREATMENT_YES)
                
                if (match_yes or any([
                _pattern_search(n_user_input, p) 
                for p in CATEGORY_PATTERNS.values()])):
                    key = "SUI_EVAL.3_MNS_disorder.existence"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    # Guardar cada categoría detectada
                    for category, patterns in CATEGORY_PATTERNS.items():
                        if _pattern_search(n_user_input, patterns):
                            key = f"SUI_EVAL.3_MNS_disorder.{category}"
                            value = True
                            db.add_user_info(telephone, key, value)
                                       
                    phase, state = "SUI_EVAL", "4"
                    return (phase, state, variant)
                
                # 3 - Variant activation
                else:
                    variant = _variant_search(n_user_input)
                    phase, state = "SUI_EVAL", "3"
                    return (phase, state, variant)
                
        elif state == "4":
            
            PATTERNS_YES: list[str] = [
                # DOLOR PERSISTENTE EN EL TIEMPO
                r"\bsi[,.]?\s*(tengo|llevo con) (un )?dolor (que no se va|constante|cronico|persistente|que siempre esta)\b",
                r"\bllevo (mucho tiempo|meses|semanas|anos|tiempo) con (este |un )?dolor\b",
                r"\bme duele (desde hace (semanas|meses|anos|mucho tiempo)|hace (semanas|meses|anos))\b",
                r"\b(es|tengo) un dolor (que no se va|que siempre esta|constante|permanente|que no mejora)\b",
                r"\bel dolor (nunca se va|siempre esta|no desaparece|no mejora|vuelve siempre)\b",
                r"\btengo dolor (cronico|desde hace mucho|desde hace meses|desde hace semanas)\b",
                r"\bme han dicho que (es|tengo) (dolor cronico|una condicion cronica)\b",
                r"\bvivo con (este )?dolor (desde hace|hace) (meses|semanas|anos|tiempo)\b",
                r"\bel dolor (lleva|dura) (semanas|meses|anos)\b",
                r"\bno (me quito|se ha ido|mejora|remite) el dolor (desde hace|en) (meses|semanas|anos|mucho tiempo)\b",
            
                # LOCALIZACIONES FRECUENTES — ESPALDA / COLUMNA
                r"\btengo dolor de (espalda|columna|lumbares?|cervicales?|espalda baja) (casi todos los dias|siempre|constantemente|desde hace meses|desde hace semanas|cronico)\b",
                r"\bme duele (mucho )?(la espalda|la columna|los lumbares?|las cervicales?) (desde hace meses|desde hace tiempo|siempre|todo el tiempo|casi siempre)\b",
                r"\btengo (lumbalgia|lumbociatalgia|ciatalgia|ciatica|hernia discal) (con dolor|que me da dolor|cronica)\b",
            
                # LOCALIZACIONES FRECUENTES — ARTICULACIONES / EXTREMIDADES
                r"\btengo dolores? (fuertes|cronicos?|constantes?) en (las |los )?(articulaciones|rodillas?|caderas?|tobillos?|munecas?|hombros?|codos?)\b",
                r"\bme duelen (las |los )?(articulaciones|rodillas?|caderas?|tobillos?|munecas?|hombros?) (siempre|todo el tiempo|constantemente|desde hace meses)\b",
                r"\btengo dolor en (las manos|los pies|los dedos) (todo el tiempo|siempre|cronico|desde hace meses)\b",
                r"\bme duelen las manos (todo el tiempo|siempre|constantemente)\b",
            
                # LOCALIZACIONES FRECUENTES — CABEZA / CUELLO
                r"\btengo (migranas?|jaquecas?|dolores? de cabeza) (muy frecuentes?|casi (todos los dias|siempre)|cronicas?|recurrentes?|constantes?)\b",
                r"\bme duele (mucho )?el cuello (desde hace (mucho|meses|tiempo)|siempre|todo el tiempo|constantemente)\b",
                r"\btengo dolores? de cabeza (casi diarios?|todos los dias|muy frecuentes|cronicos?)\b",
                r"\blas migranas (no me dejan|me limitan|me incapacitan|me tienen)\b",
            
                # DOLOR GENERALIZADO
                r"\btengo dolor en todo el cuerpo\b",
                r"\bme duele todo (el cuerpo|el tiempo)?\b",
                r"\btengo (fibromialgia|fatiga cronica con dolor|dolor difuso)\b",
                r"\bel dolor es (generalizado|por todo el cuerpo|en todas partes)\b",
                r"\btengo dolor (por todas partes|en multiples sitios|generalizado)\b",
            
                # CAUSAS MÉDICAS CONOCIDAS
                r"\btengo dolor (por|a causa de|debido a) (cancer|oncologico|una enfermedad cronica|artritis|artritis reumatoide|artrosis|poliartritis)\b",
                r"\btengo dolor (por|a causa de|debido a) (una lesion (antigua|vieja|de hace)|una hernia|una hernia discal|una operacion)\b",
                r"\btengo (neuropatia (dolorosa|periferica)?|dolor neuropatico|dolor neural)\b",
                r"\btengo dolor (por|asociado a) (vih|sida|diabetes|esclerosis|lupus|crohn|colitis)\b",
                r"\btengo dolor (por|a causa de) (la quimio|el tratamiento|la enfermedad)\b",
                r"\btengo (artritis|artrosis|espondilitis|espondiloartritis)( con dolor| dolorosa)?\b",
                r"\btengo (endometriosis|vulvodinia|cistitis intersticial)( con dolor cronica| con dolor persistente)?\b",
            
                # IMPACTO EN VIDA DIARIA
                r"\bel dolor (no me deja|me impide|me limita) (hacer mi vida|vivir|trabajar|dormir|salir|moverme)\b",
                r"\bpor (el |este )?dolor (casi no salgo|no puedo trabajar|no duermo|no me muevo|no hago nada)\b",
                r"\bel dolor me (limita|incapacita|tiene|condiciona|afecta) (mucho|bastante|un monton)\b",
                r"\bno puedo (hacer casi nada|trabajar|salir|dormir|funcionar) (por|a causa del) dolor\b",
                r"\bmi (vida|dia a dia|dia) (gira|depende|esta condicionada?) (alrededor del|por el|en torno al) dolor\b",
                r"\bno (puedo|soy capaz de) (hacer vida normal|funcionar|moverme) (por|con|a causa del) (el )?dolor\b",
                r"\bel dolor me (tiene|deja) (en cama|sin poder moverme|sin poder hacer nada|postrado)\b",
            
                # RESISTENCIA A TRATAMIENTO
                r"\b(he probado|tomo|tomé|me dan) (medicacion|pastillas|analgesicos|antiinflamatorios|morfina|calmantes) (y no (se me va|mejora|funciona|sirve)|pero sigo igual|sin resultado|y nada)\b",
                r"\bnada (me quita|me alivia|me calma) (el )?dolor\b",
                r"\baunque (tome|tomo|me tome) (pastillas|analgesicos|calmantes|medicacion) (sigo (igual|con dolor)|no mejoro|no sirve)\b",
                r"\bhe (probado|intentado) (de todo|muchos tratamientos|varios medicos) (y nada|sin mejora|sin exito)\b",
                r"\bllevo (anos|meses) (con este dolor|asi|con el mismo dolor)\b",
                r"\bdesde hace mas de (seis meses|un ano|dos anos) (tengo|llevo con) (este )?dolor\b",
                r"\bes un dolor (antiguo|de hace anos|de hace mucho) que (nunca se ha resuelto|no se va|persiste)\b",
            
                # FORMULACIONES GENÉRICAS AFIRMATIVAS
                r"\bsi[,.]?\s*(tengo dolores fuertes|vivo con dolor|siempre me duele algo|el dolor es constante)\b",
                r"\bsi[,.]?\s*(es un dolor que no cesa|tengo dolor cronico|tengo dolor todo el tiempo)\b",
                r"\bsi[,.]?\s*(me duele (mucho|bastante|todo el tiempo|siempre)|tengo dolor (fuerte|intenso|constante))\b",
                r"\bvivo con (dolor|este dolor) (desde hace|hace) (meses|anos|tiempo)\b",
                r"\bel dolor (es|se ha vuelto) (parte de|constante en) mi (vida|dia a dia)\b",
            ]
                
            PATTERNS_NO: list[str] = [
            
                # NEGACIÓN DIRECTA
                r"\bno[,.]?\s*(tengo dolor cronico|tengo ningun dolor que dure tanto|tengo dolores persistentes)\b",
                r"\bno tengo (un dolor|ningun dolor) (que lleve|que dure|que persista) (semanas|meses|anos|tanto tiempo)\b",
                r"\bno me duele nada (de forma (constante|persistente|cronica)|que dure mucho)\b",
                r"\bno tengo dolor (ahora mismo|ahora) y tampoco (desde hace tiempo|antes)\b",
                r"\bno tengo (dolores cronicos?|dolor persistente|ningun dolor importante)\b",
                r"\bno[,.]?\s*(nada de eso|en absoluto|para nada|no es mi caso|estoy bien de dolor)\b",
                r"\bno tengo nada (cronico|que me limite|que me preocupe en ese sentido)\b",
                r"\ben ese sentido (estoy bien|no tengo problemas|no me pasa nada)\b",
                r"\bno[,.]?\s*(no tengo dolor|no me duele nada)\b",
            
                # DOLOR PUNTUAL / AGUDO / PASADO
                r"\bsolo (dolores? puntuales?|algún dolor de vez en cuando|dolor esporadico)\b",
                r"\ba veces me duele (algo|un poco) pero (se me pasa (rapido|pronto|enseguida)|no es grave|no es nada)\b",
                r"\bsolo me (dolio|ha dolido) (unos dias|un tiempo) y (ya esta|ya paso|se fue)\b",
                r"\btuve (un dolor|dolor) pero (ya se fue|ya paso|ya no tengo|se resolvio)\b",
                r"\bahora mismo no tengo (ningun |ningún )?(dolor|dolor importante)\b",
                r"\bel dolor (ya paso|ya se fue|se resolvio|desaparecio)\b",
                r"\bme (dolio|duele) a veces pero (se me pasa|no dura|no persiste)\b",
            
                # DOLOR LEVE SIN IMPACTO FUNCIONAL
                r"\btengo (pequenas molestias|molestias leves|alguna molestia) (pero|aunque) (no (es grave|me impide|me limita)|hago vida normal|nada serio)\b",
                r"\bsi[,.]?\s*a veces me duele (la espalda|algo|un poco)[,.]?\s*pero (no es grave|no me limita|no afecta a mi dia a dia|no es para tanto)\b",
                r"\btengo (algún|algun) (dolorcito|dolor leve|malestar)[,.]?\s*(pero )?(no afecta|no me limita|no es importante|nada serio)\b",
                r"\btengo molestias (leves|de vez en cuando) (pero )?(nada (serio|importante|que me limite))\b",
                r"\bme duele (algo|un poco) (pero )?(no (me impide|me limita|afecta|es grave|es nada))\b",
                r"\bes (solo|tan solo) (una molestia|una pequena molestia|algo leve)[,.]?\s*(no me limita|no es grave|nada importante)\b",
            
                # DOLOR ANTIGUO YA RESUELTO
                r"\b(tuve|he tenido) (dolor cronico|dolores persistentes|ese tipo de dolor) (antes|hace anos|en otra epoca)[,.]?\s*pero (ahora no|ya no|ya paso)\b",
                r"\bantes (si|tenia dolor) pero (ahora|ya) no (tengo|me duele nada)\b",
                r"\bhace (anos|mucho tiempo|tiempo) (tuve|tenia) dolor (cronico|persistente)[,.]?\s*pero (ya no|ahora no)\b",
            
                # ACLARACIONES EXPLÍCITAS
                r"\bno tengo ningun dolor que (me limite|me preocupe|afecte a mi vida|me impida)\b",
                r"\bno hay ningun dolor (que me preocupe|importante|que me limite)\b",
                r"\bno tengo dolores (antiguos|que no se vayan|que persistan)\b",
                r"\bfisicamente (estoy bien|no tengo problemas|no tengo dolor)\b",
                r"\bno tengo (problemas fisicos|dolor fisico|nada fisico) (que me limite|importante|cronico)\b",
                r"\bno[,.]?\s*no tengo ese (tipo de )?dolor\b",
                r"\bno es (mi caso|algo que me pase|algo que tenga)\b",
            ]
            
            # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.4_chronic_pain"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "SUI_EVAL", "5"
                return (phase, state, variant)
            
            else:
                # 2 - Self harm detected
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "SUI_EVAL.4_chronic_pain"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "SUI_EVAL", "5"
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = _variant_search(n_user_input)
                    phase, state = "SUI_EVAL", "4"
                    return (phase, state, variant)
                
        elif state == "5":
            
            PATTERNS_YES: list[str] = [
                # DIFICULTAD PARA FUNCIONAR EN LA VIDA DIARIA
                r"\bno (puedo|soy capaz) (con el|llevar el|mi) dia a dia\b",
                r"\bno (tengo|me quedan) (fuerzas|energias|ganas) para nada\b",
                r"\bno (consigo|puedo|soy capaz de) levantarme (de la cama|por las mananas)\b",
                r"\bme cuesta (muchisimo|un mundo|un horror) hacer (cualquier cosa|nada)\b",
                r"\bno (puedo|he podido) (trabajar|estudiar|ir a clase|ir al trabajo)\b",
                r"\bhe (dejado|abandonado) (el trabajo|los estudios|la carrera|de ir) por (como me siento|esto)\b",
                r"\bno (puedo|tengo fuerzas para) ocuparme de (la casa|mis hijos|mi familia|mis padres)\b",

                # AUTOCUIDADO AFECTADO
                r"\bme cuesta (hasta|incluso|mucho) (ducharme|asearme|banarme|lavarme)\b",
                r"\bno tengo (energia|fuerzas) (ni |siquiera )?para (ducharme|vestirme|asearme)\b",
                r"\b(no como|he dejado de comer|como muy poco) (bien|nada)? (por como me siento|por la tristeza|por la ansiedad)\b",
                r"\b(duermo fatal|no duermo|tengo insomnio) por (la ansiedad|la tristeza|el agobio)\b",
                r"\bno tengo ganas de (levantarme|vestirme|salir de la cama)\b",

                # AISLAMIENTO SOCIAL
                r"\bhe dejado de (ver|quedar con) (mis |a mis )?(amigos|amistades|familia)\b",
                r"\bno (salgo|quiero salir) de (la )?casa\b",
                r"\bno (quiero|tengo ganas de) hablar con nadie\b",
                r"\bme estoy aislando (de todo el mundo|de todos|en casa)\b",
                r"\bno tengo (fuerzas|ganas) para relacionarme\b",

                # CONCENTRACIÓN Y RENDIMIENTO
                r"\bno (me concentro|puedo concentrarme) en nada\b",
                r"\bno (consigo|puedo) (leer|ver una pelicula|ver la tele|centrarme)\b",
                r"\bmi rendimiento (ha bajado|es muy bajo|es nulo)\b",

                # MALESTAR EMOCIONAL INTENSO
                r"\bestoy (hundido|destrozado|fatal|mal|por los suelos) todo el (dia|tiempo)\b",
                r"\blloro (casi |todos los )?cada dia\b",
                r"\bestoy (desesperado|al limite|agotado emocionalmente)\b",
                r"\b(siento|tengo) una (angustia|ansiedad) constante\b",
                r"\bno veo (salida|solucion|futuro)\b",
                r"\b(la tristeza|el vacio) no se me va\b",

                # CAMBIOS RESPECTO AL NIVEL HABITUAL
                r"\bantes podia con todo y ahora (no puedo|nada)\b",
                r"\bya no soy el mismo\b",
                r"\bhe cambiado mucho (por esto|ultimamente)\b",

                # GENÉRICOS AFIRMATIVOS
                r"\bsi[,.]?\s*(me esta afectando|me esta superando|me tiene bloqueado|me limita mucho)\b",
                r"\bsi[,.]?\s*(mi vida esta limitada|no puedo seguir asi)\b",
                # Red de seguridad simple
                r"^(si|exacto|efectivamente|claro|si me afecta)$"
            ]
                
            PATTERNS_NO: list[str] = [
                # NIEGA IMPACTO FUNCIONAL
                r"\b(sigo|continuo) (haciendo|con) mi vida( normal)?\b",
                r"\b(puedo|consigo) (trabajar|estudiar|cumplir) (igual|bien|a pesar de todo)\b",
                r"\bno me (impide|limita|dificulta) (hacer las cosas|mi dia a dia|mi rutina)\b",
                r"\b(sigo|voy) cumpliendo con (todo|mis obligaciones|mis responsabilidades)\b",
                r"\bno he dejado de hacer (mis actividades|cosas|nada)\b",

                # MALESTAR LEVE O MANEJABLE
                r"\bsolo son (rachas|momentos|dias malos)\b",
                r"\blo (llevo|manejo|voy llevando|controlo)\b",
                r"\bestoy (agobiado|mal) a veces pero (puedo con ello|lo manejo)\b",
                r"\bno (es para tanto|llega a ese punto|es tan grave)\b",

                # ACLARACIONES TRANQUILIZADORAS
                r"\bno ha cambiado (mucho |nada )?mi dia a dia\b",
                r"\bsigo haciendo (lo mismo|lo de siempre)\b",
                r"\bno me bloquea( del todo)?\b",

                # RESPUESTAS BREVES / DIRECTAS
                r"\bno[,.]?\s*(no me impide|no me limita|no me pasa eso)\b",
                r"\bno[,.]?\s*(puedo seguir|estoy bien en ese sentido)\b",
                r"\bno[,.]?\s*no he dejado (de hacer )?nada\b",
                # Red de seguridad simple
                r"^(no|para nada|que va|no es mi caso)$"
            ]
            
            # 1 - Negación (Impacto no significativo)
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.5_functional_impact"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "CHAT", ""
                key = "SCREENING.SUI"
                value = "others"
                db.add_user_info(telephone, key, value)
                return (phase, state, variant)
            
            else:
                # 2 - Afirmación (Impacto detectado)
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "SUI_EVAL.5_functional_impact"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "CHAT", ""
                    return (phase, state, variant)
                
                else:
                    # 3 - No entiende / Respuesta ambigua
                    variant = _variant_search(n_user_input)
                    phase, state = "SUI_EVAL", "5"
                    return (phase, state, variant)
        
        
    elif phase == "FOLLOWUP":
        
        print("\n[FASE DE SEGUIMIENTO]\n")
        
        if state == "emergency_followup":
            
            PATTERNS_YES = [
                r"\b(si+s?|sip|sisi+|claro|ok|vale|listo|hecho|afirma|afirmativo)\b",
                r"\b(pude|logre|hable|llame|contacte|atendieron|atendido)\b",
                r"\b(lo hice|ya esta|ya hable|ya llame)\b"
            ]
            
            PATTERNS_NO = [
                r"\b(no+|nop|nanay|ninguno|para nada|que va)\b",
                r"\b(no (pude|logre|llame|hable|me atrevi|contesto|contestan|respondieron))\b",
                r"\b(ocupado|comunicaba|nadie|fallo|error|corto|espera|colgue)\b",
                r"\b(miedo|temor|duda|ansiedad|verguenza)\b",
                r"\b(todavia no|aun no|luego lo hago)\b"
            ]
            
            # 1 - Negation
            match_no = _pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "ctx.emergency_followup"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase, state = "FOLLOWUP", "non_contact_reason"
                return (phase, state, variant)
            
            else:
                # 2 - Contact
                match_yes = _pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "ctx.emergency_followup"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "FOLLOWUP", "post_help"
                    return (phase, state, variant)
                
                else:
                    key = "ctx.emergency_followup"
                    value = None
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "FOLLOWUP", "family"
                    return (phase, state, variant)
                
        elif state == "non_contact_reason":
            
            DIFFICULTY_PATTERNS = [
                r"\b(ocupado|comunicaba|comunicando|espera|larga|cola)\b",
                r"\b(no (contestan|contesto|respondieron|responde|atendieron))\b",
                r"\b(fallo|error|corto|se corto|linea|caida|funciona|numero equivocado)\b",
                r"\b(mucho tiempo|tardaron|nadie respondio)\b"
            ]
            
            DECISION_PATTERNS = [
                r"\b(decidi|preferi|pense|crei|quise|atrevi|dude|arrepenti)\b",
                r"\b(miedo|temor|pavor|panico|verguenza|corte|pena|nervios)\b",
                r"\b(no (quería|quise|pude hacerlo|me salia|me dio))\b",
                r"\b(colgue|no llame|lo deje|pase|otro momento)\b",
                r"\b(no se que decir|me bloquee|ansiedad)\b"
            ]
            
            # 1 - Decision
            match_decision = _pattern_search(n_user_input, DECISION_PATTERNS) 
            if match_decision:
                key = f"ctx.non_contact_reason"
                value = "personal_decision"
                db.add_user_info(telephone, key, value)
                
                phase, state = "FOLLOWUP", "second_try"
                return (phase, state, variant)
            
            else:
                # 2 - Difficulty
                match_diff = _pattern_search(n_user_input, DIFFICULTY_PATTERNS) 
                if match_diff:
                    key = "ctx.non_contact_reason"
                    value = "difficulty"
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "FOLLOWUP", "second_try"
                    return (phase, state, variant)
                
                else:
                    key = "ctx.non_contact_reason"
                    value = None
                    db.add_user_info(telephone, key, value)
                    
                    phase, state = "FOLLOWUP", "second_try"
                    return (phase, state, variant)
                    
        elif state == "second_try":
            phase, state = "FOLLOWUP", "family"
            return (phase, state, variant)
               
        elif state == "post_help":
            phase, state = "FOLLOWUP", "continuity_plan"
            return (phase, state, variant)
                 
        elif state == "continuity_plan":
            phase, state = "FOLLOWUP", "family"
            return (phase, state, variant)
                
        elif state == "family":
            phase, state = "CHAT", ""
            return (phase, state, variant)
        
        else:
            phase, state = "CHAT", ""
            return (phase, state, variant)
            
                         
def security_control(phase, state, variant, user_input):
    """Overrides the current state if emergency language is detected, redirecting to SUI_EVAL. Returns (phase, state, variant)."""
    PATTERNS_EMERGENCY: list[str] = [
                # PASTILLAS / SOBREDOSIS
                r"\btome (muchas )?pastillas\b",
                r"\btome (el bote( entero)?|toda la caja|todo el frasco)\b",
                r"\bme tome todo el frasco\b",
                r"\bpastillas de mas\b",
                r"\bmedicacion de mas\b",
                r"\btome demasiado\b",
                r"\bsobredosis\b",
                r"\bme pase con (las )?pastillas\b",
                r"\bacabo de tomar\b",
                r"\bhace un rato tome\b",

                # CORTES / HERIDAS
                r"\bme (he )?cort[eo]\b",
                r"\bme (he )?cortado\b",
                r"\bme cort[eo] (las )?venas\b",
                r"\bme hice cortes\b",
                r"\btengo cortes\b",
                r"\bvenas cortadas\b",
                r"\bme hice un corte\b",
                r"\bcorte profundo\b",
                r"\bsangro por cortes\b",
                r"\bme (he )?(herido?|lastimado?)\b",
                r"\bheridas?\b",
                r"\bme hice dano\b",
                r"\bhoy me cort[eo]\b",

                # SANGRADO
                r"\bestoy sangrando\b",
                r"\bsangro mucho\b",
                r"\bno para de sangrar\b",
                r"\bsangre por todos lados\b",
                r"\bestoy perdiendo sangre\b",
                r"\bsangro\b",

                # QUEMADURAS / VENENO
                r"\bme (he )?quem[eo]\b",
                r"\bquemaduras?\b",
                r"\bme puse fuego\b",
                r"\b(ingeri|trague|tome) (lejia|veneno|algo toxico|una sustancia quimica|producto (de )?limpieza|matarratas)\b",
                r"\btome algo (toxico|peligroso|que hace dano)\b",
                
                # CONCRETE PLAN
                r"\btengo un plan\b",
                r"\bse como lo voy a hacer\b",
                r"\btengo todo planeado\b",
                r"\bya tengo mi plan\b",
                r"\bvoy a tomar (todas las |el bote entero de )?pastillas\b",
                r"\btengo pastillas guardadas\b",
                r"\bbote entero\b",
                r"\bvoy a saltar\b",
                r"\bvoy a tirarme del (puente|balcon|ventana)\b",
                r"\btengo una cuerda\b",
                r"\bvoy a colgarme\b",
                r"\bvoy a cortarme las venas\b",
                r"\btengo un cuchillo preparado\b",
                r"\bvoy a ingerir (veneno|lejia|algo toxico)\b",
                r"\btengo el metodo listo\b",
                r"\bvoy a hacerlo con pastillas y alcohol\b",
                r"\bmi plan es\b",
                r"\blo voy a hacer (este fin de semana|manana|hoy)\b",
                r"\bme voy a matar ahora\b",
                
                # SUICIDE IDEATION
                r"\bsi[,.]?\s*(he tenido|he pensado en ello|en los ultimos dias|ahora mismo)\b",
                r"\b(he tenido|he pensado en ello|en los ultimos dias|ahora mismo)\b",
                r"\bpienso en (quitarme la vida|suicidarme|hacerme dano|ello|(?:acabar|terminar) con todo)\b",
                r"\bestoy pensando en matarme\b",
                r"\bquiero morir\b",
                r"\btengo ganas de morir\b",
                r"\bno quiero seguir viviendo\b",
                r"\bojala me muriera?\b",
                r"\bmejor me muero\b",
                r"\bquiero desaparecer\b",
                r"\bno aguanto más esta vida\b",
                r"\btengo pensamientos suicidas\b",
                r"\bideacion suicida\b",
                r"\bpensamientos de (muerte|autolesion)\b",
                r"\bhe pensado en acabar con todo\b",
                r"\bno quiero vivir mas\b",
                r"\bla vida no vale la pena\b",
                r"\bestoy cansado de vivir\b",
                r"\bsolo pienso en morir\b",
                r"\bme paso el dia pensando en morirme\b",
                r"\b(si[,.]?\s*)?(ultimamente|en los ultimos dias|hace poco|recientemente)\s*si\b",
                r"\bvoy a hacerlo ahora\b",
                r"\blo voy a hacer hoy\b",
                r"\bya no puedo mas[,.]?\s*lo hago ya\b",
                r"\bestoy a punto de hacerlo\b",
                r"\ben este momento lo estoy pensando seriamente\b",
                r"\btengo la intención de hacerlo\b",
                r"\bestoy decidida?[,.]?\b",
                r"\bno voy a esperar mas\b",
                r"\besto se acaba hoy\b",
                r"\bya no aguanto[,.]?\s*me despido\b",
                r"\bojalsa (me durmiera? y no despertara?|no hubiera nacido|no existiera)\b",
                r"\bno le importaria a nadie (si me muriera?|que desapareciera?)\b",
                r"\btodo seria mejor sin mi\b",
                r"\bseria mejor desaparecer\b",
                r"\bno tiene sentido seguir (viviendo|adelante)\b",
            ]
    
             # 1 - Negation
    
    n_user_input = _normalize_text(user_input)
    
    match_emergency = _pattern_search(n_user_input, PATTERNS_EMERGENCY) 
    
    # En caso de detectar un trigger pasa a evaluacion de suicidio
    if match_emergency:
        new_variant = 0
        new_phase, new_state = "SUI_EVAL", "1"
        print("\n[CONTROL DE SEGURIDAD HA DETECTADO UNA ALERTA!]\n")
        return (new_phase, new_state, new_variant)
    
    # En caso contrario se queda igual        
    else:
        new_variant = variant
        new_phase, new_state = phase, state
        return (new_phase, new_state, new_variant)
    

def bot_output_image(phase, state) -> str:
    """Returns (image_path_user, image_path_family) for the given phase and state, or (None, None) if no image applies."""
    image_path_user = None
    image_path_family = None
    
    if phase == "DEP_PROTOCOLS":
        return image_path_user, image_path_family
    
    elif phase == "SUI_PROTOCOLS":
        if state == "1":
            image_path_user = None
            image_path_family = "images/SUI/Emergency/family_esp.png"
        elif state == "2":
            image_path_user = "images/SUI/Psicoeducation/user_esp.png"
            image_path_family = "images/SUI/Emergency/family_esp.png"
        else: # state == "3"
            image_path_user = "images/SUI/Psicoeducation/user_esp.png"
            image_path_family = "images/SUI/Psicoeducation/family_esp.png"

    return image_path_user, image_path_family