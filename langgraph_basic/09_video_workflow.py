# LangGraph 复杂工作流示例：视频智能分析系统
# 场景：用户输入一句话，系统自动进行视频检索 -> (并行) 大模型分析 + CV分析 -> BI统计 -> 汇总报告

import time
import random
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

# ==========================================
# 1. 定义状态 (State)
# ==========================================
class VideoAnalysisState(TypedDict):
    query: str                  # 用户输入的查询
    video_id: Optional[str]     # 检索到的视频ID
    video_title: Optional[str]  # 视频标题
    
    # 分析结果
    llm_summary: Optional[str]  # 大模型对视频内容的总结
    cv_objects: Optional[list]  # CV检测到的物体列表
    bi_stats: Optional[dict]    # BI生成的统计数据
    
    final_report: Optional[str] # 最终生成的报告

# ==========================================
# 2. 定义节点 (Nodes) - 模拟各个工具的执行
# ==========================================

def retrieve_node(state: VideoAnalysisState):
    """节点1：视频检索"""
    query = state["query"]
    print(f"\n🔍 [检索] 正在检索视频: '{query}' ...")
    time.sleep(1) # 模拟耗时
    
    # Mock 结果
    video_id = "VID_20240520_001"
    video_title = "城市交通早高峰监控录像"
    
    print(f"✅ [检索] 找到视频: {video_title} (ID: {video_id})")
    return {"video_id": video_id, "video_title": video_title}

def llm_analysis_node(state: VideoAnalysisState):
    """节点2：大模型视频内容分析 (并行分支 A)"""
    video_title = state["video_title"]
    print(f"\n🧠 [LLM] 正在理解视频内容: {video_title} ...")
    time.sleep(2) # 模拟较长的耗时
    
    # Mock 结果
    summary = "视频显示早高峰时段交通拥堵，主要集中在十字路口。有两辆车发生了轻微剐蹭，导致后方车辆排队。"
    
    print(f"✅ [LLM] 内容分析完成")
    return {"llm_summary": summary}

def cv_analysis_node(state: VideoAnalysisState):
    """节点3：CV 算法分析 (并行分支 B)"""
    video_id = state["video_id"]
    print(f"\n👁️ [CV] 正在进行物体检测与识别: {video_id} ...")
    time.sleep(1.5) # 模拟耗时
    
    # Mock 结果
    objects = ["Car", "Car", "Bus", "Person", "TrafficLight", "Car"]
    
    print(f"✅ [CV] 视觉分析完成，检测到 {len(objects)} 个物体")
    return {"cv_objects": objects}

def bi_stats_node(state: VideoAnalysisState):
    """节点4：BI 统计分析 (依赖 CV 结果)"""
    objects = state["cv_objects"]
    print(f"\n📊 [BI] 正在生成统计图表...")
    time.sleep(0.5)
    
    # 简单的统计
    stats = {item: objects.count(item) for item in set(objects)}
    
    print(f"✅ [BI] 统计完成: {stats}")
    return {"bi_stats": stats}

def report_node(state: VideoAnalysisState):
    """节点5：生成最终报告 (汇聚节点)"""
    print(f"\n📝 [Report] 正在生成最终分析报告...")
    
    summary = state["llm_summary"]
    stats = state["bi_stats"]
    title = state["video_title"]
    
    report = f"""
==================================================
📄 视频智能分析报告
==================================================
🎬 视频标题：{title}

1️⃣ 内容摘要 (LLM)：
   {summary}

2️⃣ 关键数据 (CV + BI)：
   - 车辆总数：{stats.get('Car', 0) + stats.get('Bus', 0)}
   - 行人数量：{stats.get('Person', 0)}
   - 交通设施：{stats.get('TrafficLight', 0)} 个信号灯

3️⃣ 综合建议：
   建议优化该路口的信号灯配时，并增加警力疏导。
==================================================
"""
    print(report)
    return {"final_report": report}

# ==========================================
# 3. 定义条件逻辑 (Edges)
# ==========================================

def check_readiness(state: VideoAnalysisState) -> str:
    """
    检查是否所有前置依赖都已完成。
    只有当 LLM 分析结果 和 BI 统计结果 都存在时，才进入报告生成节点。
    否则，当前分支结束（等待另一个分支完成）。
    """
    llm_done = state.get("llm_summary") is not None
    bi_done = state.get("bi_stats") is not None
    
    if llm_done and bi_done:
        print("   Checking... 🟢 所有数据准备就绪 -> 生成报告")
        return "generate_report"
    else:
        missing = []
        if not llm_done: missing.append("LLM分析")
        if not bi_done: missing.append("BI统计")
        print(f"   Checking... 🟡 等待其他分支完成 (缺少: {', '.join(missing)}) -> 挂起")
        return "wait"

# ==========================================
# 4. 构建图 (Graph)
# ==========================================

def create_video_analysis_graph():
    workflow = StateGraph(VideoAnalysisState)
    
    # 添加节点
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("analyze_llm", llm_analysis_node)
    workflow.add_node("analyze_cv", cv_analysis_node)
    workflow.add_node("analyze_bi", bi_stats_node)
    workflow.add_node("generate_report", report_node)
    
    # 设置入口
    workflow.set_entry_point("retrieve")
    
    # 定义流程
    
    # 1. 检索完成后，同时触发 LLM 和 CV (并行)
    workflow.add_edge("retrieve", "analyze_llm")
    workflow.add_edge("retrieve", "analyze_cv")
    
    # 2. CV 完成后，触发 BI
    workflow.add_edge("analyze_cv", "analyze_bi")
    
    # 3. 汇聚逻辑：LLM 和 BI 完成后，都尝试去生成报告
    # 使用条件边来实现“等待所有分支完成”的效果
    
    workflow.add_conditional_edges(
        "analyze_llm",
        check_readiness,
        {
            "generate_report": "generate_report",
            "wait": END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_bi",
        check_readiness,
        {
            "generate_report": "generate_report",
            "wait": END
        }
    )
    
    # 4. 报告生成后结束
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

# ==========================================
# 5. 运行
# ==========================================

def main():
    print("🚀 启动视频智能分析系统 Demo...")
    
    app = create_video_analysis_graph()
    
    initial_state = {
        "query": "帮我分析一下今天早高峰的监控视频，看看有没有异常",
        # 其他字段留空，由节点填充
    }
    
    # 使用 invoke 运行（LangGraph 会自动处理并行调度）
    app.invoke(initial_state)
    
    print("\n✅ 流程执行完毕")

if __name__ == "__main__":
    main()
