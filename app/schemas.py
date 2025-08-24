from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str        # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    history: List[Message]          # return convo so you can debug in tests/clients
