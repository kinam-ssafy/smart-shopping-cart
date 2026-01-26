import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    service_uuid: str = "7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a01"
    char_uuid: str    = "7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a02"

    uid_ttl_sec: float = 5.0
    expiry_check_sec: float = 0.5

    mqtt_host: str = os.getenv("MQTT_HOST", "")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_topic: str = os.getenv("MQTT_TOPIC", "")
    mqtt_id: str = os.getenv("MQTT_ID", "")
    mqtt_pw: str = os.getenv("MQTT_PW", "")

settings = Settings()
