# LangGraph 动态规划与执行 (Plan-and-Execute) 模式
# 场景：完全动态的流程，由 Agent 根据每一步的结果实时决定下一步做什么

import os
import time
import json
from typing import TypedDict, List, Annotated, Union
import operator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# ==========================================
# 1. 定义工具 (Mock)
# ==========================================

def video_search_tool(query: str):
    """检索视频"""
    print(f"   🛠️ [执行工具] 视频检索: {query}")
    time.sleep(0.5)
    return "Found video: VID_20240520_001 (Title: City Traffic)"

def video_cv_analysis_tool(video_id: str, event_type: str = "general"):
    """CV分析"""
    print(f"   🛠️ [执行工具] CV分析: {video_id}, 事件: {event_type}")
    time.sleep(1)
    # 模拟：如果是检测入侵，返回有入侵
    if "入侵" in event_type or "intrusion" in event_type:
        return "Detected: 2 Person Intrusion Events at 10:05 and 10:15"
    return "Detected: 5 Cars, 2 Buses, 10 Pedestrians"

def video_llm_analysis_tool(video_id: str):
    """大模型分析"""
    print(f"   🛠️ [执行工具] LLM分析: {video_id}")
    time.sleep(1)
    return "Summary: The video shows a busy street. Traffic is flowing smoothly."

def bi_analysis_tool(data: str):
    """BI分析"""
    print(f"   🛠️ [执行工具] BI统计: 基于 {data[:20]}...")
    time.sleep(0.5)
    return "Stats: Intrusion Frequency = 2/day (High Risk)"

def report_generation_tool(context: str):
    """报告生成"""
    print(f"   🛠️ [执行工具] 生成报告...")
    return f"Report Generated based on: {context[:30]}..."

# 工具映射表
TOOL_MAP = {
    "video_search": video_search_tool,
    "cv_analysis": video_cv_analysis_tool,
    "llm_analysis": video_llm_analysis_tool,
    "bi_analysis": bi_analysis_tool,
    "report_generation": report_generation_tool
}

# ==========================================
# 2. 定义状态 (State)
# ==========================================

class Plan(BaseModel):
    """计划模型：包含接下来要执行的工具列表"""
    steps: List[str] = Field(description="List of tool names to execute next. Available tools: video_search, cv_analysis, llm_analysis, bi_analysis, report_generation")
    reasoning: str = Field(description="Reasoning for the current plan")

class AgentState(TypedDict):
    input: str
    plan: List[str]              # 当前待执行的计划队列
    # 关键修复：使用 operator.add 确保是“追加”而不是“覆盖”
    # 如果不加这个，每次 executor 返回时，旧的历史记录会被清空，导致模型“失忆”从而循环调用
    past_steps: Annotated[List[str], operator.add]
    completed_tools: Annotated[List[str], operator.add]
    final_response: str          # 最终结果

# ==========================================
# 3. 节点定义
# ==========================================

def planner_node(state: AgentState):
    """
    规划节点 (Re-Planner)
    根据用户目标 + 已有的执行结果，决定接下来还要做什么。
    """
    print("\n🧠 [Planner] 正在思考下一步计划...")
    
    input_text = state["input"]
    past_steps = state.get("past_steps", [])
    completed_tools = state.get("completed_tools", [])
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0
    )
    
    # ---------------------------------------------------------
    # 修复：不使用 with_structured_output，改用纯 Prompt + JSON 解析
    # 以兼容不支持 response_format 的模型接口
    # ---------------------------------------------------------
    
    system_prompt = f"""你是一个智能任务调度员。你的目标是完成用户的请求。
    
    可用工具：
    1. video_search: 查找视频 (必须先执行)
    2. cv_analysis: 视觉分析 (检测物体、入侵事件等)
    3. llm_analysis: 内容理解 (总结、描述画面)
    4. bi_analysis: 数据统计 (频率、趋势)
    5. report_generation: 生成报告
    
    当前已完成的步骤和结果：
    {past_steps}
    
    已执行过的工具列表（绝对不要再次执行）：
    {completed_tools}
    
    请根据用户请求和已完成的结果，生成**接下来**需要执行的工具列表。
    
    请严格以 JSON 格式输出，不要包含 Markdown 格式（如 ```json），格式如下：
    {{
        "steps": ["tool_name1", "tool_name2"],
        "reasoning": "你的理由"
    }}
    
    规则：
    - 仔细检查“当前已完成的步骤”，如果某个工具已经执行成功（Result不为空），**绝对不要**再次添加到计划中！
    - 如果任务已全部完成（所有要求的分析都已在 past_steps 中出现），"steps" 返回空列表 []。
    - 如果需要根据上一步的结果决定下一步（例如：只有检测到入侵才生成报告），请在当前计划中只包含下一步。
    - 不要死循环。如果发现自己重复建议同一个工具，请立即停止。
    """
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", input_text)
    ])
    
    # 简单的 JSON 解析
    content = response.content.strip()
    # 去除可能的 markdown 代码块标记
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    try:
        plan_dict = json.loads(content)
        plan = Plan(**plan_dict)
    except Exception as e:
        print(f"❌ [Planner] JSON 解析失败: {e}, 原始内容: {content}")
        # 兜底策略：如果解析失败，假设结束
        plan = Plan(steps=[], reasoning="解析失败，停止执行")
    
    # 关键：显式过滤掉已经执行过的工具
    filtered_steps = [step for step in plan.steps if step not in completed_tools]
    
    if len(filtered_steps) < len(plan.steps):
        print(f"⚠️ [Planner] 过滤了重复的工具: {set(plan.steps) - set(filtered_steps)}")
    
    print(f"📋 [Planner] 更新计划: {filtered_steps} (理由: {plan.reasoning})")
    
    return {"plan": filtered_steps}

