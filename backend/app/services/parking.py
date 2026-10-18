from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4
import logging
from app.models import SLOT_IDS, SlotStatus


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')

class ParkingService:
    """Single-process state owner. MQTT worker and REST share the same lock."""
    def __init__(self, database):
        self.database = database
        self.stream_id = str(uuid4())
        self.revision = 0
        self.timestamp = utc_now()
        self.lock = RLock()
        self.mqtt_status = 'DISCONNECTED'
        self.device_status = 'UNKNOWN'
        self.listeners = set()

    def subscribe(self, callback):
        with self.lock: self.listeners.add(callback)
        def unsubscribe():
            with self.lock: self.listeners.discard(callback)
        return unsubscribe

    def notify(self, command=None):
        # Called under the shared state lock, after DB commit and revision update.
        snapshot = self.snapshot()
        messages = []
        if command is not None:
            messages.append(dict(type='gate.command',schema_version='1.0',stream_id=self.stream_id,revision=self.revision,data=command))
        messages.append(dict(type='parking.snapshot',schema_version='1.0',data=snapshot))
        for callback in tuple(self.listeners):
            try: callback(messages)
            except Exception: logging.getLogger(__name__).exception('Realtime observer failed after commit')

    def update_slot(self, slot_id, status, received_at=None):
        if slot_id not in SLOT_IDS:
            raise ValueError('Invalid slot_id')
        status = SlotStatus(status).value
        if received_at is not None:
            parsed = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError('received_at must have a timezone')
            received_at = parsed.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
        with self.lock:
            with self.database.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT * FROM parking_slots WHERE slot_id=?', (slot_id,)).fetchone()
                previous = row['status'] if row['session_id'] == self.stream_id else 'UNKNOWN'
                changed = previous != status or row['session_id'] != self.stream_id
                if not changed and received_at is None:
                    return False
                timestamp = received_at or utc_now()
                # Reconnect replay of persisted last-known is not another vehicle event.
                if row['status'] != status:
                    kind = 'IN' if previous == 'EMPTY' and status == 'OCCUPIED' else 'OUT' if previous == 'OCCUPIED' and status == 'EMPTY' else 'STATUS'
                    db.execute('INSERT INTO parking_events(id,timestamp,slot_id,type,previous,current) VALUES (?,?,?,?,?,?)', (str(uuid4()), timestamp, slot_id, kind, previous, status))
                db.execute('UPDATE parking_slots SET status=?,received_at=?,session_id=? WHERE slot_id=?', (status, timestamp, self.stream_id, slot_id))
            self.revision += 1
            self.timestamp = utc_now()
            self.notify()
            return changed

    def set_connection(self, *, mqtt=None, device=None, invalidate=False):
        if mqtt is not None and mqtt not in ('CONNECTED','DISCONNECTED'):
            raise ValueError('Invalid transport state')
        if device is not None and device not in ('ONLINE','OFFLINE','UNKNOWN'):
            raise ValueError('Invalid device state')
        with self.lock:
            changed = (mqtt is not None and mqtt != self.mqtt_status) or (device is not None and device != self.device_status)
            with self.database.connect() as db:
                if invalidate:
                    # Preserve last-known values/history, revoke trust only. Health is not a vehicle event.
                    count = db.execute('UPDATE parking_slots SET session_id=NULL WHERE session_id IS NOT NULL').rowcount
                    gate_count = db.execute('UPDATE gate_state SET confirmed=0 WHERE confirmed=1').rowcount
                    changed = changed or bool(count) or bool(gate_count)
            if mqtt is not None:
                self.mqtt_status = mqtt
            if device is not None:
                self.device_status = device
            if changed:
                self.revision += 1
                self.timestamp = utc_now()
                self.notify()

    def snapshot(self):
        with self.lock, self.database.connect() as db:
            rows = db.execute('SELECT * FROM parking_slots ORDER BY slot_id').fetchall()
            slots = {r['slot_id']: r['status'] if r['session_id'] == self.stream_id else 'UNKNOWN' for r in rows}
            events = [dict(id=r['id'], timestamp=r['timestamp'], slotId=r['slot_id'], type=r['type'], previous=r['previous'], current=r['current']) for r in db.execute('SELECT * FROM parking_events ORDER BY sequence DESC')]
            gate = db.execute('SELECT * FROM gate_state WHERE singleton=1').fetchone()
            pending = db.execute("SELECT command_id FROM gate_commands WHERE state='PENDING' ORDER BY created_at LIMIT 1").fetchone()
            return dict(schema_version='1.0', source='LIVE', timestamp=self.timestamp, slots=slots, gate=gate['status'],
                        gate_meta=dict(confirmed=bool(gate['confirmed']),confirmed_at=gate['confirmed_at'],pending_command_id=pending['command_id'] if pending else None),
                        connection=dict(mqtt=self.mqtt_status,device=self.device_status,synchronized=self.mqtt_status == 'CONNECTED' and self.device_status == 'ONLINE' and all(r['session_id'] == self.stream_id for r in rows)),
                        stream_id=self.stream_id,revision=self.revision,events=events)

    def summary(self):
        state = self.snapshot()
        values = list(state['slots'].values())
        occupied, free, unknown = (values.count(x) for x in ('OCCUPIED','EMPTY','UNKNOWN'))
        return dict(schema_version='1.0',stream_id=state['stream_id'],revision=state['revision'],total=4,occupied=occupied,free=free,unknown=unknown,status='FULL' if occupied == 4 else 'AVAILABLE' if free else 'UNKNOWN',full=occupied == 4)

    def statistics(self):
        state = self.snapshot()
        return dict(schema_version='1.0',stream_id=state['stream_id'],revision=state['revision'],scope='DATABASE_LIFETIME',
                    entries=sum(e['type']=='IN' for e in state['events']),exits=sum(e['type']=='OUT' for e in state['events']),
                    by_slot={slot:sum(e['type']=='IN' and e['slotId']==slot for e in state['events']) for slot in SLOT_IDS})
