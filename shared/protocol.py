"""
- [ ] BaseMessage 基类
- [ ] RegisterNodeMessage 注册
- [ ] HeartbeatMessage 心跳检测
- [ ] ClientRequest client请求
- [ ] TaskAssignment 任务分配
- [ ] NodeResult 节点结果
- [ ] ErrorMessage 错误消息
- [ ] AnyMessage Union 类型，包含所有消息类型，方便处理不同类型的消息
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal
from typing import List, Dict, Optional, Union

class BaseMessage(BaseModel):
    """
    基础消息类，包含所有消息的公共字段
    """
    version: str = "1.0"
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RegisterNodeMessage(BaseMessage):
    """
    注册节点消息
    capabilities: 节点的能力列表,例如 capabilities = ["llm", "fast_inference", "embedding", "cuda"]
    """
    type: Literal["register"] = "register"
    node_id: str
    capabilities: list[str]

class HeartbeatMessage(BaseMessage):
    """
    心跳检测消息，同时返回节点的负载状态
    """
    type: Literal["heartbeat"] = "heartbeat"
    node_id: str
    load: float = Field(ge=0.0, le=1.0)  # 负载状态，范围0.0-1.0

class ClientRequest(BaseMessage):
    type: Literal["client_request"] = "client_request"
    request_id: str                         
    npc_id: str                             
    player_id: str                           
    game_day: int = Field(ge=1, description="游戏内天数，第1天春季")
    context: List[Dict[str, str]]            # 对话历史，例如 [{"role":"user","content":"hello"}]
    env: Optional[Dict] = None               # 环境信息，如 {"weather":"rain","location":"farm"}
    prefer_local: bool = False               # 是否优先本地节点（可选项）

class TaskAssignment(BaseMessage):
    """
    任务分配消息
    """
    type: Literal["task_assignment"] = "task_assignment"
    task_id: str
    node_id: str
    request_id: str

    prompt: str
    max_tokens: int = 256
    temperature: float = Field(ge=0.0, le=1.0, default=0.7)
    model: Optional[str] = None  # 可选的模型名称，例如 "gpt-4"
    max_latency_ms: Optional[float] = 25000  # 可选的最大延迟要求，单位毫秒

class NodeResult(BaseMessage):
    """
    节点结果消息
    """
    type: Literal["node_result"] = "node_result"
    task_id: str
    node_id: str
    request_id: str
    status: Literal["success", "failure"] = "success"
    result: str = ""
    error_msg: Optional[str] = None
    latency_ms: Optional[float] = None  # 可选的实际延迟，单位毫秒     

class ErrorMessage(BaseMessage):
    """
    错误消息
    """
    type: Literal["error"] = "error"
    error_code: int
    error_msg: str
    request_id: Optional[str] = None    # 关联的客户端请求ID（如果有）
    task_id: Optional[str] = None       # 关联的任务ID（如果有）


if __name__ == "__main__":
    # 1. 测试 RegisterNodeMessage
    reg = RegisterNodeMessage(node_id="node1", capabilities=["llm", "cuda"])
    json_str = reg.model_dump_json(indent=2)
    print("RegisterNodeMessage JSON:\n", json_str)
    reg2 = RegisterNodeMessage.model_validate_json(json_str)
    assert reg2.node_id == "node1"
    print("✅ RegisterNodeMessage 序列化/反序列化通过\n")

    # 2. 测试 HeartbeatMessage（注意 load 范围）
    hb = HeartbeatMessage(node_id="node1", load=0.5)
    json_str = hb.model_dump_json()
    hb2 = HeartbeatMessage.model_validate_json(json_str)
    assert hb2.load == 0.5
    print("✅ HeartbeatMessage 通过")

    # 测试 load 超出范围是否报错
    try:
        hb_bad = HeartbeatMessage(node_id="node1", load=1.5)
    except Exception as e:
        print("✅ 非法 load 值被拦截:", e)

    # 3. 测试 ClientRequest
    req = ClientRequest(
        request_id="req_001",
        npc_id="Abigail",
        player_id="p1",
        game_day=5,
        context=[{"role": "user", "content": "hello"}]
    )
    json_str = req.model_dump_json()
    req2 = ClientRequest.model_validate_json(json_str)
    assert req2.game_day == 5
    print("✅ ClientRequest 通过")

    # 测试 game_day <1 报错
    try:
        bad_req = ClientRequest(
            request_id="req_bad",
            npc_id="Abigail",
            player_id="p1",
            game_day=0,
            context=[]
        )
    except Exception as e:
        print("✅ 非法 game_day 被拦截:", e)

    # 4. 测试 TaskAssignment
    task = TaskAssignment(
        task_id="task_01",
        node_id="node1",
        request_id="req_001",
        prompt="Hello, world!"
    )
    json_str = task.model_dump_json()
    task2 = TaskAssignment.model_validate_json(json_str)
    assert task2.prompt == "Hello, world!"
    print("✅ TaskAssignment 通过")

    # 5. 测试 NodeResult
    res = NodeResult(
        task_id="task_01",
        node_id="node1",
        request_id="req_001",
        status="success",
        result="Hi there!"
    )
    json_str = res.model_dump_json()
    res2 = NodeResult.model_validate_json(json_str)
    assert res2.result == "Hi there!"
    print("✅ NodeResult 通过")

    # 6. 测试 ErrorMessage
    err = ErrorMessage(error_code=4001, error_msg="timeout", request_id="req_001")
    json_str = err.model_dump_json()
    err2 = ErrorMessage.model_validate_json(json_str)
    assert err2.error_code == 4001
    print("✅ ErrorMessage 通过")

    print("\n🎉 所有协议测试通过！")
