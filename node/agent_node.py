import asyncio
import websockets
import json
import uuid
import logging
from datetime import datetime

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
CAPABILITIES = ["llm", "dummy"]            # dummy 表示当前是模拟推理


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


# ===== 主函数 =====
async def main():
    # 连接 Host
    async with websockets.connect(HOST_URI) as websocket:
        # 1. 发送注册消息
        register_msg = RegisterNodeMessage(
            node_id=NODE_ID,
            capabilities=CAPABILITIES
        )
        await websocket.send(register_msg.model_dump_json())
        logger.info(f"Registered with node_id={NODE_ID}")

        # 2. 启动心跳任务
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket))

        # 3. 接收并处理消息（主要是 TaskAssignment）
        try:
            async for raw_message in websocket:
                data = json.loads(raw_message)
                msg_type = data.get("type")

                if msg_type == "task_assignment":
                    # 解析任务
                    task = TaskAssignment.model_validate(data)
                    logger.info(f"Received task {task.task_id} for request {task.request_id}")

                    # TODO: 在这里实现真正的推理（或模拟）
                    # 当前为 dummy 实现：固定回复 + 模拟延迟
                    await asyncio.sleep(0.5)   # 模拟计算耗时
                    dummy_reply = f"[Dummy] 收到 prompt: {task.prompt[:50]}..."
                    
                    # 构造结果消息
                    result = NodeResult(
                        task_id=task.task_id,
                        node_id=NODE_ID,
                        request_id=task.request_id,
                        status="success",
                        result=dummy_reply,
                        latency_ms=500,       # 模拟耗时
                    )
                    # 发送结果
                    await websocket.send(result.model_dump_json())
                    logger.info(f"Sent result for task {task.task_id}")

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