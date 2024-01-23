import logging
from io import BytesIO

from nats.aio.client import Client as NATS
import asyncio
import base64
import json
from PIL import Image
from torchvision.transforms import transforms

from style_transfer import StyleTransfer
from cyclegan import CycleGan


async def run():
    logging.basicConfig(level=logging.INFO, filename="neuro_log.log", filemode="w",
                       format="%(asctime)s %(levelname)s %(message)s")

    nc = NATS()

    async def message_handler(msg):
        logging.info('начало обработки запроса')

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

        logging.info('конец обработки запроса')
        await nc.publish(reply, json_data.encode())

    await nc.connect("nats://localhost:4222")
    await nc.subscribe("example_subject", cb=message_handler)
    logging.info('Запуск NATS соединения')

def process_image(images, obj, **kwargs):
    result, error = obj(*images, **kwargs)

    #result.save(f"saved_image_.jpg")

    return result, error


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.run_forever()
    loop.close()
