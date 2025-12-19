"""
Human In The Loop + LangGraph 完整示例

本示例展示了 LangGraph 中实现人机协作的几种常见模式：
1. 基础中断模式 - 使用 interrupt 暂停执行等待人类输入
2. 内容审核模式 - LLM 生成内容后需要人工审核修改
3. 敏感操作确认模式 - 执行敏感工具调用前需要人工确认
4. 多轮对话中断模式 - 在对话过程中请求人类协助
"""

import os
import uuid
from typing import TypedDict, Annotated, Literal
from operator import add

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import tool

load_dotenv()

# 初始化 LLM
llm = ChatTongyi(
    model=os.getenv("TONGYI_MODEL"),
    api_key=os.getenv("DASHSCOPE_KEY"),
)


# ============================================
# 示例 1: 基础中断模式 - 简单的文本审核
# ============================================
def example_1_basic_interrupt():
    """基础中断模式：人工审核并编辑文本"""
    print("\n" + "=" * 60)
    print("示例 1: 基础中断模式 - 简单的文本审核")
    print("=" * 60)

    class State(TypedDict):
        text: str
        approved: bool

    def generate_text(state: State) -> dict:
        """生成文本节点"""
        return {"text": "这是一段自动生成的文本，可能需要人工审核和修改。"}

    def human_review(state: State) -> dict:
        """人工审核节点 - 使用 interrupt 暂停等待人类输入"""
        result = interrupt({
            "task": "请审核以下文本，可以选择批准或修改",
            "current_text": state["text"],
            "options": ["approve", "edit", "reject"]
        })

        if result["action"] == "approve":
            return {"approved": True}
        elif result["action"] == "edit":
            return {"text": result["edited_text"], "approved": True}
        else:
            return {"text": "文本被拒绝", "approved": False}

    def process_result(state: State) -> dict:
        """处理审核结果"""
        if state["approved"]:
            print(f"✅ 文本已通过审核: {state['text']}")
        else:
            print(f"❌ 文本被拒绝")
        return state

    # 构建图
    builder = StateGraph(State)
    builder.add_node("generate_text", generate_text)
    builder.add_node("human_review", human_review)
    builder.add_node("process_result", process_result)

    builder.add_edge(START, "generate_text")
    builder.add_edge("generate_text", "human_review")
    builder.add_edge("human_review", "process_result")
    builder.add_edge("process_result", END)

    # 编译图（需要 checkpointer 来支持中断）
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    # 执行图直到中断点
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke({"text": "", "approved": False}, config=config)

    # 打印中断信息
    print("\n📋 收到中断请求:")
    interrupt_info = result["__interrupt__"][0]
    print(f"  任务: {interrupt_info.value['task']}")
    print(f"  当前文本: {interrupt_info.value['current_text']}")
    print(f"  可选操作: {interrupt_info.value['options']}")

    # 模拟人类输入（编辑文本）
    print("\n👤 人类操作: 选择编辑文本")
    human_response = {
        "action": "edit",
        "edited_text": "这是经过人工审核和修改后的优质文本内容。"
    }

    # 恢复执行
    final_result = graph.invoke(Command(resume=human_response), config=config)
    print(f"\n📄 最终文本: {final_result['text']}")


