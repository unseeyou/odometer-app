import sqlite3
from sqlite3 import Cursor
from typing import Any, Generator, Literal, Iterable, AnyStr

import logging
import bcrypt

from contextlib import contextmanager
from datetime import datetime

DATABASE = "database/database.db"


def datetime_to_str(dt: datetime) -> str:
    return f"{dt.year}-{dt.month}-{dt.day} {dt.hour}:{dt.minute}:{dt.second}"


def str_to_datetime(date_string: AnyStr) -> datetime:
    return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")


class DatabaseUnableToMultiThreadError(Exception):
    pass


class LogEntry:
    def __init__(
        self, username: str, start: str, end: str, notes: str, date: str
    ) -> None:
        self.username = username
        self.start = start
        self.end = end
        self.notes = notes
        self.datetime = str_to_datetime(date)


# noinspection SqlResolve
class Database:
    def __init__(self, path: str = DATABASE):
        def get_sqlite3_thread_safety():  # https://ricardoanderegg.com/posts/python-sqlite-thread-safety/ a tutorial script to check if it is safe to use the database over multiple threads
            # Mape value from SQLite's THREADSAFE to Python's DBAPI 2.0
            # threadsafety attribute.
            sqlite_threadsafe2python_dbapi = {0: 0, 2: 1, 1: 3}
            conn = sqlite3.connect(":memory:")
            threadsafety = conn.execute(
                """
        select * from pragma_compile_options
        where compile_options like 'THREADSAFE=%'
        """
            ).fetchone()[0]
            conn.close()

            threadsafety_value = int(threadsafety.split("=")[1])

            return sqlite_threadsafe2python_dbapi[threadsafety_value]

        if get_sqlite3_thread_safety() == 3:
            self.__check_same_thread = False
            logging.info("allowing database to be accessed through multiple threads")
        else:
            logging.error(
                "SITE WILL NOT RUN DUE TO UNSAFE THREADING SETTINGS FOR DATABASE"
            )
            self.__check_same_thread = True
            raise DatabaseUnableToMultiThreadError

        self.__path = path

    def __create_connection(self) -> sqlite3.Connection | None:
        try:
            connection = sqlite3.connect(
                self.__path, check_same_thread=self.__check_same_thread
            )
        except sqlite3.Error as err:
            connection = None
            print(err)
        return connection

    @contextmanager
    def cursor(self) -> Generator[Cursor, Any, None]:
        """
        Provides a transactional database connection as a context manager.

        Ensures the connection is properly opened and closed, and that
        transactions are committed or rolled back.

        Yields:
            sqlite3.Cursor: A cursor for interacting with the database.
        """
        conn = self.__create_connection()
        cursor = None
        try:
            # check_same_thread is False because we've already verified
            # the library is compiled with full thread-safety.
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except sqlite3.Error as err:
            logging.error(f"Database error: {err}")
            if conn:
                conn.rollback()
            raise  # Re-raise the exception after logging and rollback
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def setup(self) -> None:
        logging.debug("setting up db")
        with self.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password BLOB NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                security_q TEXT NOT NULL,
                security_ans TEXT NOT NULL
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                notes TEXT,
                date TEXT NOT NULL
            )
            """)

    def reset(self) -> None:
        logging.debug("resetting db")
        with self.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS users")

    def register_user(
        self, username: str, password: str, security_q: str, security_ans: str
    ) -> None:
        logging.debug("Registering User to DB")
        # hash + salt password
        enc_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        with self.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, security_q, security_ans) VALUES (?, ?, ?, ?)",
                (username, enc_password, security_q, security_ans),
            )

    def check_user_pw(self, username: str, password: str):
        with self.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            hashed = cursor.fetchone()[0]

        return bcrypt.checkpw(password.encode("utf-8"), hashed)

    def retrieve_usernames(self):
        with self.cursor() as cursor:
            cursor.execute("SELECT username FROM users")
            usernames = [i[0] for i in cursor.fetchall()]
        print(usernames)
        return usernames

    def get_security_question(self, username: str) -> str:
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT security_q FROM users WHERE username = ?", (username,)
            )
            return cursor.fetchone()[0]

    def get_security_answer(self, username: str) -> str:
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT security_ans FROM users WHERE username = ?", (username,)
            )
            return cursor.fetchone()[0]

    def check_user_active_status(self, username: str):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT is_active FROM users WHERE username = ?", (username,)
            )
            return cursor.fetchone() is not False

    def add_log_entry(
        self, username: str, start: str, end: str, notes: str, date: datetime
    ) -> None:
        with self.cursor() as cursor:
            cursor.execute(
                "INSERT INTO log_entries (username, start, end, notes, date) VALUES (?, ?, ?, ?, ?)",
                (username, start, end, notes, datetime_to_str(date)),
            )

    def fetch_log_entries(
        self,
        username: str,
        sort: Literal["asc", "desc"],
        amount: int = -1,
        skip: int = 0,
    ) -> Iterable[LogEntry]:
        """
        :param username: username to fetch entries for
        :param sort: asc = latest first, desc = oldest first
        :param amount: amt of entries to fetch, -1 for all
        :param skip: amt of entries to skip, default 0
        :return Iterable[LogEntry]:
        """
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT start, end, notes, date FROM log_entries WHERE username = ? ORDER BY datetime(date) {0}".format(
                    sort.upper()
                ),
                (username,),
            )
            if amount == -1:
                for row in cursor.fetchall()[skip:]:
                    yield LogEntry(username, row[0], row[1], row[2], row[3])
            else:
                for row in cursor.fetchmany(amount + skip)[skip:]:
                    yield LogEntry(username, row[0], row[1], row[2], row[3])
