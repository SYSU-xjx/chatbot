from graph.chatbot_graph import create_graph
from llm.factory import create_llm
from memory import MemoryContext, MemoryManager
from mcp import get_mcp_langchain_tools_as_list
from tools import create_search_tools


# ── Initialisation ──────────────────────────────────────────────────

memory_manager = MemoryManager(context_window=30)  # last 30 messages (15 turns)

# Default thread: auto-create on first run
memory_manager.ensure_thread("default", "Main Chat")

active_thread = "default"
active_user = "default_user"

# Combine built-in search tools with MCP tools
_search_tools = create_search_tools()
_mcp_tools = get_mcp_langchain_tools_as_list()
all_tools = _search_tools + _mcp_tools

llm = create_llm()
llm_with_tools = llm.bind_tools(all_tools)
graph = create_graph(llm_with_tools, all_tools)


# ── Helper ─────────────────────────────────────────────────────────-


def extract_assistant_output(message) -> str | None:
    message_type = getattr(message, "type", None)
    if message_type == "ai" and getattr(message, "content", ""):
        return message.content
    return None


# ── CLI commands ────────────────────────────────────────────────────


_COMMAND_HELP = """
Available commands:
  /new [name]   Create a new thread
  /list         List all threads
  /switch <id>  Switch to a thread by id
  /current      Show current thread info
  /rename <n>   Rename current thread
  /rm <id>      Delete a thread
  /remember k=v Save a long-term memory fact
  /forget <k>   Forget a memory fact (NYI)
  /help         Show this help
  /quit         Exit
"""


def handle_cli_command(user_input: str) -> bool:
    global active_thread, active_user

    parts = user_input.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    # ── /quit ──
    if cmd in ("/quit", "/exit", "/q"):
        print("Goodbye!")
        exit(0)

    # ── /help ──
    if cmd == "/help":
        print(_COMMAND_HELP)
        return True

    # ── /new [name] ──
    if cmd in ("/new", "/create"):
        tid = memory_manager.create_thread(arg or "")
        active_thread = tid
        _ctx = MemoryContext(user_id=active_user, thread_id=active_thread)
        t = memory_manager.get_thread(tid)
        print(f"Switched to new thread [{tid}] \"{t['name']}\"")
        return True

    # ── /list ──
    if cmd == "/list":
        threads = memory_manager.list_threads()
        if not threads:
            print("No threads found.")
            return True
        for t in threads:
            marker = " <--" if t["thread_id"] == active_thread else ""
            msg_count = memory_manager.message_count(t["thread_id"])
            print(
                f"  [{t['thread_id']:12s}] {t['name']:20s} "
                f"{msg_count:3d} msgs  {t['updated_at']}{marker}"
            )
        return True

    # ── /switch <id> ──
    if cmd == "/switch":
        if not arg:
            print("Usage: /switch <thread_id>")
            return True
        t = memory_manager.get_thread(arg)
        if not t:
            print(f"Thread '{arg}' not found.")
            return True
        active_thread = arg
        print(f"Switched to thread [{arg}] \"{t['name']}\"")
        return True

    # ── /current ──
    if cmd == "/current":
        t = memory_manager.get_thread(active_thread)
        cnt = memory_manager.message_count(active_thread)
        print(
            f"Thread: [{active_thread}] \"{t['name'] if t else '?'}\"  "
            f"Messages: {cnt}"
        )
        return True

    # ── /rename <name> ──
    if cmd == "/rename":
        if not arg:
            print("Usage: /rename <new name>")
            return True
        memory_manager.rename_thread(active_thread, arg)
        print(f"Thread renamed to '{arg}'.")
        return True

    # ── /rm <id> ──
    if cmd in ("/rm", "/delete"):
        target = arg or active_thread
        if target == active_thread and len(memory_manager.list_threads()) <= 1:
            print("Cannot delete the only remaining thread.")
            return True
        memory_manager.delete_thread(target)
        print(f"Thread '{target}' deleted.")
        if target == active_thread:
            threads = memory_manager.list_threads()
            if threads:
                active_thread = threads[0]["thread_id"]
                print(f"Auto-switched to [{active_thread}].")
        return True

    # ── /remember key=value ──
    if cmd == "/remember":
        if "=" not in arg:
            print("Usage: /remember key=value")
            return True
        key, value = arg.split("=", 1)
        ctx = MemoryContext(user_id=active_user, thread_id=active_thread)
        memory_manager.save_long_term_memory(ctx, key.strip(), value.strip())
        print("Memory saved.")
        return True

    # ── /forget <key> ──
    if cmd == "/forget":
        if not arg:
            print("Usage: /forget <key>")
            return True
        ctx = MemoryContext(user_id=active_user, thread_id=active_thread)
        memory_manager.long_term_store.forget_memory(ctx.user_id, arg.strip())
        print(f"Memory '{arg}' forgotten.")
        return True

    # ── Unknown command ──
    if cmd.startswith("/"):
        print(f"Unknown command: {cmd}. Type /help for available commands.")
        return True

    return False  # not a command, treat as normal input


# ── Main loop ───────────────────────────────────────────────────────


def stream_graph_updates(user_input: str):
    ctx = MemoryContext(user_id=active_user, thread_id=active_thread)
    final_assistant_output: str | None = None
    for event in graph.stream(
            {
                "messages": memory_manager.build_conversation_input(
                    ctx,
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
            ctx,
            user_input,
            final_assistant_output,
        )


print("=== Chatbot with MCP tools ===")
print("Type /help for available commands.\n")

while True:
    try:
        user_input = input("User: ")
        if handle_cli_command(user_input):
            continue
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
