import os
import math
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class Settings:
    db_path: Path
    cors_origins: tuple[str, ...] = ()

    mqtt_enabled: bool = False  # explicit Settings in unit tests never opens the network
    mqtt_host: str = 'broker.hivemq.com'
    mqtt_port: int = 1883
    mqtt_device_id: str = 'esp32-01'
    heartbeat_timeout: float = 30.0

    ack_timeout: float = 5.0

    def __post_init__(self):
        if not self.mqtt_host or not 1 <= self.mqtt_port <= 65535:
            raise ValueError('Invalid MQTT host/port')
        if not math.isfinite(self.ack_timeout) or self.ack_timeout <= 0:
            raise ValueError('ack_timeout must be positive')
        if not math.isfinite(self.heartbeat_timeout) or self.heartbeat_timeout <= 0:
            raise ValueError('heartbeat_timeout must be positive')

    @classmethod
    def from_env(cls):
        load_dotenv(BACKEND_ROOT / '.env', override=False)
        raw = Path(os.getenv('SMART_PARKING_DB_PATH', 'data/smartparking.sqlite3'))
        path = raw if raw.is_absolute() else BACKEND_ROOT / raw
        origins = tuple(x.strip() for x in os.getenv('SMART_PARKING_CORS_ORIGINS', 'http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173').split(',') if x.strip())
        flag = os.getenv('SMART_PARKING_MQTT_ENABLED', 'true').lower()
        if flag not in ('true', 'false'):
            raise ValueError('SMART_PARKING_MQTT_ENABLED must be true/false')
        return cls(path.resolve(), origins, mqtt_enabled=flag == 'true',
                   mqtt_host=os.getenv('SMART_PARKING_MQTT_HOST', 'broker.hivemq.com'),
                   mqtt_port=int(os.getenv('SMART_PARKING_MQTT_PORT', '1883')),
                   heartbeat_timeout=float(os.getenv('SMART_PARKING_HEARTBEAT_TIMEOUT', '30')),
                   ack_timeout=float(os.getenv('SMART_PARKING_ACK_TIMEOUT', '5')))
