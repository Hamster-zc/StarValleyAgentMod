import sqlite3
from typing import List, Tuple, Optional
import uuid
import time

def init_db(db_path:str) -> None:
    """读取 storage/sqlite_schema.sql 文件，执行建表语句。"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open('storage/sqlite_schema.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()

def append_turn(db_path: str, turn: dict) -> str:
    """ 
    添加一轮对话记录，返回该轮对话的唯一ID
    param db_path: 数据库文件路径
    param turn: {request_id, npc_id, player_id, role, text, timestamp, game_day} 
    """
    turn_id = str(uuid.uuid4())
    timestamp = int(time.time())
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation_turns (id, request_id, npc_id, player_id, role, text, timestamp, game_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        turn_id,
        turn['request_id'],
        turn['npc_id'],
        turn['player_id'],
        turn['role'],
        turn['text'],
        timestamp,
        turn['game_day']
    ))
    conn.commit()
    conn.close()
    return turn_id

def query_recent_turns(db_path: str, npc_id: str, game_day: int, limit: int = 20) -> List[dict]:
    """查询最近的对话记录，按时间倒序排列"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, request_id, npc_id, player_id, role, text, game_day
        FROM conversation_turns
        WHERE npc_id = ? AND game_day = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (npc_id, game_day, limit))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'request_id': row[1],
            'npc_id': row[2],
            'player_id': row[3],
            'role': row[4],
            'text': row[5],
            'game_day': row[6]
        }
        for row in rows
    ]

def write_daily_summary(db_path: str, npc_id: str, game_day: int, summary: str) -> None:
    """写入每日总结"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO daily_summaries (id, npc_id, game_day, summary, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        npc_id,
        game_day,
        summary,
        int(time.time())
    ))
    conn.commit()
    conn.close()

def get_daily_summary(db_path: str, npc_id: str, game_day: int) -> Optional[str]:
    """获取每日总结"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT summary
        FROM daily_summaries
        WHERE npc_id = ? AND game_day = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (npc_id, game_day))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    init_db('test.db')
    turn = {
        "request_id": "req_001",
        "npc_id": "Abigail",
        "player_id": "player1",
        "role": "user",
        "text": "今天有什么新闻？",   # 必须要有
        "game_day": 5
    }
    tid = append_turn('test.db', turn)
    print(f"Inserted turn id: {tid}")
    turns = query_recent_turns('test.db', "Abigail", 5, limit=10)
    print("Recent turns:", turns)
    write_daily_summary('test.db', "Abigail", 5, "Abigail talked about the weather.")
    summary = get_daily_summary('test.db', "Abigail", 5)
    print("Daily summary:", summary)
