import logging
from os import getenv
from dotenv import load_dotenv

from .db import Database, DatabaseException
from .lastfm import LastFM, LastFMException
from .runner import Runner

load_dotenv()
logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())
