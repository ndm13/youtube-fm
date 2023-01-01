from pylast import LastFMNetwork, SessionKeyGenerator


class LastFMException(Exception):
    pass


class LastFM:
    def __init__(self, api_key, secret_key, session_token=None, api_root='https://ws.audioscrobbler.com/2.0/'):
        self.pylast = LastFMNetwork(api_key, secret_key, session_token if not None else "")

    def authorize(self, user_token):
        return SessionKeyGenerator(self.pylast).get_web_auth_session_key_username(None, user_token)

    def scrobble(self, artist, title, timestamp):
        if self.pylast.session_key == "":
            raise LastFMException("session_key is not set: please call authorize(user_token)")
        self.pylast.scrobble(artist, title, timestamp)
        return True
