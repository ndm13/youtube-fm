import logging
from os.path import exists
from os import getenv
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from time import time

from lastfm import LastFM


def init_ytmusicapi_headers():
    if not exists("headers_auth.json"):
        if len(getenv('HEADERS_FILE', '')) > 0 and exists(getenv('HEADERS_FILE')):
            with open(getenv('HEADERS_FILE'), 'r') as file:
                YTMusic.setup("headers_auth.json", headers_raw=file.read())
        else:
            YTMusic.setup("headers_auth.json")


def scrobble(timestamp):
    logging.debug("Found history entry: %s", entry)

    title = entry.get("title")

    if split_title and " - " in title:
        (artist, title) = title.split(" - ")
    else:
        artist = ", ".join(map(lambda e: e["name"], filter(lambda e: e["id"] is not None, entry.get("artists"))))

    logging.info("Scrobbling '%s' by %s", title, artist)
    logging.debug("min_time=%i", timestamp)
    if not lastfm.scrobble(artist, title, timestamp):
        logging.error("Failed to scrobble track: '%s' by %s (id: %s)", title, artist, entry.get('videoId'))


if __name__ == "__main__":
    load_dotenv()
    split_title = getenv('SPLIT_TITLE', '').lower() in ['true', 't', '1']

    logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())

    if getenv('LASTFM_SESSION'):
        lastfm = LastFM(getenv('LASTFM_API'), getenv('LASTFM_SECRET'), session_token=getenv('LASTFM_SESSION'))
    elif getenv('LASTFM_TOKEN'):
        lastfm = LastFM(getenv('LASTFM_API'), getenv('LASTFM_SECRET'))
        logging.warning("Using LASTFM_TOKEN: You will need to generate a new token every run!")
        session_key = lastfm.authorize(getenv('LASTFM_TOKEN'))
        logging.warning("To prevent this, set the LASTFM_SESSION environment variable generated below:")
        logging.warning("\tLASTFM_SESSION=%s", session_key)
    else:
        logging.error("You will need to generate a user token:")
        logging.error("https://www.last.fm/api/auth?api_key=%s&cb=http://localhost:5555", getenv('LASTFM_API'))
        raise Exception("Can't authenticate! Set LASTFM_TOKEN or LASTFM_SESSION to access Last.FM")

    init_ytmusicapi_headers()

    max_time = int(time())
    history = YTMusic('headers_auth.json').get_history()
    ids = list(map(lambda e: e['videoId'], history))

    if exists("last_id.txt"):
        with open("last_id.txt") as file:
            last_id = file.readline()
        logging.info("Found last played ID: %s", last_id)
        history = history[0:ids.index(last_id)]

    if len(history) == 0:
        logging.info("No new tracks to log, exiting...")
        exit(0)

    for entry in history:
        scrobble(max_time)
        max_time -= entry.get("duration_seconds")

    with open("last_id.txt", 'w') as file:
        logging.info("Writing ID %s as new last", ids[0])
        file.write(ids[0])
