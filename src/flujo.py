import prompt_builder
import llm
import phrase_dictionary
import state_machine
import summarize
import generate_responses


def flujo(telephone, phase, state, last_bot_output, last_user_input, i, j):
    
    # Retrieve memory from the database
    memory = summarize.memory_summary(telephone)
    
    # Get triggers for the current phase and state
    triggers = phrase_dictionary.trigger_dict(phase, state)
    
    # Classify the user's response based on the last bot output and the triggers
    classification = generate_responses.response_classification(
        last_bot_output, last_user_input, triggers)
    
    # Update the state machine based on the classification 
    new_state, i, j = state_machine.StateMachine_DEP(telephone, state, classification, i, j)
    
    # Obtain a variant output (we remain at same state)
    if new_state == state:
        nucleo = phrase_dictionary.variant(phase, state, classification)
        
        prompt = prompt_builder.prompt_generation(last_bot_output,
                                              last_user_input,
                                              nucleo,
                                              memory)
        bot_output = llm.send_prompt(prompt)
        print("\nBOT: ", bot_output)
        
        # Get the next user input
        user_input = input("\nUSER: ")
        
        # Update the last bot output and last user input for the next iteration
        last_bot_output = bot_output
        last_user_input = user_input
        
        return (last_bot_output, last_user_input, new_state, i, j)
    
    
    # Generate the next bot output based on the new state and the conversation context  
    else:
        nucleo = phrase_dictionary.bot_output_info(phase, state)
        
        prompt = prompt_builder.prompt_generation(last_bot_output,
                                              last_user_input,
                                              nucleo,
                                              memory)
        bot_output = llm.send_prompt(prompt)
        print("\nBOT: ", bot_output)
        
        # Get the next user input
        user_input = input("\nUSER: ")
        
        # Update the last bot output and last user input for the next iteration
        last_bot_output = bot_output
        last_user_input = user_input
        
        return (last_bot_output, last_user_input, new_state, i, j)
        
    
    

##########################################################################
# Example
telephone = 123456
phase = "DEP"
state = "1B.1"
i = 0
j = 0

last_bot_output = """¿Has notado que tu estado de ánimo ha estado persistentemente bajo, 
triste o vacío, o que has perdido el interés o el placer en cosas que antes disfrutabas?"""
last_user_input = """Sí, estoy triste desde la muerte de mi perro."""

print("\nBOT : ", last_bot_output)
print("\nUSER : ", last_user_input)

for _ in range(0):
    last_bot_output, last_user_input, state, i, j = flujo(
        telephone, phase, state, last_bot_output, last_user_input, i, j)