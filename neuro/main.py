import logging
import os
from io import BytesIO

from nats.aio.client import Client as NATS
import asyncio
import base64
import json
from PIL import Image

from config import load_config, Config
from style_transfer import StyleTransfer
from cyclegan import CycleGan


class RequestHandler:
    def __init__(self, nats):
        self.nc = nats

    async def handle_request(self, msg):
        logging.info('start of request processing')

        reply = msg.reply
        data = json.loads(msg.data.decode())

        images_data = [Image.open(BytesIO(base64.b64decode(image))) for image in data["images"]]

        result = None
        error = None

        if data['model'] == 'CycleGan':
            obj = CycleGan()
            try:
                result, error = process_image(images_data, obj, mode=data["mode"])
            except Exception as r:
                logging.error(f'In CycleGAN happened {r}')
                result, error = None, 'idk_error'
        elif data['model'] == 'StyleTransfer':
            obj = StyleTransfer()
            result, error = process_image(images_data, obj, num_steps=data["steps"])

        img_bytes_arr = BytesIO()

        result.save(img_bytes_arr, format="JPEG")
        img_bytes_arr.seek(0)
        result = base64.b64encode(img_bytes_arr.getvalue()).decode()

        json_data = json.dumps({"result": result, "error": error})

        logging.info('end of request processing')
        await self.nc.publish(reply, json_data.encode())


async def run():
    logging.basicConfig(level=logging.INFO, filename="neuro_log.log", filemode="a",
                        format="%(asctime)s %(levelname)s %(message)s")

    configfile = os.environ.get("CONFIG", "config.ini")
    config: Config = load_config(configfile)
    nc = NATS()

    request_handler = RequestHandler(nc)

    async def message_handler(msg):
        await request_handler.handle_request(msg)

    await nc.connect(f"nats://{config.ip}:{config.port}")
    await nc.subscribe("neuro", cb=message_handler)
    logging.info('connected to NATS')


def process_image(images, obj, **kwargs):
    result, error = obj(*images, **kwargs)

    return result, error


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.run_forever()
    loop.close()
