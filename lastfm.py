import hashlib
import requests
from bs4 import BeautifulSoup


class LastFMException(BaseException):
    pass


class LastFM:
    api_head = 'https://ws.audioscrobbler.com/2.0/'

    def __init__(self, api_key, secret_key, session_token=None, api_head=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.session_key = session_token
        if api_head is not None:
            self.api_head = api_head

    def authorize(self, user_token):
        params = {
            'api_key': self.api_key,
            'method': 'auth.getSession',
            'token': user_token
        }
        params['api_sig'] = self.hash_request(params)

        xml = BeautifulSoup(requests.post(self.api_head, params).text, 'xml')
        if xml.find('lfm').attrs.get('status') == 'failed':
            raise LastFMException(xml.find('error').text)

        self.session_key = xml.find('key').text
        return self.session_key

    def scrobble(self, artist, title, timestamp):
        if self.session_key is None:
            raise LastFMException("session_key is not set: please call authorize(user_token)")
        params = {
            'method': 'track.scrobble',
            'api_key': self.api_key,
            'timestamp': timestamp,
            'track': title,
            'artist': artist,
            'sk': self.session_key
        }
        params['api_sig'] = self.hash_request(params)

        xml = BeautifulSoup(requests.post(self.api_head, params).text, 'xml')
        return xml.find('lfm').attrs.get("status") == "ok"

    def hash_request(self, obj):
        string = ''
        for i in sorted(obj.keys()):
            string += i
            string += str(obj[i])
        string += self.secret_key
        return hashlib.md5(string.encode('utf8')).hexdigest()
