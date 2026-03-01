"""Data models for agent execution tracking."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class ToolCallRecord:
    """Record of a tool call execution."""

    tool_name: str
    arguments: dict
    result: Any
    status: str  # "success", "error", "duplicate", "circuit_open"
    timestamp: datetime
    duration_ms: float
    error_message: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result if isinstance(self.result, dict) else str(self.result),
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


@dataclass
class ExecutionSummary:
    """Summary of agent execution."""

    thread_id: str
    total_steps: int
    total_tool_calls: int
    successful_tool_calls: int
    failed_tool_calls: int
    circuit_breaker_trips: int
    execution_time_ms: float
    termination_reason: str  # "completed", "recursion_limit", "error"
    tools_used: list[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "thread_id": self.thread_id,
            "total_steps": self.total_steps,
            "total_tool_calls": self.total_tool_calls,
            "successful_tool_calls": self.successful_tool_calls,
            "failed_tool_calls": self.failed_tool_calls,
            "circuit_breaker_trips": self.circuit_breaker_trips,
            "execution_time_ms": self.execution_time_ms,
            "termination_reason": self.termination_reason,
            "tools_used": self.tools_used,
        }
