from flask import Blueprint, request, render_template, session, redirect, url_for
from database.user import User
from datetime import datetime
import flask_login
import pytz

logbook = Blueprint("logbook", __name__)


@logbook.route("/logbook", methods=["GET", "POST"])
@flask_login.login_required
def logbook_main():
    timezone = pytz.timezone(session.get("user_timezone"))
    if session.get("current_start") is None:
        session["current_start"] = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
    page = request.args.get("page", 1, type=int)
    user: User = flask_login.current_user
    display = user.get_log_display(page)

    logs = []
    for log in display:
        logs.append(
            [
                log.datetime.astimezone(timezone).strftime("%Y-%m-%d %H:%M:%S"),
                log.start,
                log.end,
                log.notes,
                log.car,
            ]
        )

    user_cars = user.get_cars()

    if request.method == "POST":
        # new car
        form = request.form
        print(form.items())
        car_name = form.get("car_name")
        if car_name is not None:
            car_notes = form.get("car_notes")
            user.add_car(car_name, car_notes)
        if "start" in form.keys():
            print("detected log form")
            start = form.get("start")
            end = form.get("end")
            car = form.get("car")
            notes = form.get("notes")
            user.add_log_entry(
                start, end, notes, datetime.now(), 0, car
            )  # no duration functionality yet
        return redirect(url_for("logbook.logbook_main"))

    return render_template("logbook.html", logs=logs, user_cars=user_cars)


@logbook.route("/backend/set_timezone", methods=["POST"])
def set_user_timezone():
    data = request.get_json()
    if data and "timezone" in data:
        user: User = flask_login.current_user
        session["user_timezone"] = data["timezone"]
        return {"message": f"Timezone for user {user.id} set successfully"}, 200
    return {"message": "Invalid request"}, 400
