import os
from pydantic import BaseModel, Field
from typing import Optional

class Settings(BaseModel):
    gemini_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    firebase_creds_path: Optional[str] = Field(None, alias="FIREBASE_CREDENTIALS")
    model_name: str = Field("gemini-2.0-flash", alias="GEMINI_MODEL")
    max_reply_secs: int = Field(30, alias="MAX_REPLY_SECS")
    history_soft_limit: int = Field(200, alias="HISTORY_SOFT_LIMIT")
    redis_url: Optional[str] = Field(None, alias="REDIS_URL")
    redis_ttl_secs: Optional[int] = Field(None, alias="REDIS_TTL_SECS")

def load_settings() -> Settings:
    data = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "FIREBASE_CREDENTIALS": os.getenv("FIREBASE_CREDENTIALS"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "MAX_REPLY_SECS": int(os.getenv("MAX_REPLY_SECS", "30")),
        "HISTORY_SOFT_LIMIT": int(os.getenv("HISTORY_SOFT_LIMIT", "200")),
        "REDIS_URL": os.getenv("REDIS_URL"),
        "REDIS_TTL_SECS": int(os.getenv("REDIS_TTL_SECS", "0") or 0),
    }
    return Settings(**data)

settings = load_settings()
