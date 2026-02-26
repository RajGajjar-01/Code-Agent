"""Chat orchestration service — LangGraph agent with WordPress tools."""

from typing import Any, Optional

from app.agent.graph import run_agent


async def process_chat(
    message: str,
    history: list[dict],
    wp_client: Optional[Any] = None,
) -> dict:
    """Process a chat message through the LangGraph WordPress agent.

    Returns dict with: response, tool_calls
    """
    return await run_agent(
        message=message,
        history=history,
        wp_client=wp_client,
    )
