import time
import uuid

import pymongo


class Store(object):
    def __init__(self, storage_url='mongodb://mongo'):
        self._client = pymongo.MongoClient(storage_url)
        self._db = self._client.muds
        self._coll = self._db.requests

    def save(self, text):
        id = str(uuid.uuid4())
        now = int(time.time())

        self._coll.insert_one({'uuid': id,
                               'timestamp': now,
                               'text': text})

        return id

    def load(self, id):
        obj = self._coll.find_one({'uuid': id})
        if obj:
            return obj['text']
        return None
