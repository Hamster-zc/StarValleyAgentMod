import asyncio
import websockets
import json
from shared.protocol import *
import logging
from datetime import datetime
import websockets.exceptions
from host.short_memory_injection import build_prompt_with_memory
import shared.memory as memory_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DB_PATH = r"storage/npc_memory.db"

# 存储节点信息
nodes = {}  # node_id -> {"websocket": websocket, "capabilities": [], "last_heartbeat": datetime, "load": 0.0}

# 存储待处理任务信息
pending_tasks = {}  # task_id -> {"future": Future, "client_ws": websocket}

async def node_handler(websocket, path):
    """处理 Node 的连接"""
    # 1. 接收 RegisterNodeMessage，存入 nodes
    # 2. 启动心跳检测任务（定期检查超时）
    # 3. 循环接收消息：心跳、NodeResult
    while True:
        raw_message = await websocket.recv()
        message = json.loads(raw_message)
        if message.get("type") == "register":
            reg_msg = RegisterNodeMessage.model_validate(message)
            nodes[reg_msg.node_id] = {
                "websocket": websocket,
                "capabilities": reg_msg.capabilities,
                "last_heartbeat": datetime.now(),
                "load": 0.0
            }
            logger.info(f"Node registered: {reg_msg.node_id} with capabilities {reg_msg.capabilities}")
        
        if message.get("type") == "heartbeat":
            hb_msg = HeartbeatMessage.model_validate(message)
            if hb_msg.node_id in nodes:
                nodes[hb_msg.node_id]["last_heartbeat"] = datetime.now()
                nodes[hb_msg.node_id]["load"] = hb_msg.load
                logger.info(f"Heartbeat received from {hb_msg.node_id}, load: {hb_msg.load}")
        
        if message.get("type") == "node_result":
            result_msg = NodeResult.model_validate(message)
            logger.info(f"Result received from {result_msg.node_id} for task {result_msg.task_id}: {result_msg.status}")
            pending = pending_tasks.get(result_msg.task_id)
            if pending:
                pending["future"].set_result(result_msg)


async def client_handler(websocket, path):
    """处理 Client 的连接"""
    # 1. 接收 ClientRequest
    # 2. 选择一个节点（简单轮询或随机）
    # 3. 发送 TaskAssignment 给节点
    # 4. 等待 NodeResult 或超时，返回给 client
    while True:
        try:
            raw_message = await websocket.recv()
        except Exception as e:
            logger.info(f"Client disconnected: {type(e).__name__} - {e}")
            break
        message = json.loads(raw_message)
        if message.get("type") =="client_request":
            client_msg = ClientRequest.model_validate(message)
            logger.info(f"Client request received: {client_msg.request_id} with context: {client_msg.context}")
            found = False
            for node_id, node_info in nodes.items():
                if "llm" in node_info["capabilities"]:
                    found = True
                    task_id = f"task_{client_msg.request_id}"
                    memory_utils.append_turn(
                        db_path=DB_PATH,
                        turn={
                            "request_id": client_msg.request_id,
                            "npc_id": client_msg.npc_id,
                            "player_id": client_msg.player_id,
                            "role": "user",
                            "text": client_msg.context[-1]["content"] if client_msg.context else "",
                            "game_day": client_msg.game_day
                        })
                    # 构建包含长短期记忆的提示词
                    temp_prompt, memory_ids = build_prompt_with_memory(
                        db_path= DB_PATH,
                        npc_id=client_msg.npc_id,
                        game_day=client_msg.game_day,
                        context=client_msg.context
                    )
                    logger.info(f"DEBUG: memory_ids = {memory_ids}")

                    task_msg = TaskAssignment(
                        task_id=task_id,
                        node_id=node_id,
                        request_id=client_msg.request_id,
                        prompt = temp_prompt,
                        max_tokens=256,
                        temperature=0.7,
                        model="gpt-4",
                        max_latency_ms=25000,
                        memory_ids=memory_ids
                    )
                    await node_info["websocket"].send(task_msg.model_dump_json())
                    logger.info(f"Task {task_id} assigned to node {node_id}")
                    # 存储待处理任务信息
                    future = asyncio.Future()
                    pending_tasks[task_id] = {"future": future, "client_ws": websocket}
                    try:
                        result_msg = await asyncio.wait_for(future, timeout=25.0)
                        # 成功，回复客户端
                        await websocket.send(json.dumps({
                            "type": "client_response",
                            "request_id": client_msg.request_id,
                            "result": result_msg.result,
                            "citations": result_msg.citations 
                        }))
                        memory_utils.append_turn(
                            db_path=DB_PATH,
                            turn={
                                "request_id": client_msg.request_id,
                                "npc_id": client_msg.npc_id,
                                "player_id": client_msg.player_id,
                                "role": "assistant",
                                "text": result_msg.result,
                                "game_day": client_msg.game_day
                            }
                        )
                    except asyncio.TimeoutError:
                        # 超时，降级回复
                        await websocket.send(json.dumps({
                            "type": "client_response",
                            "request_id": client_msg.request_id,
                            "error": "请求超时，请稍后重试"
                        }))
                    finally:
                        pending_tasks.pop(task_id, None)
                    break
            if not found:
                await websocket.send(json.dumps({
                    "type": "client_response",
                    "request_id": client_msg.request_id,
                    "error": "当前无可用节点，请稍后重试"
                }))

async def check_heartbeat_timeout():
    while True:
        await asyncio.sleep(10)
        now = datetime.now()
        timeout_nodes = []
        for node_id, info in nodes.items():
            if (now - info["last_heartbeat"]).total_seconds() > 30:
                timeout_nodes.append(node_id)
        for node_id in timeout_nodes:
            logger.warning(f"Node {node_id} heartbeat timeout, removing")
            del nodes[node_id]

async def main():
    async def combined_handler(websocket):
        path = websocket.request.path
        if path == "/node":
            await node_handler(websocket, path)
        elif path == "/client":
            await client_handler(websocket, path)
        else:
            logger.warning(f"Unknown path: {path}")
            await websocket.close()

    async with websockets.serve(combined_handler, "localhost", 8765):
        logger.info("Host started on ws://localhost:8765 (paths: /node, /client)")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())