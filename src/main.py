import generate_output
import PRESENTATION
import state_machine
import phrase_dictionary
import summarize
import db

def main(telephone):
    
    ### 1. PRESENTATION
    last_bot_output, last_user_input, phase, state, memory = PRESENTATION.Init(telephone)
    
    
    ### 2. PROFILE
    if phase == "PROFILE":
        i = 0
        j = 0   
        while True:
            
            # Creamos `bot_output` dependiendo de la `phase` y `state` actuales
            nucleo = phrase_dictionary.bot_output_info(phase, state)      
            bot_output = generate_output.bot_output(last_bot_output, 
                                                    last_user_input, nucleo, memory)
            print(f"\nBOT: {bot_output}")
            
            # Esperamos la respuesta del usuario
            user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
            
            # Salimos del bucle en caso de que el usuario lo desee
            if user_input.lower() in ["salir", "Salir", "SALIR"]:
                phase = "FAREWELL"
                state = "normal"
                break 
            
            else:
                # En caso contrario, actualizamos `phase` i `state`
                phase, state, i = state_machine.StateMachine(telephone, phase, 
                                                             state, user_input, i)
                
                # Actualizar variables
                last_bot_output = bot_output
                last_user_input = user_input
                
                # Actualizar memoria: Guardar la nueva información relevante en la BD
                db.add_user_info(telephone, f"user_input_{j}", user_input)
                db.add_user_info(telephone, f"bot_output_{j}", bot_output)
                j += 1
                memory = summarize.memory_summary(telephone)
                
                # Rompemos el bucle si llegamos a phase `DEP` o `SUI`    
                if phase == ("DEP" or "SUI"):
                    break
        
        
    ### 3. CONTENTION
    elif phase == "CONTENTION":
        return


    ### 4. DEP
    elif phase == "DEP":
        return
    
   
    ### 5. SUI
    elif phase == "SUI":
        return


    ### 6. FAREWELL
    # Despedida
    elif phase == "FAREWELL":
        farewell = generate_output.farewell(state)
        print(f"\nBOT: {farewell}")
        print("\n[Finalizando sesión de apoyo...]")
        
        # Obtenemos fecha y hora actuales
        datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Obtenemos un resumen de la sessión y la añadimos a la BD
        summary = summarize.session_summary(telephone)
        db.add_user_info(telephone, f"{datetime}_session_summary", summary)
        
        # Eliminamos historial de interacciones de la sessión
        db.delete_interaction_history(telephone)
        
        return
    
    
    ### ERROR OR OTR
    else:
        return



if __name__ == "__main__":
    # Example
    NUMERO_ENTRANTE = "1234"
    
    main(NUMERO_ENTRANTE)