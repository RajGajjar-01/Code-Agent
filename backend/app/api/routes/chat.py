import uuid
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.crypto import maybe_decrypt_secret
from app.core.database import get_db
from app.agent.tools import set_wp_cli_context, discover_wordpress_path
from app.models.user import User
from app.models.wordpress_site import WordPressSite
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    AttachmentRef,
    ConversationDetail,
    ConversationOut,
    MessageOut,
    WpCliValidateRequest,
    WpCliValidateResponse,
)
from app.services.chat import process_chat
from app.services.conversation import (
    append_messages,
    get_conversation_detail,
    get_or_create_conversation,
    list_conversations,
    soft_delete_conversation,
)
from app.services.wordpress import WordPressClient
from app.services.supabase_storage import upload_image as supabase_upload
from app.agent.errors import create_error_response
from app.agent.tools import ALL_TOOLS, reset_wp_client, set_wp_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# wp_client is injected at startup from main.py (same pattern as before)
wp_client = None

_MAX_FILES_PER_MESSAGE = 5
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/api/wp-cli/validate", response_model=WpCliValidateResponse)
async def validate_wp_cli_path(
    request: WpCliValidateRequest,
    current_user: User = Depends(get_current_active_user),
):
    wp_path = (request.wp_cli_wp_path or "").strip()
    if not wp_path:
        return WpCliValidateResponse(valid=False, detail="WP filesystem path is required")

    wp_path_obj = Path(wp_path)
    if not wp_path_obj.exists() or not wp_path_obj.is_dir():
        return WpCliValidateResponse(valid=False, detail="Path does not exist or is not a folder")

    if not (wp_path_obj / "wp-config.php").exists():
        return WpCliValidateResponse(
            valid=False,
            detail="wp-config.php not found in this folder",
        )

    return WpCliValidateResponse(valid=True, detail="Valid WordPress folder")


