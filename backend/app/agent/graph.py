import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph

from app.agent.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from app.agent.config import get_agent_config
from app.agent.errors import create_error_response
from app.agent.llm_factory import LLMProviderFactory
from app.agent.models import ExecutionSummary, ToolCallRecord
from app.agent.retry import RetryConfig, retry_with_backoff
from app.agent.state import AgentState
from app.agent.tools import READ_TOOLS, WRITE_TOOLS, reset_wp_client, set_wp_client

from app.agent.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_circuit_breaker: CircuitBreaker | None = None


def get_circuit_breaker() -> CircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        config = get_agent_config()
        _circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout=config.circuit_breaker_timeout,
            name="wordpress_api",
        )
    return _circuit_breaker


def _build_llm(tools: list[Any]):
    config = get_agent_config()
    llm = LLMProviderFactory.create(config)
    return llm.bind_tools(tools)


async def agent_node(state: AgentState) -> dict:
    llm = _build_llm(state.get("tools", []))

    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    if not state.get("wp_client"):
        messages = messages + [
            SystemMessage(
                content=(
                    "WordPress site is not connected for this chat session. "
                    "Answer normally, but do not attempt to perform WordPress actions."
                )
            )
        ]

    remaining = state.get("remaining_steps", 25)
    if remaining <= 3:
        warning_msg = SystemMessage(
            content=f"⚠️ Only {remaining} steps remaining. Please wrap up your response."
        )
        messages = messages + [warning_msg]

    response = await llm.ainvoke(messages)

    return {"messages": [response]}


async def tool_node(state: AgentState) -> dict:
    messages = state["messages"]
    last_msg = messages[-1]

    tool_results = []
    executed = list(state.get("tool_calls_executed", []))
    execution_metadata = state.get("execution_metadata", {
        "start_time": datetime.now(),
        "total_tool_calls": 0,
        "failed_tool_calls": 0,
        "circuit_breaker_trips": 0,
    })

    tools = state.get("tools", [])
    tool_map = {t.name: t for t in tools}
    circuit_breaker = get_circuit_breaker()
    config = get_agent_config()
    retry_config = RetryConfig(max_attempts=config.retry_attempts)

    # Tools that mutate WordPress state. These must be explicitly confirmed by the user
    # before execution.
    write_tools: set[str] = {
        "create_page",
        "update_page",
        "delete_page",
        "create_post",
        "update_post",
        "delete_post",
        "upload_media",
        "delete_media",
        "bulk_update_pages",
        "bulk_delete_pages",
        "bulk_update_posts",
        "bulk_delete_posts",
        "bulk_upload_media",
        "create_menu",
        "delete_menu",
        "create_menu_item",
        "bulk_create_menus",
        "bulk_create_menu_items",
        "create_menu_tree",
        "assign_menu_locations",
        "wp_cli_menu_create",
        "wp_cli_menu_location_assign",
        "wp_cli_menu_item_add_post",
        "wp_cli_menu_item_add_custom",
        "create_theme_file",
        "activate_theme",
        "wp_cli_activate_theme",
        "update_acf_fields",
        "create_category",
        "create_tag",
    }

    def _compact_tool_result(value: Any, tool_name: str) -> Any:
        # Keep ToolMessage payloads small to avoid re-sending huge JSON back to the LLM.
        if isinstance(value, dict):
            if "error" in value:
                return {"error": value.get("error")}
            if "message" in value and "needs_confirmation" in value:
                # Keep confirmation payload minimal but functional.
                out = {
                    "needs_confirmation": value.get("needs_confirmation"),
                    "message": value.get("message"),
                }
                if "pending_tool_call" in value:
                    out["pending_tool_call"] = value.get("pending_tool_call")
                if "next_call" in value:
                    out["next_call"] = value.get("next_call")
                if "status" in value:
                    out["status"] = value.get("status")
                return out

            # Common list keys: keep only a small sample and light fields.
            for key in ("pages", "posts", "media", "themes", "menus", "items", "users"):
                if key in value and isinstance(value[key], list):
                    items = value[key]
                    sample = items[:10]

                    def light(obj: Any) -> Any:
                        if not isinstance(obj, dict):
                            return obj
                        keep_keys = ("id", "title", "name", "slug", "link", "status", "url")
                        return {k: obj.get(k) for k in keep_keys if k in obj}

                    return {
                        key: [light(x) for x in sample],
                        "returned": len(sample),
                        "total": len(items),
                        "truncated": len(items) > len(sample),
                    }

        # Strings can be huge (e.g., HTML). Cap them.
        if isinstance(value, str) and len(value) > 4000:
            return value[:4000] + "\n...[truncated]"
        return value

    for tc in last_msg.tool_calls:
        func_name = tc["name"]
        func_args = tc["args"]
        start_time = time.time()

        if func_name in write_tools:
            # Do not execute. Return a structured confirmation request.
            result = {
                "needs_confirmation": True,
                "pending_tool_call": {
                    "tool": func_name,
                    "arguments": func_args,
                },
                "message": (
                    "This action will modify WordPress content. "
                    "Reply with 'yes' to proceed or 'no' to cancel."
                ),
            }
            status = "pending_confirmation"
            content = json.dumps(result)
            tool_results.append(ToolMessage(content=content, tool_call_id=tc["id"]))
            duration_ms = (time.time() - start_time) * 1000
            execution_metadata["total_tool_calls"] += 1
            executed.append(
                {
                    "name": func_name,
                    "arguments": func_args,
                    "result": result,
                    "status": status,
                    "duration_ms": duration_ms,
                }
            )
            continue

        try:
            tool_func = tool_map.get(func_name)
            if not tool_func:
                result = {"error": f"Tool '{func_name}' not found."}
                status = "error"
            else:
                async def execute_tool():
                    return await tool_func.ainvoke(func_args)

                try:
                    result = await circuit_breaker.call(
                        retry_with_backoff,
                        execute_tool,
                        config=retry_config,
                    )
                    status = "success"
                    logger.info(f"Tool {func_name} executed successfully")
                except CircuitBreakerOpenError as e:
                    logger.error(f"Circuit breaker open for {func_name}: {e}")
                    execution_metadata["circuit_breaker_trips"] += 1
                    error_response = create_error_response(
                        e, context=f"Calling {func_name}"
                    )
                    result = error_response.to_dict()
                    status = "circuit_open"

        except Exception as e:
            logger.error(f"Tool {func_name} failed: {e}", exc_info=True)
            execution_metadata["failed_tool_calls"] += 1
            error_response = create_error_response(e, context=f"Calling {func_name}")
            result = error_response.to_dict()
            status = "error"

        compact = _compact_tool_result(result, func_name)
        content = json.dumps(compact) if isinstance(compact, dict) else str(compact)
        tool_results.append(ToolMessage(content=content, tool_call_id=tc["id"]))

        duration_ms = (time.time() - start_time) * 1000
        execution_metadata["total_tool_calls"] += 1

        executed.append({
            "name": func_name,
            "arguments": func_args,
            "result": result if isinstance(result, dict) else {"output": str(result)},
            "status": status,
            "duration_ms": duration_ms,
        })

    return {
        "messages": tool_results,
        "tool_calls_executed": executed,
        "execution_metadata": execution_metadata,
    }


