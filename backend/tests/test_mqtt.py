import json
import logging
import time
from queue import Empty
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.database import Database
from app.main import create_app
from app.services.parking import ParkingService
from app.services.mqtt_subscriber import MQTTIngestor, MQTTSubscriber, Delivery
from app.schemas.mqtt import PREFIX, SLOT_TOPICS, DEVICE_TOPIC, GATE_TOPIC, TOPICS, parse_message

class Clock:
    def __init__(self): self.value=100.
    def __call__(self): return self.value
    def advance(self,n): self.value+=n

def slot_body(slot='P01',occupied=True,**extra):
    return dict(device_id='esp32-01',slot_id=slot,occupied=occupied,**extra)

def body(**extra):
    return json.dumps(dict(device_id='esp32-01',**extra)).encode()

def slot_topic(slot='P01'):
    return f'{PREFIX}/slots/{slot}/state'

@pytest.fixture
def setup(tmp_path):
    db=Database(tmp_path/'mqtt.sqlite3');db.initialize()
    service=ParkingService(db);clock=Clock()
    ingest=MQTTIngestor(service,clock=clock)
    ingest.on_connected()
    return service,ingest,clock

def online(ingest,uptime=1000):
    return ingest.ingest(DEVICE_TOPIC,body(status='online',uptime_ms=uptime))

def baseline(ingest,occupied=False):
    for slot in ('P01','P02','P03','P04'):
        assert ingest.ingest(slot_topic(slot),json.dumps(slot_body(slot,occupied)).encode())

@pytest.mark.parametrize('slot',['P01','P02','P03','P04'])
def test_valid_slot_roundtrip_rest_and_db(setup,slot):
    service,ingest,clock=setup
    online(ingest)
    assert ingest.ingest(slot_topic(slot),json.dumps(slot_body(slot,False)).encode())
    assert ingest.ingest(slot_topic(slot),json.dumps(slot_body(slot,True)).encode(),received_at='2026-10-18T23:00:00+07:00')
    assert service.snapshot()['slots'][slot]=='OCCUPIED'
    assert service.statistics()['entries']==1
    with service.database.connect() as db:
        row=db.execute('SELECT * FROM parking_slots WHERE slot_id=?',(slot,)).fetchone()
        assert row['received_at']=='2026-10-18T16:00:00.000000Z'
    assert service.snapshot()['events'][0]['timestamp'].endswith('Z')

@pytest.mark.parametrize('payload',[
    b'{',b'[]',b'null',b'"text"',b'',b'\xff',b'x'*1025,
    b'{"device_id":"esp32-01","slot_id":"P01","occupied":true,"occupied":false}',
    b'{"device_id":"esp32-01","slot_id":"P01","occupied":NaN}',
    json.dumps(slot_body(occupied='false')).encode(),
    json.dumps(slot_body(occupied=1)).encode(),
    json.dumps(slot_body(extra='unexpected')).encode(),
    b'{"device_id":"wrong","slot_id":"P01","occupied":true}',
    b'{"slot_id":"P01","occupied":true}',
    b'{"device_id":"esp32-01","slot_id":"P01"}',
])
def test_bad_payload_has_no_side_effect(setup,payload,caplog):
    service,ingest,clock=setup;before=service.snapshot()
    assert not ingest.ingest(slot_topic(),payload)
    assert service.snapshot()==before
    assert ingest.rejected==1
    assert 'rejected' in caplog.text

@pytest.mark.parametrize('topic',[f'{PREFIX}/slots/P99/state',f'{PREFIX}/slots/P01/state/extra',f'{PREFIX}/gate/command','unrelated/topic'])
def test_wrong_topic(setup,topic):
    service,ingest,_=setup
    assert not ingest.ingest(topic,json.dumps(slot_body()).encode())
    assert service.snapshot()['events']==[]

def test_slot_topic_mismatch(setup):
    service,ingest,_=setup
    assert not ingest.ingest(slot_topic('P01'),json.dumps(slot_body('P02')).encode())
    assert service.snapshot()['slots']['P02']=='UNKNOWN'

