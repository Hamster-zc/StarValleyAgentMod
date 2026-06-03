# Day1 计划：协议定义与项目骨架

**日期**：2026-06-03  
**目标**：完成 M1 的第一部分——定义所有消息协议（pydantic 模型） + 创建项目目录结构 + 文档。

## 1. 今日最终产出
- [ ] 项目目录结构（见下方）
- [ ] `shared/protocol.py` 包含所有消息模型（7个消息类 + Union 类型）
- [ ] `docs/protocol.md` 简要说明每个消息的字段和方向
- [ ] `README.md` 基本介绍与安装命令
- [ ] 基础测试：运行 `python shared/protocol.py` 能输出序列化成功的提示

## 2. 目录结构
stardew_npc_agent/
├── README.md
├── requirements.txt # 只包含 pydantic (后续再加)
├── shared/
│ ├── init.py
│ └── protocol.py
├── host/
│ └── init.py
├── node/
│ └── init.py
├── client/
│ └── init.py
└── docs/
├── protocol.md
└── day1_plan.md (本文件)
## 3. 需要定义的消息（参考 protocol.md 草案）
- [ ] BaseMessage（含 version, type, timestamp）
- [ ] RegisterNodeMessage
- [ ] HeartbeatMessage
- [ ] ClientRequest
- [ ] TaskAssignment
- [ ] NodeResult
- [ ] ErrorMessage
- [ ] AnyMessage Union

## 4. 实施步骤
1. 创建目录及 `__init__.py`
2. 写 `requirements.txt` 并安装 `pydantic`
3. 在 `shared/protocol.py` 中依次实现上述类（每个类写完后运行快速测试）
4. 在文件末尾写一个简单的 `if __name__ == "__main__"` 测试块
5. 编写 `docs/protocol.md`（字段表 + 示例）
6. 更新 `README.md`

## 5. 验证标准
- 执行 `python shared/protocol.py` 无报错，且输出 ✅
- 手动检查：创建任意消息，能正确转 JSON 再转回对象