"""
Deep Research Agent - 基于 LangGraph 的多 Agent 深度研究系统 (异步版)

架构:
    用户问题 → Planner → Researcher (内部并行) → Synthesizer → Reflector → 输出报告
                              ↑__________________|  (信息不足时回退)
                                        ↑________________________|  (质量不合格时回退)

异步策略:
    - 使用 asyncio + httpx 实现异步网络请求
    - 使用 asyncio.gather() 实现并行搜索
    - 使用 llm.ainvoke() 实现异步 LLM 调用
"""

import asyncio
from typing import TypedDict, List, Literal
import json
import httpx
import os
import re
from pathlib import Path
from datetime import datetime

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. 初始化 LLM
# ============================================================

llm = ChatTongyi(
    model=os.getenv("TONGYI_MODEL"),
    api_key=os.getenv("DASHSCOPE_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
)


# ============================================================
# 2. 定义状态 (State) - 所有 Node 共享的数据结构
# ============================================================


class ResearchState(TypedDict):
    """研究状态，在各个 Node 之间传递"""

    # 输入
    original_question: str  # 用户原始问题

    # Planner 输出
    sub_questions: List[str]  # 分解后的子问题列表

    # Researcher 输出
    search_results: List[dict]  # 搜索结果

    # Synthesizer 输出
    draft_report: str  # 报告草稿

    # Reflector 输出
    reflection_result: dict  # 反思结果 {passed: bool, issues: [], action: str}
    reflection_count: int  # 反思次数（防止无限循环）

    # 最终输出
    final_report: str  # 最终报告


# ============================================================
# 3. 工具函数 (异步版)
# ============================================================


async def web_search_async(query: str, count: int = 5) -> List[dict]:
    """异步调用博查 API 进行网页搜索"""
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {os.getenv('BOCHA_API_KEY', 'sk-77103117515748ca9df587b606992aa4')}",
        "Content-Type": "application/json",
    }
    data = {
        "query": query,
        "freshness": "noLimit",
        "summary": True,
        "count": count,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get("code") == 200 and json_response.get("data"):
                    webpages = (
                        json_response["data"].get("webPages", {}).get("value", [])
                    )
                    return [
                        {
                            "title": page.get("name", ""),
                            "url": page.get("url", ""),
                            "summary": page.get("summary", ""),
                            "site": page.get("siteName", ""),
                            "date": page.get("dateLastCrawled", ""),
                        }
                        for page in webpages
                    ]
    except Exception as e:
        print(f"搜索出错: {e}")

    return []


# ============================================================
# 4. 定义各个 Node (Agent) - 异步版
# ============================================================


async def planner_node(state: ResearchState) -> dict:
    """
    Planner Node: 将用户问题分解为多个子问题 (异步版)
    """
    question = state["original_question"]

    prompt = f"""你是一个研究规划专家。请将用户的问题分解为 3-5 个具体的子问题，以便进行深入研究。

用户问题: {question}
当前时间: {datetime.now().strftime("%Y-%m-%d")}

要求:
1. 子问题应该具体、可搜索
2. 子问题应该覆盖问题的各个方面
3. 按照逻辑顺序排列

请直接输出 JSON 格式:
{{"sub_questions": ["子问题1", "子问题2", "子问题3"]}}
"""

    # 异步调用 LLM
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        # 解析 JSON 响应
        content = response.content.strip()
        # 处理可能的 markdown 代码块
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)
        sub_questions = result.get("sub_questions", [question])
    except (json.JSONDecodeError, KeyError):
        # 解析失败时，使用原问题
        sub_questions = [question]

    print(f"[Planner] 分解为 {len(sub_questions)} 个子问题:")
    for i, q in enumerate(sub_questions, 1):
        print(f"  {i}. {q}")

    return {
        "sub_questions": sub_questions,
        "search_results": [],
    }


