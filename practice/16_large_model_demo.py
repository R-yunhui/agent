import os

from dotenv import load_dotenv
from typing import Any

from langchain_openai.chat_models import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import LLMResult, ChatGeneration
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.runnables import RunnableConfig

# 加载环境变量
load_dotenv()

chat_model = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_KEY"),
    model=os.getenv("TONGYI_MODEL"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    streaming=True
)


class TokenUsageCallback(BaseCallbackHandler):

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def reset(self):
        """重置计数器"""
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Collect token usage."""
        try:
            generation = response.generations[0][0]
        except IndexError:
            generation = None

        if isinstance(generation, ChatGeneration):
            try:
                message = generation.message
                if isinstance(message, AIMessage):
                    metadata = message.response_metadata
                    if metadata and metadata.get('token_usage'):
                        usages = metadata.get('token_usage')
                        self.input_tokens = usages.get('input_tokens')
                        self.output_tokens = usages.get('output_tokens')
                        self.total_tokens = usages.get('total_tokens')
            except AttributeError:
                pass

    def print_usage(self):
        """打印使用情况"""
        print(f"\n{'=' * 50}")
        print(f"Token 使用统计:")
        print(f"  输入 tokens: {self.input_tokens}")
        print(f"  输出 tokens: {self.output_tokens}")
        print(f"  总计 tokens: {self.total_tokens}")
        print(f"{'=' * 50}\n")
        self.reset()


token_callback = TokenUsageCallback()

usage_callback = UsageMetadataCallbackHandler()


def chat_with_large_model(question: str):
    system_message = SystemMessage(
        content="你是一个专业的聊天助手，可以回答用户的任意问题，必须使用中文且通俗易懂的语言进行回答。")
    human_message = HumanMessage(content=[
        {
            "type": "text",
            "text": question,
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://lf-flow-web-cdn.doubao.com/obj/flow-doubao/doubao/web/creation/main_banner_text_sc.png"
            }
        }
    ])

    for chunk in chat_model.stream(input=[system_message, human_message],
                                   config=RunnableConfig(callbacks=[token_callback])):
        if chunk and hasattr(chunk, 'content'):
            print(chunk.content, end="", flush=True)

    # 获取最终统计
    token_callback.print_usage()


def main():
    chat_with_large_model("下图里面有什么？")


if __name__ == "__main__":
    main()
