import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.database import Database
from app.main import create_app
from app.models import SLOT_IDS
from app.services.parking import ParkingService
from app.schemas import Snapshot, Summary, Statistics, EventList, SlotList, Health

@pytest.fixture
def core(tmp_path):
    db = Database(tmp_path/'test.sqlite3')
    db.initialize()
    return ParkingService(db)

@pytest.fixture
def client(tmp_path):
    app=create_app(Settings(tmp_path/'api.sqlite3',('http://127.0.0.1:5173',)))
    with TestClient(app) as client:
        yield client

def test_database_initialization_is_idempotent(core):
    core.database.initialize()
    with core.database.connect() as db:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {'parking_slots','parking_events','gate_commands'} <= tables
        assert db.execute('SELECT COUNT(*) FROM parking_slots').fetchone()[0]==4
        assert db.execute('PRAGMA user_version').fetchone()[0]==2
    state=core.snapshot()
    assert set(state['slots'])==set(SLOT_IDS)
    assert set(state['slots'].values())=={'UNKNOWN'}
    assert state['events']==[]
    assert core.summary()['unknown']==4
    assert core.summary()['free']==0
    assert core.summary()['status']=='UNKNOWN'

def test_transitions_and_utc(core):
    core.update_slot('P01','EMPTY')
    core.update_slot('P01','OCCUPIED')
    core.update_slot('P01','EMPTY')
    events=core.snapshot()['events']
    assert [e['type'] for e in events]==['OUT','IN','STATUS']
    assert len({e['id'] for e in events})==3
    assert events[0]['previous']=='OCCUPIED'
    for e in events:
        assert e['timestamp'].endswith('Z')
        assert datetime.fromisoformat(e['timestamp'].replace('Z','+00:00')).utcoffset().total_seconds()==0
    stats=core.statistics()
    assert stats['entries']==stats['exits']==1
    assert stats['by_slot']['P01']==1

def test_duplicate_is_noop(core):
    core.update_slot('P01','OCCUPIED')
    before=core.snapshot()
    assert core.update_slot('P01','OCCUPIED') is False
    assert core.snapshot()==before

@pytest.mark.parametrize('invalid_id,status',[('P99','EMPTY'),('__proto__','EMPTY'),('P01','FREE'),('P01',None)])
def test_invalid_input_no_mutation(core,invalid_id,status):
    before=core.snapshot()
    with pytest.raises((ValueError,TypeError)):
        core.update_slot(invalid_id,status)
    assert core.snapshot()==before

def test_full_and_unknown_not_free(core):
    for slot in SLOT_IDS:
        core.update_slot(slot,'OCCUPIED')
    assert core.summary()['full'] is True
    assert core.summary()['free']==0
    core.update_slot('P01','UNKNOWN')
    s=core.summary()
    assert (s['occupied'],s['free'],s['unknown'],s['status'])==(3,0,1,'UNKNOWN')
    core.update_slot('P02','EMPTY')
    assert core.summary()['status']=='AVAILABLE'

def test_unknown_recovery_is_not_entry(core):
    core.update_slot('P01','OCCUPIED')
    core.update_slot('P01','UNKNOWN')
    core.update_slot('P01','OCCUPIED')
    assert all(e['type']=='STATUS' for e in core.snapshot()['events'])
    assert core.statistics()['entries']==0

def test_restart_keeps_history_last_known_but_invalidates_trust(core):
    core.update_slot('P01','EMPTY')
    core.update_slot('P01','OCCUPIED')
    before=core.snapshot()
    fresh_db=Database(core.database.path)
    fresh_db.initialize()
    restarted=ParkingService(fresh_db)
    state=restarted.snapshot()
    assert state['slots']['P01']=='UNKNOWN'
    assert state['events']==before['events']
    assert state['stream_id']!=before['stream_id']
    assert state['revision']==0
    assert restarted.statistics()['entries']==1
    with fresh_db.connect() as db:
        assert db.execute("SELECT status FROM parking_slots WHERE slot_id='P01'").fetchone()[0]=='OCCUPIED'
    restarted.update_slot('P01','OCCUPIED')
    assert restarted.snapshot()['slots']['P01']=='OCCUPIED'
    assert restarted.snapshot()['events']==before['events']

