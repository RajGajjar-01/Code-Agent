"""Agent state definition for LangGraph."""

from typing import Annotated, Any, Optional

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State that flows through the LangGraph agent."""

    # ── Core conversation ─────────────────────────────────────
    messages: Annotated[list, add_messages]

    # ── WordPress context ─────────────────────────────────────
    # The WordPress client instance (injected at runtime)
    wp_client: Optional[Any]

    # ── Tracking ──────────────────────────────────────────────
    tool_calls_executed: list[dict]
