## Week2 Day1 任务：实现短期记忆（Working Memory）与 SQLite 持久化

### 目标
- 设计 SQLite 数据库表结构（至少 `conversation_turns` 和 `daily_summary`）。
- 实现 Python 函数：初始化数据库、写入对话轮次、按 NPC/游戏天查询最近轮次、写入/读取每日摘要。
- 写一个简单的测试脚本（`test_memory.py`）验证这些功能。

### 1. 数据库表设计（你需编写 `storage/sqlite_schema.sql`）

**表1：`conversation_turns`**  
用于存储每一轮对话（玩家输入和助手输出）。建议字段：
- `id`：主键，字符串（可用 UUID）
- `request_id`：对应 client 请求的唯一 ID
- `npc_id`：NPC 名称（如 "Abigail"）
- `player_id`：玩家标识
- `role`：`'user'` 或 `'assistant'`
- `text`：消息内容
- `timestamp`：Unix 时间戳（整数）
- `game_day`：游戏内天数（整数）

**表2：`daily_summary`**  
存储每天结束时生成的摘要（用于长期记忆）。字段：
- `id`：主键（例如 `f"{npc_id}_day{day}"`）
- `npc_id`
- `day`
- `summary`：文本
- `created_at`：Unix 时间戳

**表3（可选）：`npc_state`**  
预留字段，可先不实现。

### 2. 实现模块 `shared/memory.py`

需要实现的函数（遵循之前规划中的签名）：

- `init_db(db_path: str) -> None`  
  读取 `storage/sqlite_schema.sql` 文件，执行建表语句。

- `append_turn(db_path: str, turn: dict) -> str`  
  `turn` 应包含 `request_id`, `npc_id`, `player_id`, `role`, `text`, `game_day`。  
  自动生成 `id`（UUID）和 `timestamp`（当前时间）。  
  插入到 `conversation_turns`，返回 `id`。

- `query_recent_turns(db_path: str, npc_id: str, game_day: int, limit: int = 20) -> List[dict]`  
  返回最近 `limit` 条对话，按时间戳**降序**（最新的在前）。每条记录为字典，至少包含 `id`, `role`, `text`, `timestamp`。

- `write_daily_summary(db_path: str, npc_id: str, day: int, summary: str) -> None`  
  插入或替换 `daily_summary` 中对应 `(npc_id, day)` 的记录。

- `get_daily_summary(db_path: str, npc_id: str, day: int) -> Optional[str]`  
  返回摘要文本，若无则返回 `None`。

### 3. 编写测试脚本

在项目根目录创建 `test_memory.py`（或直接使用 `if __name__ == "__main__"` 放在 `memory.py` 末尾），执行以下操作：

1. 调用 `init_db('test.db')`。
2. 插入两条 `user` 和一条 `assistant` 的对话轮次（模拟对话）。
3. 调用 `query_recent_turns` 查询并打印结果。
4. 调用 `write_daily_summary` 写入一条摘要。
5. 调用 `get_daily_summary` 读取并打印。
6. 确认没有异常，输出符合预期。

### 4. 验收标准

- 运行测试脚本后，无报错，打印出插入的 turn id、查询到的对话列表、摘要内容。
- 检查 `test.db` 文件是否生成，可以用 `sqlite3` 命令行工具查看表结构及数据（`sqlite3 test.db ".schema"` 和 `"SELECT * FROM conversation_turns;"`）。
- 重启 Python 进程后再次运行测试脚本，之前写入的数据应仍然存在（持久化验证）。

### 5. 提示与注意事项

- 使用 `sqlite3` 模块（Python 内置）。
- 时间戳可使用 `int(time.time())`。
- UUID 可使用 `uuid.uuid4().hex`。
- 查询时注意排序方向：`ORDER BY timestamp DESC`。
- 插入或替换摘要：可以使用 `INSERT OR REPLACE` 语句，前提是建立了唯一约束 `UNIQUE(npc_id, day)`（建议在 schema 中添加）。
