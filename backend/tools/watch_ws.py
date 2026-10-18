"""Read-only CLI WebSocket viewer for manual verification; never sends gate commands."""
import asyncio
import json
import argparse
from websockets.asyncio.client import connect

async def watch(url):
    retry=1
    while True:
        try:
            async with connect(url) as socket:
                print('Connected; first message is a full snapshot',flush=True)
                retry=1
                async for raw in socket:
                    print(json.dumps(json.loads(raw),ensure_ascii=False),flush=True)
        except Exception as error:
            print(f'Disconnected ({type(error).__name__}); retry in {retry}s',flush=True)
        await asyncio.sleep(retry)
        retry=min(retry*2,10)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='ws://127.0.0.1:8000/ws/parking')
    args=parser.parse_args()
    try:asyncio.run(watch(args.url))
    except KeyboardInterrupt:pass
