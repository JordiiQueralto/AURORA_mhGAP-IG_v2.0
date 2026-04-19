import state_machine

telephone = 1234
phase = "SUI_EVAL"
state = "3"
user_input = "ultimamente he estado tomando"
n_user_input = state_machine.normalize_text(user_input)

phase, state = state_machine.StateMachine(telephone, phase, state, user_input)

print(f"\n\nUser input: {n_user_input}\nFase: {phase}\nEstat: {state}")