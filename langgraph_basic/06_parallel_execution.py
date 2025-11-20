"""
LangGraph 基础示例5：并行执行
演示如何在图中使用并行分支同时执行多个任务
"""
import os
import operator
import time
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# 加载环境变量
load_dotenv()

# 1. 定义状态
class ParallelState(TypedDict):
    topic: str
    # 使用 Annotated 和 operator.add 来合并并行节点的结果
    # 这样多个节点同时写入 results 时，会自动合并成一个列表
    results: Annotated[List[str], operator.add]

# 2. 定义节点函数
def search_wikipedia(state: ParallelState) -> ParallelState:
    """模拟搜索维基百科"""
    print(f"   [Wiki] 开始搜索: {state['topic']}...")
    time.sleep(1)  # 模拟耗时操作
    return {"results": [f"Wiki result for {state['topic']}"]}

def search_google(state: ParallelState) -> ParallelState:
    """模拟搜索谷歌"""
    print(f"   [Google] 开始搜索: {state['topic']}...")
    time.sleep(1)  # 模拟耗时操作
    return {"results": [f"Google result for {state['topic']}"]}

def aggregator(state: ParallelState) -> ParallelState:
    """聚合结果"""
    print("\n🔄 聚合所有搜索结果...")
    results = state['results']
    print(f"   收到 {len(results)} 个结果")
    return state

# 3. 创建图
def create_parallel_graph():
    workflow = StateGraph(ParallelState)
    
    # 添加节点
    workflow.add_node("wiki", search_wikipedia)
    workflow.add_node("google", search_google)
    workflow.add_node("aggregator", aggregator)
    
    # 设置入口点 - 这里我们演示从一个虚拟的起点同时分发给两个节点
    # 在 LangGraph 中，可以通过 set_entry_point 指定一个节点，
    # 或者创建一个起始节点然后连接到多个节点来实现并行
    
    # 这里我们添加一个简单的 start 节点作为分发点
    def start_node(state: ParallelState):
        print(f"🚀 开始任务: {state['topic']}")
        return state
        
    workflow.add_node("start", start_node)
    workflow.set_entry_point("start")
    
    # 添加并行边：从 start 同时指向 wiki 和 google
    workflow.add_edge("start", "wiki")
    workflow.add_edge("start", "google")
    
    # 汇聚：两个搜索节点都指向聚合节点
    workflow.add_edge("wiki", "aggregator")
    workflow.add_edge("google", "aggregator")
    
    # 结束
    workflow.add_edge("aggregator", END)
    
    return workflow.compile()

if __name__ == "__main__":
    app = create_parallel_graph()
    
    print("=" * 50)
    print("LangGraph 并行执行示例")
    print("=" * 50)
    
    start_time = time.time()
    
    # 运行图
    result = app.invoke({
        "topic": "LangGraph Parallelism",
        "results": []
    })
    
    end_time = time.time()
    
    print("-" * 50)
    print(f"总耗时: {end_time - start_time:.2f} 秒")
    print("最终结果列表:")
    for res in result["results"]:
        print(f"- {res}")
    print("=" * 50)
