-- 创建conversation_turns表，用于存储每一轮对话（玩家输入和助手输出）
CREATE TABLE IF NOT EXISTS conversation_turns (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    npc_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    game_day INTEGER NOT NULL
);

-- 创建daily_summary表，加上唯一约束确保每个npc每天只有一条摘要
CREATE TABLE IF NOT EXISTS daily_summaries (
    id TEXT PRIMARY KEY,
    npc_id TEXT NOT NULL,
    game_day INTEGER NOT NULL,
    summary TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(npc_id, game_day)
);