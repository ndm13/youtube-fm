import logging
from os import getenv, path
from dotenv import load_dotenv

from .db import Database, DatabaseException
from .lastfm import LastFM, LastFMException
from .runner import Runner

envfile = path.abspath(path.join(path.dirname(path.abspath(__file__)), "..", ".env"))
load_dotenv(envfile)
logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())
