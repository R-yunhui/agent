"""
LangGraph 开发规范与最佳实践示例

================================================================================
【核心规范】LangGraph State 管理的关键原则
================================================================================

1. 【节点返回值】
   - 每个节点函数必须返回一个 dict，明确声明要更新的 State 字段
   - 返回 None 或不返回任何值 = 不更新任何字段
   - ❌ 错误: 直接修改 state["field"] = value 但不返回
   - ✅ 正确: return {"field": value}

2. 【并行节点的 State 合并】
   - 当多个节点并行执行并更新同一个字段时，LangGraph 需要知道如何合并
   - 默认的 LastValue channel 只接受一个值，会报 InvalidUpdateError
   - 解决方案: 使用 Annotated[type, reducer_func] 定义合并策略

3. 【Reducer 函数】
   - Reducer 接收 (当前值, 新值) -> 合并后的值
   - 常用场景: 合并字典、追加列表、累加数值等

4. 【条件边 (Conditional Edges)】
   - 条件函数只负责返回下一个节点的名称，不应修改 state
   - 条件函数接收的是上一个节点更新后的 state

5. 【State 初始化】
   - 对于可变类型 (dict, list)，需要在初始化时提供默认值
   - 使用 Annotated 时，reducer 会处理初始值的合并

================================================================================
"""

from dotenv import load_dotenv
import os
import time
import random
from threading import Thread
from pathlib import Path
from typing import TypedDict, Literal, Annotated

from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.graph import StateGraph, END

load_dotenv()

# 获取当前脚本所在目录 + image
graph_image_dir = Path(__file__).parent.resolve() / "image"

# 创建 image 目录（exist_ok=True 表示如果已存在也不报错）
graph_image_dir.mkdir(exist_ok=True)

