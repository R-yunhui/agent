"""
LangGraph 基础示例2：条件路由
演示如何根据状态进行条件分支
"""
import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# 加载环境变量
load_dotenv()


# 1. 定义状态
class State(TypedDict):
    """定义图的状态结构"""
    message: str
    sentiment: str  # positive, negative, neutral
    response: str


# 2. 定义节点函数
def analyze_sentiment(state: State) -> State:
    """分析情感的节点"""
    message = state['message'].lower()
    
    # 简单的情感分析逻辑
    if any(word in message for word in ['好', '棒', '喜欢', '开心', '高兴']):
        state['sentiment'] = 'positive'
    elif any(word in message for word in ['坏', '差', '讨厌', '生气', '难过']):
        state['sentiment'] = 'negative'
    else:
        state['sentiment'] = 'neutral'
    
    print(f"✓ 情感分析完成: {state['sentiment']}")
    return state


def handle_positive(state: State) -> State:
    """处理积极情感"""
    state['response'] = f"太好了！很高兴听到你说：{state['message']}"
    print(f"✓ 积极响应已生成")
    return state


def handle_negative(state: State) -> State:
    """处理消极情感"""
    state['response'] = f"我理解你的感受。关于：{state['message']}，我们来解决它。"
    print(f"✓ 消极响应已生成")
    return state


def handle_neutral(state: State) -> State:
    """处理中性情感"""
    state['response'] = f"收到你的消息：{state['message']}"
    print(f"✓ 中性响应已生成")
    return state


# 3. 条件路由函数
def route_by_sentiment(state: State) -> Literal["positive", "negative", "neutral"]:
    """根据情感决定路由"""
    sentiment = state['sentiment']
    print(f"→ 路由到: {sentiment}")
    return sentiment


# 4. 创建条件图
def create_conditional_graph():
    """创建带条件路由的状态图"""
    workflow = StateGraph(State)
    
    # 添加节点
    workflow.add_node("analyze", analyze_sentiment)
    workflow.add_node("positive", handle_positive)
    workflow.add_node("negative", handle_negative)
    workflow.add_node("neutral", handle_neutral)
    
    # 设置入口
    workflow.set_entry_point("analyze")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "analyze",  # 从哪个节点出发
        route_by_sentiment,  # 路由函数
        {
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral"
        }
    )
    
    # 所有响应节点都指向结束
    workflow.add_edge("positive", END)
    workflow.add_edge("negative", END)
    workflow.add_edge("neutral", END)
    
    return workflow.compile()


# 5. 运行示例
if __name__ == "__main__":
    app = create_conditional_graph()
    
    # 测试不同情感的消息
    test_messages = [
        "今天天气真好，我很开心！",
        "这个产品太差了，我很失望",
        "今天去超市买了东西"
    ]
    
    print("=" * 60)
    print("LangGraph 条件路由示例")
    print("=" * 60)
    
    for msg in test_messages:
        print(f"\n输入消息: {msg}")
        print("-" * 60)
        
        result = app.invoke({
            "message": msg,
            "sentiment": "",
            "response": ""
        })
        
        print(f"情感: {result['sentiment']}")
        print(f"响应: {result['response']}")
        print("-" * 60)