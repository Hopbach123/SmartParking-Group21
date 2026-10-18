import anyio
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import GateRequest, GateCommand

router=APIRouter()

@router.post('/api/parking/gate',response_model=GateCommand,status_code=202)
def gate(request: Request,command: GateRequest):
    record,status=request.app.state.gate.submit(command)
    return JSONResponse(status_code=status,content=jsonable_encoder(GateCommand.model_validate(record)))

@router.get('/api/parking/commands/{command_id}',response_model=GateCommand)
def command(request: Request,command_id: str):
    return request.app.state.gate.get(command_id)

@router.websocket('/ws/parking')
async def realtime(socket: WebSocket):
    origins=socket.app.state.settings.cors_origins
    origin=socket.headers.get('origin')
    if origin is not None and origin not in origins:
        await socket.close(code=1008)
        return
    await socket.accept()
    hub=socket.app.state.realtime
    peer=hub.register(socket)
    async def receiver():
        while True:
            message=await socket.receive()
            if message['type']=='websocket.disconnect': return
            # v1 is server-push only. Gate commands must go through REST policy checks.
            await socket.close(code=1008,reason='Use REST for gate commands')
            return
    try:
        async with anyio.create_task_group() as group:
            async def sender():
                try:
                    await hub.sender(peer)
                except (WebSocketDisconnect,TimeoutError,RuntimeError):
                    pass
                finally:
                    group.cancel_scope.cancel()
            group.start_soon(sender)
            try:
                await receiver()
            except (WebSocketDisconnect,RuntimeError):
                pass
            finally:
                group.cancel_scope.cancel()
    finally:
        hub.peers.discard(peer)
        # Parent cancellation must not interrupt cleanup and leave a sender task alive.
        with anyio.CancelScope(shield=True):
            with anyio.move_on_after(1):
                try: await socket.close()
                except (RuntimeError,WebSocketDisconnect): pass
