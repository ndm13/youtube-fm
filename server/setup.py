import logging
import os

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)
from ytmusicapi import YTMusic

from core import LastFM, LastFMException
from .db import get_db

bp = Blueprint('setup', __name__, url_prefix='/setup')
logger = logging.getLogger("setup")

lastfm_key = os.getenv('LASTFM_API')
lastfm_secret = os.getenv('LASTFM_SECRET')


@bp.route("")
def index():
    return render_template('setup/index.html', api_token=lastfm_key)


@bp.route("/lastfm", methods=['GET'])
def lastfm():
    token = request.args['token']

    try:
        api = LastFM(lastfm_key, lastfm_secret)
        (lastfm_session, name) = api.authorize(token)
    except LastFMException as lfme:
        logger.error(lfme)
        flash("Exception while authorizing LastFM user: " + lfme.args[0], "error")
        return render_template("setup/lastfm.html", api_token=lastfm_key), 401

    session.pop("_flashes", None)
    db = get_db()
    user = db.create_user()
    db.update_token(user, name, lastfm_session)
    logger.info("Updated token for user %s", user)
    session['user'] = user
    return render_template("setup/lastfm.html")


@bp.route("/ytmusic", methods=['GET', 'POST'])
def ytmusic():
    user = session["user"]
    if request.method == 'POST':
        cookies = request.form['cookies']
        if cookies is None:
            flash("Error submitting form: couldn't find cookies!", "error"), 400
            return render_template("setup/ytmusic.html")

        if user is None:
            flash("Session error: user info is missing!", "error"), 401
            return render_template("setup/ytmusic.html")

        try:
            creds = YTMusic.setup(headers_raw=cookies)
        except Exception as e:
            logging.error(user, e)
            flash("Error in YouTube Music API: " + e, "error")
            return render_template("setup/ytmusic.html")

        session.pop("_flashes", None)
        db = get_db()
        db.update_cookie(user, creds)
        logging.info("Updated cookies for user %s", user)
        return redirect(url_for("setup.done"))

    return render_template("setup/ytmusic.html")


@bp.route("/done")
def done():
    return render_template("setup/done.html")