# ============================================
# 示例 2: 内容生成 + 人工审核模式
# ============================================
def example_2_content_review():
    """LLM 生成内容后进行人工审核"""
    print("\n" + "=" * 60)
    print("示例 2: LLM 内容生成 + 人工审核模式")
    print("=" * 60)

    class State(TypedDict):
        topic: str
        draft: str
        final_content: str
        revision_count: int

    def generate_draft(state: State) -> dict:
        """使用 LLM 生成初稿"""
        messages = [
            SystemMessage(content="你是一个专业的内容创作者，请根据主题生成一段简短的内容。"),
            HumanMessage(content=f"请为以下主题生成一段 50 字左右的内容：{state['topic']}")
        ]
        response = llm.invoke(messages)
        return {"draft": response.content, "revision_count": 0}

    def human_review_edit(state: State) -> dict:
        """人工审核和编辑节点"""
        result = interrupt({
            "task": "请审核 AI 生成的内容草稿",
            "topic": state["topic"],
            "draft": state["draft"],
            "revision_count": state["revision_count"],
            "instructions": "请选择: approve(批准), edit(编辑), regenerate(重新生成)"
        })

        if result["action"] == "approve":
            return {"final_content": state["draft"]}
        elif result["action"] == "edit":
            return {"final_content": result["edited_content"]}
        elif result["action"] == "regenerate":
            return {"revision_count": state["revision_count"] + 1}
        return {}

    def should_regenerate(state: State) -> Literal["regenerate", "finalize"]:
        """决定是否需要重新生成"""
        if state.get("final_content"):
            return "finalize"
        return "regenerate"

    def regenerate_draft(state: State) -> dict:
        """重新生成草稿"""
        messages = [
            SystemMessage(content="你是一个专业的内容创作者，请根据主题重新生成内容，尝试不同的角度。"),
            HumanMessage(content=f"请为主题 '{state['topic']}' 重新生成内容（第 {state['revision_count'] + 1} 次尝试）")
        ]
        response = llm.invoke(messages)
        return {"draft": response.content}

    def finalize_content(state: State) -> dict:
        """最终确认内容"""
        print(f"\n✅ 内容已最终确认!")
        print(f"📝 最终内容: {state['final_content']}")
        return state

    # 构建图
    builder = StateGraph(State)
    builder.add_node("generate_draft", generate_draft)
    builder.add_node("human_review_edit", human_review_edit)
    builder.add_node("regenerate_draft", regenerate_draft)
    builder.add_node("finalize_content", finalize_content)

    builder.add_edge(START, "generate_draft")
    builder.add_edge("generate_draft", "human_review_edit")
    builder.add_conditional_edges(
        "human_review_edit",
        should_regenerate,
        {"regenerate": "regenerate_draft", "finalize": "finalize_content"}
    )
    builder.add_edge("regenerate_draft", "human_review_edit")
    builder.add_edge("finalize_content", END)

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    # 执行
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke(
        {"topic": "人工智能的未来发展", "draft": "", "final_content": "", "revision_count": 0},
        config=config
    )

    # 打印中断信息
    print("\n📋 收到审核请求:")
    interrupt_info = result["__interrupt__"][0]
    print(f"  主题: {interrupt_info.value['topic']}")
    print(f"  AI 草稿: {interrupt_info.value['draft']}")

    # 模拟人类批准
    print("\n👤 人类操作: 批准内容")
    human_response = {"action": "approve"}

    # 恢复执行
    final_result = graph.invoke(Command(resume=human_response), config=config)


