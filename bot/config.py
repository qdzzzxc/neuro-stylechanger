import configparser
from dataclasses import dataclass


@dataclass
class Config:
    tg_token: str
    json_path: str
    logging_path: str


def load_config(path: str | None = None) -> Config:
    config = configparser.ConfigParser()
    config.read(path)

    return Config(tg_token=config.get("tg_bot", "token"),
                  json_path=config.get("json", "path"),
                  logging_path=config.get("logging", "path"),
                  )
