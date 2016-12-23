import uuid

from pymemcache.client.base import Client


class Store(object):
    def __init__(self):
        self._client = Client(('memcache', 11211))

    def save(self, text):
        id = str(uuid.uuid4())
        self._client.set(id, text)
        return id

    def load(self, id):
        return self._client.get(id)
