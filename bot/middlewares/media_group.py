import asyncio
import logging
from typing import List, Union

from aiogram import Bot, Dispatcher, types
from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler


class SomeMiddleware(BaseMiddleware):
    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.1):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency
        super().__init__()

    async def __call__(
            self,
            handler,
            event,
            data):
        if not (event.message and event.message.media_group_id and event.message.photo):
            return await handler(event, data)
        try:
            self.album_data[event.message.media_group_id].append(event.message)
            logging.info(f'{event.message.media_group_id}: another media group object')
            return
        except KeyError:
            logging.info(f'{event.message.media_group_id}: first media group object')
            self.album_data[event.message.media_group_id] = [event.message]
            await asyncio.sleep(self.latency)

            data["album"] = self.album_data[event.message.media_group_id]

        result = await handler(event, data)

        # After handler
        if event.message.media_group_id:
            logging.info(f'{event.message.media_group_id}: deleting media group album')
            del self.album_data[event.message.media_group_id]

        return result

# @dp.message(is_media_group=True, content_types=types.ContentType.ANY)
# async def handle_albums(message: types.Message, album: List[types.Message]):
#     """This handler will receive a complete album of any type."""
#     media_group = types.MediaGroup()
#     for obj in album:
#         if obj.photo:
#             file_id = obj.photo[-1].file_id
#         else:
#             file_id = obj[obj.content_type].file_id
#
#         try:
#             # We can also add a caption to each file by specifying `"caption": "text"`
#             media_group.attach({"media": file_id, "type": obj.content_type})
#         except ValueError:
#             return await message.answer("This type of album is not supported by aiogram.")
#
#     await message.answer_media_group(media_group)
