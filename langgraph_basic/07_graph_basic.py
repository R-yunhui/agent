# langgraph 学习
import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import re

# 加载环境配置
load_dotenv()


# 定义状态
class ArticleState(TypedDict):
    topic: str  # 文章主题
    article: str  # 生成的文章
    score: int  # 评分
    review: str  # 评测意见
    final_result: str  # 最终结果


def create_chat_model():
    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        temperature=0.7,
        max_tokens=3000,
        api_key=os.getenv("OPENAI_API_KEY")
    )


# 节点1：写文章
def write_article_node(state: ArticleState):
    print(f"\n📝 正在撰写文章，主题: {state['topic']}")

    chat_model = create_chat_model()

    system_prompt = """你是一个精炼的短文作家。你的任务是根据用户提供的主题撰写一篇短文。
要求：
1. 字数严格控制在 100 字左右。
2. 内容积极向上，逻辑清晰，语言通顺。
3. 不要输出多余的解释性文字，直接输出文章内容。"""

    user_prompt = f'请以"{state["topic"]}"为主题写一篇短文。'

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = chat_model.invoke(messages)
    article = response.content

    print(f"✅ 文章生成完成！\n{article}\n")

    return {"article": article}


# 节点2：评测文章
def review_article_node(state: ArticleState):
    print(f"\n🔍 正在评测文章...")

    chat_model = create_chat_model()

    system_prompt = """你是一个公正的文章评审员。你的任务是阅读用户提供的文章，并进行评测。
请按以下格式输出：
【评分】：给出 1-100 分的整数打分。
【评价】：一句话概括文章的优点。
【建议】：一句话提出改进建议。"""

    user_prompt = f"""请评测以下文章：
            {state['article']}
        """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = chat_model.invoke(messages)
    review_text = response.content

    # 提取评分（使用正则表达式）
    score_match = re.search(r'【评分】[：:]\s*(\d+)', review_text)
    score = int(score_match.group(1)) if score_match else 0

    print(f"✅ 评测完成！\n{review_text}\n")
    print(f"📊 评分: {score}")

    return {"score": score, "review": review_text}


# 节点3：决策输出
def decision_node(state: ArticleState):
    print(f"\n⚖️ 正在根据评测结果做出决策...")

    score = state['score']
    review = state['review']

    if score >= 85:
        result = f"""
🎉 评测结果：优秀！

{review}

恭喜！文章质量达到优秀标准。
"""
    else:
        result = f"""
⚠️ 评测结果：需要重新生成

{review}

文章评分未达到 85 分，建议重新生成以提升质量。
"""

    print(result)

    return {"final_result": result}


def main():
    print("=" * 60)
    print("🚀 LangGraph 文章生成与评测系统")
    print("=" * 60)

    workflow = StateGraph(ArticleState)

    # 添加节点
    workflow.add_node("write_article", write_article_node)
    workflow.add_node("review_article", review_article_node)
    workflow.add_node("decision", decision_node)

    # 设置入口点
    workflow.set_entry_point("write_article")

    # 添加边（定义流程）
    workflow.add_edge("write_article", "review_article")
    workflow.add_edge("review_article", "decision")
    workflow.add_edge("decision", END)

    # 编译图
    app = workflow.compile()

    # 运行工作流
    initial_state = {
        "topic": "人工智能的未来",
        "article": "",
        "score": 0,
        "review": "",
        "final_result": ""
    }

    result = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("📋 最终结果")
    print("=" * 60)
    print(result["final_result"])


if __name__ == "__main__":
    main()
