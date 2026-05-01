import db
import re
import unicodedata
import time

def strip_accents(user_input: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', user_input)
        if unicodedata.category(c) != 'Mn'
    )


def normalize_text(user_input: str) -> str:
    user_input = user_input.lower().strip()
    user_input = strip_accents(user_input)
    user_input = re.sub(r'[“”"\'`´]', '', user_input)
    user_input = re.sub(r'[\(\)\[\]\{\},;:¡!¿?\.\-_/]+', ' ', user_input)
    n_user_input = re.sub(r'\s+', ' ', user_input).strip()
    return n_user_input

  
def pattern_search(user_input: str, patterns: list[str]) -> list[str]:
    """"""
    match = []
    for pattern in patterns:
        if re.search(pattern, user_input, flags=re.IGNORECASE):
            match.append(pattern)
    return match


def variant_search(n_user_input: str) -> str:
    
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
    match_ambiguity = pattern_search(n_user_input, PATTERNS_AMBIGUITY)
    if match_ambiguity:
        variant = "ambiguity"
        
        return variant
    
    else:
        # 2 - Evasion
        match_evasion = pattern_search(n_user_input, PATTERNS_EVASION)
        if match_evasion:
            variant = "evasion"
            
            return variant
        
        else:
            # 3 - Direct refusal
            match_refusal = pattern_search(n_user_input, PATTERNS_DIRECT_REFUSAL)
            if match_refusal:
                variant = "refusal"
                
                return variant
            
            else:
                # 4 - Hostility
                match_hostility = pattern_search(n_user_input, PATTERNS_HOSTILITY)
                if match_hostility:
                    variant = "hostility"
                    
                    return variant
                
                else:
                    # Non classificable
                    variant = "non_class"
                        
                    return variant
    

