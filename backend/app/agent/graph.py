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
from app.agent.tools import ALL_TOOLS, set_wp_client

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


def _build_llm():
    config = get_agent_config()
    llm = LLMProviderFactory.create(config)
    return llm.bind_tools(ALL_TOOLS)


async def agent_node(state: AgentState) -> dict:
    llm = _build_llm()

    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

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

    tool_map = {t.name: t for t in ALL_TOOLS}
    circuit_breaker = get_circuit_breaker()
    config = get_agent_config()
    retry_config = RetryConfig(max_attempts=config.retry_attempts)

    for tc in last_msg.tool_calls:
        func_name = tc["name"]
        func_args = tc["args"]
        start_time = time.time()

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

        content = json.dumps(result) if isinstance(result, dict) else str(result)
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
    set_wp_client(wp_client)

    if not thread_id:
        thread_id = str(uuid.uuid4())

    if llm_provider:
        config = get_agent_config()
        config.llm_provider = llm_provider
        logger.info(f"Using LLM provider: {llm_provider}")

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in history:
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
        result = await graph.ainvoke(
            {
                "messages": messages,
                "wp_client": wp_client,
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
