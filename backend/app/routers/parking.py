from fastapi import APIRouter, Request
from app.schemas import Snapshot, EventList, Statistics, Summary, SlotList, Health

router = APIRouter()

@router.get('/health', response_model=Health)
def health(request: Request):
    with request.app.state.parking.database.connect() as db:
        db.execute('SELECT 1').fetchone()
    enabled = request.app.state.mqtt is not None
    return Health(phase='REALTIME_GATE',mqtt_enabled=enabled,websocket_enabled=True)

@router.get('/api/parking/status', response_model=Snapshot)
def status(request: Request):
    return request.app.state.parking.snapshot()

@router.get('/api/parking/events', response_model=EventList)
def events(request: Request):
    state = request.app.state.parking.snapshot()
    return {key:state[key] for key in ('schema_version','stream_id','revision','events')}

@router.get('/api/parking/statistics', response_model=Statistics)
def statistics(request: Request):
    return request.app.state.parking.statistics()

# Read-only convenience views requested for core phase, not replacement v1 endpoints.
@router.get('/api/parking/summary', response_model=Summary)
def summary(request: Request):
    return request.app.state.parking.summary()

@router.get('/api/parking/slots', response_model=SlotList)
def slots(request: Request):
    state = request.app.state.parking.snapshot()
    return dict(schema_version=state['schema_version'],stream_id=state['stream_id'],revision=state['revision'],slots=[dict(slot_id=k,status=v) for k,v in state['slots'].items()])
