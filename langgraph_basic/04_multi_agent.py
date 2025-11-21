"""
LangGraph 基础示例4：多Agent协作
演示如何创建多个Agent协同工作
"""
import os
from typing import TypedDict, Annotated, Literal
from langgraph.typing import StateT
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import operator

# 加载环境变量
load_dotenv()


# 1. 定义状态
class MultiAgentState(StateT):
    """多Agent状态"""
    task: str  # 用户任务
    research_result: str  # 研究结果
    writing_result: str  # 写作结果
    review_result: str  # 审核结果
    final_output: str  # 最终输出
    current_agent: str  # 当前处理的agent


# 2. 创建不同角色的LLM
def create_llm():
    """创建LLM实例"""
    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )


# 3. 定义各个Agent节点
def research_agent(state: MultiAgentState) -> MultiAgentState:
    """研究Agent：负责收集信息"""
    print("\n📚 研究Agent工作中...")
    
    llm = create_llm()
    messages = [
        SystemMessage(content="你是一个研究专家，负责收集和总结信息。请简洁但全面地研究给定主题。"),
        HumanMessage(content=f"请研究以下主题并提供关键信息：{state['task']}")
    ]
    
    response = llm.invoke(messages)
    state['research_result'] = response.content
    state['current_agent'] = 'researcher'
    
    print(f"✓ 研究完成: {len(state['research_result'])} 字符")
    return state


def writing_agent(state: MultiAgentState) -> MultiAgentState:
    """写作Agent：基于研究结果进行创作"""
    print("\n✍️  写作Agent工作中...")
    
    llm = create_llm()
    messages = [
        SystemMessage(content="你是一个专业的内容创作者。基于研究结果，创作优质内容。"),
        HumanMessage(content=f"""任务：{state['task']}

研究结果：
{state['research_result']}

请基于以上研究结果，创作一篇简短但有价值的文章。""")
    ]
    
    response = llm.invoke(messages)
    state['writing_result'] = response.content
    state['current_agent'] = 'writer'
    
    print(f"✓ 写作完成: {len(state['writing_result'])} 字符")
    return state


def review_agent(state: MultiAgentState) -> MultiAgentState:
    """审核Agent：审核和改进内容"""
    print("\n🔍 审核Agent工作中...")
    
    llm = create_llm()
    messages = [
        SystemMessage(content="你是一个内容审核专家。检查内容质量并提供反馈或直接改进。"),
        HumanMessage(content=f"""原始任务：{state['task']}

当前内容：
{state['writing_result']}

请审核以上内容，并提供最终优化版本。""")
    ]
    
    response = llm.invoke(messages)
    state['review_result'] = response.content
    state['final_output'] = response.content
    state['current_agent'] = 'reviewer'
    
    print(f"✓ 审核完成: {len(state['review_result'])} 字符")
    return state


# 4. 创建多Agent图
def create_multi_agent_graph():
    """创建多Agent协作图"""
    workflow = StateGraph(MultiAgentState)
    
    # 添加所有Agent节点
    workflow.add_node("researcher", research_agent)
    workflow.add_node("writer", writing_agent)
    workflow.add_node("reviewer", review_agent)
    
    # 设置入口点
    workflow.set_entry_point("researcher")
    
    # 定义工作流：研究 -> 写作 -> 审核 -> 结束
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "reviewer")
    workflow.add_edge("reviewer", END)
    
    return workflow.compile()


# 5. 运行示例
if __name__ == "__main__":
    app = create_multi_agent_graph()
    
    print("=" * 70)
    print("LangGraph 多Agent协作示例")
    print("=" * 70)
    
    # 定义任务
    task = "人工智能在医疗领域的应用"
    
    print(f"\n📝 任务: {task}")
    print("-" * 70)
    
    # 运行多Agent工作流
    result = app.invoke({
        "task": task,
        "research_result": "",
        "writing_result": "",
        "review_result": "",
        "final_output": "",
        "current_agent": ""
    })
    
    # 显示结果
    print("\n" + "=" * 70)
    print("工作流完成！")
    print("=" * 70)
    
    print(f"\n📚 研究阶段输出:")
    print("-" * 70)
    print(result['research_result'][:200] + "..." if len(result['research_result']) > 200 else result['research_result'])
    
    print(f"\n✍️  写作阶段输出:")
    print("-" * 70)
    print(result['writing_result'][:200] + "..." if len(result['writing_result']) > 200 else result['writing_result'])
    
    print(f"\n📄 最终输出:")
    print("=" * 70)
    print(result['final_output'])
    print("=" * 70)
