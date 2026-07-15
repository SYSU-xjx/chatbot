from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from tools.basic_tool_node import BasicToolNode

class State(TypedDict):
    messages: Annotated[list, add_messages]

def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

def create_graph(llm, tools: list):
    builder = StateGraph(State)

    def chatbot(state: State):
        response = llm.invoke(state["messages"])

        return {
            "messages": [response]
        }

    tool_node = BasicToolNode(tools=tools)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", tool_node)

    builder.add_conditional_edges(
        "chatbot",
        route_tools,
        {"tools": "tools", END: END},
    )

    builder.add_edge("tools", "chatbot")

    builder.add_edge(START, "chatbot")

    return builder.compile()
