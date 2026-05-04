import state_machine

telephone = "+34999"
phase = "SUI_EVAL"
state = "5"
user_input = "me cuesta hasta ducharme"

n_user_input = state_machine.normalize_text(user_input)

phase, state, variant = state_machine.StateMachine(telephone, phase, state, user_input)

print(f"\n\nUser input: {n_user_input}\nFase: {phase}\nEstat: {state}\nVariante: {variant}")