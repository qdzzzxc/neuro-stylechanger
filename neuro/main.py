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


async def run():
    logging.basicConfig(level=logging.INFO, filename="neuro_log.log", filemode="w",
                        format="%(asctime)s %(levelname)s %(message)s")

    configfile = os.environ.get("CONFIG", "config.ini")
    config: Config = load_config(configfile)
    nc = NATS()

    async def message_handler(msg):
        logging.info('start of request processing')

        reply = msg.reply
        data = json.loads(msg.data.decode())

        images_data = [Image.open(BytesIO(base64.b64decode(image))) for image in data["images"]]

        result = None
        error = None

        if data['model'] == 'CycleGan':
            obj = CycleGan()
            result, error = process_image(images_data, obj, mode=data["mode"])
        elif data['model'] == 'StyleTransfer':
            obj = StyleTransfer()
            result, error = process_image(images_data, obj, num_steps=data["steps"])

        img_bytes_arr = BytesIO()

        result.save(img_bytes_arr, format="JPEG")
        img_bytes_arr.seek(0)
        result = base64.b64encode(img_bytes_arr.getvalue()).decode()

        json_data = json.dumps({"result": result, "error": error})

        logging.info('end of request processing')
        await nc.publish(reply, json_data.encode())

    await nc.connect(f"nats://{config.ip}:{config.port}")
    await nc.subscribe("tg_bot", cb=message_handler)
    logging.info('connected to NATS')


def process_image(images, obj, **kwargs):
    result, error = obj(*images, **kwargs)

    return result, error


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.run_forever()
    loop.close()
