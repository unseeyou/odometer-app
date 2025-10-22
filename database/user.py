import flask_login
from constants import CustomApp, manager, app

from datetime import datetime


class User(flask_login.UserMixin):
    def __init__(self, username: str, password: str, app: CustomApp) -> None:
        self.id = username
        self.password = password
        self.__active = app.database.check_user_active_status(self.id)
        self.__app = app
        self.__entries = []

    def add_log_entry(
        self, start: str, end: str, notes: str | None, date: datetime, duration: int
    ):
        if notes is None:
            notes = ""
        self.__app.database.add_log_entry(self.id, start, end, notes, date, duration)

    def get_log_display(self, page: int = 1):
        return self.__app.database.fetch_log_entries(
            self.id, "asc", 10, (page - 1) * 10
        )

    def get_complete_logs(self):
        return self.__app.database.fetch_log_entries(self.id, "asc")

    def get_id(self) -> str:
        return self.id

    @property
    def is_authenticated(self) -> bool:
        if self.password != "":
            return True
        return False

    @property
    def is_anonymous(self) -> bool:
        if self.id == "":
            return True
        return False

    @property
    def is_active(
        self,
    ) -> bool:  # I guess there could be a ban system using this? can set a flag in db
        return self.__active

    def save_to_db(self, sec_q: str, sec_ans: str) -> None:
        self.__app.database.register_user(self.id, self.password, sec_q, sec_ans)

    @classmethod
    def from_db(cls, app: CustomApp, username: str, password: str) -> "User":
        if app.database.check_user_pw(username, password):
            return cls(username, password)
        return None

    @classmethod
    def from_user(cls, username: str):
        return cls(username, "password", app)


@manager.user_loader
def load_user(user: str) -> User:
    return User.from_user(user)
