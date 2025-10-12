from flask import Blueprint
from constants import app
import flask_login

logbook = Blueprint("logbook", __name__)
logbook.url_prefix = "/logbook"

@logbook.route("/")
@flask_login.login_required
def logbook_main():
    return app.render_template("logbook.html")

app.register_blueprint(logbook)