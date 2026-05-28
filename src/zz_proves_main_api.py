import services_user
import state_machine

telephone = "+3477"
memory = ""
last_bot_output = "¿Tienes planes o pensamientos de hacerte daño o de quitarte la vida actualmente?"
user_input = "tengo un plan"
variant = 0
phase = "SUI_EVAL"
state = "2A"

new_phase, new_state, new_variant = state_machine.StateMachine(
            telephone, phase, state, user_input
        )

if phase == "DEP_EVAL":
    new_phase, new_state, new_variant = state_machine.security_control(
        new_phase, new_state, new_variant, user_input)

# Generar la pregunta del BOT para el NUEVO estado
bot_output, image_path, is_ended, new_phase, new_state, new_variant = services_user._generate_response(
    telephone, new_phase, new_state, new_variant, user_input, last_bot_output, memory)

print("\n" + "="*50)
print("🔍 RESULTADO DE LA API")
print("="*50)
print(f"🤖 Bot Output:  {bot_output}")
print(f"🖼️  Image Path: {image_path}")
print(f"🏁 Is Ended:   {is_ended}")
print("-" * 30)
print(f"📍 New Phase:  {new_phase}")
print(f"⚙️  New State:  {new_state}")
print(f"🔢 New Variant: {new_variant}")
print("="*50 + "\n")