import db
import session_summary
import datetime

datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
telephone = 123456

summary = session_summary.summarize(telephone)
db.add_user_info(telephone, f"{datetime}_session_summary", summary)
db.delete_interaction_history(telephone)