# ============================================================================
# 大模型配置 (当前示例未实际使用，但保留供后续扩展)
# ============================================================================
chat_model = ChatTongyi(
    model=os.getenv("TONGYI_MODEL"),
    api_key=os.getenv("DASHSCOPE_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    temperature=0.7,
    max_retries=3,
    max_tokens=4096,
)


# ============================================================================
# Reducer 函数定义
# ============================================================================
def merge_dicts(left: dict, right: dict) -> dict:
    """
    合并两个字典的 Reducer 函数
    用于处理并行节点同时更新同一个字典字段的场景

    Args:
        left: 当前 state 中的字典值
        right: 节点返回的新字典值

    Returns:
        合并后的字典
    """
    if left is None:
        left = {}
    if right is None:
        return left
    return {**left, **right}


# ============================================================================
# State 定义
# ============================================================================
class DeepAgentState(TypedDict):
    """
    Agent 的全局状态定义

    【规范说明】
    1. 对于会被并行节点同时更新的字段，使用 Annotated[type, reducer] 定义合并策略
    2. 普通字段（只被单个节点更新）可以直接定义类型
    """

    # 用户的原始问题 - 只读字段，不会被节点更新
    original_input: str

    # 联网检索结果 - 会被 baidu_search 和 google_search 并行更新
    # 使用 merge_dicts 作为 reducer，合并两个搜索引擎的结果
    web_search_results: Annotated[dict[str, list[str]], merge_dicts]

    # 计划节点产生的计划信息 - 单节点更新，不需要 reducer
    planner_result: str

    # 总结节点结果 - 单节点更新
    summary_result: dict[str, str]

    # 评分 - 单节点更新
    score: int


# ============================================================================
# 节点函数定义
# ============================================================================
def planner_node(state: DeepAgentState) -> dict:
    """
    规划节点 - 负责分析用户问题并制定搜索计划

    【规范】节点函数签名:
    - 参数: state (当前 State 的快照)
    - 返回: dict (要更新的字段)

    【重要】
    - 只返回需要更新的字段
    - 不要返回整个 state 对象
    """
    time.sleep(1)  # 模拟耗时处理
    print(f"[Planner] 收到问题: {state['original_input']}")

    plan = f"为「{state['original_input']}」制定的搜索计划: 1.百度搜索 2.谷歌搜索"
    print(f"[Planner] 生成计划: {plan}")

    # ✅ 正确: 返回要更新的字段
    return {"planner_result": plan}


def baidu_search(state: DeepAgentState) -> dict:
    """
    百度搜索节点 - 与 google_search 并行执行

    【并行节点注意事项】
    - 多个并行节点如果更新同一字段，必须配置 Reducer
    - 本节点更新 web_search_results，该字段使用 merge_dicts reducer
    """
    time.sleep(1)
    query = state["original_input"]
    print(f"[Baidu] 搜索: {query}")

    # 模拟搜索结果
    results = [f"百度结果1: {query}相关信息", f"百度结果2: {query}详细介绍"]

    # ✅ 返回的 dict 会通过 merge_dicts 与其他并行节点的结果合并
    return {"web_search_results": {"baidu": results}}


def google_search(state: DeepAgentState) -> dict:
    """
    谷歌搜索节点 - 与 baidu_search 并行执行
    """
    time.sleep(1)
    query = state["original_input"]
    print(f"[Google] 搜索: {query}")

    results = [f"Google结果1: {query} overview", f"Google结果2: {query} details"]

    return {"web_search_results": {"google": results}}


def summary_node(state: DeepAgentState) -> dict:
    """
    汇总节点 - 等待所有搜索节点完成后执行

    【汇聚点说明】
    - 当多条边指向同一个节点时，该节点会等待所有上游节点完成
    - 此时 state 已经包含了所有并行节点的更新结果（通过 reducer 合并）
    """
    time.sleep(1)
    print(f"[Summary] 开始汇总搜索结果...")

    summary = {}
    for source, results in state["web_search_results"].items():
        summary[source] = f"来自 {source} 的 {len(results)} 条结果已汇总"
        print(f"[Summary] 处理 {source}: {len(results)} 条结果")

    return {"summary_result": summary}


def evaluation_node(state: DeepAgentState) -> dict:
    """
    评估节点 - 对当前结果进行评分

    【条件分支前置节点】
    - 本节点返回的 score 将被用于后续的条件判断
    - 条件函数 should_continue 会根据 score 决定下一步
    """
    time.sleep(1)
    print(f"[Evaluation] 评估搜索质量...")

    # 模拟评分逻辑（实际场景中可能调用 LLM 进行评估）
    score = random.randint(0, 100)
    print(f"[Evaluation] 评分结果: {score}/100")

    # ✅ 必须返回 score，否则 should_continue 无法获取
    return {"score": score}


# ============================================================================
# 条件路由函数
# ============================================================================
def should_continue(state: DeepAgentState) -> Literal["planner_node", "end"]:
    """
    条件路由函数 - 决定是继续迭代还是结束

    【规范】
    - 条件函数只负责返回下一个节点的名称
    - 不应该修改 state (不需要返回 dict)
    - 返回值必须是 add_conditional_edges 中定义的 key 之一

    【循环控制】
    - score > 60: 结果满意，结束流程
    - score <= 60: 结果不满意，返回规划节点重新搜索
    """
    score = state["score"]

    if score > 60:
        print(f"[Router] 评分 {score} > 60，结果满意，结束流程")
        return "end"
    else:
        print(f"[Router] 评分 {score} <= 60，需要重新规划")
        return "planner_node"


# ============================================================================
# 图构建
# ============================================================================
def create_state_graph() -> StateGraph:
    """
    构建 LangGraph 状态图

    【图结构说明】
    ```
    START
      │
      ▼
    planner_node
      │
      ├───────────┬───────────┐
      ▼           ▼           │
    baidu_search  google_search  (并行执行)
      │           │           │
      └─────┬─────┘           │
            ▼                 │
      summary_node            │
            │                 │
            ▼                 │
      evaluation_node         │
            │                 │
            ▼                 │
      should_continue ────────┘  (条件: score <= 60 时循环)
            │
            ▼ (score > 60)
           END
    ```
    """
    graph = StateGraph(DeepAgentState)

    # --------------------------------------------------
    # 添加节点
    # --------------------------------------------------
    graph.add_node("planner_node", planner_node)
    graph.add_node("baidu_search", baidu_search)
    graph.add_node("google_search", google_search)
    graph.add_node("summary_node", summary_node)
    graph.add_node("evaluation_node", evaluation_node)

    # --------------------------------------------------
    # 设置入口点
    # --------------------------------------------------
    graph.set_entry_point("planner_node")

    # --------------------------------------------------
    # 添加边 - 构建图的拓扑结构
    # --------------------------------------------------

    # 并行分支: planner -> baidu_search 和 google_search 同时执行
    graph.add_edge("planner_node", "baidu_search")
    graph.add_edge("planner_node", "google_search")

    # 汇聚: 两个搜索节点都完成后，进入 summary_node
    graph.add_edge("baidu_search", "summary_node")
    graph.add_edge("google_search", "summary_node")

    # 串行: summary -> evaluation
    graph.add_edge("summary_node", "evaluation_node")

    # --------------------------------------------------
    # 条件边 - 实现循环/分支逻辑
    # --------------------------------------------------
    graph.add_conditional_edges(
        source="evaluation_node",  # 从哪个节点出发
        path=should_continue,  # 条件判断函数
        path_map={  # 返回值 -> 目标节点 的映射
            "planner_node": "planner_node",
            "end": END,
        },
    )

    app = graph.compile()

    # 暂时使用一个额外的线程打印出来流程图
    Thread(target=create_graph_img, args=[app]).start()

    return app


def create_graph_img(app):
    print(f"开始异步执行流程图保存任务, {Thread.getName}")
    # 打印流程图
    png_data = app.get_graph().draw_mermaid_png()

    # 将生成的PNG数据写入文件
    with open(graph_image_dir / "output_graph.png", "wb") as file:
        file.write(png_data)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """主函数 - 演示 LangGraph 的执行流程"""
    query = "成都旅游攻略"

    print("=" * 60)
    print(f"开始处理查询: {query}")
    print("=" * 60)

    # 创建编译后的图
    graph = create_state_graph()

    # 初始化 State
    # 【注意】使用了 Annotated reducer 的字段不需要手动初始化
    initial_state: DeepAgentState = {
        "original_input": query,
        "web_search_results": {},  # 虽然有 reducer，但显式初始化更清晰
        "planner_result": "",
        "summary_result": {},
        "score": 0,
    }

    # 执行图
    final_state = graph.invoke(initial_state)

    # 输出最终结果
    print("=" * 60)
    print("执行完成！最终状态:")
    print("=" * 60)
    print(f"  原始问题: {final_state['original_input']}")
    print(f"  规划结果: {final_state['planner_result']}")
    print(f"  搜索结果来源: {list(final_state['web_search_results'].keys())}")
    print(f"  汇总结果: {final_state['summary_result']}")
    print(f"  最终评分: {final_state['score']}")


if __name__ == "__main__":
    main()
