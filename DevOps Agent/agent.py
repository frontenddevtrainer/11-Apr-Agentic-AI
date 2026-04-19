"""
DevOps Agent - LangGraph-based agent that analyzes logs, queries runbooks,
and generates HTML incident reports.
"""

import json
import operator
from typing import Annotated, TypedDict
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from tools import ALL_TOOLS
from report_generator import generate_html_report

# --- State ---

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    errors_found: list[dict]
    report_path: str


# --- System Prompt ---

SYSTEM_PROMPT = """You are a DevOps Agent specializing in log analysis and incident resolution.

Your workflow:
1. Query logs from Loki/Grafana to find errors and critical issues
2. For each error found, search the runbook knowledge base for resolution steps
3. Optionally use Docker CLI or SSH to gather more diagnostic info
4. Compile a comprehensive analysis

When analyzing logs:
- Focus on ERROR and CRITICAL level logs
- Group similar errors together
- Identify the root cause when possible
- Look for patterns (e.g., cascading failures, repeated errors)

When you have completed your analysis, respond with a JSON block in this exact format:
```json
{
    "summary": "Brief overall summary of the incident",
    "errors": [
        {
            "service": "service-name",
            "level": "ERROR or CRITICAL",
            "message": "Brief error description",
            "resolution": "Resolution steps from runbooks"
        }
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ]
}
```

Always provide actionable resolutions based on the runbooks. Be thorough but concise."""


# --- Agent Logic ---

def create_agent():
    """Create the DevOps LangGraph agent."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    tool_node = ToolNode(ALL_TOOLS)

    def agent_node(state: AgentState) -> dict:
        """Main agent reasoning node."""
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """Decide whether to call tools or finish."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "process_results"

    def process_results(state: AgentState) -> dict:
        """Extract the analysis from the agent's final response and generate report."""
        last_message = state["messages"][-1]
        content = last_message.content if hasattr(last_message, "content") else str(last_message)

        # Try to extract JSON from the response
        analysis = None
        if "```json" in content:
            try:
                json_str = content.split("```json")[1].split("```")[0].strip()
                analysis = json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                pass

        if not analysis:
            # If no structured JSON, create a basic analysis from the content
            analysis = {
                "summary": content[:500],
                "errors": state.get("errors_found", []),
                "recommendations": ["Review the full agent output for details."],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            analysis["timestamp"] = datetime.now(timezone.utc).isoformat()

        report_path = generate_html_report(analysis)
        return {
            "messages": [AIMessage(content=f"Analysis complete. HTML report generated: {report_path}")],
            "report_path": report_path,
        }

    # Build the graph
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("process_results", process_results)

    graph.set_entry_point("agent")

    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "process_results": "process_results"})
    graph.add_edge("tools", "agent")
    graph.add_edge("process_results", END)

    return graph.compile()


def run_agent(task: str = "Analyze recent logs for errors and provide resolutions.") -> dict:
    """Run the DevOps agent with a given task."""
    agent = create_agent()
    initial_state = {
        "messages": [HumanMessage(content=task)],
        "errors_found": [],
        "report_path": "",
    }

    print(f"Starting DevOps Agent with task: {task}")
    print("=" * 60)

    final_state = agent.invoke(initial_state)

    print("=" * 60)
    print("Agent execution complete.")

    if final_state.get("report_path"):
        print(f"Report: {final_state['report_path']}")

    return final_state
