import logging
import os

from flask import (
    Blueprint, flash, Markup, redirect, render_template, request, session, url_for
)

from .db import get_db

bp = Blueprint('configure', __name__, url_prefix='/configure')
logger = logging.getLogger("setup")

lastfm_key = os.getenv('LASTFM_API')
lastfm_secret = os.getenv('LASTFM_SECRET')


@bp.route("", methods=['GET', 'POST'])
def index():
    db = get_db()

    if request.method == "POST" and 'user' in request.form.keys():
        uid = request.form.get('user').replace('-', '')
        try:
            user = db.get_user(uid)
        except ValueError:
            flash("Invalid user ID", "error")
            return render_template("configure.html"), 401

        if not user:
            flash("Invalid user ID", "error")
            return render_template("configure.html"), 401

        session['user'] = user.uuid
        return render_template('configure.html', user=user)

    if 'user' in session:
        user = db.get_user(session['user'])

        if not user:
            flash("Invalid user ID", "error")
            session.pop('user', None)
            return render_template("configure.html"), 401

        return render_template("configure.html", user=user)

    return render_template('configure.html')


@bp.route("/split_title", methods=['POST'])
def split_title():
    if request.form.get('value') and session['user']:
        value = request.form.get('value').lower() in ("t", "true", "1", "yes", "on")
        db = get_db()
        old = db.get_user(session['user'])
        db.update_split_title(old.uuid, value)
        flash("Split Title is now " + ("enabled" if value else "disabled"))

    return redirect(url_for('configure.index'))


@bp.route("/interval", methods=['POST'])
def interval():
    if request.form.get('value') and session['user']:
        value = int(request.form.get('value'))
        db = get_db()
        old = db.get_user(session['user'])
        db.update_interval(old.uuid, value)
        flash("Update interval is now " + str(value) + " seconds")

    return redirect(url_for('configure.index'))


@bp.route("/pause", methods=['POST'])
def pause():
    if request.form.get('value') and session['user']:
        value = request.form.get('value').lower() in ("t", "true", "1", "yes", "on")
        db = get_db()
        old = db.get_user(session['user'])
        db.update_pause(old.uuid, value)
        flash("Updates are currently " + ("paused" if value else "active"))

    return redirect(url_for('configure.index'))


@bp.route("/reset_id", methods=['POST'])
def reset_id():
    if session['user']:
        db = get_db()
        old = db.get_user(session['user'])
        new = db.reset_uuid(old.uuid)
        session['user'] = new
        flash("Your new account ID is " + Markup("<kbd>" + new + "</kbd>") + ".  Keep this somewhere safe!")

    return redirect(url_for('configure.index'))


@bp.route('/signout')
def sign_out():
    session.pop('user', None)
    return redirect(url_for('index'))
