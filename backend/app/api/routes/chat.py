
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationOut,
    MessageOut,
)
from app.services.chat import process_chat
from app.services.conversation import (
    append_messages,
    get_conversation_detail,
    get_or_create_conversation,
    list_conversations,
    soft_delete_conversation,
)

router = APIRouter(tags=["chat"])

# wp_client is injected at startup from main.py (same pattern as before)
wp_client = None



@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process a chat message and persist both results to the DB."""
    try:
        # 1. Resolve / create conversation
        convo = await get_or_create_conversation(
            db,
            conversation_id=request.conversation_id,
            user_email=request.user_email or "anonymous",
            first_message=request.message,
        )

        # 2. Build history from persisted messages
        history = [
            {"role": m.role, "content": m.content}
            for m in convo.messages
        ]

        # 3. Call the agent
        result = await process_chat(
            message=request.message,
            history=history,
            wp_client=wp_client,
        )

        # 4. Persist both turns
        await append_messages(
            db,
            conversation_id=convo.id,
            user_content=request.message,
            assistant_content=result["response"],
            tool_calls=result.get("tool_calls") or [],
        )

        await db.commit()

        return ChatResponse(
            response=result["response"],
            tool_calls=result.get("tool_calls") or [],
            conversation_id=str(convo.id),
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/api/conversations", response_model=list[ConversationOut])
async def get_conversations(
    user_email: str = "anonymous",
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all active (non-deleted) conversations for a user, newest first."""
    limit = min(limit, 200)
    rows = await list_conversations(
        db, user_email=user_email, skip=skip, limit=limit
    )
    return [ConversationOut(**row) for row in rows]



@router.get(
    "/api/conversations/{conversation_id}",
    response_model=ConversationDetail,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return a conversation with its full message history."""
    convo = await get_conversation_detail(
        db, conversation_id=str(conversation_id)
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=convo.id,
        title=convo.title,
        created_at=convo.created_at,
        updated_at=convo.updated_at,
        message_count=len(convo.messages),
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                tool_calls=m.tool_calls,
                created_at=m.created_at,
            )
            for m in convo.messages
        ],
    )



@router.delete("/api/conversations/{conversation_id}", status_code=200)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a conversation."""
    deleted = await soft_delete_conversation(
        db, conversation_id=str(conversation_id)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.commit()

    return {"detail": "Conversation deleted", "id": str(conversation_id)}