async def researcher_node(state: ResearchState) -> dict:
    """
    Researcher Node: 对所有子问题进行并行搜索研究 (异步版)

    使用 asyncio.gather() 实现并行搜索，所有子问题同时发起请求
    """
    sub_questions = state["sub_questions"]

    print(f"[Researcher] 启动 {len(sub_questions)} 个并行搜索任务...")

    async def search_single_question(index: int, question: str) -> dict:
        """异步搜索单个子问题"""
        print(f"  [Task {index + 1}] 正在搜索: {question}")
        results = await web_search_async(question, count=5)
        print(f"  [Task {index + 1}] 完成，找到 {len(results)} 条结果")
        return {
            "question": question,
            "question_index": index,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    # 使用 asyncio.gather() 并行执行所有搜索
    tasks = [search_single_question(i, q) for i, q in enumerate(sub_questions)]
    search_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 过滤掉异常结果并排序
    valid_results = [r for r in search_results if isinstance(r, dict)]
    valid_results.sort(key=lambda x: x["question_index"])

    print(f"[Researcher] 所有搜索完成，共 {len(valid_results)} 个结果")

    return {
        "search_results": valid_results,
    }


async def synthesizer_node(state: ResearchState) -> dict:
    """
    Synthesizer Node: 综合所有搜索结果，生成研究报告草稿 (异步版)
    注意: 这里生成的是草稿，需要经过 Reflector 评估后才能确定是否输出
    """
    print("[Synthesizer] 正在综合信息生成报告草稿...")

    original_question = state["original_question"]
    search_results = state["search_results"]

    # 构建搜索结果摘要
    results_summary = ""
    for i, sr in enumerate(search_results, 1):
        results_summary += f"\n### 子问题 {i}: {sr['question']}\n"
        for j, r in enumerate(sr["results"], 1):
            results_summary += f"- [{r['title']}]({r['url']}): {r['summary']}\n"

    prompt = f"""你是一个专业的研究报告撰写专家。请根据以下搜索结果，撰写一份完整的研究报告。

用户原始问题: {original_question}
当前时间: {datetime.now().strftime("%Y-%m-%d")}

搜索结果:
{results_summary}

要求:
1. 报告结构清晰，包含摘要、正文分析、结论和建议
2. 引用来源，标注 URL
3. 数据和观点要有依据
4. 语言专业但易于理解
5. 如果信息不足，明确指出哪些方面需要更多研究

请撰写研究报告:
"""

    # 异步生成报告草稿
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    print("[Synthesizer] 报告草稿生成完成，等待评估...")

    return {
        "draft_report": response.content,
    }


async def reflector_node(state: ResearchState) -> dict:
    """
    Reflector Node: 评估报告质量，决定是否需要改进 (异步版)
    """
    print("[Reflector] 正在评估报告质量...")

    draft_report = state["draft_report"]
    original_question = state["original_question"]
    reflection_count = state.get("reflection_count", 0)

    prompt = f"""你是一个严格的研究报告评审专家。请评估以下报告的质量。

用户原始问题: {original_question}

报告内容:
{draft_report}

请从以下维度评分 (1-10):
1. 完整性: 是否完整回答了用户问题?
2. 准确性: 数据和结论是否有来源支撑?
3. 深度: 分析是否有洞察力?
4. 可读性: 结构是否清晰?

请输出 JSON 格式:
{{
    "scores": {{"完整性": 8, "准确性": 7, "深度": 6, "可读性": 9}},
    "total": 30,
    "passed": true,
    "issues": ["问题1", "问题2"],
    "action": "pass"
}}

action 可选值:
- "pass": 质量合格，可以输出
- "research_more": 信息不足，需要补充研究
- "rewrite": 逻辑或结构有问题，需要重写

注意: 总分 >= 28 才算通过 (passed=true)
"""

    # 异步调用 LLM
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)
    except (json.JSONDecodeError, KeyError):
        # 解析失败，默认通过
        result = {"passed": True, "action": "pass", "issues": [], "total": 32}

    print(
        f"[Reflector] 评估结果: 总分 {result.get('total', 'N/A')}, 通过: {result.get('passed', True)}"
    )

    # 防止无限循环：最多反思 2 次
    if reflection_count >= 2:
        result["passed"] = True
        result["action"] = "pass"
        print("[Reflector] 达到最大反思次数，强制通过")

    return {
        "reflection_result": result,
        "reflection_count": reflection_count + 1,
    }


