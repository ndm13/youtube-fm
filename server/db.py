from os import getenv

from flask import g

from core import Database


def get_db():
    if 'db' not in g:
        g.db = Database("users.sqlite", getenv('SECRET_KEY'))
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.con.close()


def init_app(app):
    app.teardown_appcontext(close_db)