def test_duplicates_refresh_received_at_without_vehicle_events(setup):
    service,ingest,_=setup
    baseline(ingest)
    ingest.ingest(slot_topic(),json.dumps(slot_body()).encode())
    before=service.snapshot()['events']
    ingest.ingest(slot_topic(),json.dumps(slot_body()).encode(),received_at='2026-10-18T10:00:01Z')
    assert service.snapshot()['events']==before
    with service.database.connect() as db:
        assert db.execute("SELECT received_at FROM parking_slots WHERE slot_id='P01'").fetchone()[0]=='2026-10-18T10:00:01.000000Z'

def test_reconnect_same_baseline_no_duplicate_history(setup):
    service,ingest,clock=setup
    online(ingest);baseline(ingest)
    ingest.ingest(slot_topic(),json.dumps(slot_body()).encode())
    before=service.snapshot()['events'];counts=service.statistics()['entries']
    assert service.snapshot()['connection']['synchronized']
    ingest.on_disconnected()
    assert set(service.snapshot()['slots'].values())=={'UNKNOWN'}
    assert service.snapshot()['connection']['mqtt']=='DISCONNECTED'
    ingest.on_connected();online(ingest)
    for slot in ('P01','P02','P03','P04'):
        ingest.ingest(slot_topic(slot),json.dumps(slot_body(slot,slot=='P01')).encode())
    assert service.snapshot()['events']==before
    assert service.statistics()['entries']==counts
    assert service.snapshot()['connection']['synchronized']


def test_reconnect_changed_baseline_is_status_not_entry(setup):
    service,ingest,_=setup
    online(ingest);baseline(ingest)
    ingest.on_disconnected();ingest.on_connected();online(ingest)
    ingest.ingest(slot_topic(),json.dumps(slot_body()).encode())
    assert service.snapshot()['events'][0]['type']=='STATUS'
    assert service.statistics()['entries']==0

def test_heartbeat_timeout_invalidates_without_erasing_last_known(setup):
    service,ingest,clock=setup
    online(ingest);baseline(ingest,True)
    before=service.snapshot()['events']
    clock.advance(30);ingest.tick()
    assert service.snapshot()['connection']['device']=='ONLINE'
    clock.advance(.01);ingest.tick()
    assert service.snapshot()['connection']['device']=='OFFLINE'
    assert set(service.snapshot()['slots'].values())=={'UNKNOWN'}
    assert service.summary()['free']==0
    with service.database.connect() as db:
        assert {r[0] for r in db.execute('SELECT status FROM parking_slots')}=={'OCCUPIED'}
    assert service.snapshot()['events']==before
    revision=service.revision;ingest.tick();assert revision==service.revision
    assert not ingest.ingest(slot_topic(),json.dumps(slot_body()).encode())
    online(ingest,40000)
    assert not service.snapshot()['connection']['synchronized']
    baseline(ingest,True)
    assert service.snapshot()['connection']['synchronized']
    assert service.snapshot()['events']==before

def test_unchanged_slot_is_not_expired_while_heartbeats_alive(setup):
    service,ingest,clock=setup
    online(ingest);baseline(ingest)
    for n in range(1,13):
        clock.advance(10);online(ingest,n*10000);ingest.tick()
    assert set(service.snapshot()['slots'].values())=={'EMPTY'}
    assert service.snapshot()['connection']['synchronized']

def test_no_initial_heartbeat_timeout_and_offline_will(setup):
    service,ingest,clock=setup
    clock.advance(31);ingest.tick()
    assert service.device_status=='OFFLINE'
    online(ingest);baseline(ingest)
    assert ingest.ingest(DEVICE_TOPIC,body(status='offline'))
    assert service.device_status=='OFFLINE'
    assert set(service.snapshot()['slots'].values())=={'UNKNOWN'}

@pytest.mark.parametrize('payload',[
    body(status='online',uptime_ms=True),body(status='online',uptime_ms=-1),
    body(status='online',uptime_ms=4294967296),body(status='online'),body(status='ONLINE',uptime_ms=1),
    body(status='offline',uptime_ms=1),body(status='online',uptime_ms='1000'),
])
def test_invalid_heartbeat_not_online(setup,payload):
    service,ingest,_=setup
    assert not ingest.ingest(DEVICE_TOPIC,payload)
    assert service.device_status=='UNKNOWN'

