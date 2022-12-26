from sqlite3 import connect, Error as SqliteError

from dataclasses import dataclass
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from base64 import urlsafe_b64encode
from uuid import UUID, uuid4
from os import path

from .config_dir import config_dir


class DatabaseException(Exception):
    pass


@dataclass()
class User:
    name: str
    uuid: str
    token: str
    cookie: str
    split_title: bool
    interval: int
    last_run: int
    last_id: str
    pause: bool


class Database:
    def __init__(self, sqlite_path, fernet_key):
        try:
            self.fernet = Fernet(
                urlsafe_b64encode(Scrypt(salt=bytes("youtube-fm", 'utf-8'), length=32, n=2 ** 14, r=8, p=1)
                                  .derive(bytes(fernet_key, 'utf-8'))))
            self.con = connect(path.join(config_dir, sqlite_path))
            self.con.row_factory = lambda c, r: User(
                r[0],
                r[1],
                str(self.fernet.decrypt(r[2]), 'utf-8').replace('\r', '') if r[2] is not None else None,
                str(self.fernet.decrypt(r[3]), 'utf-8').replace('\r', '') if r[3] is not None else None,
                r[4] == 1,
                r[5],
                r[6],
                r[7],
                r[8] == 1
            ) if r is not None else None

            cursor = self.con.cursor()
            cursor.execute("create table if not exists users "
                           "(uuid unique, name, token, cookie, split_title default false, interval default 300,"
                           "last_run default 0, last_id, pause default false)")
            cursor.close()
            self.con.commit()
        except UnsupportedAlgorithm:
            raise DatabaseException("Unsupported algorithm for encryption: requires Scrypt and Fernet")
        except SqliteError as se:
            raise DatabaseException("Error connecting to database/creating table", se)

    def create_user(self):
        uuid = uuid4()
        cursor = self.con.cursor()
        cursor.execute("insert into users (uuid) values (?)", [uuid.hex])
        cursor.close()
        self.con.commit()
        return str(uuid)

    def get_user(self, uuid):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        user = cursor.execute("select name, uuid, token, cookie, split_title, interval, last_run, last_id, pause "
                              "from users where uuid = ?", [uuid]).fetchone()
        cursor.close()
        return user

    def reset_uuid(self, uuid):
        uuid = UUID(uuid).hex
        new = uuid4()
        cursor = self.con.cursor()
        cursor.execute("update users set uuid = ? where uuid = ?", [new.hex, uuid])
        cursor.close()
        self.con.commit()
        return new.hex

    def update_token(self, uuid, name, token):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        cursor.execute("update users set name = ?, token = ? where uuid = ?",
                       [name, self.fernet.encrypt(bytes(token, 'utf-8')), uuid])
        cursor.close()
        self.con.commit()

    def update_cookie(self, uuid, cookie):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        cursor.execute("update users set cookie = ? where uuid = ?",
                       [(self.fernet.encrypt(bytes(cookie, 'utf-8'))), uuid])
        cursor.close()
        self.con.commit()

    def update_split_title(self, uuid, split_title):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        cursor.execute("update users set split_title = ? where uuid = ?", [split_title, uuid])
        cursor.close()
        self.con.commit()

    def update_interval(self, uuid, interval):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        cursor.execute("update users set interval = ? where uuid = ?", [interval, uuid])
        cursor.close()
        self.con.commit()

    def update_last_run(self, uuid, time):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        cursor.execute("update users set last_run = ? where uuid = ?", [time, uuid])
        cursor.close()
        self.con.commit()

    def update_last_id(self, uuid, id):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        cursor.execute("update users set last_id = ? where uuid = ?", [id, uuid])
        cursor.close()
        self.con.commit()

    def update_pause(self, uuid, pause):
        uuid = UUID(uuid).hex
        cursor = self.con.cursor()
        cursor.execute("update users set pause = ? where uuid = ?", [pause, uuid])
        cursor.close()
        self.con.commit()

    def get_users_for_run(self, time):
        cursor = self.con.cursor()
        users = cursor.execute("select name, uuid, token, cookie, split_title, interval, last_run, last_id, pause "
                               "from users where last_run + interval <= ? and pause = false "
                               "and token is not null and cookie is not null",
                               [time]).fetchall()
        cursor.close()
        return users
