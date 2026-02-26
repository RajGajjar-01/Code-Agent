from typing import Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None
    history: Optional[list[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[list[dict]] = []
    chat_id: Optional[str] = None


class ScrapeRequest(BaseModel):
    url: str
    output_dir: Optional[str] = None
