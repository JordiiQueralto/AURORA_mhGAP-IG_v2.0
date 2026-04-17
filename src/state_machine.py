import db

def StateMachine(telephone, phase, state, classification, i):
    
    if phase == "DEP":
        if state == "1A.1":
            if classification == "yes":
                key = "DEP.1a_depressed_mood"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "1B.1"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.1a_depressed_mood"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "1A.2"
                return (phase, state, i)   
            else:
                i = 0
                state = "1A.1"
                return (phase, state, i)
            
        elif state == "1A.2":
            if classification == "yes":
                key = "DEP.1a_anhedonia"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "1B.1"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.1a_anhedonia"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "OTR"
                return (phase, state, i)   
            else:
                i = 0
                state = "1A.2"
                return (phase, state, i)
            
        elif state == "1B.1":
            if classification == "yes":
                key = "DEP.1b_sleep_disturbance"
                value = True
                db.add_user_info(telephone, key, value)
                i = 1
                state = "1B.2"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.1b_sleep_disturbance"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "1B.2"
                return (phase, state, i)
            else:
                i = 0
                state = "1B.1"
                return (phase, state, i)

        elif state == "1B.2":
            if classification == "yes":
                key = "DEP.1b_appetite_weight"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:
                    state = "1C"
                    return (phase, state, i)
                else:
                    state = "1B.3"
                    return (phase, state, i)
            elif classification == "no":
                key = "DEP.1b_appetite_weight"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.3"
                return (phase, state, i)
            else:
                i = i
                state = "1B.2"
                return (phase, state, i)
            
        elif state == "1B.3":
            if classification == "yes":
                key = "DEP.1b_fatigue"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, i)
                else:
                    state = "1B.4"
                    return (phase, state, i)
            elif classification == "no":
                key = "DEP.1b_fatigue"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.4"
                return (phase, state, i)
            else:
                i = i
                state = "1B.3"
                return (phase, state, i)
            
        elif state == "1B.4":
            if classification == "yes":
                key = "DEP.1b_concentration"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, i)
                else:
                    state = "1B.5"
                    return (phase, state, i)
            elif classification == "no":
                key = "DEP.1b_concentration"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.5"
                return (phase, state, i)
            else:
                i = i
                state = "1B.4"
                return (phase, state, i)
        
        elif state == "1B.5":
            if classification == "yes":
                key = "DEP.1b_low_self_worth"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, i)
                else:
                    state = "1B.6"
                    return (phase, state, i)
            elif classification == "no":
                key = "DEP.1b_low_self_worth"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "1B.6"
                return (phase, state, i)
            else:
                i = i
                state = "1B.5"
                return (phase, state, i)
            
        elif state == "1B.6":
            if classification == "yes":
                key = "DEP.1b_hopelessness"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                if i == 2:  
                    state = "1C"
                    return (phase, state, i)
                else:
                    state = "OTR"
                    return (phase, state, i)
            elif classification == "no":
                key = "DEP.1b_hopelessness"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "OTR"
                return (phase, state, i)    
            else:
                i = i
                state = "1B.5"
                return (phase, state, i)
            
        elif state == "1C":
            if classification == "yes":
                key = "DEP.1c_functional_impairment"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2A.1"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.1c_functional_impairment"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "OTR"
                return (phase, state, i)    
            else:
                i = 0
                state = "1C"
                return (phase, state, i)
            
        elif state == "2A.1":
            if classification == "yes":
                key = "DEP.2a_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2A.2"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2a_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2A.2"
                return (phase, state, i)    
            else:
                i = 0
                state = "2A.1"
                return (phase, state, i) 
        
        elif state == "2A.2":
            if classification == "yes":
                key = "DEP.2a_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2B.1"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2a_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2B.1"
                return (phase, state, i)    
            else:
                i = 0
                state = "2A.2"
                return (phase, state, i)
        
        elif state == "2B.1":
            if classification == "yes":
                key = "DEP.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 1
                state = "2B.2"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2B.2"
                return (phase, state, i)    
            else:
                i = 0
                state = "2B.1"
                return (phase, state, i)
            
        elif state == "2B.2":
            if classification == "yes":
                key = "DEP.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2B.3"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2B.3"
                return (phase, state, i)    
            else:
                i = i
                state = "2B.2"
                return (phase, state, i)
            
        elif state == "2B.3":
            if classification == "yes":
                key = "DEP.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2B.4"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2B.4"
                return (phase, state, i)    
            else:
                i = i
                state = "2B.3"
                return (phase, state, i)
            
        elif state == "2B.4":
            if classification == "yes":
                key = "DEP.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2B.5"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2B.5"
                return (phase, state, i)    
            else:
                i = i
                state = "2B.4"
                return (phase, state, i)
            
        elif state == "2B.5":
            if classification == "yes":
                key = "DEP.2b_"
                value = True
                db.add_user_info(telephone, key, value)
                i += 1
                state = "2C"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2b_"
                value = False
                db.add_user_info(telephone, key, value)
                i = i
                state = "2C"
                return (phase, state, i)    
            else:
                i = i
                state = "2B.5"
                return (phase, state, i)
            
        elif state == "2C":
            if classification == "yes":
                key = "DEP.2c_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.1"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2c_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, i)    
            else:
                i = 0
                state = "2C"
                return (phase, state, i)
            
        elif state == "2D.1":
            if classification == "yes":
                key = "DEP.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.2"
                return (phase, state, i)    
            else:
                i = 0
                state = "2D.1"
                return (phase, state, i)
            
        elif state == "2D.2":
            if classification == "yes":
                key = "DEP.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.3"
                return (phase, state, i)    
            else:
                i = 0
                state = "2D.2"
                return (phase, state, i)
            
        elif state == "2D.3":
            if classification == "yes":
                key = "DEP.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "2D.3.1"
                return (phase, state, i)    
            else:
                i = 0
                state = "2D.3"
                return (phase, state, i)
            
        elif state == "2D.3.1":
            if classification == "yes":
                key = "DEP.2d_"
                value = True
                db.add_user_info(telephone, key, value)
                i = 0
                state = "3"
                return (phase, state, i)
            elif classification == "no":
                key = "DEP.2d_"
                value = False
                db.add_user_info(telephone, key, value)
                i = 0
                state = "OTR"
                return (phase, state, i)    
            else:
                i = 0
                state = "2D.3.1"
                return (phase, state, i)
            
    elif phase == "SUI":
        if state == "1":
            return