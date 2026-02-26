"""Chat endpoint route."""

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import process_chat

router = APIRouter(tags=["chat"])


# wp_client will be set during app lifespan
wp_client = None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through Groq AI with WordPress tool calling."""
    try:
        history = [{"role": m.role, "content": m.content} for m in (request.history or [])]

        result = await process_chat(
            message=request.message,
            history=history,
            wp_client=wp_client,
        )

        return ChatResponse(
            response=result["response"],
            tool_calls=result["tool_calls"],
            chat_id=request.chat_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
