"""
LangGraph 基础示例5：循环和迭代
演示如何在图中使用循环进行迭代优化
"""
import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 加载环境变量
load_dotenv()


# 1. 定义状态
class IterativeState(TypedDict):
    """迭代优化状态"""
    original_text: str  # 原始文本
    current_text: str  # 当前文本
    iteration: int  # 当前迭代次数
    max_iterations: int  # 最大迭代次数
    quality_score: float  # 质量评分 (0-10)
    improvements: list  # 改进历史


# 2. 创建LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)


# 3. 定义节点函数
def improve_text(state: IterativeState) -> IterativeState:
    """改进文本节点"""
    print(f"\n🔄 迭代 {state['iteration']}/{state['max_iterations']}")
    
    messages = [
        SystemMessage(content="""你是一个文本优化专家。请改进给定的文本，使其更加清晰、专业和易读。
只返回改进后的文本，不要添加额外说明。"""),
        HumanMessage(content=f"请优化以下文本：\n\n{state['current_text']}")
    ]
    
    response = llm.invoke(messages)
    improved_text = response.content.strip()
    
    # 记录改进
    state['improvements'].append({
        'iteration': state['iteration'],
        'text': improved_text
    })
    
    state['current_text'] = improved_text
    print(f"✓ 文本已优化")
    
    return state


def evaluate_quality(state: IterativeState) -> IterativeState:
    """评估文本质量"""
    print("📊 评估质量...")
    
    messages = [
        SystemMessage(content="""你是一个文本质量评估专家。
请对文本的清晰度、专业性和可读性进行评分（0-10分）。
只返回一个数字分数，不要有其他内容。"""),
        HumanMessage(content=f"请评分：\n\n{state['current_text']}")
    ]
    
    response = llm.invoke(messages)
    
    # 尝试提取分数
    try:
        score = float(response.content.strip().split()[0])
        score = max(0, min(10, score))  # 确保在0-10范围内
    except:
        score = 7.0  # 默认分数
    
    state['quality_score'] = score
    state['iteration'] += 1
    
    print(f"✓ 质量评分: {score}/10")
    
    return state


def should_continue(state: IterativeState) -> Literal["continue", "end"]:
    """决定是否继续迭代"""
    # 如果达到最大迭代次数，或质量足够高，则停止
    if state['iteration'] > state['max_iterations']:
        print("→ 达到最大迭代次数，停止优化")
        return "end"
    
    if state['quality_score'] >= 9.0:
        print("→ 质量已达标，停止优化")
        return "end"
    
    print("→ 继续优化")
    return "continue"


# 4. 创建循环图
def create_iterative_graph():
    """创建带循环的迭代优化图"""
    workflow = StateGraph(IterativeState)
    
    # 添加节点
    workflow.add_node("improve", improve_text)
    workflow.add_node("evaluate", evaluate_quality)
    
    # 设置入口
    workflow.set_entry_point("improve")
    
    # 改进后评估
    workflow.add_edge("improve", "evaluate")
    
    # 根据评估结果决定是否继续
    workflow.add_conditional_edges(
        "evaluate",
        should_continue,
        {
            "continue": "improve",  # 继续循环
            "end": END  # 结束
        }
    )
    
    return workflow.compile()


# 5. 运行示例
if __name__ == "__main__":
    app = create_iterative_graph()
    
    print("=" * 70)
    print("LangGraph 循环迭代示例 - 文本优化器")
    print("=" * 70)
    
    # 原始文本（故意写得不太好）
    original_text = """
    这个产品很好用，我用了之后感觉还不错，挺方便的。
    就是有时候会有点卡，不过总的来说还可以吧。
    价格也不贵，性价比挺高的。
    """
    
    print(f"\n📝 原始文本:")
    print("-" * 70)
    print(original_text.strip())
    print("-" * 70)
    
    # 运行迭代优化
    result = app.invoke({
        "original_text": original_text,
        "current_text": original_text,
        "iteration": 1,
        "max_iterations": 3,
        "quality_score": 0.0,
        "improvements": []
    })
    
    # 显示结果
    print("\n" + "=" * 70)
    print("优化完成！")
    print("=" * 70)
    
    print(f"\n📈 优化过程:")
    for imp in result['improvements']:
        print(f"\n--- 迭代 {imp['iteration']} ---")
        print(imp['text'][:150] + "..." if len(imp['text']) > 150 else imp['text'])
    
    print(f"\n✨ 最终文本:")
    print("=" * 70)
    print(result['current_text'])
    print("=" * 70)
    print(f"\n最终评分: {result['quality_score']}/10")
    print(f"总迭代次数: {len(result['improvements'])}")
