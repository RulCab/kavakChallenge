from pydantic import BaseModel, Field, constr
from typing import Optional, List, Literal

class ChatMessage(BaseModel):
    role: Literal["user", "bot"]
    message: constr(strip_whitespace=True, min_length=1)

class MessageRequest(BaseModel):
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID. If null/omitted, starts a new conversation."
    )
    message: constr(strip_whitespace=True, min_length=1, max_length=2000) = Field(
        ..., description="User's message."
    )

class ChatResponse(BaseModel):
    conversation_id: str
    message: List[ChatMessage]

class ErrorResponse(BaseModel):
    detail: str
