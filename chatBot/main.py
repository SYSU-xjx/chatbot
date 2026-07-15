from graph.chatbot_graph import create_graph
from llm.factory import create_llm
from memory import MemoryContext, MemoryManager
from tools import create_search_tools

llm = create_llm()
tools = create_search_tools()
llm_with_tools = llm.bind_tools(tools)
memory_manager = MemoryManager()
memory_context = MemoryContext(user_id="default_user", thread_id="default_thread")

graph = create_graph(llm_with_tools, tools)


def extract_assistant_output(message) -> str | None:
    message_type = getattr(message, "type", None)
    if message_type == "ai" and getattr(message, "content", ""):
        return message.content
    return None


def handle_memory_command(user_input: str) -> bool:
    if not user_input.startswith("/remember "):
        return False

    payload = user_input.removeprefix("/remember ").strip()
    if "=" not in payload:
        print("Assistant: Use /remember key=value")
        return True

    memory_key, memory_value = payload.split("=", 1)
    memory_manager.save_long_term_memory(
        memory_context,
        memory_key.strip(),
        memory_value.strip(),
    )
    print("Assistant: Memory saved.")
    return True


def stream_graph_updates(user_input: str):
    final_assistant_output: str | None = None
    for event in graph.stream(
            {
                "messages": memory_manager.build_conversation_input(
                    memory_context,
                    user_input,
                )
            },
    ):
        for value in event.values():
            assistant_output = extract_assistant_output(value["messages"][-1])
            if assistant_output is None:
                continue

            final_assistant_output = assistant_output
            print("Assistant:", assistant_output)

    if final_assistant_output:
        memory_manager.save_turn(
            memory_context,
            user_input,
            final_assistant_output,
        )


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        if handle_memory_command(user_input):
            continue
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