@router.get("/api/wp-cli/discover")
async def discover_wp_path(
    current_user: User = Depends(get_current_active_user),
):
    """Auto-discover WordPress installation path from current working directory."""
    return discover_wordpress_path()


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

    uploaded: list[AttachmentRef] = []
    for f in files:
        if not (f.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are supported")

        attachment_id = str(uuid.uuid4())
        safe_name = Path(f.filename or "upload").name

        total = 0
        chunks = []
        try:
            while True:
                chunk = await f.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_FILE_SIZE_BYTES:
                    raise HTTPException(status_code=400, detail="Image exceeds 10MB limit")
                chunks.append(chunk)
        finally:
            await f.close()

        file_data = b"".join(chunks)
        folder = f"chat/{current_user.email}"

        try:
            result = await supabase_upload(
                file_data=file_data,
                filename=safe_name,
                folder=folder,
                content_type=f.content_type,
            )
        except Exception as e:
            logger.error(f"Supabase upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")

        uploaded.append(
            AttachmentRef(
                id=attachment_id,
                filename=safe_name,
                content_type=f.content_type or "application/octet-stream",
                size_bytes=total,
                url=result["public_url"],
                local_path=result["path"],
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
    if request.user_email is not None and request.user_email != current_user.email:
        logger.warning(
            f"User {current_user.email} attempted to send message as {request.user_email}"
        )
        raise HTTPException(
            status_code=403,
            detail="Cannot send messages as another user"
        )
    
    wp_for_request = None
    created_client: WordPressClient | None = None
    site = None

    try:
        set_wp_cli_context(
            wp_path=request.wp_cli_wp_path,
            default_url=request.wp_cli_default_url,
        )

        if request.wp_site_id is not None:
            res = await db.execute(
                select(WordPressSite).where(
                    WordPressSite.id == request.wp_site_id,
                    WordPressSite.user_id == current_user.id,
                )
            )
            site = res.scalar_one_or_none()
            if not site:
                raise HTTPException(status_code=404, detail="WordPress site not found")

            app_password = maybe_decrypt_secret(site.app_password_encrypted)
            created_client = WordPressClient(site.base_url, site.username, app_password)
            wp_for_request = created_client

        # If a WordPress site is selected, do a fast connectivity/auth check.
        # If no site is selected, we still allow general chat (tools will be disabled at the agent layer).
        if wp_for_request is not None:
            try:
                resp = await wp_for_request.client.get(f"{wp_for_request.base_url}/wp-json", timeout=5.0)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Selected WordPress site is not reachable/active. Please verify the site URL and that it is running, then try again.",
                )
            if resp.status_code >= 400:
                raise HTTPException(
                    status_code=400,
                    detail="Selected WordPress site is not reachable/active or credentials are invalid. Please verify the site URL and application password, then try again.",
                )

        # 1. Resolve / create conversation using authenticated user's email
        convo = await get_or_create_conversation(
            db,
            conversation_id=request.conversation_id,
            user_email=current_user.email,
            first_message=request.message,
        )

        def _extract_pending_tool_call() -> dict[str, Any] | None:
            if not convo.messages:
                return None
            last = convo.messages[-1]
            if last.role != "assistant":
                return None
            tc = last.tool_calls or {}
            calls = tc.get("calls") if isinstance(tc, dict) else None
            if not isinstance(calls, list) or not calls:
                return None
            # Find the most recent pending confirmation tool call.
            for c in reversed(calls):
                if not isinstance(c, dict):
                    continue
                if c.get("status") != "pending_confirmation":
                    continue
                result = c.get("result")
                if isinstance(result, dict) and isinstance(result.get("pending_tool_call"), dict):
                    return result["pending_tool_call"]
            return None

        def _is_yes(msg: str) -> bool:
            return (msg or "").strip().lower() in {"y", "yes", "ok", "okay", "confirm", "proceed"}

        def _is_no(msg: str) -> bool:
            return (msg or "").strip().lower() in {"n", "no", "cancel", "stop"}

        pending = _extract_pending_tool_call()
        if pending is not None and (_is_yes(request.message) or _is_no(request.message)):
            if _is_no(request.message):
                result = {
                    "response": "Cancelled. No changes were made.",
                    "tool_calls": [],
                }
            else:
                tool_name = pending.get("tool")
                tool_args = pending.get("arguments") or {}

                tool_map = {t.name: t for t in (ALL_TOOLS if wp_for_request is not None else [])}
                tool_func = tool_map.get(tool_name)
                if not tool_func:
                    result = {
                        "response": f"⚠️ Pending action failed: tool '{tool_name}' not found.",
                        "tool_calls": [
                            {
                                "name": tool_name,
                                "arguments": tool_args,
                                "status": "error",
                                "result": {"error": f"Tool '{tool_name}' not found."},
                            }
                        ],
                    }
                else:
                    wp_token = set_wp_client(wp_for_request)
                    try:
                        out = await tool_func.ainvoke(tool_args)
                        result = {
                            "response": "Done.",
                            "tool_calls": [
                                {
                                    "name": tool_name,
                                    "arguments": tool_args,
                                    "status": "success",
                                    "result": out if isinstance(out, dict) else {"output": str(out)},
                                }
                            ],
                        }
                    except Exception as e:
                        err = create_error_response(e, context=f"Calling {tool_name}").to_dict()
                        result = {
                            "response": f"⚠️ {err.get('message') or str(e)}",
                            "tool_calls": [
                                {
                                    "name": tool_name,
                                    "arguments": tool_args,
                                    "status": "error",
                                    "result": err,
                                }
                            ],
                        }
                    finally:
                        reset_wp_client(wp_token)

            await append_messages(
                db,
                conversation_id=convo.id,
                user_content=request.message,
                user_tool_calls={"attachments": [a.model_dump() for a in (request.attachments or [])]}
                if request.attachments
                else None,
                assistant_content=result["response"],
                tool_calls=result.get("tool_calls") or [],
            )
            await db.commit()

            return ChatResponse(
                response=result["response"],
                tool_calls=result.get("tool_calls") or [],
                conversation_id=str(convo.id),
            )

        # 2. Build history from persisted messages
        user_count = 0
        assistant_count = 0
        trimmed: list[dict] = []
        for m in reversed(convo.messages):
            if m.role == "user":
                if user_count >= 5:
                    continue
                user_count += 1
            elif m.role == "assistant":
                if assistant_count >= 5:
                    continue
                assistant_count += 1
            else:
                continue

            trimmed.append({"role": m.role, "content": m.content})

            if user_count >= 5 and assistant_count >= 5:
                break

        history = list(reversed(trimmed))

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
            wp_client=wp_for_request,
            llm_provider=request.llm_provider,
            wp_site_id=request.wp_site_id,
            wp_site_name=site.name if site else None,
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

    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if created_client:
            try:
                await created_client.close()
            except Exception:
                pass


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
