from pydantic import BaseModel
from typing import List

class ChatCreate(BaseModel):
    message: str  # user's prompt

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: float

class ChatResponse(BaseModel):
    chat_id: str
    messages: List[ChatMessage]