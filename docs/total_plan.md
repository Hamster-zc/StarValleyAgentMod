# 项目整体计划（4周压缩版）

## 当前进度状态
- ✅ **M1（Week0）**：host/node/client 三进程骨架（注册/心跳/任务分配/超时降级） — 已完成  
- ✅ **M2 Day1**：SQLite schema + memory API（`init_db`, `append_turn`, `query_recent_turns`, `write_daily_summary`, `get_daily_summary`） — 已完成  
- ✅ **M2 Day2–3**：`llama-cpp-python` 集成 → 异步 wrapper（`run_in_executor`）、超时控制（`asyncio.wait_for`）、并发限制（`Semaphore`） — 已完成  
- 🔄 **M2 Day4**：短期记忆注入 + citations 返回 — 进行中（文档已提供）  
- ⬜ 剩余任务按以下计划执行。

---

## 总目标（4周后交付）
一个可本地运行的 **星露谷 NPC Agent 演示**，具备：
- 玩家与 NPC 多轮对话（WebSocket）
- 短期记忆（SQLite）+ 长期记忆（FAISS 检索）
- 本地 LLM 推理（llama-cpp-python）
- 调度与降级（host 选节点、超时处理）
- 可观测性（trace 日志 + 简单查看器）
- 一键启动脚本、README、录屏

---

## 里程碑（M1–M5）与时间分配

| 里程碑 | 内容 | 原计划周 | 实际起止 | 状态 |
|--------|------|----------|----------|------|
| M1 | 三进程骨架 + 心跳/超时/降级 | Week0 | 已完成 | ✅ |
| M2 | 本地 LLM + 短期记忆 + citations | Week1 | Day1–3 ✅；Day4 进行中 | 🔄 |
| M3 | 长期记忆 + FAISS 检索（RAG v1） + 20问评测 | Week2 | 待开始 | ⬜ |
| M4 | 调度器增强（能力感知、负载均衡、降级） + trace 查看器 | Week3 | 待开始 | ⬜ |
| M5 | 打磨交付（一键脚本、README、录屏、简历） | Week4 | 待开始 | ⬜ |

---

## 每周详细任务

### Week1（M2 剩余 + 收尾）—— 已完成大部分，剩余 Day4–Day5

| 天数 | 任务 | 验收标准 |
|------|------|----------|
| Day4（当前） | 短期记忆注入 + citations 返回 | prompt 包含记忆文本；`NodeResult.citations` 非空 |
| Day5 | 持久化验证 + 文档 | 重启 host 后记忆不丢失；`docs/week2_notes.md` 记录模型路径/并发设置 |

> 注：原计划中的 Day2–3 已提前完成，Day4 按最新文档实现。

---

### Week2（M3：长期记忆 + FAISS 检索）

| 天数 | 任务 | 关键库/设计 |
|------|------|------------|
| Day1 | 选 embedding 模型，实现文本向量化 pipeline | `sentence-transformers`（轻量如 `all-MiniLM-L6-v2`），`numpy` |
| Day2 | 集成 FAISS，实现 build/load/query | `faiss-cpu`（或 `faiss-gpu`），索引类型 `IndexFlatIP` |
| Day3 | 在 host 或 node 中实现 `retrieve()` 调用 | 决定检索时机（host 侧预检索）；返回 top-k 文档 + 分数 |
| Day4 | 改造 prompt，注入长期记忆片段 + citations | 将检索到的文本拼入 prompt；长期记忆 ID 放入 `citations`（与短期 ID 区分或合并） |
| Day5 | 20 个问题人工评测 | 编写评测脚本，计算召回率或人工打分 |
| Day6 | 调整与 bugfix（增量更新、缓存） | 实现新对话自动插入向量库（可简单全量重建） |
| Day7 | 整合 + 文档 | 更新 `docs/week3_notes.md`；录屏展示检索+生成 |

---

### Week3（M4：调度器增强 + trace 查看器）

| 天数 | 任务 | 关键设计 |
|------|------|----------|
| Day1 | 节点能力结构设计，注册时上报 | `capabilities` 增加 `gpu_mem`, `concurrency`, `avg_latency` 等 |
| Day2 | 实现调度策略（最短队列/最低延迟） | 在 `choose_node()` 中根据负载和能力选择 |
| Day3 | 降级策略（无节点/超时时） | host 返回 canned reply 或减少 token 数 |
| Day4 | trace logger（结构化日志） | 每条请求记录 routing, retrieval, latency, status，存 JSON 文件或 SQLite |
| Day5 | 简单 trace viewer | CLI 或 Flask 网页，按 `request_id` 查询展示 |
| Day6 | 压测与调优 | 并发 20 请求，观察超时率，调整超时/并发参数 |
| Day7 | 整合 + 文档 | 更新 `docs/week4_notes.md`；演示调度与 trace |

---

### Week4（M5：打磨与交付）

| 天数 | 任务 | 输出 |
|------|------|------|
| Day1 | 一键启动脚本 `scripts/start_demo.sh` | 依次启动 host, node, client |
| Day2 | 配置参数化（`.env` 或 `config.yaml`） | 支持修改模型路径、端口、并发数等 |
| Day3 | 整理评测报告（从 Week2 的 20 问结果） | PDF 或 Markdown 表格 |
| Day4 | 录制 demo 视频（3–5 分钟） | 展示对话、记忆引用、检索、调度、trace 查看 |
| Day5 | 完善 README（架构图、运行步骤、依赖） | 包含所有验收点的说明 |
| Day6 | 缓冲：处理遗留 bug、补充文档 | 确保 `git push` 后仓库干净 |
| Day7 | 复盘 + 简历项目描述撰写 | 列出关键技术点、个人贡献 |

---

## 每日建议工时（可灵活调整）
- **周一至周五**：2–4 小时（课程繁忙时可压缩到 1–2 小时，只做核心代码）
- **周末**：4–6 小时（集中整合、测试、文档、录屏）

---

## 关键技术栈清单
| 类别 | 库/工具 |
|------|----------|
| WebSocket | `websockets` |
| 数据校验 | `pydantic` |
| 数据库 | `sqlite3` |
| 向量检索 | `faiss-cpu`, `numpy`, `sentence-transformers` |
| LLM 推理 | `llama-cpp-python` |
| 异步控制 | `asyncio` |
| 日志 | `logging` |
| 配置 | `python-dotenv` (可选) |
| 测试 | `pytest` 或简单 `assert` 脚本 |

---

## 下一步行动
- 立即完成 **Week2 Day4**（短期记忆注入 + citations）。  
- Day4 验收后，进入 **Week2 Day5**（持久化验证与文档）。  
- 然后按 Week2 计划开始长期记忆（RAG）部分。

如果你需要某一天更详细的设计文档（例如 FAISS 集成步骤、调度策略伪代码），请单独提出，我会给出无代码的指导文档。