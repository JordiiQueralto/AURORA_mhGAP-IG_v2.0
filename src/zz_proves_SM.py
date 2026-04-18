import state_machine

telephone = 1234
phase = "PROFILE"
state = "reason"
classification = "Desde que murió mi perro estoy mu triste."
i = 0

phase, state, i = state_machine.StateMachine(telephone, phase, state, classification, i)

print(f"\nEstat: {state}\ni: {i}")