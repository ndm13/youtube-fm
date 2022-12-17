import logging
from os import getenv
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from time import time

from lastfm import LastFM
from db import Database


def run_user():
    max_time = start_time = int(time())
    logging.info("Running update for user %s (%s)", user.name, user.uuid)

    lastfm = LastFM(getenv('LASTFM_API'), getenv('LASTFM_SECRET'), session_token=user.token)
    ytm = YTMusic(user.cookie)
    # Storing the headers in the DB introduces carriage returns... somehow.
    # Could be a bug in the DB or the API.  Easiest solution is to manually strip the headers here.
    for key, value in ytm.headers.items():
        ytm.headers[key] = ytm.headers[key].strip()
    history = ytm.get_history()

    ids = list(map(lambda e: e['videoId'], history))

    if user.last_id:
        logging.info("Found last played ID: %s", user.last_id)
        history = history[0:ids.index(user.last_id)]

    if len(history) == 0:
        logging.info("No new tracks to log, skipping...")
        return

    for entry in history:
        logging.debug("Found history entry: %s", entry)
        title = entry.get("title")
        if user.split_title and " - " in title:
            (artist, title) = title.split(" - ")
        else:
            artist = ", ".join(map(lambda e: e["name"], filter(lambda e: e["id"] is not None, entry.get("artists"))))
        logging.info("Scrobbling '%s' by %s", title, artist)
        logging.debug("min_time=%i", max_time)
        if not lastfm.scrobble(artist, title, max_time):
            logging.error("Failed to scrobble track: '%s' by %s (id: %s)", title, artist, entry.get('videoId'))
        max_time -= entry.get("duration_seconds")

    logging.info("Writing ID %s as new last", ids[0])
    db.update_last_id(user.uuid, ids[0])
    db.update_last_run(user.uuid, start_time)


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())

    logging.info("Connecting to database")
    db = Database("users.sqlite", getenv('SECRET_KEY'))
    logging.info("Started run, pulling users")
    users = db.get_users_for_run(int(time()))
    for user in users:
        run_user()
    logging.info("Ran stats for %i users", len(users))
