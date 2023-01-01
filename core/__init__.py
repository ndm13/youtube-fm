import logging
from os import getenv, path
from dotenv import load_dotenv

from .config_dir import config_dir
from .db import Database, DatabaseException
from .runner import Runner

load_dotenv(path.join(config_dir, ".env"))
logging.basicConfig(level=getenv('LOG_LEVEL', 'INFO').upper())
