import state_machine

telephone = "+34999"
phase = "SUI_EVAL"
state = "4"
user_input = "tengo dolor de espalda casi todos los dias"

n_user_input = state_machine._normalize_text(user_input)

phase, state, variant = state_machine.StateMachine(telephone, phase, state, user_input)

print(f"\n\nUser input: {n_user_input}\nFase: {phase}\nEstat: {state}\nVariante: {variant}")