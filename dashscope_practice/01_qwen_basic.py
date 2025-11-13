"""
langchain + qwen + dashscope_practice 百炼大模型
"""
import os

from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# 加载环境配置
load_dotenv()


def chat_with_qwen(user_question: str, url: str, stream: bool = True):
    chat_model = ChatTongyi(
        api_key=os.getenv("DASHSCOPE_KEY"),
        model="qwen3-vl-plus",
        streaming=stream,
        # 传递额外参数
        model_kwargs={
            "enable_thinking": True
        }
    )

    message = HumanMessage(content=[
        {
            "text": user_question,
        },
        {
            "image": url
        }
    ])

    if stream:
        for chunk in chat_model.stream(input=[message]):
            if chunk.additional_kwargs:
                print(chunk.additional_kwargs.get("reasoning_content"), end="")
            elif chunk.content:
                print(chunk.content[0].get("text"), end="")
    else:
        res = chat_model.invoke(input=[message])
        print(res.content)


def chat_with_openai_qwen(user_question: str, url: str, stream: bool = True):
    chat_model = ChatOpenAI(
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_KEY"),
        model="qwen3-vl-plus",
        streaming=stream,
    )


def main():
    user_question = "answer this question"
    url = "https://img.alicdn.com/imgextra/i1/O1CN01gDEY8M1W114Hi3XcN_!!6000000002727-0-tps-1024-406.jpg"
    chat_with_qwen(user_question, url)


if __name__ == "__main__":
    main()
