import asyncio
import logging
from dataclasses import dataclass
from threading import BoundedSemaphore, Event
from fastapi.encoders import jsonable_encoder
from app.schemas import SnapshotMessage, GateMessage

LOG=logging.getLogger('uvicorn.error.realtime')

@dataclass(eq=False)
class Peer:
    socket: object
    queue: asyncio.Queue
    revision: int

class RealtimeHub:
    def __init__(self,parking,loop):
        self.parking,self.loop=parking,loop
        self.peers=set()
        self.capacity=BoundedSemaphore(256)
        self.overloaded=Event()
        self.closed=False

    def publish(self,messages):
        if self.closed: return
        # Bound cross-thread callbacks as well as per-client queues.
        if not self.capacity.acquire(blocking=False):
            if not self.overloaded.is_set():
                self.overloaded.set()
                self.loop.call_soon_threadsafe(self._overflow)
            return
        self.loop.call_soon_threadsafe(self._deliver,messages)

    def _close_peer(self,peer,code):
        while not peer.queue.empty(): peer.queue.get_nowait()
        peer.queue.put_nowait(code)

    def _overflow(self):
        for peer in tuple(self.peers): self._close_peer(peer,1013)
        self.overloaded.clear()
        LOG.warning('Realtime overloaded; clients must reconnect and resnapshot')

    def _deliver(self,messages):
        try:
            if self.closed: return
            validated=[jsonable_encoder((GateMessage if item['type']=='gate.command' else SnapshotMessage).model_validate(item)) for item in messages]
            revision=validated[-1]['data']['revision']
            for peer in tuple(self.peers):
                if revision<=peer.revision: continue
                try:
                    peer.queue.put_nowait(validated)
                    peer.revision=revision
                except asyncio.QueueFull:
                    self._close_peer(peer,1013)
        except Exception:
            LOG.exception('Invalid realtime batch; disconnect clients to force REST resync')
            for peer in tuple(self.peers): self._close_peer(peer,1011)
        finally: self.capacity.release()

    def register(self,socket):
        # Snapshot and registration are atomic with respect to state commits.
        with self.parking.lock:
            snapshot=self.parking.snapshot()
            peer=Peer(socket,asyncio.Queue(maxsize=64),snapshot['revision'])
            initial=SnapshotMessage(type='parking.snapshot',schema_version='1.0',data=snapshot)
            peer.queue.put_nowait([jsonable_encoder(initial)])
            self.peers.add(peer)
        return peer

    async def sender(self,peer):
        while True:
            batch=await peer.queue.get()
            if isinstance(batch,int):
                await peer.socket.close(code=batch)
                return
            for message in batch:
                await asyncio.wait_for(peer.socket.send_json(message),timeout=5)

    async def close(self):
        self.closed=True
        for peer in tuple(self.peers): self._close_peer(peer,1001)
