# 消息协议文档 v1.0

本文档定义了 `stardew_npc_agent` 中 Host、Node、Client 三方通过 WebSocket 通信的消息格式。所有消息均为 JSON 格式，使用 Pydantic 模型进行序列化/反序列化。

## 通用字段（BaseMessage）

所有消息都包含以下字段：

| 字段       | 类型             | 必填 | 说明                                    |
| ---------- | ---------------- | ---- | --------------------------------------- |
| `version`  | string           | 是   | 协议版本号，当前为 `"1.0"`              |
| `type`     | string           | 是   | 消息类型标识，见各消息具体定义          |
| `timestamp`| string (ISO 8601) | 是   | 消息发送的系统时间（UTC），自动生成     |

## 1. 节点注册（RegisterNodeMessage）

**方向**：Node → Host

**字段**：

| 字段          | 类型         | 必填 | 说明                                                       |
| ------------- | ------------ | ---- | ---------------------------------------------------------- |
| `type`        | `"register"` | 是   | 固定值                                                     |
| `node_id`     | string       | 是   | 节点唯一标识                                               |
| `capabilities`| list[string] | 是   | 节点能力，例如 `["llm", "embedding", "cuda"]`              |

**示例**：
```json
{
  "version": "1.0",
  "type": "register",
  "timestamp": "2026-06-03T10:30:00.123Z",
  "node_id": "node_abc123",
  "capabilities": ["llm", "fast_inference", "cuda"]
}
```

## 2. 心跳检测（HeartbeatMessage）

**方向**：Node → Host

**字段**：

| 字段      | 类型             | 必填 | 说明                                    |
| --------- | ---------------- | ---- | --------------------------------------- |
| `type`    | `"heartbeat"`    | 是   | 固定值                                  |
| `node_id` | string           | 是   | 节点ID                                  |
| `load`    | float (0.0–1.0)  | 是   | 节点当前负载，0=空闲，1=满载            |

**示例**：
```json
{
  "version": "1.0",
  "type": "heartbeat",
  "timestamp": "2026-06-03T10:30:10.456Z",
  "node_id": "node_abc123",
  "load": 0.3
}
```

## 3. 客户端请求（ClientRequest）

**方向**：Client → Host

**字段**：

| 字段           | 类型                       | 必填 | 说明                                    |
| -------------- | -------------------------- | ---- | --------------------------------------- |
| `type`         | `"client_request"`         | 是   | 固定值                                  |
| `request_id`   | string                     | 是   | 客户端生成的请求唯一ID                  |
| `npc_id`       | string                     | 是   | NPC名称，例如 `"Abigail"`               |
| `player_id`    | string                     | 是   | 玩家ID                                  |
| `game_day`     | int (>=1)                  | 是   | 游戏内天数（春季第1天为1）              |
| `context`      | list[dict]                 | 是   | 对话历史，每个元素含 `role` 和 `content`|
| `env`          | dict 或 null               | 否   | 环境信息，例如天气、地点                |
| `prefer_local` | bool                       | 否   | 是否优先本地节点，默认 `false`          |

**示例**：
```json
{
  "version": "1.0",
  "type": "client_request",
  "timestamp": "2026-06-03T10:30:15.789Z",
  "request_id": "req_001",
  "npc_id": "Abigail",
  "player_id": "player123",
  "game_day": 5,
  "context": [
    {"role": "user", "content": "今天有什么新闻？"}
  ],
  "env": {"weather": "sunny", "location": "town"},
  "prefer_local": false
}
```

## 4. 任务分配（TaskAssignment）

**方向**：Host → Node

**字段**：

| 字段            | 类型                | 必填 | 说明                                    |
| --------------- | ------------------- | ---- | --------------------------------------- |
| `type`          | `"task_assignment"` | 是   | 固定值                                  |
| `task_id`       | string              | 是   | Host 生成的任务唯一ID                   |
| `node_id`       | string              | 是   | 目标节点ID                              |
| `request_id`    | string              | 是   | 对应的客户端请求ID                      |
| `prompt`        | string              | 是   | 组装好的完整 prompt（包含系统指令、对话历史、检索结果等） |
| `max_tokens`    | int                 | 否   | 生成最大 token 数，默认 256             |
| `temperature`   | float (0.0–1.0)     | 否   | 采样温度，默认 0.7                      |
| `model`         | string 或 null      | 否   | 指定模型名称（如有多个）                |
| `max_latency_ms`| float 或 null       | 否   | 最大允许延迟（毫秒），默认 25000        |