def should_continue_after_reflection(
    state: ResearchState,
) -> Literal["planner", "synthesizer", "output"]:
    """
    条件边: 根据反思结果决定下一步
    """
    result = state.get("reflection_result", {})
    action = result.get("action", "pass")

    if action == "research_more":
        print("[Router] 需要补充研究，回到 Planner 重新规划")
        return "planner"
    elif action == "rewrite":
        print("[Router] 需要重写报告")
        return "synthesizer"
    else:
        print("[Router] 质量合格，输出报告")
        return "output"


async def output_node(state: ResearchState) -> dict:
    """
    Output Node: 输出最终报告 (异步版)
    只有经过 Reflector 评估通过后才会执行到这里
    """
    final_report = state["draft_report"]

    # 直接输出完整报告
    print()
    print("=" * 60)
    print("📝 研究报告")
    print("=" * 60)
    # print(final_report)
    print("=" * 60)

    return {
        "final_report": final_report,
    }


# ============================================================
# 5. 构建 LangGraph 工作流
# ============================================================


def build_research_graph():
    """
    构建研究工作流图 (异步版)

    工作流程:
    1. planner: 分解问题为子问题
    2. researcher: 并行搜索所有子问题 (使用 asyncio.gather)
    3. synthesizer: 综合所有结果
    4. reflector: 评估质量
    5. output: 输出报告
    """

    # 创建状态图
    workflow = StateGraph(ResearchState)

    # 添加节点 (异步节点函数)
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("reflector", reflector_node)
    workflow.add_node("output", output_node)

    # 设置入口点
    workflow.set_entry_point("planner")

    # 添加边: 简单的线性流程
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "synthesizer")
    workflow.add_edge("synthesizer", "reflector")

    # 条件边: 反思后的路由
    workflow.add_conditional_edges(
        "reflector",
        should_continue_after_reflection,
        {
            "planner": "planner",  # 信息不足，回到 planner 重新规划
            "synthesizer": "synthesizer",  # 需要重写报告
            "output": "output",  # 质量合格，输出
        },
    )

    workflow.add_edge("output", END)

    # 编译图
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)

    return app


# ============================================================
# 6. 主函数 (异步版)
# ============================================================


async def deep_research(question: str, session_id: str = "default") -> str:
    """
    执行深度研究 (异步版)

    Args:
        question: 用户问题
        session_id: 会话 ID

    Returns:
        研究报告
    """
    print()
    print("═" * 60)
    print("🔍 深度研究系统 (Async)")
    print("═" * 60)
    print(f"用户问题: {question}")
    print("-" * 60)

    app = build_research_graph()

    # 初始状态
    initial_state = {
        "original_question": question,
        "sub_questions": [],
        "search_results": [],
        "draft_report": "",
        "reflection_result": {},
        "reflection_count": 0,
        "final_report": "",
    }

    # 异步执行工作流
    config = {"configurable": {"thread_id": session_id}}
    final_report = ""

    async for event in app.astream(initial_state, config):
        for node_name, node_output in event.items():
            if node_name == "output":
                final_report = node_output.get("final_report", "")
                print()
                print("═" * 60)
                print("✅ 研究完成!")
                print("═" * 60)

    return final_report


def save_report_to_markdown(
    report: str, question: str, output_dir: str = "reports"
) -> str:
    """
    将研究报告保存为 Markdown 文件

    Args:
        report: 报告内容
        question: 用户问题 (用于生成文件名)
        output_dir: 输出目录

    Returns:
        保存的文件路径
    """

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成文件名：时间戳 + 问题前20字符
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 清理问题中的非法文件名字符
    safe_question = re.sub(r'[\\/:*?"<>|]', "", question)[:20].strip()
    filename = f"{timestamp}_{safe_question}.md"

    filepath = output_path / filename

    # 构建 Markdown 内容
    markdown_content = f"""# 研究报告

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 
> 研究问题: {question}

---

{report}

---

*本报告由 Deep Research Agent 自动生成*
"""

    # 写入文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"\n📄 报告已保存至: {filepath}")

    return str(filepath)


if __name__ == "__main__":
    # 使用 asyncio.run() 启动异步主函数
    question = """
    生成一份DeeepResearch智能体竞品调研的报告
    """
    report = asyncio.run(deep_research(question))

    # 保存为 Markdown 文件
    if report:
        save_report_to_markdown(report, question)
