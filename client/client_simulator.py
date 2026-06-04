import asyncio, websockets, json, uuid, logging
from shared.protocol import ClientRequest

HOST_URI = "ws://localhost:8765/client"
NUM_REQUESTS = 5  # 先小规模测试

async def main():
    async with websockets.connect(HOST_URI) as ws:
        for i in range(NUM_REQUESTS):
            req_id = f"req_{i}"
            req = ClientRequest(
                request_id=req_id,
                npc_id="Abigail",
                player_id="player1",
                game_day=1,
                context=[{"role": "user", "content": f"Hello {i}"}],
                env=None,
                prefer_local=False
            )
            await ws.send(req.model_dump_json())
            print(f"Sent {req_id}")

            # 等待回复（带超时）
            try:
                resp_raw = await asyncio.wait_for(ws.recv(), timeout=30.0)
                resp = json.loads(resp_raw)
                print(f"Received for {req_id}: {resp.get('result', resp.get('error'))[:100]}")
            except asyncio.TimeoutError:
                print(f"Timeout for {req_id}")
            except websockets.ConnectionClosed:
                print("Connection closed, exiting")
                break

            await asyncio.sleep(0.5)  # 请求间隔

if __name__ == "__main__":
    asyncio.run(main())