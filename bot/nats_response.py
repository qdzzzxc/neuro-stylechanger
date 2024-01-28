import logging

import json
import base64
import asyncio


async def request_to_neuro(images, model, connection, mode="Monet", steps=50):

    images_data = [base64.b64encode(image.getvalue()).decode() for image in images]

    json_data = json.dumps({"images": images_data, "model": model, "mode": mode, "steps": steps})

    try:
        response = await connection.request("neuro", json_data.encode(), timeout=200)

        data = json.loads(response.data.decode())

        result = base64.b64decode(data["result"])
        error = data["error"]

        return result, error
    except asyncio.TimeoutError:

        logging.error(f'TimeoutError in nats request')
        return None, 'timeout'

    except Exception as error:
        logging.error(f'{error} in nats request')
        return None, 'idk_error'
