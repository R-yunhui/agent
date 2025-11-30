"""
大模型服务

提供日报生成相关的大模型调用功能。
"""

import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径（解决直接运行时的导入问题）
# 必须在导入 app 模块之前执行
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models import WorkRecordCreate

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

def create_larget_model() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=os.getenv("DASHSCOPE_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        model=os.getenv("TONGYI_MODEL"),
    )
    

def create_daily_report(work_record: WorkRecordCreate):
    # 日报生成的 Prompt 模板
    daily_report_prompt = ChatPromptTemplate.from_messages([
        # 系统提示词：定义 AI 的角色和任务
        ("system", """你是一位专业的工作报告助手，擅长将零散的工作记录整理成结构清晰、简洁专业的日报。

            你的任务：
            1. 根据用户提供的工作记录，生成一份格式规范的日报
            2. 提炼关键信息，去除冗余内容
            3. 使用简洁专业的语言，突出重点
            4. 特别关注风险问题，如有风险需重点标注
            5. 保持客观准确，不添加用户未提及的内容

            输出要求：
            - 使用 Markdown 格式
            - 条理清晰，分段落展示
            - 字数控制在 200-300 字
            - 重点突出，便于阅读

            输出格式：
            ## {{日期}} 工作日报

            ### 今日完成
            **产品**
            - {{产品相关工作内容，如果为空则显示"暂无"}}

            **项目**
            - {{项目相关工作内容}}

            **其它**
            - {{其它工作内容，如果为空则显示"暂无"}}

            ### 风险与问题
            - {{风险内容，如果为空则显示"暂无"}}

            ### 明日计划
            - {{明日计划内容}}

            ---
            **生成时间**: {{当前时间}}
            """),
                
        # 用户提示词：提供具体的工作记录数据
        ("user", """请根据以下工作记录生成日报：

            【基本信息】
            日期：{record_date}

            【工作记录】
            产品方面：
            {product}

            项目方面：
            {project}

            其它工作：
            {others}

            风险与问题：
            {risks}

            明日计划：
            {tomorrow}

            ---
            请严格按照系统提示中的格式生成日报，确保内容简洁专业。
        """)
    ])
    
    llm = create_larget_model()
    
    chain = daily_report_prompt | llm
    
    # 准备输入数据，处理可能的 None 值
    input_data = {
        "record_date": work_record.record_date,
        "product": work_record.product,
        "project": work_record.project,
        "others": work_record.others,
        "risks": work_record.risks,
        "tomorrow": work_record.tomorrow,
    }

    logger.info(f"准备调用 LLM 生成日报，输入数据: {input_data}")

    try:
        response = chain.invoke(input_data)
        logger.info(f"LLM 调用成功，返回内容长度: {len(response.content)}")
        return response.content
    except Exception as e:
        logger.error(f"LLM 调用失败: {str(e)}", exc_info=True)
        raise e


def main():
    # 测试数据
    work_record = WorkRecordCreate(
        record_date="2025-11-29",
        product="""
            1.城市大脑智能中枢：
                1.1.学习中心的相关开发，包含模型训练，模型部署。整体进度50%
                1.2.能力中心的相关开发，包含能力上架。整体进度30%
        """,
        project="暂无",
        others="暂无",
        risks="涉及到和算法团队对接，存在一定的沟通成本，可能导致产品delay",
        tomorrow="继续城市大脑智能中枢的开发"
    )
    
    # 配置日志以便在直接运行时看到输出
    logging.basicConfig(level=logging.INFO)
    
    daily_record = create_daily_report(work_record)
    print(daily_record)
    

if __name__ == "__main__":
    main()
