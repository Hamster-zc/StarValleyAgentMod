#!/usr/bin/env python
"""
Week2 Day5 持久化测试
验证：
1. 对话能正确写入数据库
2. 重启 Host/Node 后，历史记忆依然存在并被引用

使用方法：
1. 确保 Host 和 Node 已启动（阶段一前）
2. 运行本脚本，按提示操作
3. 脚本会先发送一批请求并写入数据，然后提示你重启 Host/Node
4. 重启完成后按 Enter，脚本继续验证重启后的数据完整性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import websockets
import json
import uuid
import sqlite3
from shared.memory import init_db, append_turn, query_recent_turns
from shared.protocol import ClientRequest

DB_PATH = "storage/npc_memory.db"
HOST_URI = "ws://localhost:8765/client"

NPC_ID = "Abigail"
PLAYER_ID = "test_player"
GAME_DAY = 5

async def clear_and_seed_db():
    """清空并插入种子数据（用于初始化）"""
    init_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversation_turns WHERE npc_id = ? AND game_day = ?", (NPC_ID, GAME_DAY))
    conn.commit()
    conn.close()
    
    # 插入三条种子记忆（与 Day4 类似）
    turns = [
        {"request_id": "seed1", "npc_id": NPC_ID, "player_id": PLAYER_ID, "role": "user", "text": "我喜欢冒险", "game_day": GAME_DAY},
        {"request_id": "seed2", "npc_id": NPC_ID, "player_id": PLAYER_ID, "role": "assistant", "text": "那你去过矿洞吗？", "game_day": GAME_DAY},
        {"request_id": "seed3", "npc_id": NPC_ID, "player_id": PLAYER_ID, "role": "user", "text": "还没有，但我很想去", "game_day": GAME_DAY},
    ]
    for turn in turns:
        append_turn(DB_PATH, turn)
    print("✅ 种子记忆已写入数据库")

async def send_request_and_check_citations(ws, request_content, expected_citation_ids=None):
    """发送一个请求，检查返回的 citations 是否包含预期 ID"""
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    context = [{"role": "user", "content": request_content}]
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
    print(f"📤 发送请求 {request_id}: {request_content}")
    
    resp_raw = await asyncio.wait_for(ws.recv(), timeout=30.0)
    resp_data = json.loads(resp_raw)
    print(f"📥 收到回复 (部分): {resp_data.get('result', '')[:100]}...")
    
    citations = resp_data.get("citations", [])
    print(f"citations: {citations}")
    
    if expected_citation_ids:
        # 验证所有预期 ID 是否都在返回的 citations 中
        missing = [cid for cid in expected_citation_ids if cid not in citations]
        if missing:
            print(f"❌ 缺失预期 citation ID: {missing}")
            return False
        else:
            print(f"✅ 所有预期 ID ({len(expected_citation_ids)}) 均被引用")
    else:
        # 没有预期 ID 时，只检查 citations 非空（如果数据库有数据）
        if citations:
            print("✅ citations 非空")
        else:
            print("⚠️ citations 为空（可能数据库无历史记录）")
    return True

async def phase1():
    """阶段一：发送两个请求，写入数据，然后提示用户重启"""
    print("=== Phase 1: 写入数据 ===")
    await clear_and_seed_db()
    
    async with websockets.connect(HOST_URI) as ws:
        # 第一个请求：希望引用种子记忆
        success = await send_request_and_check_citations(ws, "我想去矿洞探险，有什么建议吗？")
        if not success:
            print("⚠️ 第一个请求的 citations 不符合预期")
        # 第二个请求：应该引用之前真实对话（包括刚才的）
        await asyncio.sleep(1)  # 确保时间戳区分
        success2 = await send_request_and_check_citations(ws, "听说矿洞里有宝藏，是真的吗？")
        if not success2:
            print("⚠️ 第二个请求的 citations 不符合预期")
    
    # 查询数据库，显示当前所有记录
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, text FROM conversation_turns WHERE npc_id=? AND game_day=? ORDER BY timestamp", (NPC_ID, GAME_DAY))
    rows = cursor.fetchall()
    conn.close()
    print("\n当前数据库中的对话记录：")
    for role, text in rows:
        print(f"  {role}: {text[:50]}...")
    print("\n📌 请现在重启 Host 和 Node（Ctrl+C 停止，然后重新启动）。")
    input("重启完成后，按 Enter 继续 Phase 2...")

async def phase2():
    """阶段二：重启后验证持久化"""
    print("=== Phase 2: 验证持久化 ===")
    # 从数据库获取所有已存在的 ID（用于检查引用）
    recent = query_recent_turns(DB_PATH, NPC_ID, GAME_DAY, limit=20)
    all_ids = [t['id'] for t in recent]
    print(f"数据库中现有记录数: {len(all_ids)}")
    
    async with websockets.connect(HOST_URI) as ws:
        # 发送一个新请求，验证 citations 包含之前的部分 ID
        success = await send_request_and_check_citations(
            ws,
            "你觉得我该带什么装备去矿洞？",
            expected_citation_ids=all_ids[:3]  # 期望至少引用前几条
        )
        if success:
            print("🎉 持久化验证通过：重启后记忆依然存在并被引用")
        else:
            print("❌ 持久化验证失败：重启后 citations 未包含预期 ID")

async def main():
    print("=== Week2 Day5 持久化测试 ===")
    await phase1()
    await phase2()

if __name__ == "__main__":
    asyncio.run(main())