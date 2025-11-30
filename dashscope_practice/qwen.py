# 调用百炼的 qwen 模型
from langchain_core.prompts.chat import ChatPromptTemplate
from dotenv.main import load_dotenv
from langchain_openai import ChatOpenAI
import os

# 加载环境变量
load_dotenv()


def create_model() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=os.getenv("DASHSCOPE_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        model=os.getenv("TONGYI_MODEL"),
    )


def main():
    llm = create_model()
    question = input("请输入问题：")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的助手,使用通俗易懂的语言回答用户的问题"),
        ("human", "{user_question}"),
    ])
    
    # 创建一个链，将提示模板和模型连接起来
    chain = prompt_template | llm
    
    while question not in ("exit", "quit", "q"):
        for chunk in chain.stream(question):
            if hasattr(chunk, 'content'):
                print(chunk.content, end="")
        print("\n")
        print("-" * 60)
        question = input("\n请输入问题：")
    print("再见！")


if __name__ == "__main__":
    main()
