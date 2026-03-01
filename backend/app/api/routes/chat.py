import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
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

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# wp_client is injected at startup from main.py (same pattern as before)
wp_client = None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a chat message and persist both results to the DB."""
    # Verify the user_email matches the authenticated user
    if request.user_email and request.user_email != current_user.email:
        logger.warning(
            f"User {current_user.email} attempted to send message as {request.user_email}"
        )
        raise HTTPException(
            status_code=403,
            detail="Cannot send messages as another user"
        )
    
    try:
        # 1. Resolve / create conversation using authenticated user's email
        convo = await get_or_create_conversation(
            db,
            conversation_id=request.conversation_id,
            user_email=current_user.email,
            first_message=request.message,
        )

        # 2. Build history from persisted messages
        history = [{"role": m.role, "content": m.content} for m in convo.messages]

        # 3. Call the agent with optional llm_provider
        result = await process_chat(
            message=request.message,
            history=history,
            wp_client=wp_client,
            llm_provider=request.llm_provider,
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
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all active (non-deleted) conversations for the authenticated user, newest first."""
    limit = min(limit, 200)
    rows = await list_conversations(db, user_email=current_user.email, skip=skip, limit=limit)
    return [ConversationOut(**row) for row in rows]


@router.get(
    "/api/conversations/{conversation_id}",
    response_model=ConversationDetail,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a conversation with its full message history."""
    convo = await get_conversation_detail(db, conversation_id=str(conversation_id))
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Verify the conversation belongs to the authenticated user
    if convo.user_email != current_user.email:
        logger.warning(
            f"User {current_user.email} attempted to access conversation owned by {convo.user_email}"
        )
        raise HTTPException(status_code=403, detail="Access denied")

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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a conversation."""
    # First check if conversation exists and belongs to user
    convo = await get_conversation_detail(db, conversation_id=str(conversation_id))
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if convo.user_email != current_user.email:
        logger.warning(
            f"User {current_user.email} attempted to delete conversation owned by {convo.user_email}"
        )
        raise HTTPException(status_code=403, detail="Access denied")
    
    deleted = await soft_delete_conversation(db, conversation_id=str(conversation_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.commit()

    return {"detail": "Conversation deleted", "id": str(conversation_id)}
