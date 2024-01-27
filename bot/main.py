import os
import handlers as handlers
from main_menu import set_main_menu
from middlewares import SomeMiddleware

from aiogram import Bot, Dispatcher
import logging

from middlewares.append_data_acces_object import JsonAndNatsMiddleware
from nats.aio.client import Client as NATS

from config import load_config, Config
from middlewares.throttling import ThrottlingMiddleware

# nats-server --config Z:/python_project/dls_project/bot/nats-server.conf


async def main():
    configfile = os.environ.get("CONFIG", "config.ini")
    config: Config = load_config(configfile)

    logging.basicConfig(level=logging.INFO, filename=config.logging_path, filemode="a",
                       format="%(asctime)s %(levelname)s %(message)s")

    bot = Bot(token=config.tg_token)
    await set_main_menu(bot, mode=config.mode)

    nc = NATS()
    await nc.connect(f"nats://{config.nats.ip}:{config.nats.port}")
    logging.info('connected to NATS')

    dp = Dispatcher()
    dp.include_router(handlers.router)

    dp.message.outer_middleware(ThrottlingMiddleware())
    dp.update.middleware(SomeMiddleware())
    dp.update.middleware(JsonAndNatsMiddleware(link_for_json=config.json_path, nats=nc, mode=config.mode))

    logging.info('starting bot')

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
