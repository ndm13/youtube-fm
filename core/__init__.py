import logging
from os import getenv
from dotenv import load_dotenv

from core.db import Database, DatabaseException
from core.lastfm import LastFM, LastFMException
from core.runner import Runner

load_dotenv()
logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())
