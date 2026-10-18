import hashlib
import json
import logging
import time
from threading import Event, Thread
from uuid import uuid4
from app.services.parking import utc_now

LOG=logging.getLogger('uvicorn.error.gate')
FIELDS=('command_id','requested_status','direction','state','created_at','completed_at','error_code')

class GateError(Exception):
    def __init__(self,status,code,message,command_id=None):
        self.status,self.code,self.message,self.command_id=status,code,message,command_id

class GateController:
    def __init__(self,parking,timeout=5,clock=time.monotonic):
        self.parking=parking
        self.timeout=timeout
        self.clock=clock
        self.publisher=None
        self.deadlines={}
        self.stop_event=Event()
        self.worker=None
        with parking.lock,parking.database.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('UPDATE gate_state SET confirmed=0')
            db.execute("UPDATE gate_commands SET state='TIMEOUT',completed_at=?,error_code='BACKEND_RESTART' WHERE state='PENDING'",(utc_now(),))
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_pending_gate ON gate_commands((1)) WHERE state='PENDING'")

    def set_publisher(self,publisher): self.publisher=publisher

    def get(self,command_id):
        with self.parking.lock,self.parking.database.connect() as db:
            row=db.execute('SELECT * FROM gate_commands WHERE command_id=?',(command_id,)).fetchone()
            if row is None: raise GateError(404,'COMMAND_NOT_FOUND','Command not found',command_id)
            return {key:row[key] for key in FIELDS}

    def _notify(self,command_id):
        self.parking.revision+=1
        self.parking.timestamp=utc_now()
        self.parking.notify(self.get(command_id))

    def submit(self,request):
        # Idempotency is checked before health: retries never republish even while offline.
        command_id=request.command_id
        fingerprint=hashlib.sha256(json.dumps({'status':request.status,'direction':request.direction},sort_keys=True).encode()).hexdigest()
        with self.parking.lock:
            self.expire()
            with self.parking.database.connect() as db:
                existing=db.execute('SELECT * FROM gate_commands WHERE command_id=?',(command_id,)).fetchone()
                if existing:
                    if existing['request_fingerprint']!=fingerprint:
                        raise GateError(409,'COMMAND_ID_CONFLICT','ID already used with different request',command_id)
                    record=self.get(command_id)
                    return record,202 if record['state']=='PENDING' else 200
                snapshot=self.parking.snapshot()
                if self.publisher is None or snapshot['connection']['mqtt']!='CONNECTED' or snapshot['connection']['device']!='ONLINE':
                    raise GateError(503,'DEVICE_UNAVAILABLE','MQTT/device not online',command_id)
                if db.execute("SELECT 1 FROM gate_commands WHERE state='PENDING'").fetchone():
                    raise GateError(409,'GATE_BUSY','Another gate command is pending',command_id)
                if request.status=='OPEN' and request.direction=='ENTRY':
                    values=list(snapshot['slots'].values())
                    if values.count('OCCUPIED')==4:
                        raise GateError(409,'PARKING_FULL','No available slot',command_id)
                    if not snapshot['connection']['synchronized'] or 'UNKNOWN' in values:
                        raise GateError(409,'PARKING_UNSYNCHRONIZED','Sensor baseline is not reliable',command_id)
                    if 'EMPTY' not in values:
                        raise GateError(409,'PARKING_UNAVAILABLE','No trusted available slot',command_id)
                created=utc_now()
                db.execute("INSERT INTO gate_commands VALUES (?,?,?,?, 'PENDING',?,NULL,NULL)",(command_id,fingerprint,request.status,request.direction,created))
            self.deadlines[command_id]=self.clock()+self.timeout
            self._notify(command_id)  # PENDING is durable before any publish.
            payload=json.dumps({'command_id':command_id,'action':'OPEN' if request.status=='OPEN' else 'CLOSE','direction':request.direction},separators=(',',':')).encode()
            if len(payload)>256: raise RuntimeError('Validated command exceeds firmware limit')
            try:
                accepted=bool(self.publisher(payload))
            except Exception:
                LOG.exception('MQTT command publish raised command_id=%s',command_id)
                accepted=False
            if not accepted:
                self._finish(command_id,'ERROR','PUBLISH_FAILED')
                raise GateError(503,'PUBLISH_FAILED','Command delivery could not be confirmed; inspect record',command_id)
            LOG.info('Gate command published command_id=%s; awaiting matching Device ACK',command_id)
            # Publish acceptance is NOT servo confirmation.
            return self.get(command_id),202

    def _finish(self,command_id,state,error=None,ack_target=None):
        with self.parking.database.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("UPDATE gate_commands SET state=?,completed_at=?,error_code=? WHERE command_id=? AND state='PENDING'",(state,utc_now(),error,command_id))
            if ack_target is not None:
                gate=db.execute('SELECT * FROM gate_state WHERE singleton=1').fetchone()
                timestamp=utc_now()
                if gate['confirmed'] and gate['status']!=ack_target:
                    db.execute("INSERT INTO parking_events(id,timestamp,slot_id,type,previous,current) VALUES (?,?,'GATE','GATE',?,?)",(str(uuid4()),timestamp,gate['status'],ack_target))
                db.execute('UPDATE gate_state SET status=?,confirmed=1,confirmed_at=? WHERE singleton=1',(ack_target,timestamp))
            else:
                db.execute('UPDATE gate_state SET confirmed=0 WHERE singleton=1')
        self.deadlines.pop(command_id,None)
        self._notify(command_id)

    def expire(self):
        with self.parking.lock:
            for command_id,deadline in list(self.deadlines.items()):
                if self.clock()>=deadline:
                    self._finish(command_id,'TIMEOUT','ACK_TIMEOUT')
                    LOG.warning('Gate ACK timeout command_id=%s; never auto-republish',command_id)

    def acknowledge(self,message,received_at=None):
        received_at=received_at or utc_now()
        with self.parking.lock:
            self.expire()
            try: record=self.get(message.command_id)
            except GateError: record=None
            target='OPEN' if message.status=='OPENED' else 'CLOSED' if message.status=='CLOSED' else None
            if record is None: outcome='UNMATCHED'
            elif record['state']!='PENDING': outcome='TERMINAL_OR_LATE'
            elif self.parking.mqtt_status!='CONNECTED' or self.parking.device_status!='ONLINE': outcome='UNTRUSTED_CONNECTION'
            elif message.status=='ERROR': outcome='DEVICE_ERROR'
            elif target!=record['requested_status']: outcome='ACK_TARGET_MISMATCH'
            else: outcome='CONFIRMED'
            with self.parking.database.connect() as db:
                db.execute('INSERT INTO gate_ack_audit(command_id,status,received_at,outcome) VALUES (?,?,?,?)',(message.command_id,message.status,received_at,outcome))
            if outcome=='CONFIRMED': self._finish(message.command_id,'CONFIRMED',ack_target=target)
            elif outcome in ('DEVICE_ERROR','ACK_TARGET_MISMATCH'): self._finish(message.command_id,'ERROR',outcome)
            LOG.info('Gate ACK command_id=%s status=%s outcome=%s; firmware ACK is not visual servo proof',message.command_id,message.status,outcome)
            return outcome

    def start(self):
        def watch():
            while not self.stop_event.wait(.1):
                try: self.expire()
                except Exception: LOG.exception('Gate timeout watchdog failed')
        self.worker=Thread(target=watch,name='smartparking-gate-timeout',daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_event.set()
        if self.worker:
            self.worker.join(timeout=15)
            if self.worker.is_alive(): raise RuntimeError('Gate watchdog did not stop')