def test_uptime_decrease_revokes_baseline(setup):
    service,ingest,_=setup
    online(ingest,10000);baseline(ingest)
    online(ingest,100)
    assert set(service.snapshot()['slots'].values())=={'UNKNOWN'}
    assert service.device_status=='ONLINE'
    assert not service.snapshot()['connection']['synchronized']

@pytest.mark.parametrize('status',['OPENED','CLOSED','ERROR'])
def test_gate_status_observation_only(setup,status,caplog):
    service,ingest,_=setup;before=service.snapshot()
    with caplog.at_level(logging.INFO):
        assert ingest.ingest(GATE_TOPIC,body(command_id='test-only-001',status=status))
    assert service.snapshot()==before
    assert 'not applied (phase 3)' in caplog.text
    with service.database.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM gate_commands').fetchone()[0]==0

def test_bad_gate_status_and_retained_data(setup):
    service,ingest,_=setup
    assert not ingest.ingest(GATE_TOPIC,body(command_id='x',status='OPEN'))
    assert not ingest.ingest(slot_topic(),json.dumps(slot_body()).encode(),retained=True)
    assert service.snapshot()['events']==[]

def test_expired_queue_message_cannot_restore_state(setup):
    service,ingest,clock=setup
    received=clock();clock.advance(31)
    assert not ingest.ingest(DEVICE_TOPIC,body(status='online',uptime_ms=1),received_mono=received)
    assert service.device_status=='OFFLINE'

class FakeClient:
    def __init__(self): self.subscriptions=[];self.connections=[];self.mid=0;self.stopped=False;self.started=False
    def reconnect_delay_set(self,**kw): self.delay=kw
    def enable_logger(self,logger): pass
    def subscribe(self,topics): self.mid+=1;self.subscriptions.append(topics);return (0,self.mid)
    def connect_async(self,*args,**kwargs): self.connections.append((args,kwargs))
    def loop_start(self): self.started=True;return 0
    def loop_stop(self): self.stopped=True
    def disconnect(self): pass
    def publish(self,*args,**kw): raise AssertionError('No publishing is allowed in phase 3')

def runtime_for(setup,tmp_path,queue_size=1000):
    service,ingest,clock=setup
    client=FakeClient();settings=Settings(tmp_path/'runtime.sqlite3',mqtt_enabled=True)
    runtime=MQTTSubscriber(service,settings,client=client,clock=clock,queue_size=queue_size)
    return runtime,client

def drain(runtime):
    runtime._recover_overflow()
    while True:
        try: delivery=runtime.queue.get_nowait()
        except Empty: break
        runtime._dispatch(delivery)
        runtime.queue.task_done()

def connect(runtime,client):
    client.on_connect(client,None,{},0,None)
    client.on_subscribe(client,None,client.mid,[1]*6,None)

def test_subscribe_exact_topics_and_again_on_reconnect(setup,tmp_path):
    runtime,client=runtime_for(setup,tmp_path)
    connect(runtime,client);drain(runtime)
    assert runtime.ingestor.parking.mqtt_status=='CONNECTED'
    assert client.subscriptions==[[(topic,1) for topic in TOPICS]]
    client.on_disconnect(client,None,{},1,None);drain(runtime)
    assert runtime.ingestor.parking.mqtt_status=='DISCONNECTED'
    connect(runtime,client);drain(runtime)
    assert len(client.subscriptions)==2
    assert all(topic!=f'{PREFIX}/gate/command' for topic,qos in client.subscriptions[0])

def test_stale_connection_epoch_packets_discarded(setup,tmp_path):
    runtime,client=runtime_for(setup,tmp_path)
    connect(runtime,client);drain(runtime)
    old=runtime.epoch
    packet=Delivery(old,'message',slot_topic(),json.dumps(slot_body()).encode(),False,'2026-10-18T10:00:00Z',runtime.clock())
    client.on_disconnect(client,None,{},1,None)
    runtime._dispatch(packet);drain(runtime)
    assert runtime.ingestor.parking.snapshot()['slots']['P01']=='UNKNOWN'

