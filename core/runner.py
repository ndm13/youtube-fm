import logging
from os import getenv
from time import time
from ytmusicapi import YTMusic

from . import LastFM


class Runner:
    def __init__(self, database):
        self.db = database
        self.logger = logging.getLogger("core.runner")

    def run_user(self, user):
        max_time = start_time = int(time())
        self.logger.info("Running update for user %s (%s)", user.name, user.uuid)

        lastfm = LastFM(getenv('LASTFM_API'), getenv('LASTFM_SECRET'), session_token=user.token)
        ytm = YTMusic(user.cookie)
        # Storing the headers in the DB introduces carriage returns... somehow.
        # Could be a bug in the DB or the API.  Easiest solution is to manually strip the headers here.
        for key, value in ytm.headers.items():
            ytm.headers[key] = ytm.headers[key].strip()
        history = ytm.get_history()

        ids = list(map(lambda e: e['videoId'], history))

        if user.last_id:
            self.logger.info("Found last played ID: %s", user.last_id)
            history = history[0:ids.index(user.last_id)]

        if len(history) == 0:
            self.logger.info("No new tracks to log, skipping...")
            self.db.update_last_run(user.uuid, start_time)
            return

        for entry in history:
            self.logger.debug("Found history entry: %s", entry)
            title = entry.get("title")
            if user.split_title and " - " in title:
                (artist, title) = title.split(" - ")
            else:
                artist = ", ".join(map(lambda e: e["name"],
                                       filter(lambda e: e["id"] is not None, entry.get("artists"))))
            self.logger.info("Scrobbling '%s' by %s", title, artist)
            self.logger.debug("min_time=%i", max_time)
            if not lastfm.scrobble(artist, title, max_time):
                self.logger.error("Failed to scrobble track: '%s' by %s (id: %s)", title, artist, entry.get('videoId'))
            max_time -= entry.get("duration_seconds")

        self.logger.info("Writing ID %s as new last", ids[0])
        self.db.update_last_id(user.uuid, ids[0])
        self.db.update_last_run(user.uuid, start_time)
