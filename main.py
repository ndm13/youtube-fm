import logging
from os.path import exists
from os import getenv
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from pylast import LastFMNetwork
from time import time

max_time = int(time())
logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())
load_dotenv()

if not exists("headers_auth.json"):
    if len(getenv('HEADERS_FILE', '')) > 0 and exists(getenv('HEADERS_FILE')):
        with open(getenv('HEADERS_FILE'), 'r') as file:
            YTMusic.setup("headers_auth.json", headers_raw=file.read())
    else:
        YTMusic.setup("headers_auth.json")

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

with open("last_id.txt", 'w') as file:
    logging.info("Writing ID %s as new last", ids[0])
    file.write(ids[0])

network = LastFMNetwork(
    api_key=getenv('LASTFM_API'),
    api_secret=getenv('LASTFM_SECRET'),
    username=getenv('LASTFM_USER'),
    password_hash=getenv('LASTFM_PASSWORD')
)

split_title = getenv('SPLIT_TITLE', '').lower() in ['true', 't', '1']

for entry in history:
    logging.debug("Found history entry: %s", entry)

    title = entry.get("title")
    artist = None

    if split_title and title.index(" - ") > 0:
        (artist, title) = title.split(" - ")
    else:
        artist = ", ".join(map(lambda e: e["name"], filter(lambda e: e["id"] is not None, entry.get("artists"))))

    logging.info("Scrobbling '%s' by %s", title, artist)
    logging.debug("min_time=%i", max_time)
    network.scrobble(artist, title, max_time)
    max_time -= entry.get("duration_seconds")
