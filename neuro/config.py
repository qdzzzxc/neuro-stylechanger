import configparser
from dataclasses import dataclass


@dataclass
class Config:
    ip: str
    port: str


def load_config(path: str | None = None) -> Config:
    config = configparser.ConfigParser()
    config.read(path)

    return Config(ip=config.get("nats", "ip"),
                  port=config.get("nats", "port")
                  )
