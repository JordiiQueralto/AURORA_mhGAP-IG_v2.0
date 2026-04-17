import state_machine

telephone = 1234
phase = "DEP"
state = "1B.5"
classification = "no"
i = 0

state, i = state_machine.StateMachine(telephone, phase, state, classification, i)

print(f"\nEstat: {state}\ni: {i}")