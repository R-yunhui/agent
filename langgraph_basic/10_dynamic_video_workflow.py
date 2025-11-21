# LangGraph 动态意图识别与路由示例
# 场景：根据用户意图，动态决定执行哪些分析步骤（检索、CV、LLM、BI、报告）

import os
import time
from typing import TypedDict, Optional, List, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

load_dotenv()

# ==========================================
# 1. 定义状态 (State)
# ==========================================

class ExecutionPlan(BaseModel):
    """执行计划结构化输出"""
    need_retrieve: bool = Field(description="是否需要检索视频，通常为True")
    need_cv_intrusion: bool = Field(description="是否需要检测人员入侵/特定事件")
    need_llm_summary: bool = Field(description="是否需要大模型总结视频内容")
    need_bi_stats: bool = Field(description="是否需要统计频率/数据")
    need_report: bool = Field(description="是否需要生成报告")
    reason: str = Field(description="做出此计划的简短理由")

class DynamicState(TypedDict):
    query: str
    plan: Optional[ExecutionPlan]  # 存储规划结果
    
    # 数据字段
    video_id: Optional[str]
    cv_result: Optional[str]
    llm_result: Optional[str]
    bi_result: Optional[str]
    final_report: Optional[str]

# ==========================================
# 2. 节点定义
# ==========================================

def planner_node(state: DynamicState):
    """大脑节点：分析意图，制定计划"""
    query = state["query"]
    print(f"\n🧠 [Planner] 分析用户意图: '{query}'")
    
    # 使用结构化输出 (Function Calling) 强制模型返回 JSON
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0
    )
    
    structured_llm = llm.with_structured_output(ExecutionPlan)
    
    system_prompt = """你是一个智能任务规划师。根据用户请求，决定需要调用哪些工具。
    规则：
    1. 只要涉及视频，必须先检索 (need_retrieve=True)。
    2. 如果用户问“有没有人闯入”、“检测事件”，开启 need_cv_intrusion。
    3. 如果用户问“里面有什么”、“总结一下”，开启 need_llm_summary。
    4. 如果用户问“统计频率”、“多少次”，开启 need_bi_stats。
    5. 如果用户明确要求“生成报告”、“总结报告”，开启 need_report。
    """
    
    plan = structured_llm.invoke([
        ("system", system_prompt),
        ("human", query)
    ])
    
    print(f"📋 [Planner] 制定计划: {plan.reason}")
    print(f"   - 检索: {plan.need_retrieve}")
    print(f"   - CV检测: {plan.need_cv_intrusion}")
    print(f"   - LLM总结: {plan.need_llm_summary}")
    print(f"   - BI统计: {plan.need_bi_stats}")
    print(f"   - 报告: {plan.need_report}")
    
    return {"plan": plan}

def retrieve_node(state: DynamicState):
    print("🔍 [Retrieve] 检索视频中...")
    time.sleep(0.5)
    return {"video_id": "VID_12345"}

def cv_node(state: DynamicState):
    print("👁️ [CV] 正在检测人员入侵事件...")
    time.sleep(1)
    return {"cv_result": "检测到 2 次人员入侵"}

def llm_node(state: DynamicState):
    print("📝 [LLM] 正在生成视频内容摘要...")
    time.sleep(1)
    return {"llm_result": "视频显示是一个安静的公园，有几个人在散步。"}

def bi_node(state: DynamicState):
    print("📊 [BI] 正在统计历史数据...")
    time.sleep(0.5)
    return {"bi_result": "本周入侵事件频率：低 (共3次)"}

def report_node(state: DynamicState):
    print("📑 [Report] 正在汇总所有数据生成报告...")
    # 汇总已有数据
    data = []
    if state.get("cv_result"): data.append(f"CV: {state['cv_result']}")
    if state.get("llm_result"): data.append(f"LLM: {state['llm_result']}")
    if state.get("bi_result"): data.append(f"BI: {state['bi_result']}")
    
    report = "\n".join(data)
    print(f"\n✅ 最终报告内容:\n{report}")
    return {"final_report": report}

# ==========================================
# 3. 路由逻辑
# ==========================================

def route_after_planner(state: DynamicState):
    """规划后的路由：决定第一步去哪（通常是检索，或者直接结束）"""
    plan = state["plan"]
    if plan.need_retrieve:
        return "retrieve"
    return END

