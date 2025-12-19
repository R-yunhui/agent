 # langgraph 动态路由/ReAct 模式示例
import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

# 加载环境配置
load_dotenv()

# 1. 定义工具
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers together."""
    return a * b

@tool
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b

tools = [multiply, add]

# 2. 定义状态
class AgentState(TypedDict):
    # messages 列表，使用 operator.add 进行追加更新
    messages: Annotated[Sequence[BaseMessage], operator.add]

# 3. 定义节点

# Agent 节点：负责思考和决策
def agent_node(state: AgentState):
    messages = state['messages']
    
    # 添加系统提示词，引导模型分步思考
    system_prompt = SystemMessage(content="""你是一个智能助手。
    请一步一步思考。
    如果你需要执行多步计算，请不要同时调用依赖于前一步结果的工具。
    等待获得前一步的结果后，再进行下一步调用。
    """)
    
    # 将系统提示词放在消息列表最前面
    # 注意：这里只是临时构建用于模型输入的消息列表，并不修改 state 中的 messages
    input_messages = [system_prompt] + list(messages)
    
    print(f"🤖 Agent 正在思考... (当前历史消息数: {len(messages)})")
    
    # 创建绑定了工具的模型
    model = ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0
    ).bind_tools(tools)
    
    response = model.invoke(input_messages)
    return {"messages": [response]}

# Tools 节点：负责执行工具
# LangGraph 提供了预构建的 ToolNode，也可以自己写
tool_node = ToolNode(tools)

# 4. 定义条件边逻辑
def should_continue(state: AgentState) -> str:
    messages = state['messages']
    last_message = messages[-1]
    
    # 如果最后一条消息包含工具调用，则路由到 "tools" 节点
    if last_message.tool_calls:
        print(f"👉 决定调用工具: {last_message.tool_calls[0]['name']}")
        return "tools"
    
    # 否则结束
    print("✅ 决定结束对话")
    return "end"

# 5. 构建图
def create_react_graph():
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # 设置入口点
    workflow.set_entry_point("agent")
    
    # 添加条件边
    # 从 agent 节点出发，根据 should_continue 的返回值决定去向
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # 添加普通边
    # 工具执行完后，总是回到 agent 继续思考
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

def main():
    print("=" * 60)
    print("🔄 LangGraph ReAct 动态路由示例")
    print("=" * 60)
    
    app = create_react_graph()
    
    # 测试问题：需要多步计算的问题
    # (3 + 5) * 4 = 32
    query = "计算 (3 加 5) 乘以 4 等于多少？"
    print(f"❓ 用户问题: {query}\n")
    
    inputs = {"messages": [HumanMessage(content=query)]}
    
    # 运行并打印中间步骤
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"\n📍 节点 '{key}' 执行完毕")
            # 打印该节点产生的最新消息
            if "messages" in value:
                messages = value["messages"]
                # 确保是列表
                if not isinstance(messages, list):
                    messages = [messages]
                
                for msg in messages:
                    if isinstance(msg, AIMessage):
                        if msg.tool_calls:
                            print(f"   输出: 呼叫工具 {msg.tool_calls}")
                        else:
                            print(f"   输出: {msg.content}")
                    elif isinstance(msg, ToolMessage):
                        print(f"   工具结果 ({msg.name}): {msg.content}")
                    elif isinstance(msg, SystemMessage):
                        print(f"   系统提示: {msg.content[:20]}...")

if __name__ == "__main__":
    main()
