import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat turn (kept for backward compatibility)."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Inbound chat message request."""

    message: str
    conversation_id: Optional[str] = None
    user_email: Optional[str] = "anonymous"
    llm_provider: Optional[str] = None  # groq, glm5, or gemini


class ChatResponse(BaseModel):
    """What the chat endpoint returns."""

    response: str
    tool_calls: Optional[list[dict]] = []
    conversation_id: str  # UUID as string


class ScrapeRequest(BaseModel):
    url: str
    output_dir: Optional[str] = None


class MessageOut(BaseModel):
    """Single message row returned to the client."""

    id: int
    role: str
    content: str
    tool_calls: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    """Conversation summary (list view)."""

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationOut):
    """Full conversation with all messages."""

    messages: list[MessageOut] = []