def route_after_retrieve(state: DynamicState):
    """检索后的路由：决定并行的分析任务"""
    plan = state["plan"]
    next_nodes = []
    
    if plan.need_cv_intrusion:
        next_nodes.append("cv_analysis")
    if plan.need_llm_summary:
        next_nodes.append("llm_analysis")
        
    # 如果不需要分析，检查是否需要直接去 BI 或 报告（虽然少见，但逻辑上要处理）
    # 或者如果没有分析任务，直接结束
    if not next_nodes:
        # 检查是否有后续依赖任务，如果有，则直接去后续
        # 这里简化处理：如果没有分析任务，看是否需要 BI
        if plan.need_bi_stats:
            return ["bi_stats"]
        elif plan.need_report:
            return ["generate_report"]
        else:
            print("✅ 任务结束 (仅检索)")
            return END
            
    return next_nodes

def route_after_analysis(state: DynamicState):
    """分析完成后的路由：汇聚"""
    # 这里需要判断是否所有并行的分析都跑完了？
    # LangGraph 的默认行为是等待所有并行的分支都汇聚到同一个点，或者各自走。
    # 为了简单，我们让所有分析节点都指向一个“同步点”或者直接指向 BI/Report
    
    # 这里的逻辑稍微复杂：
    # CV -> BI (如果需要) -> Report (如果需要)
    # LLM -> Report (如果需要)
    
    # 简化策略：所有分析节点都去检查“下一步该去哪”
    # 但为了避免重复执行后续节点，通常需要一个专门的“汇聚节点”或者利用 LangGraph 的特性。
    
    # 我们采用：分析节点 -> join_node (空节点，用于同步) -> 后续
    return "join"

def join_logic(state: DynamicState):
    """汇聚后的路由"""
    plan = state["plan"]
    next_nodes = []
    
    # 只有当还没执行过 BI 且需要 BI 时
    if plan.need_bi_stats and state.get("bi_result") is None:
        return "bi_stats"
    
    # 只有当还没执行过 Report 且需要 Report 时
    if plan.need_report and state.get("final_report") is None:
        return "generate_report"
        
    return END

# ==========================================
# 4. 构建图
# ==========================================

def create_dynamic_graph():
    workflow = StateGraph(DynamicState)
    
    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("cv_analysis", cv_node)
    workflow.add_node("llm_analysis", llm_node)
    
    # 这是一个特殊的空节点，用于等待并行任务完成
    workflow.add_node("join", lambda s: s) 
    
    workflow.add_node("bi_stats", bi_node)
    workflow.add_node("generate_report", report_node)
    
    # 入口
    workflow.set_entry_point("planner")
    
    # 1. Planner -> Retrieve
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "retrieve": "retrieve",
            END: END
        }
    )
    
    # 2. Retrieve -> [CV, LLM] (并行)
    workflow.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        ["cv_analysis", "llm_analysis", "bi_stats", "generate_report", END]
    )
    
    # 3. 分析节点 -> Join
    workflow.add_edge("cv_analysis", "join")
    workflow.add_edge("llm_analysis", "join")
    
    # 4. Join -> BI / Report / End
    workflow.add_conditional_edges(
        "join",
        join_logic,
        {
            "bi_stats": "bi_stats",
            "generate_report": "generate_report",
            END: END
        }
    )
    
    # 5. BI -> Report / End
    # BI 执行完后，通常去 Report，或者结束
    def after_bi(state):
        if state["plan"].need_report:
            return "generate_report"
        return END
        
    workflow.add_conditional_edges(
        "bi_stats",
        after_bi,
        {
            "generate_report": "generate_report",
            END: END
        }
    )
    
    # 6. Report -> End
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

# ==========================================
# 5. 测试用例
# ==========================================

def run_demo(query: str):
    print("\n" + "="*50)
    print(f"🗣️ 用户指令: {query}")
    print("="*50)
    
    app = create_dynamic_graph()
    app.invoke({"query": query})

if __name__ == "__main__":
    # 场景 1: 仅检索
    run_demo("帮我查找一下龙山路附近的视频")
    
    # 场景 2: 检索 + 特定事件检测 (CV)
    run_demo("帮我查找一下龙山路附近的视频，看下里面是否有人员入侵事件")
    
    # 场景 3: 检索 + 泛化分析 (LLM)
    run_demo("帮我查找一下龙山路附近的视频，看下视频里面都有什么")
    
    # 场景 4: 全流程 (检索 + CV + 报告 + 统计)
    run_demo("帮我查找一下龙山路附近的视频，看下里面是否有人员入侵事件，如果有则生成一份总结报告，然后统计一下最近一周的该事件发生的频率")
