import uuid
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Conversation, Message


async def get_or_create_conversation(
    db: AsyncSession,
    *,
    conversation_id: Optional[str],
    user_email: str,
    first_message: str = "",
) -> Conversation:
    """Return an existing Conversation or create a new one."""
    if conversation_id:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == uuid.UUID(conversation_id),
                Conversation.is_deleted.is_(False),
            )
        )
        convo = result.scalar_one_or_none()
        if convo:
            return convo

    # Auto-generate a readable title from the first message
    title = (first_message[:80] + "…") if len(first_message) > 80 else first_message
    title = title.strip() or "New Conversation"

    convo = Conversation(user_email=user_email, title=title)
    convo.messages = []  # initialise to empty list so callers don't need to query
    db.add(convo)
    await db.flush()  # populate id without committing the outer transaction
    return convo


async def append_messages(
    db: AsyncSession,
    *,
    conversation_id: uuid.UUID,
    user_content: str,
    assistant_content: str,
    tool_calls: Optional[list[dict]] = None,
) -> tuple[Message, Message]:
    """Persist one user turn + one assistant turn atomically."""
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_content,
    )
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
        tool_calls={"calls": tool_calls} if tool_calls else None,
    )
    db.add_all([user_msg, assistant_msg])

    # Bump the conversation's updated_at so list ordering stays correct
    await db.execute(
        update(Conversation).where(Conversation.id == conversation_id).values(updated_at=func.now())
    )
    await db.flush()
    return user_msg, assistant_msg


async def list_conversations(
    db: AsyncSession,
    *,
    user_email: str,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Return a paginated list of active conversations for a user."""
    msg_count_subq = (
        select(
            Message.conversation_id,
            func.count(Message.id).label("message_count"),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Conversation,
            func.coalesce(msg_count_subq.c.message_count, 0).label("message_count"),
        )
        .outerjoin(
            msg_count_subq,
            Conversation.id == msg_count_subq.c.conversation_id,
        )
        .where(
            Conversation.user_email == user_email,
            Conversation.is_deleted.is_(False),
        )
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )

    rows = result.all()
    return [
        {
            "id": row.Conversation.id,
            "title": row.Conversation.title,
            "created_at": row.Conversation.created_at,
            "updated_at": row.Conversation.updated_at,
            "message_count": row.message_count,
        }
        for row in rows
    ]


async def get_conversation_detail(
    db: AsyncSession,
    *,
    conversation_id: str,
) -> Optional[Conversation]:
    """Return a Conversation with its messages eagerly loaded, or None."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def soft_delete_conversation(
    db: AsyncSession,
    *,
    conversation_id: str,
) -> bool:
    """Soft-delete a conversation by setting is_deleted=True."""
    result = await db.execute(
        update(Conversation)
        .where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.is_deleted.is_(False),
        )
        .values(is_deleted=True)
        .returning(Conversation.id)
    )
    updated = result.scalar_one_or_none()
    await db.flush()
    return updated is not None
