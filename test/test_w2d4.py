#!/usr/bin/env python
"""
Week2 Day4 测试：验证短期记忆注入与 citations 返回
使用方法：
1. 先启动 Host 和 Node（在终端1和终端2）
2. 运行本脚本（终端3）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import websockets
import json
import uuid
from shared.memory import init_db, append_turn, query_recent_turns
from shared.protocol import ClientRequest, NodeResult

DB_PATH = "storage/npc_memory.db"
HOST_URI = "ws://localhost:8765/client"

# 测试用的 NPC 信息
NPC_ID = "Abigail"
PLAYER_ID = "test_player"
GAME_DAY = 5

async def prepare_memory():
    """向数据库插入几条测试记忆，确保有短期记忆可供引用"""
    init_db(DB_PATH)  # 确保表存在
    # 清空之前的数据（可选，避免重复）
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversation_turns WHERE npc_id = ? AND game_day = ?", (NPC_ID, GAME_DAY))
    conn.commit()
    conn.close()
    
    # 插入三条对话作为记忆
    turns = [
        {"request_id": "test1", "npc_id": NPC_ID, "player_id": PLAYER_ID, "role": "user", "text": "我喜欢冒险", "game_day": GAME_DAY},
        {"request_id": "test2", "npc_id": NPC_ID, "player_id": PLAYER_ID, "role": "assistant", "text": "那你去过矿洞吗？", "game_day": GAME_DAY},
        {"request_id": "test3", "npc_id": NPC_ID, "player_id": PLAYER_ID, "role": "user", "text": "还没有，但我很想去", "game_day": GAME_DAY},
    ]
    for turn in turns:
        append_turn(DB_PATH, turn)
    print("✅ 测试记忆已写入数据库")

async def send_test_request():
    """发送一个客户端请求，并检查返回结果中的 citations"""
    async with websockets.connect(HOST_URI) as ws:
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        # 构造当前的对话上下文（只包含当前用户输入）
        context = [{"role": "user", "content": "我想去矿洞探险，有什么建议吗？"}]
        req = ClientRequest(
            request_id=request_id,
            npc_id=NPC_ID,
            player_id=PLAYER_ID,
            game_day=GAME_DAY,
            context=context,
            env=None,
            prefer_local=False
        )
        await ws.send(req.model_dump_json())
        print(f"📤 发送请求 {request_id}")
        
        # 等待回复
        resp_raw = await asyncio.wait_for(ws.recv(), timeout=30.0)
        resp_data = json.loads(resp_raw)
        print(f"📥 收到回复: {resp_data}")
        
        # 检查是否包含 citations
        if "citations" in resp_data and resp_data["citations"]:
            print(f"✅ citations 非空: {resp_data['citations']}")
            # 可选：验证 citations 中的 ID 是否确实存在于数据库中
            recent = query_recent_turns(DB_PATH, NPC_ID, GAME_DAY, limit=10)
            memory_ids = [t['id'] for t in recent]
            if all(cid in memory_ids for cid in resp_data['citations']):
                print("✅ citations 中的 ID 均为有效记忆")
            else:
                print("❌ citations 包含无效 ID")
        else:
            print("❌ 未找到 citations 字段或为空")
            return False
        return True

async def main():
    print("=== Week2 Day4 功能测试 ===")
    await prepare_memory()
    success = await send_test_request()
    if success:
        print("🎉 测试通过：短期记忆注入和 citations 返回工作正常")
    else:
        print("⚠️ 测试失败，请检查 Host/Node 日志")

if __name__ == "__main__":
    asyncio.run(main())