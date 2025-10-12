from constants import app, manager
from database.user import User
from flask_wtf.csrf import CSRFProtect

from flask import request
import flask
from flask_login import login_user
import flask_login
from urllib.parse import urlparse, urljoin

# csrf = CSRFProtect(app)


def url_has_allowed_host_and_scheme(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        app.logger.debug("Submission received")

        form = request.form

        username = form.get("username")
        password = form.get("pw")
        remember_login = form.get("remember") == "on"

        if not username or not password:
            flask.flash("All fields are required to be filled!")
            return flask.redirect(flask.url_for("login"))

        if username not in app.database.retrieve_usernames():
            flask.flash("Username doesn't exist!")
            return flask.redirect(flask.url_for("login"))

        if not app.database.check_user_pw(username, password):
            flask.flash("Incorrect password!")
            return flask.redirect(flask.url_for("login"))

        user = User(username, password, app)
        login_user(user)

        flask.flash('Logged in successfully.')

        next = request.args.get('next')

        if not url_has_allowed_host_and_scheme(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return flask.render_template("login.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        app.logger.debug("Submission received")
        form = request.form
        username = form.get("username")
        password = form.get("pw")
        password_confirm = form.get("pwc")
        security_q = form.get("secq")
        security_ans = form.get("seca")
        remember_login = form.get("remember") == "on"

        if password != password_confirm:
            flask.flash("Passwords do not match!")
            return flask.redirect(flask.url_for("signup"))

        if not username or not password or not security_q or not security_ans:
            flask.flash("All fields are required to be filled!")
            return flask.redirect(flask.url_for("signup"))

        if username in app.database.retrieve_usernames():
            flask.flash("Username already exists!")
            return flask.redirect(flask.url_for("signup"))

        if not 4 <= len(username) <= 25:
            flask.flash("Username must be between 4 and 25 characters long!")
            return flask.redirect(flask.url_for("signup"))

        if not 6 <= len(password) <= 35:
            flask.flash("Password must be between 6 and 35 characters long!")
            return flask.redirect(flask.url_for("signup"))

        user = User(username, password, app)
        user.save_to_db(security_q, security_ans)
        login_user(user, remember=remember_login)
        flask.flash("Account created successfully!")
        return flask.redirect(flask.url_for("index"))
    return flask.render_template("signup.html")


@app.route("/")
@flask_login.login_required
def index():
    return flask.render_template("index.html")


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login"))


if __name__ == "__main__":
    # csrf.init_app(app)
    manager.init_app(app)
    app.run(debug=True)
