import os

from dotenv import load_dotenv
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_community.tools import tool
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.runnables import RunnableConfig
from langchain.agents.middleware import AgentState, before_agent, after_agent, before_model, after_model
from langgraph.runtime import Runtime
from datetime import datetime

# 加载环境配置
load_dotenv()


@tool(description="获取当前时间")
def get_current_time() -> str:
    """获取当前时间"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@before_agent()
def before_agent_do(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"Before agent do: {state}")
    return None


@after_agent()
def after_agent_do(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"After agent do: {state}")
    return None


@before_model()
def before_model_do(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"Before model do: {state}")
    # 校验消息的梳理
    if state['messages']:
        print(f"消息数量: {len(state['messages'])}")
        # 最多保留 10 条数据
        state['messages'] = state['messages'][-10:]
    return None


@after_model()
def after_model_do(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"After model do: {state}")
    return None


llm = ChatOpenAI(
    model=os.getenv("OPENAI_CHAT_MODEL"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7,
    max_retries=3,
    max_tokens=4096
)


def chat(question: str, thread_id: str) -> str:
    system_prompt = """
    你是一个智能助手，可以帮助用户解决问题获取当前时间。
    """

    middleware_list = [
        before_agent_do,
        after_agent_do,
        before_model_do,
        after_model_do,
    ]

    with SqliteSaver.from_conn_string("chat_memory.db") as checkpointer:
        agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=[get_current_time],
            middleware=middleware_list,
            checkpointer=checkpointer,
            debug=False,
        )

        response = agent.invoke(
            input={"messages": [HumanMessage(content=question)]},
            config=RunnableConfig(configurable={"thread_id": thread_id})
        )
        return response["messages"][-1].content


def main():
    session_id = "user-session-123"
    print("🤖 聊天机器人启动！输入 'exit' 退出")

    while True:
        question = input("\n👤 你: ").strip()
        if question.lower() == "exit":
            print("👋 再见！")
            break

        try:
            response = chat(question, session_id)
            print(f"🤖 助手: {response}")
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
