import logging
from math import ceil
import string
from time import time
from ytmusicapi import YTMusic
from pylast import _Network, PyLastError


def _normalize(text):
    return text.translate(text.maketrans('', '', string.punctuation)).lower()


class Runner:
    def __init__(self):
        self.logger = logging.getLogger("core.runner")

    def run(self, pylast: _Network, ytm: YTMusic, last_run=0, last_id=None, split_title=False):
        max_time = start_time = int(time())
        ytm_history = ytm.get_history()
        ytm_history_ids = list(map(lambda e: e['videoId'], ytm_history))

        if last_id:
            self.logger.info("Found last played ID: %s", last_id)
            if last_id in ytm_history_ids:
                ytm_history = ytm_history[0:ytm_history_ids.index(last_id)]
            else:
                self.logger.warning("Last played ID %s not in history: some tracks may not be scrobbled", last_id)

        if len(ytm_history) == 0:
            self.logger.info("No new tracks to log, skipping...")
            return start_time, last_id

        scrobbles = self.convert_to_scrobble_list(ytm_history, last_run, max_time, split_title)

        # Whichever is bigger: 1.5x the YTM history, or one song per minute we've been offline
        lfm_recent_cap = ceil(max(len(scrobbles) * 1.5, (start_time - last_run) / 60))
        lfm_history = self.get_lastfm_history(pylast, last_run, lfm_recent_cap)

        self.filter_scrobbled_tracks(scrobbles, lfm_history)
        if len(scrobbles) == 0:
            self.logger.info("All recent tracks already scrobbled")
            return start_time, ytm_history_ids[0]

        try:
            pylast.scrobble_many(scrobbles)
            self.logger.info("Writing ID %s as new last", ytm_history_ids[0])
            return start_time, ytm_history_ids[0]
        except PyLastError as ple:
            self.logger.error(ple)
            return last_run, last_id

    @staticmethod
    def filter_scrobbled_tracks(pending, current):
        start = 0
        for scrobble in current:
            trim = None
            for play in pending[start:]:
                if _normalize(scrobble['title']) == _normalize(play['title']) and \
                        _normalize(scrobble['artist']) == _normalize(play['artist']):
                    logging.info("Skipping track '%s' by %s (already scrobbled)", play['title'], play['artist'])
                    trim = pending.index(play)
                    break
            if trim is not None:
                start = trim
                pending.remove(pending[trim])

    def convert_to_scrobble_list(self, history, last_run, max_time, split_title):
        scrobbles = []
        for play in history:
            self.logger.debug("Found history entry: %s", play)
            artist, title = Runner.get_artist_and_title(play, split_title)
            self.logger.info("Scrobbling '%s' by %s", title, artist)
            self.logger.debug("max_time=%i", max_time)
            scrobble = {
                'artist': artist,
                'title': title,
                'timestamp': max_time,
                'duration': play['duration_seconds'],
            }
            if "album" in play.keys() and play['album'] is not None and "name" in play['album'].keys():
                album = play['album']['name']
                if album is not None and album != '':
                    scrobble['album'] = album
            scrobbles.append(scrobble)
            max_time -= play['duration_seconds']
            if max_time < last_run:
                self.logger.warning("Track %s has a max_time of %i, which is less than last run (%i).  Cutting off...",
                                    play['videoId'], max_time, last_run)
                break
        return scrobbles

    @staticmethod
    def get_lastfm_history(pylast, last_run, limit):
        # Workaround for pylast#422
        now_playing = pylast.get_authenticated_user().get_now_playing()
        history = [now_playing] if now_playing is not None else []
        history.extend(map(lambda e: e.track,
                           pylast.get_authenticated_user().get_recent_tracks(limit, True, last_run, stream=True)))
        if len(history) >= 2 and history[0] == history[1]:
            history = history[1:]
        return map(lambda e: {"artist": e.artist.name, "title": e.title}, history)

    @staticmethod
    def get_artist_and_title(play, split_title):
        title = play['title']
        if split_title and " - " in title:
            artist, title = title.split(" - ", 1)
        else:
            artist = ", ".join(map(lambda e: e['name'],
                                   filter(lambda e: e['id'] is not None, play['artists'])))
        return artist, title

    @staticmethod
    def get_ytm(headers):
        ytm = YTMusic(headers)
        # Storing the headers in the DB introduces carriage returns... somehow.
        # Could be a bug in the DB or the API.  Easiest solution is to manually strip the headers here.
        for key, value in ytm.headers.items():
            ytm.headers[key] = ytm.headers[key].strip()
        return ytm
