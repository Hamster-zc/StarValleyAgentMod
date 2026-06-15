import asyncio
import websockets
import json
import uuid
import logging
from datetime import datetime
from .llm_wrapper import LLMWrapper
import time

# 导入协议消息类
from shared.protocol import (
    RegisterNodeMessage,
    HeartbeatMessage,
    TaskAssignment,
    NodeResult,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== 配置常量 =====
HOST_URI = "ws://localhost:8765/node"      # Host 的 node 端点
HEARTBEAT_INTERVAL = 10                    # 心跳间隔（秒）
NODE_ID = f"node_{uuid.uuid4().hex[:6]}"   # 唯一节点ID

# 节点声称的能力（可根据实际修改）
CAPABILITIES = ["llm"]            # dummy 表示当前是模拟推理

# 最大并发任务数
MAX_CONCURRENT = 1
sem = asyncio.Semaphore(MAX_CONCURRENT)

MODELPATH = r"./model/Qwen2.5-7B-Instruct-Q4_K_M.gguf"

# ===== 心跳发送任务 =====
async def send_heartbeat(websocket):
    """定期发送心跳消息"""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        # TODO: 计算真实负载（例如队列长度、GPU使用率等），目前暂用 0.0
        load = 0.0
        hb_msg = HeartbeatMessage(node_id=NODE_ID, load=load)
        await websocket.send(hb_msg.model_dump_json())
        logger.debug(f"Heartbeat sent, load={load}")

async def process_task(websocket, task: TaskAssignment, llm: LLMWrapper):  
    try:
        response = await asyncio.wait_for(
            llm.generate(
                prompt=task.prompt, 
                max_tokens=task.max_tokens,
                temperature=task.temperature), 
                timeout=task.max_latency_ms / 1000.0)
        generated_text = response['choices'][0]["text"].strip()                
        result = NodeResult(
                task_id=task.task_id,
                node_id=NODE_ID,
                request_id=task.request_id,
                status="success",
                result=generated_text,
                citations=task.memory_ids
                )
        logger.info(f"DEBUG: task.memory_ids = {task.memory_ids}")
    except asyncio.TimeoutError:
        result = NodeResult(
            task_id=task.task_id,
            node_id=NODE_ID,
            request_id=task.request_id,
            status="failure",
            result="",
            error_msg="LLM generation timeout"
        )    
    except Exception as e:
        result = NodeResult(
            task_id=task.task_id,
            node_id=NODE_ID,
            request_id=task.request_id,
            status="failure",
            result="",
            error_msg=str(e)
        )
    # 发送结果
    await websocket.send(result.model_dump_json())
    logger.info(f"Sent result for task {task.task_id}")


# ===== 主函数 =====
async def main():
    llm = LLMWrapper(model_path=MODELPATH)
    # 连接 Host
    async with websockets.connect(HOST_URI) as websocket:
        # 发送注册消息
        register_msg = RegisterNodeMessage(
            node_id=NODE_ID,
            capabilities=CAPABILITIES
        )
        await websocket.send(register_msg.model_dump_json())
        logger.info(f"Registered with node_id={NODE_ID}")

        # 启动心跳任务
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket))

        # 接收并处理消息（主要是 TaskAssignment）
        try:
            async for raw_message in websocket:
                data = json.loads(raw_message)
                msg_type = data.get("type")

                if msg_type == "task_assignment":
                    async with sem:
                        task = TaskAssignment.model_validate(data)
                        await process_task(websocket, task, llm)
                        

                elif msg_type == "error":
                    # 可选：处理来自 Host 的错误消息
                    logger.warning(f"Received error from host: {data}")
                else:
                    logger.warning(f"Unknown message type: {msg_type}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to host closed")
        finally:
            # 取消心跳任务
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down node")