def StateMachine(telephone, phase, state, user_input):
    
    n_user_input = normalize_text(user_input)
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
                
                phase = "PROFILE"
                state = "age"
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
            
            else:
                variant = "repeat"
                phase = "PROFILE"
                state = "name"
                return (phase, state, variant)

        elif state == "age":
            age_match = re.search(r'\b(\d{1,3})\s*años\b', user_input, re.IGNORECASE)
            if age_match:
                key = "age (years)"
                value = int(age_match.group(1))
                if 18 <= value < 120:  # Range of validation
                    db.add_user_info(telephone, key, value)
                    
                    phase = "PROFILE"
                    state = "reason"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                elif value < 18:
                    
                    phase = "FAREWELL"
                    state = "age"
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                
                else:
                    
                    phase = "PROFILE"
                    state = "age"
                    return (phase, state, variant)
                
            else:
                variant = "repeat"
                phase = "PROFILE"
                state = "age"
                return (phase, state, variant)
            
        elif state == "reason":
            key = "PROFILE.call_reason"
            value = user_input
            db.add_user_info(telephone, key, value)
            
            phase = "PROFILE"
            state = "expectation"
            db.save_flow(telephone, phase, state)
            return (phase, state, variant)
        
        elif state == "expectation":
            key = "PROFILE.expectation"
            value = user_input
            db.add_user_info(telephone, key, value)
            
            phase = "PROFILE"
            state = "commitment"
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
            match_no = pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "PROFILE.commitment"
                value = "Non commited"
                db.add_user_info(telephone, key, value)
                
                time.sleep(2)
                raw_bot_output = """Te escucho igualmente, pero ten en cuenta que cuanto más te guardes, 
                más difícil será para mí darte herramientas que realmente te ayuden."""
                bot_output = " ".join(raw_bot_output.split())
                print(f"\nBOT: {bot_output}")
                
                phase = "USE_CASE_EVAL"
                state = ""
                db.save_flow(telephone, phase, state)
                return (phase, state, variant)
                
            else:
                # 2 - Accept
                match_yes = pattern_search(n_user_input, PATTERNS_YES)
                if match_yes:
                    key = "PROFILE.commitment"
                    value = "Fully commited"
                    db.add_user_info(telephone, key, value)
                    
                    time.sleep(2)
                    raw_bot_output = """Perfecto. Tu sinceridad es la base para que este espacio te 
                    sirva de verdad."""
                    bot_output = " ".join(raw_bot_output.split())
                    print(f"\nBOT: {bot_output}")
                    
                    phase = "USE_CASE_EVAL"
                    state = ""
                    db.save_flow(telephone, phase, state)
                    return (phase, state, variant)
                    
                else:
                    # 3 - Ambiguous
                    match_ambiguous = pattern_search(n_user_input, PATTERNS_AMBIGUOUS) 
                    if match_ambiguous:
                        key = "PROFILE.commitment"
                        value = "Partially commited"
                        db.add_user_info(telephone, key, value)
                        
                        time.sleep(2)
                        raw_bot_output = """No pasa nada, vamos poco a poco. Solo recuerda que mis 
                        consejos serán mucho más útiles si compartes lo que de verdad sientes."""
                        bot_output = " ".join(raw_bot_output.split())
                        print(f"\nBOT: {bot_output}")
                        
                        phase = "USE_CASE_EVAL"
                        state = ""
                        db.save_flow(telephone, phase, state)
                        return (phase, state, variant)
                        
                    else:
                        variant = "repeat"
                        phase = "PROFILE"
                        state = "commitment"
                        return (phase, state, variant) 
    
    
    elif phase == "CHAT":
        return (phase, state, variant)                    
    
                            
    elif phase == "DEP_EVAL":
        if state == "1A.1":
            
            PATTERNS_YES = [

                # Afirmaciones directas
                r"\bsí\b",
                r"\bsí[,\s]+he\s+notado\b",
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
                r"\bvacío\b",
                r"\bme\s+siento\s+vac[ií]o\b",
                r"\bsiento\s+un\s+vacío\b",
                r"\bdeprimid[oa]\b",
                r"\bdepresión\b",
                r"\bme\s+siento\s+deprimid[oa]\b",
                r"\bpersistentemente\s+triste\b",
                r"\bno\s+estoy\s+content[oa]\b",
                r"\bno\s+estoy\s+feliz\b",

                # Pérdida de interés / placer
                r"\bperdí\s+el\s+interés\b",
                r"\bsin\s+ganas\b",
                r"\bdesganad[oa]\b",
                r"\bnada\s+me\s+gusta\b",
                r"\bno\s+disfruto\s+nada\b",
                r"\bperdí\s+el\s+placer\b",
                r"\bno\s+me\s+motiva\s+nada\b",
                r"\bsin\s+interés\b",
                r"\bpérdida\s+de\s+interés\b",
                r"\bno\s+tengo\s+ganas\s+de\s+nada\b",
                r"\bcosas\s+que\s+antes\s+disfrutaba\b",
                r"\bya\s+no\s+disfruto\b",
                r"\bno\s+me\s+apetece\s+nada\b",
            ]
            
            PATTERNS_NO = [

                # Negaciones directas
                r"\bno\b",
                r"\bno\s+he\s+notado\b",
                r"\bnunca\b",
                r"\bjamás\b",
                r"\bnada\s+de\s+eso\b",
                r"\bpara\s+nada\b",
                r"\ben\s+absoluto\b",
                r"\bde\s+ninguna\s+manera\b",

                # Ausencia de síntomas de ánimo bajo
                r"\bno\s+estoy\s+triste\b",
                r"\bno\s+me\s+siento\s+vac[ií]o\b",
                r"\bno\s+estoy\s+deprimid[oa]\b",
                r"\bno\s+tengo\s+depresión\b",
                r"\bmi\s+ánimo\s+está\s+bien\b",
                r"\bestado\s+de\s+ánimo\s+normal\b",

                # Interés / placer intacto
                r"\bsigo\s+disfrutando\b",
                r"\bme\s+gusta\s+lo\s+mismo\b",
                r"\btengo\s+interés\b",
                r"\bdisfruto\s+las\s+cosas\b",
                r"\bme\s+motivan\b",
                r"\btengo\s+ganas\b",
                r"\bestoy\s+motivad[oa]\b",
                r"\bsigo\s+con\s+ganas\b",
            ]
                        
            # 1 - Negation
            match_no = pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "DEP_EVAL.1_A1_depressed_mood"
                value = False
                db.add_user_info(telephone, key, value)
                
                
                phase = "DEP_EVAL"
                state = "1A.2"
                return (phase, state, variant)
            
            else:
                # 2 - Confirmation
                match_yes = pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "DEP_EVAL.1_A1_depressed_mood"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    
                    phase = "SUI_PROTOCOL"
                    state = "1"
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = variant_search(n_user_input)
                    phase = "DEP_EVAL"
                    state = "1A.1"
                    return (phase, state, variant)
            
        elif state == "1A.2":
            if n_user_input == "yes":
                key = "DEP_EVAL.1a_anhedonia"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "1B.1"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1a_anhedonia"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "OTR"
                return (phase, state, variant)   
            else:
                i = 0
                state = "1A.2"
                return (phase, state, variant)
            
        elif state == "1B.1":
            if n_user_input == "yes":
                key = "DEP_EVAL.1b_sleep_disturbance"
                value = True
                db.add_user_info(telephone, key, value)
                i = 1
                state = "1B.2"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1b_sleep_disturbance"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "1B.2"
                return (phase, state, variant)
            else:
                i = 0
                state = "1B.1"
                return (phase, state, variant)

        elif state == "1B.2":
            if n_user_input == "yes":
                key = "DEP_EVAL.1b_appetite_weight"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:
                    state = "1C"
                    return (phase, state, variant)
                else:
                    state = "1B.3"
                    return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1b_appetite_weight"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.3"
                return (phase, state, variant)
            else:
                i = i
                state = "1B.2"
                return (phase, state, variant)
            
        elif state == "1B.3":
            if n_user_input == "yes":
                key = "DEP_EVAL.1b_fatigue"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, variant)
                else:
                    state = "1B.4"
                    return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1b_fatigue"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.4"
                return (phase, state, variant)
            else:
                i = i
                state = "1B.3"
                return (phase, state, variant)
            
        elif state == "1B.4":
            if n_user_input == "yes":
                key = "DEP_EVAL.1b_concentration"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, variant)
                else:
                    state = "1B.5"
                    return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1b_concentration"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.5"
                return (phase, state, variant)
            else:
                i = i
                state = "1B.4"
                return (phase, state, variant)
        
        elif state == "1B.5":
            if n_user_input == "yes":
                key = "DEP_EVAL.1b_low_self_worth"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, variant)
                else:
                    state = "1B.6"
                    return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1b_low_self_worth"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.6"
                return (phase, state, variant)
            else:
                i = i
                state = "1B.5"
                return (phase, state, variant)
            
        elif state == "1B.6":
            if n_user_input == "yes":
                key = "DEP_EVAL.1b_hopelessness"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, variant)
                else:
                    state = "OTR"
                    return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1b_hopelessness"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "OTR"
                return (phase, state, variant)    
            else:
                i = i
                state = "1B.5"
                return (phase, state, variant)
            
        elif state == "1C":
            if n_user_input == "yes":
                key = "DEP_EVAL.1c_functional_impairment"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2A.1"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.1c_functional_impairment"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "OTR"
                return (phase, state, variant)    
            else:
                i = 0
                state = "1C"
                return (phase, state, variant)
            
        elif state == "2A.1":
            if n_user_input == "yes":
                key = "DEP_EVAL.2a_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2A.2"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2a_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2A.2"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2A.1"
                return (phase, state, variant) 
        
        elif state == "2A.2":
            if n_user_input == "yes":
                key = "DEP_EVAL.2a_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2B.1"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2a_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2B.1"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2A.2"
                return (phase, state, variant)
        
        elif state == "2B.1":
            if n_user_input == "yes":
                key = "DEP_EVAL.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 1
                state = "2B.2"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2B.2"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2B.1"
                return (phase, state, variant)
            
        elif state == "2B.2":
            if n_user_input == "yes":
                key = "DEP_EVAL.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2B.3"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2B.3"
                return (phase, state, variant)    
            else:
                i = i
                state = "2B.2"
                return (phase, state, variant)
            
        elif state == "2B.3":
            if n_user_input == "yes":
                key = "DEP_EVAL.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2B.4"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2B.4"
                return (phase, state, variant)    
            else:
                i = i
                state = "2B.3"
                return (phase, state, variant)
            
        elif state == "2B.4":
            if n_user_input == "yes":
                key = "DEP_EVAL.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2B.5"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2B.5"
                return (phase, state, variant)    
            else:
                i = i
                state = "2B.4"
                return (phase, state, variant)
            
        elif state == "2B.5":
            if n_user_input == "yes":
                key = "DEP_EVAL.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2C"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2C"
                return (phase, state, variant)    
            else:
                i = i
                state = "2B.5"
                return (phase, state, variant)
            
        elif state == "2C":
            if n_user_input == "yes":
                key = "DEP_EVAL.2c_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.1"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2c_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2C"
                return (phase, state, variant)
            
        elif state == "2D.1":
            if n_user_input == "yes":
                key = "DEP_EVAL.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.2"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2D.1"
                return (phase, state, variant)
            
        elif state == "2D.2":
            if n_user_input == "yes":
                key = "DEP_EVAL.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.3"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2D.2"
                return (phase, state, variant)
            
        elif state == "2D.3":
            if n_user_input == "yes":
                key = "DEP_EVAL.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.3.1"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2D.3"
                return (phase, state, variant)
            
        elif state == "2D.3.1":
            if n_user_input == "yes":
                key = "DEP_EVAL.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, variant)
            elif n_user_input == "no":
                key = "DEP_EVAL.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "OTR"
                return (phase, state, variant)    
            else:
                i = 0
                state = "2D.3.1"
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
            match_no = pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.1_self_harm"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase = "SUI_EVAL"
                state = "2A"
                return (phase, state, variant)
            
            else:
                # 2 - Self harm detected
                match_yes = pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "SUI_EVAL.1_self_harm"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase = "SUI_PROTOCOLS"
                    state = "1"
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = variant_search(n_user_input)
                    phase = "SUI_EVAL"
                    state = "1"
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
            match_no = pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.2_A_active_ideation"
                value = "no"
                db.add_user_info(telephone, key, value)
                
                phase = "SUI_EVAL"
                state = "2B.1"
                return (phase, state, variant)
        
            else:
                # 2 - Concrete plans
                match_plan = pattern_search(n_user_input, PATTERNS_CONCRETE_PLANS)
                if match_plan:
                    key = "SUI_EVAL.2_A_active_ideation"
                    value = "concrete_plan"
                    db.add_user_info(telephone, key, value)
                    
                    phase = "SUI_PROTOCOLS"
                    state = "2"
                    return (phase, state, variant) 
                
                else:
                    # 3 - Ideation
                    match_ideation = pattern_search(n_user_input, PATTERNS_IDEATION)
                    if match_ideation:
                        key = "SUI_EVAL.2_A_active_ideation"
                        value = "ideation"
                        db.add_user_info(telephone, key, value)
                        
                        
                        phase = "SUI_PROTOCOLS"
                        state = "2"
                        return (phase, state, variant)
                    
                    # 4 - Variant activation
                    else:
                        variant = variant_search(n_user_input)
                        phase = "SUI_EVAL"
                        state = "2A"
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
            match_no = pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.2_B1_last_month_ideation"
                value = "no"
                db.add_user_info(telephone, key, value)
                
                
                phase = "SUI_EVAL"
                state = "2B.2"
                return (phase, state, variant)
        
            else:
                # 2 - Concrete plans
                match_plan = pattern_search(n_user_input, PATTERNS_PLAN)
                if match_plan:
                    key = "SUI_EVAL.2_B1_last_month_ideation"
                    value = "concrete_plan"
                    db.add_user_info(telephone, key, value)
                    
                    
                    phase = "SUI_PROTOCOLS"
                    state = "3"
                    return (phase, state, variant) 
                
                else:
                    # 3 - Ideation
                    match_ideation = pattern_search(n_user_input, PATTERNS_IDEATION)
                    if match_ideation:
                        key = "SUI_EVAL.2_B1_last_month_ideation"
                        value = "ideation"
                        db.add_user_info(telephone, key, value)
                        
                        
                        phase = "SUI_PROTOCOLS"
                        state = "3"
                        return (phase, state, variant)
                    
                    # 4 - Variant activation
                    else:
                        variant = variant_search(n_user_input)
                        phase = "SUI_EVAL"
                        state = "2B.1"
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
            match_no = pattern_search(n_user_input, PATTERNS_NO) 
            if match_no:
                key = "SUI_EVAL.2_B2_last_year_self_harm"
                value = False
                db.add_user_info(telephone, key, value)
                
                phase = "SUI_EVAL"
                state = "3"
                return (phase, state, variant)
            
            else:
                # 2 - Self harm detected
                match_yes = pattern_search(n_user_input, PATTERNS_YES) 
                if match_yes:
                    key = "SUI_EVAL.2_B2_last_year_self_harm"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    phase = "SUI_PROTOCOLS"
                    state = "3"
                    return (phase, state, variant)
                
                else:
                    # 3 - Variant activation
                    variant = variant_search(n_user_input)
                    phase = "SUI_EVAL"
                    state = "2B.2"
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
            match_no = pattern_search(n_user_input, PATTERNS_TREATMENT_NO)
            if match_no and not any([
                pattern_search(n_user_input, p) 
                for p in CATEGORY_PATTERNS.values()
            ]):
                key = "SUI_EVAL.3_MNS_disorder.existence"
                value = False
                db.add_user_info(telephone, key, value)
                
                
                phase = "SUI_EVAL"
                state = "4"
                return (phase, state, variant)

            else:
                # 2 - YES + extraer categorías
                match_yes = pattern_search(n_user_input, PATTERNS_TREATMENT_YES)
                
                if (match_yes or any([
                pattern_search(n_user_input, p) 
                for p in CATEGORY_PATTERNS.values()])):
                    key = "SUI_EVAL.3_MNS_disorder.existence"
                    value = True
                    db.add_user_info(telephone, key, value)
                    
                    # Guardar cada categoría detectada
                    for category, patterns in CATEGORY_PATTERNS.items():
                        if pattern_search(n_user_input, patterns):
                            key = f"SUI_EVAL.3_MNS_disorder.{category}"
                            value = True
                            db.add_user_info(telephone, key, value)
                    
                    
                    phase = "SUI_EVAL"
                    state = "4"
                    return (phase, state, variant)
                
                # 3 - Variant activation
                else:
                    variant = variant_search(n_user_input)
                    phase = "SUI_EVAL"
                    state = "3"
                    return (phase, state, variant)
  
            
    elif phase == "SUI_PROTOCOLS":
        
        if state == "1":
            phase, state = "FAREWELL", "normal"
            return (phase, state, variant)
            
        elif state == "2":
            phase, state = "FAREWELL", "normal"
            return (phase, state, variant)
        
        else:
            return (phase, state, variant)
    

def security_control(phase, state, variant, user_input):
    
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
                r"\btengo el método listo\b",
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
    
    n_user_input = normalize_text(user_input)
    
    match_emergency = pattern_search(n_user_input, PATTERNS_EMERGENCY) 
    
    # En caso de detectar un trigger pasa a evaluacion de suicidio
    if match_emergency:
        new_phase = "SUI_EVAL"
        new_state = "1"
        new_variant = 0
        print("\n[CONTROL DE SEGURIDAD HA DETECTADO UNA ALERTA!]\n")
        return (new_phase, new_state, new_variant)
    
    # En caso contrario se queda igual        
    else:
        new_phase = phase
        new_state = state
        new_variant = variant
        return (new_phase, new_state, new_variant)