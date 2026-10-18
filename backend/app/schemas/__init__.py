from typing import Literal
from pydantic import BaseModel, ConfigDict, AwareDatetime, Field, model_validator
from app.models import SLOT_IDS, SlotStatus

class Schema(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Event(Schema):
    id: str
    timestamp: AwareDatetime
    slotId: Literal['P01','P02','P03','P04','GATE']
    type: Literal['IN','OUT','STATUS','GATE']
    previous: SlotStatus | Literal['OPEN','CLOSED']
    current: SlotStatus | Literal['OPEN','CLOSED']

    @model_validator(mode='after')
    def coherent_event(self):
        if self.slotId == 'GATE':
            if self.type != 'GATE' or self.previous not in ('OPEN','CLOSED') or self.current not in ('OPEN','CLOSED'): raise ValueError('Invalid gate event')
        elif self.type == 'GATE' or self.previous not in ('EMPTY','OCCUPIED','UNKNOWN') or self.current not in ('EMPTY','OCCUPIED','UNKNOWN'): raise ValueError('Invalid slot event')
        return self

class GateMeta(Schema):
    confirmed: bool = False
    confirmed_at: AwareDatetime | None = None
    pending_command_id: str | None = None

class Connection(Schema):
    mqtt: Literal['CONNECTED','DISCONNECTED'] = 'DISCONNECTED'
    device: Literal['ONLINE','OFFLINE','UNKNOWN'] = 'UNKNOWN'
    synchronized: bool = False

class Snapshot(Schema):
    schema_version: Literal['1.0'] = '1.0'
    source: Literal['LIVE'] = 'LIVE'
    timestamp: AwareDatetime
    slots: dict[str, SlotStatus]
    gate: Literal['OPEN','CLOSED'] = 'CLOSED'
    gate_meta: GateMeta = Field(default_factory=GateMeta)
    connection: Connection = Field(default_factory=Connection)
    stream_id: str
    revision: int = Field(ge=0)
    events: list[Event]

    @model_validator(mode='after')
    def exact_slots(self):
        if set(self.slots) != set(SLOT_IDS):
            raise ValueError('Exactly P01-P04 required')
        return self

class Envelope(Schema):
    schema_version: Literal['1.0'] = '1.0'
    stream_id: str
    revision: int = Field(ge=0)

class EventList(Envelope):
    events: list[Event]

class Statistics(Envelope):
    scope: Literal['DATABASE_LIFETIME'] = 'DATABASE_LIFETIME'
    entries: int = Field(ge=0)
    exits: int = Field(ge=0)
    by_slot: dict[str, int]

class Summary(Envelope):
    total: int = 4
    occupied: int
    free: int
    unknown: int
    status: Literal['AVAILABLE','FULL','UNKNOWN']
    full: bool

class SlotItem(Schema):
    slot_id: Literal['P01','P02','P03','P04']
    status: SlotStatus

class SlotList(Envelope):
    slots: list[SlotItem]

class Health(Schema):
    status: Literal['ok'] = 'ok'
    database: Literal['ok'] = 'ok'
    phase: Literal['BACKEND_CORE','MQTT_SUBSCRIBER','REALTIME_GATE'] = 'BACKEND_CORE'
    mqtt_enabled: bool = False
    websocket_enabled: bool = True


class GateRequest(Schema):
    command_id: str = Field(strict=True,pattern=r'^[!-~]{1,80}$')
    status: Literal['OPEN','CLOSED']
    direction: Literal['ENTRY','EXIT']

class GateCommand(Schema):
    command_id: str
    requested_status: Literal['OPEN','CLOSED']
    direction: Literal['ENTRY','EXIT']
    state: Literal['PENDING','CONFIRMED','ERROR','TIMEOUT']
    created_at: AwareDatetime
    completed_at: AwareDatetime | None
    error_code: str | None

class SnapshotMessage(Schema):
    type: Literal['parking.snapshot']
    schema_version: Literal['1.0']
    data: Snapshot

class GateMessage(Envelope):
    type: Literal['gate.command']
    data: GateCommand
