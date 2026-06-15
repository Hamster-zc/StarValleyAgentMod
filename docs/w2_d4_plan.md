# Week2 Day4：短期记忆注入 & 引用返回

## 目标
- 在 Host 下发 `TaskAssignment` 前，从 SQLite 中查询指定 NPC 在当天（`game_day`）的最近对话记录（短期记忆），并将这些记录的内容拼接到 `prompt` 中。
- 将被引用的记忆条目的 ID 列表通过 `TaskAssignment` 传递给 Node。
- Node 在构造 `NodeResult` 时，将此 ID 列表填入 `citations` 字段（若 `NodeResult` 无此字段，可先在协议中扩展）。
- 最终 Client 收到的 `NodeResult` 中包含 `citations`，用于验证记忆被使用。

## 涉及模块与依赖
- `shared/memory.py`：已有 `query_recent_turns` 函数，需要修改使其返回包含 `id` 的字典。
- `shared/protocol.py`：需要扩展 `TaskAssignment` 和 `NodeResult` 的字段。
- `host/server.py`：在 `client_handler` 中调用记忆注入函数，构造 `TaskAssignment`。
- `host/short_memory_injection.py`：新建文件，实现 prompt 构建与记忆 ID 收集。
- `node/agent_node.py`：在 `process_task` 中将 `task.memory_ids` 填入 `NodeResult.citations`。
- 数据库路径：使用 `storage/npc_memory.db`（或你已有的路径）。

## 设计思路
1. **获取短期记忆**：利用 `query_recent_turns` 根据 `npc_id` 和 `game_day` 获取最近若干条对话（例如 `max_memory_items=6`），按时间倒序（最新的在前）。每条记录包含 `id` 和 `text`。
2. **构建 Prompt**：将记忆文本格式化为 `Memory: {text}` 行，并与系统指令、对话历史（`context`）拼接成最终 prompt。注意避免将当前用户输入重复加入。
3. **传递记忆 ID**：将取到的记忆 ID 列表放入 `TaskAssignment` 的新字段 `memory_ids`。
4. **返回引用**：Node 收到 `TaskAssignment` 后，直接将 `task.memory_ids` 作为 `citations` 字段的内容放入 `NodeResult`。
5. **协议向后兼容**：新字段设置默认值（如 `field(default_factory=list)`），避免旧客户端/节点报错。

## 具体步骤（无代码）

### 1. 修改 `shared/memory.py`
- 在 `query_recent_turns` 的 SQL 查询中增加 `id` 字段。
- 在返回的字典列表里包含 `'id'` 键。

### 2. 修改 `shared/protocol.py`
- 在 `TaskAssignment` 类中添加：
  ```python
  memory_ids: List[str] = Field(default_factory=list)
  ```
- 在 `NodeResult` 类中添加：
  ```python
  citations: List[str] = Field(default_factory=list)
  ```
- 确保导入 `List` 和 `Field`。

### 3. 创建 `host/short_memory_injection.py`
- 定义函数：
  ```python
  def build_prompt_with_memory(db_path, npc_id, game_day, context, max_memory_items=6) -> Tuple[str, List[str]]:
  ```
- 内部调用 `query_recent_turns` 获取记忆记录。
- 将记忆文本按顺序拼接（例如 `"Memory: {text}\n"`）。
- 将对话历史（`context`）中的每条消息按 `role: content` 格式拼接。
- 组合最终 prompt（可以包含一个简单的 system 提示）。
- 返回 `(prompt, memory_ids)`。

### 4. 修改 `host/server.py` 中的 `client_handler`
- 在收到 `ClientRequest` 且找到可用节点后，调用 `build_prompt_with_memory` 获得 `prompt` 和 `memory_ids`。
- 在构造 `TaskAssignment` 时，传入 `prompt=prompt` 和 `memory_ids=memory_ids`。
- 原有的 `temp_prompt` 构造方式替换为上述调用。
- 确保传入正确的 `db_path`（可配置）。

### 5. 修改 `node/agent_node.py` 中的 `process_task`
- 在构造 `NodeResult` 时，增加 `citations=task.memory_ids`。
- 如果之前没有 `citations` 字段，请确认协议已更新。

### 6. 测试验收
- 先手动向数据库插入几条 `conversation_turns`（例如使用 `append_turn`）。
- 启动 Host、Node、Client。
- 发送一条 `ClientRequest`，观察 Host 日志中打印的 `prompt` 是否包含记忆文本。
- 查看 Node 返回的 `NodeResult` 中的 `citations` 字段是否包含那些记忆 ID。
- 连续发送两条请求，第二条应能引用第一条（如果都在同一天）。

## 验收标准
- [ ] `query_recent_turns` 返回的字典包含 `'id'` 字段。
- [ ] `TaskAssignment` 和 `NodeResult` 协议已更新，旧消息不受影响。
- [ ] `build_prompt_with_memory` 函数正确返回包含记忆的 prompt 和 ID 列表。
- [ ] Host 下发的 `TaskAssignment` 中 `memory_ids` 非空（假设 DB 中有记录）。
- [ ] Node 返回的 `NodeResult` 中 `citations` 与 `memory_ids` 一致。
- [ ] 客户端能够打印或记录 `citations`，证明引用被传递。

## 注意事项
- 短期记忆数量不宜过多（建议 ≤6 条），防止 prompt 超长。
- 如果 `context` 已经包含了最近一次对话，可考虑从记忆中排除最后一条，避免重复。但 Day4 可以先简单实现，后续再优化。
- 记忆文本可能包含换行符，需要适当清理。
- 确保 `db_path` 在 `server.py` 中可配置（例如全局变量或从环境变量读取）。

请按照以上指导实现 Day4。如果你在具体某一步需要代码示例（例如如何修改协议字段或如何调用 `query_recent_turns`），可以单独提问并要求给出示例代码。