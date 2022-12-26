import logging
from os import getenv
from time import time

from core import Runner, Database

logger = logging.getLogger("daemon")

logger.info("Connecting to database")
db = Database("users.sqlite", getenv('SECRET_KEY'))
runner = Runner(db)

logger.info("Started run, pulling users")
users = db.get_users_for_run(int(time()))
for user in users:
    runner.run_user(user)
logger.info("Ran stats for %i users", len(users))
db.con.close()