def executor_node(state: AgentState):
    """
    执行节点
    从计划队列中取出第一个工具并执行。
    """
    plan = state["plan"]
    if not plan:
        return {}
    
    # 取出第一个任务
    tool_name = plan[0]
    remaining_plan = plan[1:]
    
    print(f"👉 [Executor] 准备执行: {tool_name}")
    
    # --- 简单的上下文提取逻辑 ---
    # 尝试从历史记录中提取 video_id
    import re
    video_id = "VID_UNKNOWN"
    for step in state.get("past_steps", []):
        # 假设 search 结果包含 "Found video: VID_..."
        match = re.search(r"(VID_\w+)", step)
        if match:
            video_id = match.group(1)
            
    # 执行逻辑
    result = "Error: Tool not found"
    
    # 简单的参数注入逻辑
    if tool_name == "video_search":
        result = TOOL_MAP[tool_name](state["input"])
    elif tool_name == "cv_analysis":
        # 简单判断参数
        event = "intrusion" if "入侵" in state["input"] else "general"
        result = TOOL_MAP[tool_name](video_id, event)
    elif tool_name == "llm_analysis":
        result = TOOL_MAP[tool_name](video_id)
    elif tool_name == "bi_analysis":
        # 获取之前的 CV 结果作为输入
        last_result = state["past_steps"][-1] if state["past_steps"] else ""
        result = TOOL_MAP[tool_name](last_result)
    elif tool_name == "report_generation":
        # 汇总所有历史信息
        context = str(state["past_steps"])
        result = TOOL_MAP[tool_name](context)
    
    # 记录执行结果
    step_record = f"Tool: {tool_name}, Result: {result}"
    
    # 更新状态：
    # 1. 减少待执行计划
    # 2. 增加历史记录
    # 3. 【关键】把工具名加入 completed_tools
    return {
        "plan": remaining_plan,
        "past_steps": [step_record],
        "completed_tools": [tool_name]
    }

# ==========================================
# 4. 路由逻辑
# ==========================================

def should_continue(state: AgentState):
    """
    决定是继续执行，还是重新规划，还是结束
    这里采用：执行一步 -> 重新规划 (Re-Plan) 的模式，以实现最大灵活性。
    """
    plan = state["plan"]
    
    # 如果计划为空，说明 Planner 认为没活干了，结束
    if not plan:
        return END
    
    # 否则，去执行
    return "executor"

def after_execution(state: AgentState):
    """
    执行完一步后，总是回到 Planner 进行重新评估 (Re-Plan)
    这样可以处理 "如果 CV 发现入侵，则添加 Report 任务" 这种动态逻辑
    """
    return "planner"

# ==========================================
# 5. 构建图
# ==========================================

def create_plan_execute_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    
    workflow.set_entry_point("planner")
    
    workflow.add_conditional_edges(
        "planner",
        should_continue,
        {
            "executor": "executor",
            END: END
        }
    )
    
    workflow.add_edge("executor", "planner")
    
    # 关键：启用 Checkpointer（内存检查点）
    # 每次节点执行后，LangGraph 会自动保存整个 State
    checkpointer = MemorySaver()
    
    return workflow.compile(checkpointer=checkpointer)

# ==========================================
# 6. 运行
# ==========================================

def run_demo(query: str, thread_id: str = "default"):
    print(f"🗣️ 用户指令: {query}")
    print(f"🆔 Thread ID: {thread_id}")
    print("#" * 60)
    
    app = create_plan_execute_graph()
    
    # 关键：使用 config 参数传入 thread_id
    # LangGraph 会自动加载该 thread 的历史状态（如果存在）
    config = {"configurable": {"thread_id": thread_id}}
    
    result = app.invoke({
        "input": query,
        "plan": [],
        "past_steps": [],
        "completed_tools": []
    }, config=config)
    
    print("\n✅ 流程结束")
    print(f"📊 最终状态: 已执行工具 = {result.get('completed_tools', [])}")
    
    return result

if __name__ == "__main__":
    # 场景 1：完整流程（条件执行）
    print("🎯 场景 1: 完整流程 - 检测入侵并生成报告")
    print("=" * 70)
    
    run_demo(
        "帮我找下龙山路的视频，检测有没有人员入侵。如果有的话，生成一份报告并统计频率。",
        thread_id="task_001"
    )
    
    # 场景 2：简单任务（演示 Checkpointer 的记忆隔离）
    print("🎯 场景 2: 简单任务 - 仅检索视频（不同 thread_id）")
    print("=" * 70)
    
    run_demo(
        "帮我找下人民路的视频",
        thread_id="task_002"  # 不同的 thread_id，状态完全隔离
    )
