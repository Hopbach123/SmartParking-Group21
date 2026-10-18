"""Inbound MQTT only: strict types, fixed slot IDs, no protocol/topic changes."""
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr, Field

PREFIX = 'smartparking/group21'
SLOT_TOPICS = {f'{PREFIX}/slots/{slot}/state': slot for slot in ('P01','P02','P03','P04')}
DEVICE_TOPIC = f'{PREFIX}/device/status'
GATE_TOPIC = f'{PREFIX}/gate/status'
TOPICS = (*SLOT_TOPICS, DEVICE_TOPIC, GATE_TOPIC)

class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    device_id: StrictStr

class SlotPayload(Payload):
    slot_id: Literal['P01','P02','P03','P04']
    occupied: StrictBool

class OnlinePayload(Payload):
    status: Literal['online']
    uptime_ms: int = Field(strict=True,ge=0,le=4294967295)

class OfflinePayload(Payload):
    status: Literal['offline']

class GatePayload(Payload):
    command_id: str = Field(strict=True,pattern=r'^[!-~]{1,80}$')
    status: Literal['OPENED','CLOSED','ERROR']


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Non-JSON numeric constant')


def parse_message(topic, payload, expected_device='esp32-01'):
    if topic not in TOPICS:
        raise ValueError('Unexpected topic')
    if not isinstance(payload, bytes) or not 0 < len(payload) <= 1024:
        raise ValueError('Invalid payload size/type')
    data = json.loads(payload.decode('utf-8'),object_pairs_hook=no_duplicate_keys,parse_constant=reject_constant)
    if not isinstance(data, dict):
        raise ValueError('Expected JSON object')
    if topic in SLOT_TOPICS:
        result = SlotPayload.model_validate(data)
        if result.slot_id != SLOT_TOPICS[topic]:
            raise ValueError('Topic/slot mismatch')
    elif topic == DEVICE_TOPIC:
        result = (OnlinePayload if data.get('status') == 'online' else OfflinePayload).model_validate(data)
    else:
        result = GatePayload.model_validate(data)
    if result.device_id != expected_device:
        raise ValueError('Unexpected device_id')
    return result
