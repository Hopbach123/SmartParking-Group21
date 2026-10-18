import asyncio
import json
import sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.config import Settings
from app.database import Database
from app.main import create_app
from app.models import SLOT_IDS
from app.schemas import GateRequest, GateCommand, GateMessage, SnapshotMessage
from app.schemas.mqtt import GatePayload, GATE_TOPIC
from app.services.parking import ParkingService
from app.services.gate import GateController, GateError
from app.services.realtime import RealtimeHub
from tests.test_mqtt import Clock, FakeClient, connect
from app.services.mqtt_subscriber import MQTTSubscriber

@pytest.fixture
def gate(tmp_path):
    db=Database(tmp_path/'gate.sqlite3');db.initialize()
    p=ParkingService(db);c=Clock();g=GateController(p,clock=c)
    sent=[];g.set_publisher(lambda payload:sent.append(json.loads(payload)) or True)
    p.set_connection(mqtt='CONNECTED',device='ONLINE')
    for slot in SLOT_IDS:p.update_slot(slot,'EMPTY')
    return p,g,c,sent

def req(id='test-001',status='OPEN',direction='ENTRY'):
    return GateRequest(command_id=id,status=status,direction=direction)

def ack(g,id='test-001',status='OPENED'):
    return g.acknowledge(GatePayload(device_id='esp32-01',command_id=id,status=status))

def test_pending_then_open_close_and_ordered_notifications(gate):
    p,g,c,sent=gate;observed=[];p.subscribe(observed.append)
    record,http=g.submit(req())
    assert http==202 and record['state']=='PENDING'
    assert sent==[dict(command_id='test-001',action='OPEN',direction='ENTRY')]
    assert not p.snapshot()['gate_meta']['confirmed']
    assert p.snapshot()['gate_meta']['pending_command_id']=='test-001'
    assert ack(g)=='CONFIRMED' and p.snapshot()['gate']=='OPEN'
    g.submit(req('close-001','CLOSED','EXIT'))
    assert sent[-1]['action']=='CLOSE'
    assert ack(g,'close-001','CLOSED')=='CONFIRMED'
    assert p.snapshot()['gate']=='CLOSED'
    assert p.snapshot()['events'][0]['type']=='GATE'
    assert p.statistics()['entries']==0
    for batch in observed:
        assert [m['type'] for m in batch]==['gate.command','parking.snapshot']
        assert batch[0]['revision']==batch[1]['data']['revision']
        GateMessage.model_validate(batch[0]);SnapshotMessage.model_validate(batch[1])

@pytest.mark.parametrize('direction,allowed',[('ENTRY',False),('EXIT',True)])
def test_full_entry_rejected_exit_allowed(gate,direction,allowed):
    p,g,_,sent=gate
    for slot in SLOT_IDS:p.update_slot(slot,'OCCUPIED')
    if allowed:assert g.submit(req(direction=direction))[1]==202
    else:
        with pytest.raises(GateError) as error:g.submit(req(direction=direction))
        assert error.value.code=='PARKING_FULL' and sent==[]

def test_unknown_rejects_entry_not_exit(gate):
    p,g,_,sent=gate;p.set_connection(invalidate=True)
    with pytest.raises(GateError) as error:g.submit(req())
    assert error.value.code=='PARKING_UNSYNCHRONIZED' and sent==[]
    assert g.submit(req('exit','OPEN','EXIT'))[1]==202

def test_idempotency_conflict_duplicate_ack_and_concurrency(gate):
    p,g,_,sent=gate
    with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(lambda _:g.submit(req()),range(20)))
    assert len(sent)==1 and all(item[1]==202 for item in results)
    with pytest.raises(GateError) as error:g.submit(req(status='CLOSED'))
    assert error.value.code=='COMMAND_ID_CONFLICT'
    with pytest.raises(GateError) as error:g.submit(req('second'))
    assert error.value.code=='GATE_BUSY'
    ack(g);before=p.snapshot()
    assert ack(g)=='TERMINAL_OR_LATE'
    assert p.snapshot()==before
    assert g.submit(req())[1]==200 and len(sent)==1

@pytest.mark.parametrize('failure',[False,RuntimeError('fixture exception')])
def test_failed_publish_not_success(gate,failure):
    p,g,_,sent=gate
    def publish(payload):
        with p.database.connect() as db:assert db.execute("SELECT state FROM gate_commands WHERE command_id='test-001'").fetchone()[0]=='PENDING'
        if isinstance(failure,Exception):raise failure
        return failure
    g.set_publisher(publish)
    with pytest.raises(GateError) as error:g.submit(req())
    assert error.value.status==503 and g.get('test-001')['state']=='ERROR'
    assert not p.snapshot()['gate_meta']['confirmed']
    assert g.submit(req())[1]==200

@pytest.mark.parametrize('mqtt,device',[('DISCONNECTED','ONLINE'),('CONNECTED','OFFLINE'),('CONNECTED','UNKNOWN')])
def test_offline_no_false_success(gate,mqtt,device):
    p,g,_,sent=gate;p.set_connection(mqtt=mqtt,device=device,invalidate=True)
    with pytest.raises(GateError) as error:g.submit(req(direction='EXIT'))
    assert error.value.status==503 and sent==[]

