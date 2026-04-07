import logging
from pathlib import Path
from typing import Annotated

from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from tools import calculate_budget, search_flights, search_hotels
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# 1. Đọc System Prompt
BASE_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = BASE_DIR / "system_prompt.txt"
with SYSTEM_PROMPT_PATH.open("r", encoding="utf-8") as f:
    system_prompt = f.read()

# 2. Khai báo State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 3. Khởi tạo LLM và Tools
tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools_list)

# 4. Agent Node
def agent_node(state: AgentState) -> AgentState:
    try:
        messages = state["messages"]

        latest_user_text = ""
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                latest_user_text = str(message.content).lower()
                break

        needs_budget_tool = any(
            keyword in latest_user_text
            for keyword in ["budget", "ngân sách", "chi phí", "triệu", "còn lại"]
        )

        prompt_content = system_prompt
        if needs_budget_tool:
            prompt_content += (
                "\n\nQUY TẮC BẮT BUỘC: Nếu người dùng có nhắc đến ngân sách hoặc cần tính tổng chi phí, "
                "bạn phải gọi tool `calculate_budget` trước khi đưa ra câu trả lời cuối cùng."
            )

        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=prompt_content)] + messages
        else:
            messages = [SystemMessage(content=prompt_content)] + messages[1:]

        response = llm_with_tools.invoke(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc.get("name", "unknown_tool")
                tool_args = tc.get("args", {})
                logger.info("Gọi tool: %s với args %s", tool_name, tool_args)
        else:
            logger.info("Trả lời trực tiếp.")

        return {"messages": [response]}
    except Exception:
        logger.exception("Agent node failed")
        return {
            "messages": [
                AIMessage(
                    content="Xin lỗi, hệ thống đang gặp lỗi tạm thời. Bạn vui lòng thử lại sau ít phút nhé."
                )
            ]
        }

# 5. Xây dựng Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)


def run_agent(user_input: str, thread_id: str = "travelbuddy-cli-session") -> str:
    """Run the TravelBuddy graph for a single user message."""
    result = graph.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    final = result["messages"][-1]
    return str(final.content)


# 6. Chat loop
if __name__ == "__main__":
    print("=" * 60)
    print("TravelBuddy - Trợ lý Du lịch Thông minh")
    print(" Gõ 'quit' để thoát")
    print("=" * 60)

    thread_id = "travelbuddy-cli-session"

    while True:
        user_input = input("\nBạn: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break

        print("\nTravelBuddy đang suy nghĩ...")
        try:
            reply = run_agent(user_input, thread_id=thread_id)
            print(f"\nTravelBuddy: {reply}")
        except Exception:
            logger.exception("Graph execution failed")
            print("\nTravelBuddy: Xin lỗi, hiện hệ thống đang gặp sự cố. Bạn vui lòng thử lại sau nhé.")