# ============================================
# 示例 3: 敏感工具调用确认模式
# ============================================
def example_3_tool_approval():
    """敏感操作需要人工确认"""
    print("\n" + "=" * 60)
    print("示例 3: 敏感工具调用确认模式")
    print("=" * 60)

    class State(TypedDict):
        user_request: str
        action_type: str
        action_params: dict
        action_approved: bool
        result: str

    def analyze_request(state: State) -> dict:
        """分析用户请求，确定需要执行的操作"""
        messages = [
            SystemMessage(content="""你是一个智能助手。分析用户请求并确定操作类型。
可选操作类型: delete_file(删除文件), send_email(发送邮件), make_payment(支付), other(其他)
请以 JSON 格式返回: {"action_type": "xxx", "params": {...}}"""),
            HumanMessage(content=state["user_request"])
        ]
        response = llm.invoke(messages)

        # 简化处理：模拟解析结果
        return {
            "action_type": "delete_file",
            "action_params": {"file_path": "/important/data.txt"}
        }

    def request_approval(state: State) -> dict:
        """对敏感操作请求人工确认"""
        # 定义敏感操作列表
        sensitive_actions = ["delete_file", "send_email", "make_payment"]

        if state["action_type"] in sensitive_actions:
            result = interrupt({
                "warning": "⚠️ 检测到敏感操作，需要人工确认!",
                "action_type": state["action_type"],
                "action_params": state["action_params"],
                "question": "是否批准执行此操作？(approve/reject)"
            })
            return {"action_approved": result["approved"]}
        else:
            return {"action_approved": True}

    def execute_action(state: State) -> dict:
        """执行操作"""
        if state["action_approved"]:
            # 模拟执行操作
            print(f"\n🔧 执行操作: {state['action_type']}")
            print(f"   参数: {state['action_params']}")
            return {"result": f"操作 {state['action_type']} 已成功执行"}
        else:
            return {"result": "操作已被用户拒绝"}

    def report_result(state: State) -> dict:
        """报告执行结果"""
        print(f"\n📊 执行结果: {state['result']}")
        return state

    # 构建图
    builder = StateGraph(State)
    builder.add_node("analyze_request", analyze_request)
    builder.add_node("request_approval", request_approval)
    builder.add_node("execute_action", execute_action)
    builder.add_node("report_result", report_result)

    builder.add_edge(START, "analyze_request")
    builder.add_edge("analyze_request", "request_approval")
    builder.add_edge("request_approval", "execute_action")
    builder.add_edge("execute_action", "report_result")
    builder.add_edge("report_result", END)

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    # 执行
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke(
        {
            "user_request": "请帮我删除 /important/data.txt 这个文件",
            "action_type": "",
            "action_params": {},
            "action_approved": False,
            "result": ""
        },
        config=config
    )

    # 打印中断信息
    print("\n🚨 收到确认请求:")
    interrupt_info = result["__interrupt__"][0]
    print(f"  警告: {interrupt_info.value['warning']}")
    print(f"  操作类型: {interrupt_info.value['action_type']}")
    print(f"  操作参数: {interrupt_info.value['action_params']}")

    # 模拟人类拒绝危险操作
    print("\n👤 人类操作: 拒绝删除文件")
    human_response = {"approved": False}

    # 恢复执行
    final_result = graph.invoke(Command(resume=human_response), config=config)


# ============================================
# 示例 4: 对话中的人类协助工具
# ============================================
def example_4_chat_with_human_assistance():
    """在对话中请求人类协助"""
    print("\n" + "=" * 60)
    print("示例 4: 对话中的人类协助工具")
    print("=" * 60)

    class State(TypedDict):
        messages: Annotated[list[BaseMessage], add]
        needs_human_help: bool
        human_response: str

    @tool
    def request_human_assistance(query: str) -> str:
        """当 AI 无法回答问题或需要人类专业知识时，请求人类协助。
        
        Args:
            query: 需要人类协助的具体问题
        """
        # 使用 interrupt 暂停并等待人类输入
        result = interrupt({
            "type": "human_assistance_request",
            "query": query,
            "instructions": "AI 需要您的帮助来回答这个问题"
        })
        return result["answer"]

    def chatbot(state: State) -> dict:
        """聊天机器人节点"""
        # 绑定工具到 LLM
        llm_with_tools = llm.bind_tools([request_human_assistance])

        system_message = SystemMessage(content="""你是一个有帮助的 AI 助手。
当遇到以下情况时，请使用 request_human_assistance 工具请求人类帮助：
1. 涉及个人隐私信息
2. 需要实时数据（如当前股价）
3. 需要专业领域知识
4. 你不确定答案的情况""")

        messages = [system_message] + state["messages"]
        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}

    def should_use_tool(state: State) -> Literal["tool", "end"]:
        """判断是否需要调用工具"""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tool"
        return "end"

    def tool_node(state: State) -> dict:
        """处理工具调用"""
        last_message = state["messages"][-1]
        tool_call = last_message.tool_calls[0]

        if tool_call["name"] == "request_human_assistance":
            query = tool_call["args"]["query"]
            result = interrupt({
                "type": "human_assistance_request",
                "query": query,
                "instructions": "AI 需要您的帮助来回答这个问题"
            })

            from langchain_core.messages import ToolMessage
            tool_response = ToolMessage(
                content=result["answer"],
                tool_call_id=tool_call["id"]
            )
            return {"messages": [tool_response]}

        return {}

    # 构建图
    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tool", tool_node)

    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", should_use_tool, {"tool": "tool", "end": END})
    builder.add_edge("tool", "chatbot")

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    # 执行 - 问一个需要人类协助的问题
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    print("\n💬 用户问题: 我们公司今年的销售目标是多少？")

    result = graph.invoke(
        {
            "messages": [HumanMessage(content="我们公司今年的销售目标是多少？")],
            "needs_human_help": False,
            "human_response": ""
        },
        config=config
    )

    # 检查是否有中断
    if "__interrupt__" in result and result["__interrupt__"]:
        print("\n📋 AI 请求人类协助:")
        interrupt_info = result["__interrupt__"][0]
        print(f"  问题: {interrupt_info.value['query']}")
        print(f"  说明: {interrupt_info.value['instructions']}")

        # 模拟人类提供答案
        print("\n👤 人类回复: 今年的销售目标是 1000 万元")
        human_response = {"answer": "今年的销售目标是 1000 万元，分四个季度完成。"}

        # 恢复执行
        final_result = graph.invoke(Command(resume=human_response), config=config)

        # 打印最终回复
        print("\n🤖 AI 最终回复:")
        print(f"   {final_result['messages'][-1].content}")