@pytest.mark.parametrize('status,outcome',[('ERROR','DEVICE_ERROR'),('CLOSED','ACK_TARGET_MISMATCH')])
def test_device_error_or_ack_wrong_target(gate,status,outcome):
    p,g,_,_=gate;g.submit(req())
    assert ack(g,status=status)==outcome
    assert g.get('test-001')['state']=='ERROR' and not p.snapshot()['gate_meta']['confirmed']

def test_wrong_id_timeout_late_and_reconnect(gate):
    p,g,c,sent=gate;g.submit(req())
    assert ack(g,'wrong')=='UNMATCHED'
    p.set_connection(mqtt='DISCONNECTED',device='UNKNOWN',invalidate=True)
    c.advance(5);g.expire()
    assert g.get('test-001')['state']=='TIMEOUT'
    p.set_connection(mqtt='CONNECTED',device='ONLINE')
    assert ack(g)=='TERMINAL_OR_LATE' and not p.snapshot()['gate_meta']['confirmed']
    assert g.submit(req())[0]['state']=='TIMEOUT' and len(sent)==1

def test_restart_pending_no_resend(gate):
    p,g,_,sent=gate;g.submit(req())
    fresh=GateController(ParkingService(Database(p.database.path)))
    assert fresh.get('test-001')['state']=='TIMEOUT'
    assert fresh.get('test-001')['error_code']=='BACKEND_RESTART'
    assert fresh.submit(req())[1]==200 and len(sent)==1

def test_migration_v1_retains_data_and_backup(tmp_path):
    path=tmp_path/'v1.sqlite3'
    with sqlite3.connect(path) as db:
        db.executescript((Path(__file__).parent/'fixtures/schema-v1.sql').read_text())
        db.execute("INSERT INTO parking_slots VALUES ('P01','EMPTY',NULL,NULL)")
        db.execute("INSERT INTO parking_events(id,timestamp,slot_id,type,previous,current) VALUES ('old','2026-10-18T00:00:00Z','P01','STATUS','UNKNOWN','EMPTY')")
    Database(path).initialize()
    assert path.with_name(path.name+'.before-phase04.bak').exists()
    with Database(path).connect() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==2
        assert db.execute('SELECT id FROM parking_events').fetchone()[0]=='old'
        db.execute("INSERT INTO parking_events(id,timestamp,slot_id,type,previous,current) VALUES ('gate','2026-10-18T01:00:00Z','GATE','GATE','OPEN','CLOSED')")
    Database(path).initialize()
    with Database(path).connect() as db:assert db.execute('SELECT COUNT(*) FROM parking_events').fetchone()[0]==2

@pytest.fixture
def api(tmp_path):
    with TestClient(create_app(Settings(tmp_path/'api.sqlite3',('http://127.0.0.1:5173',)))) as client:
        p=client.app.state.parking;p.set_connection(mqtt='CONNECTED',device='ONLINE')
        for slot in SLOT_IDS:p.update_slot(slot,'EMPTY')
        sent=[];client.app.state.gate.set_publisher(lambda payload:sent.append(payload) or True)
        yield client,sent

def test_rest_schema_validation(api):
    client,sent=api;r=client.post('/api/parking/gate',json=req().model_dump())
    assert r.status_code==202;GateCommand.model_validate(r.json())
    assert client.get('/api/parking/commands/test-001').json()['state']=='PENDING'
    assert client.post('/api/parking/gate',json={'status':'OPEN','direction':'ENTRY'}).status_code==422
    assert client.post('/api/parking/gate',json={'command_id':'bad','status':'CLOSE','direction':'ENTRY'}).json()['error']['code']=='INVALID_REQUEST'
    assert client.get('/api/parking/commands/missing').status_code==404 and len(sent)==1

def test_two_ws_clients_snapshot_and_reconnect(api):
    client,_=api
    with client.websocket_connect('/ws/parking') as one,client.websocket_connect('/ws/parking') as two:
        first=one.receive_json();assert first==two.receive_json();SnapshotMessage.model_validate(first)
        client.app.state.parking.update_slot('P01','OCCUPIED')
        a=one.receive_json();assert a==two.receive_json()
        assert a['data']['revision']>first['data']['revision'] and a['data']['slots']['P01']=='OCCUPIED'
        assert client.get('/api/parking/status').json()==a['data']
    with client.websocket_connect('/ws/parking') as ws:assert ws.receive_json()['data']['slots']['P01']=='OCCUPIED'

def test_ws_command_then_snapshot_same_revision(api):
    client,_=api
    with client.websocket_connect('/ws/parking') as ws:
        ws.receive_json();client.post('/api/parking/gate',json=req().model_dump())
        pending=ws.receive_json();snapshot=ws.receive_json()
        assert pending['type']=='gate.command' and pending['data']['state']=='PENDING'
        assert pending['revision']==snapshot['data']['revision']
        ack(client.app.state.gate)
        confirmed=ws.receive_json();updated=ws.receive_json()
        assert confirmed['data']['state']=='CONFIRMED' and updated['data']['gate']=='OPEN'
        assert confirmed['revision']==updated['data']['revision']
        GateMessage.model_validate(confirmed);SnapshotMessage.model_validate(updated)

