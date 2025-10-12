from flask import Flask
from database.database import Database

from pydantic_settings import BaseSettings, SettingsConfigDict
from flask_login import LoginManager


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ODO_")
    secret_key: str


 # noinspection PyArgumentList
 # settings will fill automatically - unseeyou
class CustomApp(Flask):
    def __init__(self, *args, **kwargs):
        super(CustomApp, self).__init__(*args, **kwargs)
        self.logger.setLevel("DEBUG")
        self.database: Database = Database()
        self.database.setup()
        self.logger.debug("initializing app")
        self.settings = Settings()
        self.secret_key = self.settings.secret_key


app = CustomApp("app")
manager = LoginManager(app)
manager.login_view = "login"
