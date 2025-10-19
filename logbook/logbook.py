from flask import Blueprint, request, render_template, session
from database.user import User
from datetime import datetime, timedelta
import flask_login
import pytz

logbook = Blueprint("logbook", __name__)


@logbook.route("/logbook", methods=["GET", "POST"])
@flask_login.login_required
def logbook_main():
    if session.get("current_start") is None:
        timezone = pytz.timezone(session.get("user_timezone"))
        session["current_start"] = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
    page = request.args.get("page", 1, type=int)
    user: User = flask_login.current_user
    display = user.get_log_display(page)
    logs = []
    for log in display:
        logs.append([log.date, log.start, log.end, log.notes])
    if request.method == "POST":
        ...
    return render_template("logbook.html", logs=logs)


@logbook.route("/backend/set_timezone", methods=["POST"])
def set_user_timezone():
    data = request.get_json()
    if data and "timezone" in data:
        user: User = flask_login.current_user
        session["user_timezone"] = data["timezone"]
        return {"message": f"Timezone for user {user.id} set successfully"}, 200
    return {"message": "Invalid request"}, 400
