import sqlite3
from typing import List, Tuple
from shared.protocol import ClientRequest
from shared.memory import query_recent_turns

def build_prompt_with_memory(db_path, npc_id, game_day, context, max_memory_items=6) -> Tuple[str, List[str]]:
    """
    构建包含短期记忆的提示词
    param db_path: 数据库文件路径
    param npc_id: NPC ID
    param game_day: 游戏内天数
    param context: 当前对话上下文（不包含记忆）
    param max_memory_items: 最多包含多少条记忆
    return: (完整提示词, memory_ids)
    """
    recent_turns = query_recent_turns(db_path, npc_id, game_day, limit=max_memory_items)
    memory_ids = [turn['id'] for turn in recent_turns]
    memory_texts = [f"{turn['role']}: {turn['text']}" for turn in recent_turns]
    memory_section = "\n".join(memory_texts)
    memory_prompt = f"以下是与NPC的近期对话记录：\n{memory_section}\n\n当前对话上下文：\n"
    context_text = "\n".join([f"{item['role']}: {item['content']}" for item in context])
    full_prompt = memory_prompt + context_text
    return full_prompt, memory_ids