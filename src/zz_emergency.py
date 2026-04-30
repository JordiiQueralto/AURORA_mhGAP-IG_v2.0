import db

telephone = "+3467"
session_path = "2026-04-30 02:49:42_session"
cause = "Ingesta de plaguicidas"
protocol = "1"
referal = "112"


db.add_emergency_instance(telephone, session_path, cause, protocol, referal)