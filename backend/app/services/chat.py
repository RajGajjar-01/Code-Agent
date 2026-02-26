"""Chat orchestration service — Groq AI with WordPress tool calling."""

import json
from typing import Any, Optional

from groq import AsyncGroq

from app.core.config import settings
from app.tools import TOOL_DEFINITIONS, execute_tool

SYSTEM_PROMPT = """You are a helpful WordPress Agent. Be conversational and concise.

Only call tools when the user explicitly asks you to perform a WordPress action such as:
- Creating, updating, listing, or deleting pages/posts
- Uploading media files
- Getting site information

IMPORTANT RULES:
- Never call delete_page or delete_post directly. Always call list_pages or list_posts FIRST to get correct IDs, then delete.
- For greetings, questions, or general chat, reply directly without calling any tools.
- When building landing pages, include: Hero, Services, Trust indicators, CTA, Testimonials, and Contact sections."""


async def process_chat(
    message: str,
    history: list[dict],
    wp_client: Optional[Any] = None,
) -> dict:
    """Process a chat message through Groq with tool calling.

    Returns dict with: response, tool_calls
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")

    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": message})
    tool_calls_executed = []

    response = await groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    while assistant_message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message.tool_calls
                ],
            }
        )

        for tool_call in assistant_message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            result = await execute_tool(func_name, func_args, wp_client)

            tool_calls_executed.append(
                {
                    "name": func_name,
                    "arguments": func_args,
                    "result": result,
                    "status": "error" if "error" in result else "success",
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        response = await groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )
        assistant_message = response.choices[0].message

    return {
        "response": assistant_message.content or "Done.",
        "tool_calls": tool_calls_executed,
    }
