import db
import generate_output

telephone = "+34666"
session_path = "2026-04-30 18:25:25_session"

#conversation_history = db.conversation_history(telephone)
#print(conversation_history)

valoration = generate_output.session_valoration(telephone, session_path)
print(valoration)