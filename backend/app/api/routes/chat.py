import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    AttachmentRef,
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
from app.agent.tools import set_wp_cli_context

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# wp_client is injected at startup from main.py (same pattern as before)
wp_client = None

_UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads" / "chat"
_MAX_FILES_PER_MESSAGE = 5
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/api/chat/attachments", response_model=list[AttachmentRef])
async def upload_chat_attachments(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
):
    if not files:
        return []
    if len(files) > _MAX_FILES_PER_MESSAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Max {_MAX_FILES_PER_MESSAGE} images per message",
        )

    user_dir = _UPLOADS_DIR / current_user.email
    user_dir.mkdir(parents=True, exist_ok=True)

    uploaded: list[AttachmentRef] = []
    for f in files:
        if not (f.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are supported")

        attachment_id = str(uuid.uuid4())
        safe_name = Path(f.filename or "upload").name
        stored_name = f"{attachment_id}_{safe_name}"
        out_path = user_dir / stored_name

        total = 0
        try:
            with open(out_path, "wb") as out:
                while True:
                    chunk = await f.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > _MAX_FILE_SIZE_BYTES:
                        raise HTTPException(status_code=400, detail="Image exceeds 10MB limit")
                    out.write(chunk)
        finally:
            await f.close()

        url = f"/uploads/chat/{current_user.email}/{stored_name}"
        uploaded.append(
            AttachmentRef(
                id=attachment_id,
                filename=safe_name,
                content_type=f.content_type or "application/octet-stream",
                size_bytes=total,
                url=url,
                local_path=str(out_path.resolve()),
            )
        )

    return uploaded


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
        set_wp_cli_context(
            wp_path=request.wp_cli_wp_path,
            default_url=request.wp_cli_default_url,
        )

        # 1. Resolve / create conversation using authenticated user's email
        convo = await get_or_create_conversation(
            db,
            conversation_id=request.conversation_id,
            user_email=current_user.email,
            first_message=request.message,
        )

        # 2. Build history from persisted messages
        history = [{"role": m.role, "content": m.content} for m in convo.messages]

        attachments = request.attachments or []
        attachment_context = ""
        if attachments:
            lines = [
                "\n\nAttached images (uploaded to server; only upload to WordPress if needed):",
            ]
            for a in attachments:
                lines.append(
                    f"- {a.filename} ({a.content_type}, {a.size_bytes} bytes) local_path={a.local_path} url={a.url}"
                )
            attachment_context = "\n".join(lines)

        message_for_agent = request.message + attachment_context

        # 3. Call the agent with optional llm_provider
        result = await process_chat(
            message=message_for_agent,
            history=history,
            wp_client=wp_client,
            llm_provider=request.llm_provider,
        )

        # 4. Persist both turns
        await append_messages(
            db,
            conversation_id=convo.id,
            user_content=request.message,
            user_tool_calls={"attachments": [a.model_dump() for a in attachments]} if attachments else None,
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
