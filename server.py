import logging

from dotenv import load_dotenv
from flask import Flask, request, render_template
from os import getenv

from ytmusicapi import YTMusic

from db import Database, DatabaseException
from lastfm import LastFM, LastFMException

load_dotenv()
logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())
app = Flask(__name__)
lastfm_api = getenv('LASTFM_API')
lastfm_secret = getenv('LASTFM_SECRET')
if None in (lastfm_api, lastfm_secret):
    raise Exception("Cannot create Last.FM API without LASTFM_API and LASTFM_SECRET!")


@app.route("/")
def index():
    return render_template('index.html', api_token=lastfm_api)


@app.route("/callback", methods=['GET'])
def lastfm_callback():
    token = request.args['token']

    if None in (token, lastfm_api, lastfm_secret):
        return render_template('callback.html', error="Missing variable(s); check query string and environment"), 500

    try:
        lastfm = LastFM(lastfm_api, lastfm_secret)
        (session, name) = lastfm.authorize(token)
    except LastFMException as lfme:
        logging.error(lfme)
        return render_template('callback.html', error="Exception while authorizing LastFM user: " + lfme.args[0]), 500

    try:
        db = Database("users.sqlite", getenv('SECRET_KEY'))
    except DatabaseException as dbe:
        logging.error(dbe)
        return render_template('callback.html', error="Failed to open DB: " + dbe.args[0]), 500

    user = db.create_user()
    db.update_token(user, name, session)
    logging.info("Updated token for user %s", user)
    return render_template('callback.html', user=user)


@app.route("/cookies", methods=['POST'])
def cookies_callback():
    user = request.form['user']

    cookies = request.form['cookies']

    if None in (user, cookies):
        return render_template('cookies.html', error="Missing variable(s); check query string and environment"), 500

    try:
        yt_creds = YTMusic.setup(headers_raw=cookies)
    except Exception as e:
        logging.error(user, e)
        return render_template('cookies.html', error="Failed to extract headers: " + e.args[0]), 500

    try:
        db = Database("users.sqlite", getenv('SECRET_KEY'))
    except DatabaseException as dbe:
        logging.error(user, dbe)
        return render_template('cookies.html', error="Failed to open DB: " + dbe.args[0]), 500

    db.update_cookie(user, yt_creds)
    logging.info("Updated cookies for user %s", user)
    return render_template('cookies.html', user=user)


@app.route("/configure", methods=['POST'])
def config_callback():
    user = request.form.get('user')
    target = request.form.get('target')
    value = request.form.get('value')

    if user is None:
        return render_template('configure.html', error="Missing variable(s); check query string and environment"), 500

    try:
        db = Database("users.sqlite", getenv('SECRET_KEY'))
    except DatabaseException as dbe:
        logging.error(user, dbe)
        return render_template('configure.html', error="Failed to open DB: " + dbe.args[0]), 500

    snapshot = db.get_user(user)
    old = new = None

    if None not in (target, value):
        match target:
            case "reset_uuid":
                old = user
                new = user = db.reset_uuid(user)

            case "cookie":
                try:
                    yt_creds = YTMusic.setup(headers_raw=value)
                except Exception as e:
                    logging.error(user, e)
                    return render_template('configure.html', user=user, snapshot=snapshot, target=target,
                                           error="Failed to extract headers: " + e.args[0]), 500
                db.update_cookie(user, yt_creds)

            case "split_title":
                old = snapshot.split_title
                new = value.lower() in ("t", "true", "1", "on")
                db.update_split_title(user, new)

            case "interval":
                old = snapshot.interval
                new = int(value)
                db.update_interval(user, new)

            case "pause":
                old = snapshot.pause
                new = value.lower() in ("t", "true", "1", "on")
                db.update_pause(user, new)

            case "_":
                return render_template('configure.html', user=user, snapshot=snapshot, error="Unknown target!"), 500

    snapshot = db.get_user(user)
    return render_template('configure.html', user=user, snapshot=snapshot, target=target,
                           old=str(old) if old is not None else None, new=str(new) if new is not None else None)


if __name__ == "__main__":
    app.run()
