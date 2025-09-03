from typing import List
import json
import redis
from app.core.settings import settings

# Conexión singleton
_redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)  # str I/O

def _key_msgs(cid: str) -> str:
    return f"conv:{cid}:messages"

def _truncate_in_redis(key: str, max_len: int):
    # Mantén solo los últimos 'max_len' elementos
    _redis.ltrim(key, -max_len, -1)

def save_conversation(cid: str, msgs: List[dict]):
    """
    Persistimos la conversación completa como lista en Redis:
    - Representamos cada msg como JSON en una LIST.
    - Reemplazamos la lista por simplicidad (pipeline).
    """
    key = _key_msgs(cid)
    pipe = _redis.pipeline()
    pipe.delete(key)
    if msgs:
        # LPUSH invierte, por eso usamos RPUSH para mantener orden original
        pipe.rpush(key, *[json.dumps(m) for m in msgs])
        if settings.history_soft_limit:
            pipe.ltrim(key, -settings.history_soft_limit, -1)
    # TTL opcional
    if settings.redis_ttl_secs:
        pipe.expire(key, settings.redis_ttl_secs)
    pipe.execute()

def load_conversation(cid: str) -> List[dict]:
    key = _key_msgs(cid)
    raw = _redis.lrange(key, 0, -1)  # orden natural (primer msg en index 0)
    if not raw:
        return []
    return [json.loads(x) for x in raw]