def test_concurrent_duplicate_does_not_duplicate_events(core):
    core.update_slot('P01','EMPTY')
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _:core.update_slot('P01','OCCUPIED'),range(24)))
    assert core.statistics()['entries']==1
    assert len(core.snapshot()['events'])==2

def test_sqlite_constraints(core):
    with pytest.raises(sqlite3.IntegrityError),core.database.connect() as db:
        db.execute("UPDATE parking_slots SET status='FREE' WHERE slot_id='P01'")
    assert core.snapshot()['slots']['P01']=='UNKNOWN'

@pytest.mark.parametrize('route,schema',[('/health',Health),('/api/parking/status',Snapshot),('/api/parking/slots',SlotList),('/api/parking/summary',Summary),('/api/parking/events',EventList),('/api/parking/statistics',Statistics)])
def test_api_schema(client,route,schema):
    response=client.get(route)
    assert response.status_code==200
    schema.model_validate(response.json())

def test_api_fixtures_are_explicit_not_esp32(client):
    service=client.app.state.parking
    for slot in SLOT_IDS:
        service.update_slot(slot,'EMPTY')  # Test fixture, no device/network input.
    service.update_slot('P01','OCCUPIED')
    assert client.get('/api/parking/summary').json()['free']==3
    assert client.get('/api/parking/statistics').json()['entries']==1
    state=client.get('/api/parking/status').json()
    assert state['connection']=={'mqtt':'DISCONNECTED','device':'UNKNOWN','synchronized':False}
    assert state['gate_meta']['confirmed'] is False
    assert state['events'][0]['type']=='IN'
    assert client.post('/api/parking/gate',json={'status':'OPEN'}).status_code==422
    assert client.patch('/api/parking/slots/P01',json={'status':'EMPTY'}).status_code in (404,405)

def test_api_restart(tmp_path):
    config=Settings(tmp_path/'restart.sqlite3')
    with TestClient(create_app(config)) as client:
        client.app.state.parking.update_slot('P01','EMPTY')
        client.app.state.parking.update_slot('P01','OCCUPIED')
        first=client.get('/api/parking/status').json()
    with TestClient(create_app(config)) as client:
        second=client.get('/api/parking/status').json()
        assert second['events']==first['events']
        assert second['slots']['P01']=='UNKNOWN'
        assert second['stream_id']!=first['stream_id']

def test_path_does_not_depend_on_cwd(tmp_path,monkeypatch):
    monkeypatch.setenv('SMART_PARKING_DB_PATH','data/path-test.sqlite3')
    first=Settings.from_env().db_path
    monkeypatch.chdir(tmp_path)
    assert Settings.from_env().db_path==first
    assert first.is_absolute()

def test_cors_allowlist(client):
    response=client.get('/health',headers={'Origin':'http://127.0.0.1:5173'})
    assert response.headers['access-control-allow-origin']=='http://127.0.0.1:5173'
    assert 'access-control-allow-origin' not in client.get('/health',headers={'Origin':'https://unexpected.invalid'}).headers

def test_failed_write_rolls_back_event_and_revision(core):
    core.update_slot('P01','EMPTY')
    before=core.snapshot()
    with core.database.connect() as db:
        db.execute("CREATE TRIGGER reject_occupied BEFORE UPDATE ON parking_slots WHEN NEW.status='OCCUPIED' BEGIN SELECT RAISE(ABORT, 'fixture rejection'); END")
    with pytest.raises(sqlite3.IntegrityError):
        core.update_slot('P01','OCCUPIED')
    assert core.snapshot()==before

def test_api_history_statistics_revision_consistent(client):
    core=client.app.state.parking
    core.update_slot('P01','EMPTY')
    core.update_slot('P01','OCCUPIED')
    snapshot=client.get('/api/parking/status').json()
    events=client.get('/api/parking/events').json()
    stats=client.get('/api/parking/statistics').json()
    assert snapshot['events']==events['events']
    assert snapshot['revision']==events['revision']==stats['revision']
    assert stats['entries']==sum(e['type']=='IN' for e in events['events'])
    assert stats['exits']==sum(e['type']=='OUT' for e in events['events'])
    assert sum(stats['by_slot'].values())==stats['entries']
