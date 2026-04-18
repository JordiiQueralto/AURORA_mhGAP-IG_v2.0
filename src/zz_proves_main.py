import generate_responses
import PRESENTATION
import state_machine
import phrase_dictionary
import summarize
import db

def main_prova(telephone):
    
    ### 1. PRESENTATION
    last_bot_output, last_user_input, phase, state, memory = PRESENTATION.Init(telephone)
    
    if last_user_input == "EXIT":
        return
    
    #### 2. PROFILE
    i = 0
    j = 0   
    while True:
        
        # Creamos `bot_output` dpeendiendo de la `phase` y `state` actuales
        nucleo = phrase_dictionary.bot_output_info(phase, state)      
        bot_output = generate_responses.bot_output(last_bot_output, last_user_input, nucleo, memory)
        print(f"\nBOT: {bot_output}")
        
        # Esperamos la respuesta del usuario
        user_input = input("\nEscribe tu mensaje (o 'salir' para terminar): ")
        
        # Salimos del bucle en caso de que el usuario lo desee
        if user_input.lower() in ["salir", "Salir", "SALIR"]:
            print("\n[Finalizando sesión de apoyo...]")
            break 
        
        else:
            # En caso contrario, actualizamos `phase` i `state`
            phase, state, i = state_machine.StateMachine(telephone, phase, state, user_input, i)
            
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
        
    #### 3. CONTENTION


    #### 4. DEP
   
   
    #### 5. SUI


    ### 6. FAREWELL
    # Obtenemos fecha y hora actuales
    #.datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Obtenemos un resumen de la sessión y la añadimos a la BD
    #.summary = summarize.session_summary(telephone)
    #.db.add_user_info(telephone, f"{datetime}_session_summary", summary)
    
    # Eliminamos historial de interacciones de la sessión
    #.db.delete_interaction_history(telephone)
    

#######################################################################################################
# Example
telephone = 12345

main_prova(telephone)