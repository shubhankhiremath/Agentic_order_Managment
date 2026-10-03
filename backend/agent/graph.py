from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from backend.agent.llm import build_chat_model
from backend.agent.prompts import SYSTEM_PROMPT
from backend.config import get_settings
from backend.logging_setup import get_logger
from backend.tools.order_tools import ORDER_TOOLS, get_trace, reset_trace

logger = get_logger("agent")


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def all_tools():
    return list(ORDER_TOOLS)


def build_graph(llm=None):
    tools = all_tools()
    model = llm or build_chat_model()
    model_with_tools = model.bind_tools(tools)

    def call_model(state: AgentState) -> dict[str, Any]:
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=MemorySaver())


_graph = None


def get_graph(llm=None):
    global _graph
    if llm is not None:
        return build_graph(llm)
    if _graph is None:
        _graph = build_graph()
    return _graph


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p)
    return str(content or "")


def _safe_trace(raw: list) -> tuple[list[dict], list[str], list[dict]]:
    tools_used = []
    sources: list[str] = []
    actions = []
    for event in raw:
        tools_used.append(
            {
                "tool": event.get("tool"),
                "purpose": event.get("purpose"),
                "status": event.get("status"),
            }
        )
        for src in event.get("sources") or []:
            if src not in sources:
                sources.append(src)
        if event.get("action"):
            actions.append(
                {
                    "action": event.get("action"),
                    "status": event.get("status"),
                    "ticket_id": event.get("ticket_id"),
                }
            )
    return tools_used, sources, actions


def run_agent(message: str, session_id: str | None = None, llm=None) -> dict:
    text = (message or "").strip()
    session = session_id or str(uuid4())
    if not text:
        return {
            "response": "Please enter a question about an order or a demo policy.",
            "session_id": session,
            "tools_used": [],
            "sources": [],
            "actions": [],
        }

    reset_trace()
    logger.info("agent_start session_id=%s", session)
    try:
        graph = get_graph(llm)
        result = graph.invoke(
            {"messages": [HumanMessage(content=text)]},
            config={
                "configurable": {"thread_id": session},
                "recursion_limit": get_settings().agent_recursion_limit,
            },
        )
        messages = result.get("messages") or []
        last_ai = next(
            (m for m in reversed(messages) if isinstance(m, AIMessage) and _message_text(m)),
            None,
        )
        reply = _message_text(last_ai) if last_ai else "I could not generate a response."
        tools_used, sources, actions = _safe_trace(get_trace())
        logger.info(
            "agent_done session_id=%s tools=%s",
            session,
            [t["tool"] for t in tools_used],
        )
        return {
            "response": reply,
            "session_id": session,
            "tools_used": tools_used,
            "sources": sources,
            "actions": actions,
        }
    except Exception:
        logger.exception("agent_failed session_id=%s", session)
        return {
            "response": "The assistant is temporarily unavailable. Please try again.",
            "session_id": session,
            "tools_used": _safe_trace(get_trace())[0],
            "sources": [],
            "actions": [],
        }


def reset_agent_graph() -> None:
    global _graph
    _graph = None