# ============================================
# 示例 5: 静态中断点模式 (interrupt_before/after)
# ============================================
def example_5_static_breakpoints():
    """使用编译时设置的静态中断点"""
    print("\n" + "=" * 60)
    print("示例 5: 静态中断点模式 (interrupt_before/after)")
    print("=" * 60)

    class State(TypedDict):
        value: int
        history: Annotated[list[str], add]

    def step_a(state: State) -> dict:
        new_value = state["value"] + 10
        return {"value": new_value, "history": [f"Step A: {state['value']} -> {new_value}"]}

    def step_b(state: State) -> dict:
        new_value = state["value"] * 2
        return {"value": new_value, "history": [f"Step B: {state['value']} -> {new_value}"]}

    def step_c(state: State) -> dict:
        new_value = state["value"] - 5
        return {"value": new_value, "history": [f"Step C: {state['value']} -> {new_value}"]}

    # 构建图
    builder = StateGraph(State)
    builder.add_node("step_a", step_a)
    builder.add_node("step_b", step_b)
    builder.add_node("step_c", step_c)

    builder.add_edge(START, "step_a")
    builder.add_edge("step_a", "step_b")
    builder.add_edge("step_b", "step_c")
    builder.add_edge("step_c", END)

    checkpointer = InMemorySaver()

    # 编译时设置静态中断点：在 step_b 之前中断
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["step_b"]  # 在 step_b 执行前中断
    )

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # 第一次执行 - 会在 step_b 之前停止
    print("\n🚀 第一次执行（会在 step_b 前停止）...")
    result1 = graph.invoke({"value": 5, "history": []}, config=config)
    print(f"   当前值: {result1['value']}")
    print(f"   执行历史: {result1['history']}")

    # 检查当前状态
    print("\n⏸️ 图已在 step_b 之前暂停")
    print("   用户可以在此检查状态并决定是否继续...")

    # 继续执行 - 传入 None 表示继续
    print("\n▶️ 继续执行...")
    result2 = graph.invoke(None, config=config)
    print(f"   最终值: {result2['value']}")
    print(f"   完整历史: {result2['history']}")


# ============================================
# 主程序
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph Human In The Loop 完整示例")
    print("=" * 60)

    # 运行所有示例
    # example_1_basic_interrupt()
    example_2_content_review()
    # example_3_tool_approval()
    # example_4_chat_with_human_assistance()
    # example_5_static_breakpoints()

    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)