def test_ws_origin_and_inbound_command_rejected(api):
    client,sent=api
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/ws/parking',headers={'Origin':'https://unexpected.invalid'}):pass
    with client.websocket_connect('/ws/parking') as ws:
        ws.receive_json();ws.send_json({'status':'OPEN'})
        with pytest.raises(WebSocketDisconnect):ws.receive_json()
    assert sent==[]

def test_ws_queue_bounded_slow_client_closed(gate):
    p,_,_,_=gate
    async def exercise():
        hub=RealtimeHub(p,asyncio.get_running_loop());peer=hub.register(None)
        for n in range(70):
            snapshot=p.snapshot();snapshot['revision']=p.revision+n+1
            hub.publish([dict(type='parking.snapshot',schema_version='1.0',data=snapshot)])
            await asyncio.sleep(0)
        assert peer.queue.qsize()<=64 and peer.queue.get_nowait()==1013
        await hub.close()
    asyncio.run(exercise())

class GateFake(FakeClient):
    def __init__(self):super().__init__();self.published=[]
    def is_connected(self):return self.started
    def publish(self,topic,payload,qos,retain):
        self.published.append((topic,json.loads(payload),qos,retain));return SimpleNamespace(rc=0)

def test_mqtt_publish_ack_no_replay_on_reconnect(tmp_path):
    db=Database(tmp_path/'duplex.sqlite3');db.initialize();p=ParkingService(db)
    fake=GateFake();runtime=MQTTSubscriber(p,Settings(db.path,mqtt_enabled=True),client=fake)
    g=GateController(p);runtime.ingestor.gate_controller=g;g.set_publisher(runtime.publish_gate_command)
    runtime.start()
    try:
        connect(runtime,fake);runtime.queue.join()
        runtime.ingestor.ingest('smartparking/group21/device/status',json.dumps(dict(device_id='esp32-01',status='online',uptime_ms=1000)).encode())
        for slot in SLOT_IDS:p.update_slot(slot,'EMPTY')
        g.submit(req())
        assert fake.published==[('smartparking/group21/gate/command',dict(command_id='test-001',action='OPEN',direction='ENTRY'),0,False)]
        fake.on_message(fake,None,SimpleNamespace(topic=GATE_TOPIC,payload=json.dumps(dict(device_id='esp32-01',command_id='test-001',status='OPENED')).encode(),retain=False))
        runtime.queue.join();assert g.get('test-001')['state']=='CONFIRMED'
        fake.on_disconnect(fake,None,{},1,None);connect(runtime,fake);runtime.queue.join()
        assert len(fake.published)==1
    finally:runtime.stop()


def test_ws_timeout_command_and_snapshot(api):
    client,_=api
    clock=Clock();client.app.state.gate.clock=clock
    with client.websocket_connect('/ws/parking') as ws:
        ws.receive_json();client.post('/api/parking/gate',json=req().model_dump())
        ws.receive_json();ws.receive_json()
        clock.advance(5);client.app.state.gate.expire()
        command=ws.receive_json();snapshot=ws.receive_json()
        assert command['data']['state']=='TIMEOUT'
        assert not snapshot['data']['gate_meta']['confirmed']
        assert snapshot['data']['gate_meta']['pending_command_id'] is None


def test_hub_invalid_batch_forces_resync(gate):
    p,_,_,_=gate
    async def exercise():
        hub=RealtimeHub(p,asyncio.get_running_loop());peer=hub.register(None)
        hub.publish([dict(type='parking.snapshot',schema_version='INVALID',data=p.snapshot())])
        await asyncio.sleep(0)
        assert peer.queue.get_nowait()==1011
        await hub.close()
    asyncio.run(exercise())


@pytest.mark.parametrize('timeout',[0,-1,float('nan'),float('inf')])
def test_invalid_ack_timeout_rejected(tmp_path,timeout):
    with pytest.raises(ValueError): Settings(tmp_path/'config.sqlite3',ack_timeout=timeout)


def test_snapshot_timestamp_is_commit_time_not_delayed_receive_time(gate):
    from datetime import datetime
    p,_,_,_=gate
    p.update_slot('P01','OCCUPIED',received_at='2020-01-01T00:00:00Z')
    snapshot=p.snapshot()
    assert snapshot['events'][0]['timestamp']=='2020-01-01T00:00:00.000000Z'
    assert datetime.fromisoformat(snapshot['timestamp'].replace('Z','+00:00'))>datetime.fromisoformat('2020-01-01T00:00:00+00:00')


def test_rapid_two_client_disconnects_leave_no_peers(api):
    client,_=api
    for _ in range(25):
        with client.websocket_connect('/ws/parking') as one,client.websocket_connect('/ws/parking') as two:
            one.receive_json();two.receive_json()
    assert not client.app.state.realtime.peers
    assert client.get('/health').status_code==200