**示例**：
```json
{
  "version": "1.0",
  "type": "task_assignment",
  "timestamp": "2026-06-03T10:30:16.001Z",
  "task_id": "task_789",
  "node_id": "node_abc123",
  "request_id": "req_001",
  "prompt": "你是一个星露谷NPC...",
  "max_tokens": 150,
  "temperature": 0.8,
  "model": "llama2-7b",
  "max_latency_ms": 20000
}
```

## 5. 节点结果（NodeResult）

**方向**：Node → Host

**字段**：

| 字段         | 类型                       | 必填 | 说明                                    |
| ------------ | -------------------------- | ---- | --------------------------------------- |
| `type`       | `"node_result"`            | 是   | 固定值                                  |
| `task_id`    | string                     | 是   | 对应的任务ID                            |
| `node_id`    | string                     | 是   | 节点ID                                  |
| `request_id` | string                     | 是   | 对应的客户端请求ID                      |
| `status`     | `"success"` 或 `"failure"` | 是   | 执行结果                                |
| `result`     | string                     | 是   | 成功时为生成的回复文本；失败时可为空    |
| `error_msg`  | string 或 null             | 否   | 失败时提供错误描述                      |
| `latency_ms` | float 或 null              | 否   | 实际推理耗时（毫秒）                    |

**示例（成功）**：
```json
{
  "version": "1.0",
  "type": "node_result",
  "timestamp": "2026-06-03T10:30:17.342Z",
  "task_id": "task_789",
  "node_id": "node_abc123",
  "request_id": "req_001",
  "status": "success",
  "result": "今天镇上有个节日，大家都在准备呢！",
  "error_msg": null,
  "latency_ms": 1234
}
```

**示例（失败）**：
```json
{
  "version": "1.0",
  "type": "node_result",
  "timestamp": "2026-06-03T10:30:20.001Z",
  "task_id": "task_789",
  "node_id": "node_abc123",
  "request_id": "req_001",
  "status": "failure",
  "result": "",
  "error_msg": "GPU out of memory",
  "latency_ms": 567
}
```

## 6. 错误消息（ErrorMessage）

**方向**：任意方向（一般由 Host 或 Node 发出）

**字段**：

| 字段         | 类型               | 必填 | 说明                                    |
| ------------ | ------------------ | ---- | --------------------------------------- |
| `type`       | `"error"`          | 是   | 固定值                                  |
| `error_code` | int                | 是   | 错误码（例如 4001 表示节点超时）        |
| `error_msg`  | string             | 是   | 人类可读的错误信息                      |
| `request_id` | string 或 null     | 否   | 关联的客户端请求ID（如果有）            |
| `task_id`    | string 或 null     | 否   | 关联的任务ID（如果有）                  |

**示例**：
```json
{
  "version": "1.0",
  "type": "error",
  "timestamp": "2026-06-03T10:30:18.999Z",
  "error_code": 4001,
  "error_msg": "Node heartbeat timeout",
  "request_id": "req_001",
  "task_id": null
}
```

---

## 消息类型汇总

| `type` 值             | 对应类                |
| --------------------- | --------------------- |
| `"register"`          | `RegisterNodeMessage` |
| `"heartbeat"`         | `HeartbeatMessage`    |
| `"client_request"`    | `ClientRequest`       |
| `"task_assignment"`   | `TaskAssignment`      |
| `"node_result"`       | `NodeResult`          |
| `"error"`             | `ErrorMessage`        |

## 通用解析方式

接收方可根据 `type` 字段选择对应的 Pydantic 模型进行解析。例如 Python 中：

```python
msg_dict = json.loads(raw_message)
msg_type = msg_dict["type"]
if msg_type == "register":
    obj = RegisterNodeMessage.model_validate(msg_dict)
elif msg_type == "heartbeat":
    obj = HeartbeatMessage.model_validate(msg_dict)
# ...
```

或者使用 `AnyMessage` Union + `TypeAdapter` 自动识别（本项目提供 `parse_message` 辅助函数）。
