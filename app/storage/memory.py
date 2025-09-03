from typing import Dict, List
from app.core.settings import settings

_memory_store: Dict[str, List[dict]] = {}

def _truncate(msgs: List[dict]) -> List[dict]:
    if len(msgs) > settings.history_soft_limit:
        return msgs[-settings.history_soft_limit:]
    return msgs

def save_conversation(cid: str, msgs: List[dict]):
    _memory_store[cid] = _truncate(msgs)

def load_conversation(cid: str) -> List[dict]:
    return _memory_store.get(cid, [])
