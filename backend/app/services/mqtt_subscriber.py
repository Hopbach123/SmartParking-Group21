"""MQTT ingress and explicit Gate API publisher; never synthetic LIVE sensor messages."""
import logging
import time
from dataclasses import dataclass
from queue import Queue, Empty, Full
from threading import Event, Lock, Thread
from uuid import uuid4
import paho.mqtt.client as mqtt
from app.schemas.mqtt import TOPICS, parse_message, SlotPayload, OnlinePayload, OfflinePayload
from app.services.parking import utc_now

LOG = logging.getLogger('uvicorn.error.mqtt')


class MQTTIngestor:
    """Deterministic single-worker consumer. Tests inject messages and a monotonic clock."""
    def __init__(self, parking, *, device_id='esp32-01', timeout=30, clock=time.monotonic):
        self.parking = parking
        self.device_id = device_id
        self.timeout = timeout
        self.clock = clock
        self.connected = False
        self.connected_at = None
        self.last_heartbeat = None
        self.last_uptime = None
        self.timed_out = False
        self.accepted = 0
        self.rejected = 0
        self.gate_controller = None

    def on_connected(self):
        self.connected = True
        self.connected_at = self.clock()
        self.last_heartbeat = None
        self.last_uptime = None
        self.timed_out = False
        self.parking.set_connection(mqtt='CONNECTED',device='UNKNOWN',invalidate=True)
        LOG.info('MQTT subscription ready; awaiting heartbeat and four-slot baseline')

    def on_disconnected(self):
        self.connected = False
        self.last_heartbeat = None
        self.last_uptime = None
        self.connected_at = None
        self.parking.set_connection(mqtt='DISCONNECTED',device='UNKNOWN',invalidate=True)
        LOG.warning('MQTT disconnected; slot trust revoked, last-known/history preserved')

    def tick(self):
        reference = self.last_heartbeat if self.last_heartbeat is not None else self.connected_at
        if self.connected and reference is not None and not self.timed_out and self.clock()-reference > self.timeout:
            self.parking.set_connection(device='OFFLINE',invalidate=True)
            self.timed_out = True
            LOG.warning('Device heartbeat timeout; OFFLINE and slots UNKNOWN')

    def ingest(self, topic, payload, *, retained=False, received_at=None, received_mono=None):
        self.tick()
        now = self.clock()
        received_mono = now if received_mono is None else received_mono
        try:
            if not self.connected:
                raise ValueError('Subscription not ready')
            if retained:
                raise ValueError('Retained payload rejected: current Device publishes non-retained only')
            if now-received_mono > self.timeout:
                raise ValueError('Queued message expired')
            message = parse_message(topic,payload,self.device_id)
        except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
            self.rejected += 1
            LOG.warning('MQTT payload rejected topic=%s reason=%s',topic,str(exc).splitlines()[0])
            return False
        received_at = received_at or utc_now()
        if isinstance(message, SlotPayload):
            if self.parking.device_status == 'OFFLINE':
                self.rejected += 1
                LOG.warning('Slot ignored while device OFFLINE; await a fresh online heartbeat')
                return False
            status = 'OCCUPIED' if message.occupied else 'EMPTY'
            changed = self.parking.update_slot(message.slot_id,status,received_at=received_at)
            LOG.info('MQTT slot received slot=%s status=%s received_at=%s state_changed=%s',message.slot_id,status,received_at,changed)
        elif isinstance(message, OnlinePayload):
            # A decreasing uptime can also be uint32 wrap: invalidate conservatively, never guess.
            reboot_or_wrap = self.last_uptime is not None and message.uptime_ms < self.last_uptime
            if reboot_or_wrap:
                LOG.warning('Device uptime decreased (restart or wrap); requesting fresh baseline by awaiting republish')
            self.parking.set_connection(device='ONLINE',invalidate=reboot_or_wrap)
            self.last_heartbeat = received_mono
            self.last_uptime = message.uptime_ms
            self.timed_out = False
            LOG.info('MQTT device heartbeat ONLINE uptime_ms=%s received_at=%s',message.uptime_ms,received_at)
        elif isinstance(message, OfflinePayload):
            self.parking.set_connection(device='OFFLINE',invalidate=True)
            self.last_heartbeat = None
            self.timed_out = True
            LOG.warning('Device Will/status OFFLINE; slots UNKNOWN received_at=%s',received_at)
        else:
            if self.gate_controller is not None:
                self.gate_controller.acknowledge(message, received_at)
            else:
                LOG.info('MQTT gate/status observed command_id=%s status=%s received_at=%s; not applied (phase 3)',message.command_id,message.status,received_at)
        self.accepted += 1
        return True


