"""
LangGraph 基础示例1：简单的链式调用
演示如何创建一个最基本的状态图
"""
import os
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()


# 1. 定义状态类型
class State(TypedDict):
    """定义图的状态结构"""
    input: str
    output: str
    step_count: int


# 2. 定义节点函数
def process_input(state: State) -> State:
    """处理输入的节点"""
    print(f"步骤 {state['step_count']}: 处理输入...")
    state['output'] = f"已处理: {state['input']}"
    state['step_count'] += 1
    return state


def add_greeting(state: State) -> State:
    """添加问候语的节点"""
    print(f"步骤 {state['step_count']}: 添加问候语...")
    state['output'] = f"你好！{state['output']}"
    state['step_count'] += 1
    return state


def finalize(state: State) -> State:
    """最终处理节点"""
    print(f"步骤 {state['step_count']}: 最终处理...")
    state['output'] = f"{state['output']} [完成]"
    return state


# 3. 创建状态图
def create_simple_graph():
    """创建并返回一个简单的状态图"""
    # 初始化状态图
    workflow = StateGraph(State)
    
    # 添加节点
    workflow.add_node("process", process_input)
    workflow.add_node("greet", add_greeting)
    workflow.add_node("finalize", finalize)
    
    # 设置入口点
    workflow.set_entry_point("process")
    
    # 添加边（定义执行顺序）
    workflow.add_edge("process", "greet")
    workflow.add_edge("greet", "finalize")
    workflow.add_edge("finalize", END)
    
    # 编译图
    app = workflow.compile()
    return app


# 4. 运行示例
if __name__ == "__main__":
    # 创建图
    app = create_simple_graph()
    
    # 准备初始状态
    initial_state = {
        "input": "这是一条测试消息",
        "output": "",
        "step_count": 1
    }
    
    print("=" * 50)
    print("开始执行LangGraph工作流")
    print("=" * 50)
    
    # 运行图
    result = app.invoke(initial_state)
    
    print("=" * 50)
    print("执行结果:")
    print(f"输入: {result['input']}")
    print(f"输出: {result['output']}")
    print(f"总步骤数: {result['step_count']}")
    print("=" * 50)
