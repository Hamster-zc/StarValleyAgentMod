## 总结

### Week2 完成内容
1. **数据库层**
   - 实现 `conversation_turns` 和 `daily_summary` 两张表
   - `append_turn` / `query_recent_turns` / `write_daily_summary` / `get_daily_summary` API
   - 已集成到 Host 流程：每次对话自动写入 user/assistant 两条记录

2. **短期记忆注入**
   - `build_prompt_with_memory` 从 DB 读取最近 N 条对话，拼接到 prompt
   - 返回 `memory_ids` 列表，通过 `TaskAssignment.memory_ids` 传递给 Node

3. **citations 返回链路**
   - `NodeResult.citations` 回传记忆 ID
   - Host 转发给 Client，形成完整的“引用可追踪”闭环

4. **LLM 集成**
   - `llama-cpp-python` 异步封装（`run_in_executor`）
   - 超时控制（`asyncio.wait_for`）
   - 并发限制（`asyncio.Semaphore`）

5. **持久化验证**
   - 重启 Host/Node 后，历史记忆依然可检索
   - 测试脚本 `test_w2d5_persistence.py` 验证通过

### 为 Week3 准备的已知信息
- 当前 `query_recent_turns` 只返回**短期记忆**（当天对话）
- `daily_summary` 表已存在但尚未集成到 prompt（Week3 可用来做长期记忆摘要）
- 短期记忆与 context 存在部分重复（暂时接受，Week3 统一优化 prompt 构造）

