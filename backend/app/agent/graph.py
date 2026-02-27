

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS, set_wp_client
from app.core.config import settings



SYSTEM_PROMPT = """You are a powerful WordPress Agent with full control over a WordPress site.

You can manage:
• **Pages & Posts** — Create, read, update, delete pages and posts with full HTML content.
• **ACF Fields** — Read and populate Advanced Custom Fields on any page or post. Use get_acf_fields to inspect available fields, then update_acf_fields to set values.
• **Custom Themes** — Create custom WordPress themes from scratch. Generate style.css, functions.php, template files (header.php, footer.php, page templates, etc.), and activate themes.
• **Media** — Upload files to the WordPress media library.
• **Site Info** — Retrieve site name, description, and configuration.

IMPORTANT RULES:
1. Before deleting pages or posts, ALWAYS list them first to get correct IDs.
2. When creating ACF content, first use list_acf_field_groups to discover available field groups and their field names.
3. When building custom themes, always include a proper style.css header with Theme Name, and a functions.php that enqueues styles.
4. For landing pages, include: Hero section, Services/Features, Trust indicators, CTA, Testimonials, and Contact sections.
5. When populating ACF fields, match the exact field names from the field group. Use get_acf_fields on a page to see what fields are available.
6. For greetings or general questions, reply directly without calling tools.
7. Be conversational but thorough. Explain what you're doing at each step."""




def _build_llm():
    """Create the ChatGroq LLM with all tools bound."""
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0,
    )
    return llm.bind_tools(ALL_TOOLS)




async def agent_node(state: AgentState) -> dict:
    """Call the LLM with the current messages. It may return tool calls or a final answer."""
    llm = _build_llm()

    # Ensure system prompt is first
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = await llm.ainvoke(messages)

    return {"messages": [response]}


async def tool_node(state: AgentState) -> dict:
    """Execute tool calls from the last AI message."""
    messages = state["messages"]
    last_msg = messages[-1]

    tool_results = []
    executed = list(state.get("tool_calls_executed", []))

    # Build a name→tool lookup
    tool_map = {t.name: t for t in ALL_TOOLS}

    for tc in last_msg.tool_calls:
        func_name = tc["name"]
        func_args = tc["args"]

        try:
            tool_func = tool_map.get(func_name)
            if not tool_func:
                result = {"error": f"Tool '{func_name}' not found."}
            else:
                result = await tool_func.ainvoke(func_args)
        except Exception as e:
            result = {"error": str(e)}

        # Track execution
        executed.append({
            "name": func_name,
            "arguments": func_args,
            "result": result if isinstance(result, dict) else {"output": str(result)},
            "status": "error" if (isinstance(result, dict) and "error" in result) else "success",
        })

        # Create ToolMessage for the LLM
        content = json.dumps(result) if isinstance(result, dict) else str(result)
        tool_results.append(
            ToolMessage(content=content, tool_call_id=tc["id"])
        )

    return {
        "messages": tool_results,
        "tool_calls_executed": executed,
    }




def should_continue(state: AgentState) -> str:
    """Decide whether to call tools or end the conversation."""
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"
    return END




def build_agent_graph() -> StateGraph:
    """Construct the LangGraph ReAct agent."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # Set entry point
    graph.set_entry_point("agent")

    # Conditional edge: agent → tools or END
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})

    # tools → agent (loop back for the LLM to process results)
    graph.add_edge("tools", "agent")

    return graph.compile()




async def run_agent(
    message: str,
    history: list[dict],
    wp_client: Any = None,
) -> dict:
    """Run the LangGraph agent and return the response."""
    # Inject the WP client into tools
    set_wp_client(wp_client)

    # Build conversation messages
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    # Run the graph
    graph = build_agent_graph()
    result = await graph.ainvoke(
        {
            "messages": messages,
            "wp_client": wp_client,
            "tool_calls_executed": [],
        }
    )

    # Extract the final AI message
    final_messages = result["messages"]
    final_response = ""
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content:
            final_response = msg.content
            break

    return {
        "response": final_response or "Done.",
        "tool_calls": result.get("tool_calls_executed", []),
    }