@dataclass(frozen=True)
class Delivery:
    epoch: int
    kind: str
    topic: str = ''
    payload: bytes = b''
    retained: bool = False
    received_at: str = ''
    received_mono: float = 0


class MQTTSubscriber:
    def __init__(self, parking, settings, *, client=None, clock=time.monotonic, queue_size=1000):
        self.settings = settings
        self.clock = clock
        self.ingestor = MQTTIngestor(parking,device_id=settings.mqtt_device_id,timeout=settings.heartbeat_timeout,clock=clock)
        self.client = client if client is not None else mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id='smartparking-group21-backend-'+uuid4().hex[:12],
            clean_session=True,protocol=mqtt.MQTTv311)
        self.client.connect_timeout = 5
        self.client.reconnect_delay_set(min_delay=1,max_delay=30)
        self.client.enable_logger(LOG)
        self.client.on_connect = self._on_connect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_disconnect = self._on_disconnect
        self.client.on_connect_fail = self._on_connect_fail
        self.client.on_message = self._on_message
        self.queue = Queue(maxsize=queue_size)
        self.guard = Lock()
        self.epoch = 0
        self.ready = False
        self.subscription_mid = None
        self.transport_up = False
        self.subscription_due = None
        self.stop_event = Event()
        self.overflow = Event()
        self.worker = None

    def _enqueue(self, delivery):
        try:
            self.queue.put_nowait(delivery)
        except Full:
            with self.guard:
                if not self.overflow.is_set():
                    self.epoch += 1  # pre-overflow queued packets must never restore stale state
                    self.overflow.set()
            LOG.error('MQTT ingest queue full; revoking baseline, no synthetic recovery data')

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        failed = reason_code.is_failure if hasattr(reason_code,'is_failure') else reason_code != 0
        with self.guard:
            self.epoch += 1
            self.ready = False
            self.subscription_mid = None
            self.subscription_due = None
            self.transport_up = False
            epoch = self.epoch
        self._enqueue(Delivery(epoch,'disconnected'))
        if failed:
            LOG.warning('MQTT CONNACK rejected reason=%s',reason_code)
            return
        with self.guard:
            self.transport_up = True
        self._request_subscription()

    def _request_subscription(self):
        with self.guard:
            if self.stop_event.is_set() or not self.transport_up:
                return
            epoch = self.epoch
            self.subscription_due = self.clock()+5
            # subscribe is non-blocking; keep MID assignment atomic against fast SUBACK.
            result, mid = self.client.subscribe([(topic,1) for topic in TOPICS])
            if epoch != self.epoch:
                return
            self.subscription_mid = mid if result == mqtt.MQTT_ERR_SUCCESS else None
        if result != mqtt.MQTT_ERR_SUCCESS:
            LOG.error('MQTT subscribe request failed rc=%s; retry in 5 seconds',result)
        else:
            LOG.info('MQTT connected broker=%s:%s; subscribe requested mid=%s topics=%s',self.settings.mqtt_host,self.settings.mqtt_port,mid,','.join(TOPICS))

    def _retry_subscription(self):
        with self.guard:
            due = self.transport_up and not self.ready and self.subscription_due is not None and self.clock() >= self.subscription_due
        if due:
            self._request_subscription()

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        rejected = len(reason_codes) != len(TOPICS) or any(
            code.is_failure if hasattr(code,'is_failure') else int(code) >= 128 for code in reason_codes)
        with self.guard:
            if mid != self.subscription_mid:
                return
            epoch = self.epoch
            self.ready = not rejected
            self.subscription_due = self.clock()+5 if rejected else None
        if rejected:
            LOG.error('MQTT SUBACK rejected or incomplete; resubscribe in 5 seconds')
            self._enqueue(Delivery(epoch,'disconnected'))
        else:
            self._enqueue(Delivery(epoch,'connected'))

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        with self.guard:
            self.epoch += 1
            self.ready = False
            self.transport_up = False
            self.subscription_due = None
            self.subscription_mid = None
            epoch = self.epoch
        self._enqueue(Delivery(epoch,'disconnected'))
        LOG.warning('MQTT transport disconnected reason=%s; reconnect handled by Paho',reason_code)

    def _on_connect_fail(self, client, userdata):
        with self.guard:
            self.epoch += 1
            self.ready = False
            self.transport_up = False
            self.subscription_due = None
            epoch = self.epoch
        self._enqueue(Delivery(epoch,'disconnected'))
        LOG.warning('MQTT connect attempt failed; backing off and retrying')

    def _on_message(self, client, userdata, message):
        if len(message.payload) > 1024:
            LOG.warning('MQTT oversized payload rejected topic=%s',message.topic)
            return
        with self.guard:
            if not self.ready:
                return
            epoch = self.epoch
        self._enqueue(Delivery(epoch,'message',message.topic,bytes(message.payload),bool(message.retain),utc_now(),self.clock()))

    def _recover_overflow(self):
        with self.guard:
            if not self.overflow.is_set():
                return
            self.overflow.clear()
            ready = self.ready
        if ready:
            self.ingestor.on_connected()
        else:
            self.ingestor.on_disconnected()

    def _dispatch(self, delivery):
        with self.guard:
            if delivery.epoch != self.epoch:
                return
        if delivery.kind == 'connected':
            self.ingestor.on_connected()
        elif delivery.kind == 'disconnected':
            self.ingestor.on_disconnected()
        else:
            self.ingestor.ingest(delivery.topic,delivery.payload,retained=delivery.retained,
                                 received_at=delivery.received_at,received_mono=delivery.received_mono)

    def _run(self):
        while not self.stop_event.is_set():
            try:
                self._recover_overflow()
                self._retry_subscription()
                self.ingestor.tick()
                try:
                    delivery = self.queue.get(timeout=.25)
                except Empty:
                    continue
                try:
                    self._dispatch(delivery)
                finally:
                    self.queue.task_done()
            except Exception:
                LOG.exception('MQTT ingest failed; worker remains active, baseline invalidated')
                try:
                    self.ingestor.parking.set_connection(device='UNKNOWN',invalidate=True)
                except Exception:
                    LOG.exception('Could not invalidate state after ingest failure')
                self.stop_event.wait(.25)

    def publish_gate_command(self, payload):
        # QoS0 intentionally avoids Paho QoS1 automatic re-publish after reconnect.
        # v1 describes QoS1 as a proposal; no-retry requirement takes precedence.
        if not isinstance(payload, bytes) or len(payload)>256:
            raise ValueError('Invalid command payload')
        with self.guard:
            if not self.ready or self.stop_event.is_set() or not self.client.is_connected():
                return False
            heartbeat = self.ingestor.last_heartbeat
            if heartbeat is None or self.clock()-heartbeat > self.settings.heartbeat_timeout:
                return False
            result = self.client.publish('smartparking/group21/gate/command', payload, qos=0, retain=False)
            return result.rc == mqtt.MQTT_ERR_SUCCESS

    def start(self):
        if self.worker is not None:
            raise RuntimeError('MQTTSubscriber already started')
        self.worker = Thread(target=self._run,name='smartparking-mqtt-ingest',daemon=True)
        self.worker.start()
        try:
            self.client.connect_async(self.settings.mqtt_host,self.settings.mqtt_port,keepalive=15)
            result = self.client.loop_start()
            if result != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError('Paho network loop could not start')
        except Exception:
            self.stop()
            raise
        LOG.info('MQTT subscriber started; gate commands only via validated REST controller')

    def stop(self):
        self.stop_event.set()
        try:
            self.client.disconnect()
        finally:
            try:
                self.client.loop_stop()
            finally:
                self.stop_event.set()
                if self.worker is not None:
                    self.worker.join(timeout=15)
                    if self.worker.is_alive():
                        raise RuntimeError('MQTT ingest worker did not stop')
                self.ingestor.on_disconnected()
        LOG.info('MQTT subscriber stopped')
