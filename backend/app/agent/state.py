from datetime import datetime
from typing import Annotated, Any, Optional

from langgraph.graph.message import add_messages
from langgraph.managed.is_last_step import RemainingSteps
from typing_extensions import TypedDict


class ExecutionMetadata(TypedDict):
    start_time: datetime
    total_tool_calls: int
    failed_tool_calls: int
    circuit_breaker_trips: int


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    remaining_steps: RemainingSteps
    tool_calls_executed: list[dict]
    wp_client: Optional[Any]
    tools: list[Any]
    execution_metadata: ExecutionMetadata
    config: dict
    pending_tool_call: Optional[dict]
