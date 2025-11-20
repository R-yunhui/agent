"""
LangGraph 基础示例3：LLM Agent
演示如何创建一个带LLM调用的智能代理
"""
import os
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import operator

# 加载环境变量
load_dotenv()


# 1. 定义状态
class AgentState(TypedDict):
    """Agent状态"""
    messages: Annotated[Sequence[BaseMessage], operator.add]  # 消息历史
    next_action: str  # 下一步动作


# 2. 创建LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_CHAT_MODEL"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)


# 3. 定义节点函数
def call_model(state: AgentState) -> AgentState:
    """调用LLM节点 - 使用流式输出"""
    messages = state['messages']
    
    # 添加系统提示
    system_message = SystemMessage(content="""你是一个有用的AI助手。
请简洁地回答用户问题。如果用户说再见或结束对话，在回复中包含'再见'。""")
    
    full_messages = [system_message] + list(messages)
    
    # 在此处直接进行流式打印，实现真正的逐字输出效果
    print("\n🤖 AI: ", end="", flush=True)
    response_content = ""
    for chunk in llm.stream(full_messages):
        print(chunk.content, end="", flush=True)
        response_content += chunk.content
    print()  # 换行
    
    response = AIMessage(content=response_content)
    
    # 检查是否应该结束对话
    if any(word in response.content.lower() for word in ['再见', 'goodbye', '拜拜']):
        state['next_action'] = 'end'
    else:
        state['next_action'] = 'continue'
    
    return {
        "messages": [response],
        "next_action": state['next_action']
    }


def should_continue(state: AgentState) -> str:
    """决定是否继续对话"""
    return state['next_action']


# 4. 创建Agent图
def create_agent_graph():
    """创建LLM Agent图"""
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("agent", call_model)
    
    # 设置入口
    workflow.set_entry_point("agent")
    
    # 添加条件边（这里简化处理，实际应用中可以更复杂）
    workflow.add_edge("agent", END)
    
    return workflow.compile()


# 5. 运行示例
if __name__ == "__main__":
    app = create_agent_graph()
    
    print("=" * 60)
    print("LangGraph LLM Agent 示例")
    print("提示：输入 'quit' 退出")
    print("=" * 60)
    
    # 初始化消息历史
    message_history = []
    
    while True:
        # 获取用户输入
        user_input = input("\n你: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("程序退出")
            break
        
        if not user_input:
            continue
        
        # 添加用户消息
        message_history.append(HumanMessage(content=user_input))
        
        # 运行图（流式输出在 call_model 内部已完成）
        result = app.invoke({
            "messages": message_history,
            "next_action": "continue"
        })
        
        # 更新消息历史
        message_history.extend(result['messages'])
        
        # 如果AI说再见，询问是否继续
        if result.get('next_action') == 'end':
            cont = input("\n是否继续对话？(y/n): ").strip().lower()
            if cont != 'y':
                print("对话结束")
                break
