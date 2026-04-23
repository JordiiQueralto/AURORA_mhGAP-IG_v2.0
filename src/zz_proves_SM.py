import state_machine

telephone = 111
phase = "PROFILE"
state = "commitment"
user_input = "no lo se"

n_user_input = state_machine.normalize_text(user_input)

phase, state, variant = state_machine.StateMachine(telephone, phase, state, user_input)

print(f"\n\nUser input: {n_user_input}\nFase: {phase}\nEstat: {state}\nVariante: {variant}")