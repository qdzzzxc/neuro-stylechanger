import os
import json

from aiogram import BaseMiddleware


class JsonAndNatsMiddleware(BaseMiddleware):
    def __init__(self, link_for_json, nats, mode):
        super().__init__()
        self.dao = DataAccess(link_for_json)
        self.nats = nats
        self.mode = mode

    async def __call__(
            self,
            handler,
            event,
            data,
    ):
        data["dao"] = self.dao
        data["nats"] = self.nats
        data["mode"] = self.mode
        return await handler(event, data)


class DataAccess(object):
    def __init__(self, file_link):
        self.file_link = file_link
        if not (os.path.exists(file_link)):
            self.data = {}
        else:
            with open(file_link, 'r') as json_file:
                self.data = json.load(json_file)

    def save(self):
        with open(self.file_link, 'w') as json_file:
            json.dump(self.data, json_file, indent=2)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()
