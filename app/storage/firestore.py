from typing import List
from app.core.deps import db
from app.core.settings import settings

def _truncate(msgs: List[dict]) -> List[dict]:
    if len(msgs) > settings.history_soft_limit:
        return msgs[-settings.history_soft_limit:]
    return msgs

def save_conversation(cid: str, msgs: List[dict]):
    if db is None:
        raise RuntimeError("Firestore not initialized")
    db.collection("conversations").document(cid).set({"messages": _truncate(msgs)})

def load_conversation(cid: str) -> List[dict]:
    if db is None:
        raise RuntimeError("Firestore not initialized")
    doc = db.collection("conversations").document(cid).get()
    return (doc.to_dict() or {}).get("messages", []) if getattr(doc, "exists", False) else []
