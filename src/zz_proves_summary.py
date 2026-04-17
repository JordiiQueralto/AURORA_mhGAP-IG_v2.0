import db
import summarize
import datetime

datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
telephone = 123456

summary = summarize.session_summary(telephone)
db.add_user_info(telephone, f"{datetime}_session_summary", summary)
db.delete_interaction_history(telephone)