def test_callback_and_worker_lifecycle(setup,tmp_path):
    runtime,client=runtime_for(setup,tmp_path)
    runtime.start()
    try:
        connect(runtime,client)
        client.on_message(client,None,SimpleNamespace(topic=DEVICE_TOPIC,payload=body(status='online',uptime_ms=1000),retain=False))
        client.on_message(client,None,SimpleNamespace(topic=slot_topic(),payload=json.dumps(slot_body()).encode(),retain=False))
        runtime.queue.join()
        assert runtime.ingestor.parking.snapshot()['slots']['P01']=='OCCUPIED'
        assert client.started
    finally:
        runtime.stop()
    assert client.stopped and not runtime.worker.is_alive()
    assert runtime.ingestor.parking.mqtt_status=='DISCONNECTED'

def test_overflow_invalidates_and_old_packets_do_not_restore(setup,tmp_path):
    runtime,client=runtime_for(setup,tmp_path,queue_size=1)
    connect(runtime,client);drain(runtime)
    # A deliberately tiny queue overflows at connect/SUBACK; reconnect logically ready state.
    runtime.ingestor.on_connected();online(runtime.ingestor);baseline(runtime.ingestor)
    old=runtime.epoch
    runtime._enqueue(Delivery(old,'message',slot_topic(),json.dumps(slot_body()).encode(),False,'2026-10-18T10:00:00Z',runtime.clock()))
    runtime._enqueue(Delivery(old,'message',slot_topic(),json.dumps(slot_body()).encode()))
    assert runtime.overflow.is_set()
    drain(runtime)
    assert set(runtime.ingestor.parking.snapshot()['slots'].values())=={'UNKNOWN'}

def test_suback_rejection_and_initial_connect_failure(setup,tmp_path):
    runtime,client=runtime_for(setup,tmp_path)
    client.on_connect(client,None,{},0,None)
    client.on_subscribe(client,None,client.mid,[128]*6,None)
    drain(runtime)
    assert runtime.ingestor.parking.mqtt_status=='DISCONNECTED'
    before=len(client.subscriptions)
    runtime.clock.advance(5);runtime._retry_subscription()
    assert len(client.subscriptions)==before+1
    client.on_connect_fail(client,None);drain(runtime)
    assert runtime.ingestor.parking.mqtt_status=='DISCONNECTED'

def test_lifespan_with_mock_mqtt_updates_rest_and_closes(tmp_path):
    holder={}
    def factory(parking,settings):
        fake=FakeClient();subscriber=MQTTSubscriber(parking,settings,client=fake)
        holder.update(fake=fake,subscriber=subscriber)
        return subscriber
    app=create_app(Settings(tmp_path/'api.sqlite3',mqtt_enabled=True),mqtt_factory=factory)
    with TestClient(app) as client:
        fake=holder['fake'];runtime=holder['subscriber'];connect(runtime,fake)
        for topic,payload in [(DEVICE_TOPIC,body(status='online',uptime_ms=1000))]+[(slot_topic(slot),json.dumps(slot_body(slot,False)).encode()) for slot in ('P01','P02','P03','P04')]:
            fake.on_message(fake,None,SimpleNamespace(topic=topic,payload=payload,retain=False))
        runtime.queue.join()
        assert client.get('/health').json()['mqtt_enabled'] is True
        state=client.get('/api/parking/status').json()
        assert state['connection']=={'mqtt':'CONNECTED','device':'ONLINE','synchronized':True}
        assert client.get('/api/parking/summary').json()['free']==4
        assert client.post('/api/parking/gate',json={}).status_code==422
    assert holder['fake'].stopped
    assert not holder['subscriber'].worker.is_alive()


def test_subscribe_call_failure_and_missing_suback_retry(setup,tmp_path):
    runtime,client=runtime_for(setup,tmp_path)
    original=client.subscribe
    client.subscribe=lambda topics:(4,None)
    client.on_connect(client,None,{},0,None);drain(runtime)
    assert runtime.subscription_mid is None and not runtime.ready
    client.subscribe=original
    runtime.clock.advance(5);runtime._retry_subscription()
    assert len(client.subscriptions)==1
    runtime.clock.advance(5);runtime._retry_subscription()
    assert len(client.subscriptions)==2  # prior SUBACK absent, retry safely
    client.on_subscribe(client,None,client.mid,[1]*6,None);drain(runtime)
    assert runtime.ready