def should_continue(state: AgentState) -> str:
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"
    return END


def build_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})

    graph.add_edge("tools", "agent")

    return graph.compile()


async def run_agent(
    message: str,
    history: list[dict],
    wp_client: Any = None,
    thread_id: str | None = None,
    llm_provider: str | None = None,
) -> dict:
    wp_token = set_wp_client(wp_client)

    # Bind both read and write tools when WordPress is connected so the LLM knows
    # which capabilities exist. Actual write execution is still gated by tool_node,
    # which returns a confirmation request instead of executing.
    tools: list[Any] = []
    if wp_client is not None:
        tools = list(READ_TOOLS) + list(WRITE_TOOLS)

    if not thread_id:
        thread_id = str(uuid.uuid4())

    if llm_provider:
        config = get_agent_config()
        config.llm_provider = llm_provider
        logger.info(f"Using LLM provider: {llm_provider}")

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Keep a small rolling history window to reduce prompt tokens.
    history_window = 10
    for msg in history[-history_window:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    start_time = datetime.now()
    execution_metadata = {
        "start_time": start_time,
        "total_tool_calls": 0,
        "failed_tool_calls": 0,
        "circuit_breaker_trips": 0,
    }

    config = get_agent_config()

    graph = build_agent_graph()
    try:
        try:
            result = await graph.ainvoke(
                {
                    "messages": messages,
                    "wp_client": wp_client,
                    "tools": tools,
                    "tool_calls_executed": [],
                    "execution_metadata": execution_metadata,
                    "config": {"thread_id": thread_id},
                },
                config={"recursion_limit": config.recursion_limit},
            )
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            return {
                "response": f"⚠️ Agent execution failed: {str(e)}",
                "tool_calls": [],
                "error": str(e),
            }
    finally:
        reset_wp_client(wp_token)

    final_messages = result["messages"]
    final_response = ""
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content:
            final_response = msg.content
            break

    end_time = datetime.now()
    execution_time_ms = (end_time - start_time).total_seconds() * 1000
    metadata = result.get("execution_metadata", execution_metadata)

    tools_used = list(set(
        call["name"] for call in result.get("tool_calls_executed", [])
    ))

    summary = ExecutionSummary(
        thread_id=thread_id,
        total_steps=len(result.get("tool_calls_executed", [])),
        total_tool_calls=metadata.get("total_tool_calls", 0),
        successful_tool_calls=metadata.get("total_tool_calls", 0) - metadata.get("failed_tool_calls", 0),
        failed_tool_calls=metadata.get("failed_tool_calls", 0),
        circuit_breaker_trips=metadata.get("circuit_breaker_trips", 0),
        execution_time_ms=execution_time_ms,
        termination_reason="completed",
        tools_used=tools_used,
    )

    logger.info(f"Agent execution completed: {summary.to_dict()}")

    return {
        "response": final_response or "Done.",
        "tool_calls": result.get("tool_calls_executed", []),
        "execution_summary": summary.to_dict(),
    }
