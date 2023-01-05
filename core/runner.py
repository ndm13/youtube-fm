import logging
from os import getenv
from time import time
from ytmusicapi import YTMusic
from pylast import LastFMNetwork, PyLastError


class Runner:
    def __init__(self, database):
        self.db = database
        self.logger = logging.getLogger("core.runner")

    def run_user(self, user):
        max_time = start_time = int(time())
        self.logger.info("Running update for user %s (%s)", user.name, user.uuid)

        # Work around a bug in pylast: https://github.com/pylast/pylast/issues/300
        pylast = LastFMNetwork(getenv('LASTFM_API'), getenv('LASTFM_SECRET'), user.token, user.name)
        ytm = YTMusic(user.cookie)

        # Storing the headers in the DB introduces carriage returns... somehow.
        # Could be a bug in the DB or the API.  Easiest solution is to manually strip the headers here.
        for key, value in ytm.headers.items():
            ytm.headers[key] = ytm.headers[key].strip()
        history = ytm.get_history()

        ids = list(map(lambda e: e['videoId'], history))

        if user.last_id:
            self.logger.info("Found last played ID: %s", user.last_id)
            if user.last_id in history:
                history = history[0:ids.index(user.last_id)]
            else:
                self.logger.warning("Last played ID missing for %s: some tracks may not be scrobbled", user.name)

        if len(history) == 0:
            self.logger.info("No new tracks to log, skipping...")
            self.db.update_last_run(user.uuid, start_time)
            return

        many = []
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
            many.append({"artist": artist, "title": title, "timestamp": max_time})
            max_time -= entry.get("duration_seconds")

        lfm_history = pylast.get_authenticated_user().get_recent_tracks(len(many) * 1.5, True, user.last_run)
        lfm_history = map(lambda e: {"artist": e.track.artist.name, "title": e.track.title}, lfm_history)
        many_start = 0
        for lfm in lfm_history:
            trim = None
            for ytm in many[many_start:]:
                if lfm["title"] == ytm["title"] and lfm["artist"] == ytm["artist"]:
                    logging.info("Skipping track '%s' by %s (already scrobbled)", ytm["title"], ytm["artist"])
                    trim = many.index(ytm)
                    break
            if trim is not None:
                many_start = trim
                many.remove(many[trim])

        if len(many) == 0:
            self.logger.info("No new tracks to log, skipping...")
            self.db.update_last_run(user.uuid, start_time)
            return

        try:
            pylast.scrobble_many(many)
            self.logger.info("Writing ID %s as new last", ids[0])
            self.db.update_last_id(user.uuid, ids[0])
            self.db.update_last_run(user.uuid, start_time)
        except PyLastError as ple:
            self.logger.error(ple)
