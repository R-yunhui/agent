# LangGraph 经典 Plan-and-Execute 模式
# 特点：Planner 一次性制定完整计划，Executor 批量执行，不重新规划

import os
import time
import json
from typing import TypedDict, List, Annotated
import operator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# ==========================================
# 1. 定义工具 (Mock)
# ==========================================

def video_search_tool(query: str):
    """检索视频"""
    print(f"   🔍 视频检索: {query}")
    time.sleep(0.3)
    return "Found video: VID_20240520_001"

def video_cv_analysis_tool(video_id: str, event_type: str = "general"):
    """CV分析"""
    print(f"   🎥 CV分析: {video_id}")
    time.sleep(0.5)
    if "入侵" in event_type or "intrusion" in event_type:
        return "Detected: 2 Person Intrusion Events"
    return "Detected: 5 Cars, 2 Buses"

def video_llm_analysis_tool(video_id: str):
    """大模型分析"""
    print(f"   🤖 LLM分析: {video_id}")
    time.sleep(0.5)
    return "Summary: Busy street, traffic flowing smoothly"

def bi_analysis_tool(data: str):
    """BI分析"""
    print(f"   📊 BI统计")
    time.sleep(0.3)
    return "Stats: Intrusion Frequency = 2/day (High Risk)"

def report_generation_tool(context: str):
    """报告生成"""
    print(f"   📝 生成报告")
    return f"Report Generated"

TOOL_MAP = {
    "video_search": video_search_tool,
    "cv_analysis": video_cv_analysis_tool,
    "llm_analysis": video_llm_analysis_tool,
    "bi_analysis": bi_analysis_tool,
    "report_generation": report_generation_tool
}

# ==========================================
# 2. 定义状态
# ==========================================

class Plan(BaseModel):
    """计划模型：一次性生成完整的执行步骤"""
    steps: List[str] = Field(description="Complete list of tool names to execute. Available: video_search, cv_analysis, llm_analysis, bi_analysis, report_generation")
    reasoning: str = Field(description="Reasoning for this plan")

class AgentState(TypedDict):
    input: str
    plan: List[str]                                      # 完整计划列表
    past_steps: Annotated[List[str], operator.add]      # 已执行的步骤记录
    final_response: str

# ==========================================
# 3. 节点定义
# ==========================================

def planner_node(state: AgentState):
    """
    规划节点：一次性制定完整计划
    关键：只调用一次，然后 Executor 批量执行
    """
    print("\n🧠 [Planner] 制定完整执行计划...")
    
    input_text = state["input"]
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0
    )
    
    system_prompt = """你是一个智能任务规划员。根据用户请求，一次性制定完整的执行计划。

可用工具：
1. video_search: 查找视频（必须先执行）
2. cv_analysis: 视觉分析（检测物体、入侵事件等）
3. llm_analysis: 内容理解（总结、描述画面）
4. bi_analysis: 数据统计（频率、趋势）
5. report_generation: 生成报告

请一次性生成完整的工具列表，按执行顺序排列。

严格以 JSON 格式输出（不要包含 Markdown 格式）：
{
    "steps": ["tool1", "tool2", "tool3"],
    "reasoning": "你的规划理由"
}

规则：
- 必须先执行 video_search
- 如果需要统计或报告，应该在分析之后
- 计划要完整，涵盖用户请求的所有需求
"""
    
    response = llm.invoke([
        ("system", system_prompt),
        ("human", input_text)
    ])
    
    content = response.content.strip()
    # 去除可能的 markdown 标记
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    try:
        plan_dict = json.loads(content.strip())
        plan = Plan(**plan_dict)
    except Exception as e:
        print(f"❌ JSON 解析失败: {e}")
        plan = Plan(steps=["video_search"], reasoning="解析失败，使用默认计划")
    
    print(f"📋 计划: {plan.steps}")
    print(f"💡 理由: {plan.reasoning}")
    
    return {"plan": plan.steps}

def executor_node(state: AgentState):
    """
    执行节点：批量执行计划列表中的所有工具
    关键：循环执行，不重新规划
    """
    plan = state["plan"]
    
    if not plan:
        return {}
    
    print(f"\n⚙️ [Executor] 开始执行 {len(plan)} 个步骤")
    
    # 批量执行所有步骤
    execution_results = []
    
    # 简单的上下文传递
    video_id = "VID_UNKNOWN"
    last_result = ""
    
    for i, tool_name in enumerate(plan, 1):
        print(f"\n[{i}/{len(plan)}] 执行: {tool_name}")
        
        result = "Error: Tool not found"
        
        # 执行工具（带简单的参数推断）
        if tool_name == "video_search":
            result = TOOL_MAP[tool_name](state["input"])
            # 提取 video_id
            import re
            match = re.search(r"(VID_\w+)", result)
            if match:
                video_id = match.group(1)
        
        elif tool_name == "cv_analysis":
            event = "intrusion" if "入侵" in state["input"] else "general"
            result = TOOL_MAP[tool_name](video_id, event)
        
        elif tool_name == "llm_analysis":
            result = TOOL_MAP[tool_name](video_id)
        
        elif tool_name == "bi_analysis":
            result = TOOL_MAP[tool_name](last_result)
        
        elif tool_name == "report_generation":
            context = str(execution_results)
            result = TOOL_MAP[tool_name](context)
        
        last_result = result
        step_record = f"Tool: {tool_name}, Result: {result}"
        execution_results.append(step_record)
    
    print(f"\n✅ [Executor] 所有步骤执行完成")
    
    return {
        "plan": [],  # 清空计划（表示已完成）
        "past_steps": execution_results,
        "final_response": execution_results[-1] if execution_results else "No results"
    }

# ==========================================
# 4. 构建图
# ==========================================

def create_plan_execute_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    
    # 关键：线性流程，不回头
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", END)  # ← 执行完直接结束，不重新规划
    
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# ==========================================
# 5. 运行
# ==========================================

def run_demo(query: str, thread_id: str = "default"):
    print(f"\n{'='*70}")
    print(f"🗣️  用户指令: {query}")
    print(f"🆔 Thread ID: {thread_id}")
    print(f"{'='*70}")
    
    app = create_plan_execute_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    result = app.invoke({
        "input": query,
        "plan": [],
        "past_steps": [],
        "final_response": ""
    }, config=config)
    
    print(f"\n{'='*70}")
    print("✅ 流程结束")
    print(f"📊 执行了 {len(result.get('past_steps', []))} 个步骤")
    print(f"{'='*70}\n")
    
    return result

if __name__ == "__main__":
    # 场景 1：完整流程
    run_demo(
        "帮我找下龙山路的视频，检测有没有人员入侵。如果有的话，生成一份报告并统计频率。",
        thread_id="task_001"
    )
    
    # 场景 2：简单任务
    run_demo(
        "帮我找下人民路的视频，做个内容总结",
        thread_id="task_002"
    )
