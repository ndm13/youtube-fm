import logging
from os import getenv
from time import time
from threading import Timer
from queue import Queue

from pylast import LastFMNetwork

from core import Runner, Database

logger = logging.getLogger("daemon")
queue = Queue()


def run():
    timer = Timer(getenv("INTERVAL", 60), run)
    timer.daemon = True
    timer.start()
    queue.put(timer)

    logger.info("Connecting to database")
    db = Database("users.sqlite", getenv('SECRET_KEY'))
    runner = Runner()

    logger.info("Started run, pulling users")
    users = db.get_users_for_run(int(time()))
    for user in users:
        logger.info("Running update for user %s (%s)", user.name, user.uuid)
        last_run, last_id = runner.run(get_pylast(user), Runner.get_ytm(user.cookie), user.last_run, user.last_id,
                                       user.split_title)
        if last_run > user.last_run:
            db.update_last_run(user.uuid, last_run)
        if last_id != user.last_id:
            db.update_last_id(user.uuid, last_id)

    logger.info("Ran stats for %i users", len(users))
    db.con.close()


def get_pylast(user):
    # Work around a bug in pylast: https://github.com/pylast/pylast/issues/300
    return LastFMNetwork(getenv('LASTFM_API'), getenv('LASTFM_SECRET'), user.token, user.name)


run()
while not queue.empty():
    queue.get().join()