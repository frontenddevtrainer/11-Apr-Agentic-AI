"""HR Agent built with LangGraph, with memory and Langfuse tracing."""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated

# ── Langfuse (optional) ─────────────────────────────────────────────────────
LANGFUSE_ENABLED = bool(os.environ.get("LANGFUSE_SECRET_KEY"))
if LANGFUSE_ENABLED:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
from tools import ALL_TOOLS

# ── LLM setup ────────────────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

SYSTEM_PROMPT = """You are an HR Assistant for the company. You help employees with:
1. HR policy questions (leave, WFH, expenses, performance reviews) - use the search_hr_policies tool.
2. Employee information lookups (salary, department, manager, leave balance) - use the query_employee_database tool.

Guidelines:
- Always use the appropriate tool to find accurate information before answering.
- Be professional, friendly, and concise.
- If the query is about a specific employee, use the database tool with a SQL SELECT query.
- If the query is about policies or rules, use the policy search tool.
- For follow-up questions, use context from the conversation history.
- Never reveal raw SQL queries to the user. Present information in a clean, readable format.
- If you don't have enough information, ask the user to clarify.
"""


# ── State ────────────────────────────────────────────────────────────────────
def _add_messages(existing: list, new: list) -> list:
    return existing + new


class AgentState(TypedDict):
    messages: Annotated[list, _add_messages]


# ── Nodes ────────────────────────────────────────────────────────────────────
def agent_node(state: AgentState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    tool_map = {t.name: t for t in ALL_TOOLS}
    results = []
    for tc in last_message.tool_calls:
        tool_fn = tool_map.get(tc["name"])
        if tool_fn:
            result = tool_fn.invoke(tc["args"])
            results.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )
    return {"messages": results}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# ── Build graph ──────────────────────────────────────────────────────────────
def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


hr_agent = build_agent()


# ── Run helper ───────────────────────────────────────────────────────────────
def chat(user_message: str, session_id: str = "default") -> str:
    callbacks = []
    if LANGFUSE_ENABLED:
        callbacks.append(LangfuseCallbackHandler())
    config = {
        "configurable": {"thread_id": session_id},
        "callbacks": callbacks,
    }
    result = hr_agent.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config,
    )
    ai_message = result["messages"][-1]
    return ai_message.content
