from flask import Blueprint, request, render_template
from database.user import User
import flask_login

logbook = Blueprint("logbook", __name__)


@logbook.route("/logbook")
@flask_login.login_required
def logbook_main():
    page = request.args.get("page", 1, type=int)
    user: User = flask_login.current_user
    display = user.get_log_display(page)
    logs = []
    for log in display:
        logs.append([log.date, log.start, log.end, log.notes])
    return render_template("logbook.html", logs=logs)
