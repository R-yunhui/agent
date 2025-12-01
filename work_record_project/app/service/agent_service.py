"""
大模型服务

提供日报、周报生成相关的大模型调用功能。
"""

import sys
import os
import logging
from pathlib import Path
from datetime import date

from typing import List
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径（解决直接运行时的导入问题）
# 必须在导入 app 模块之前执行
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from work_record_project.app.models import WorkRecordCreate
from work_record_project.app.service.in_memory_storage import storage

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
            **产品工作**
            - {{产品相关工作内容，如果为空则显示"暂无"}}

            **项目工作**
            - {{项目相关工作内容}}

            **其它**
            - {{其它工作内容，如果为空则显示"暂无"}}

            ### 风险问题
            - {{风险内容，如果为空则显示"暂无"}}

            ### 次日计划
            - {{次日计划内容}}

            ---
            **生成时间**: {{当前时间}}
            """),

        # 用户提示词：提供具体的工作记录数据
        ("user", """请根据以下工作记录生成日报：

            【基本信息】
            日期：{record_date}

            【工作记录】
            产品工作：
            {product}

            项目工作：
            {project}

            其它工作：
            {others}

            风险问题：
            {risks}

            次日计划：
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


def _format_daily_records_for_weekly(records: List[dict]) -> str:
    """
    将每日工作记录格式化为周报输入文本
    """
    if not records:
        return "本周暂无工作记录"

    formatted_parts = []
    for record in records:
        record_date = record.get("record_date", "未知日期")
        product = record.get("product", "") or "暂无"
        project = record.get("project", "") or "暂无"
        others = record.get("others", "") or "暂无"
        risks = record.get("risks", "") or "暂无"
        tomorrow = record.get("tomorrow", "") or "暂无"

        daily_text = f"""【{record_date}】
            - 产品工作：{product}
            - 项目工作：{project}
            - 其它工作：{others}
            - 风险问题：{risks}
            - 次日计划：{tomorrow}
        """
        formatted_parts.append(daily_text)

    return "\n".join(formatted_parts)


def create_weekly_report(start_date: date, end_date: date) -> str:
    """
    生成周报
    
    Args:
        start_date: 周报开始日期
        end_date: 周报结束日期

    Returns:
        生成的周报内容（Markdown 格式）
    """
    # 周报生成的 Prompt 模板
    weekly_report_prompt = ChatPromptTemplate.from_messages([
        # 系统提示词：定义 AI 的角色和任务
        ("system", """你是一位专业的工作报告助手，擅长将一周的工作记录汇总整理成结构清晰、重点突出的周报。

            你的任务：
            1. 根据用户提供的一周工作记录，生成一份格式规范的周报
            2. 识别连续性工作：将同一项目/任务在不同日期的工作合并描述，体现工作进展
            3. 提炼重点成果：突出本周完成的关键工作和里程碑
            4. 汇总风险问题：合并去重，标注问题状态（已解决/进行中/待解决）
            5. 梳理下周计划：基于本周工作情况，整理下周重点工作
            6. 保持客观准确，不添加用户未提及的内容
            
            输出要求：
            - 使用 Markdown 格式
            - 条理清晰，逻辑性强
            - 字数控制在 400-600 字
            - 重点突出，便于汇报
            
            输出格式：
            ## {start_date} 至 {end_date} 工作周报
            
            ### 本周概览
            - 工作天数：{{实际有记录的天数}}
            - 主要聚焦：{{本周主要工作方向，1-2句话概括}}
            
            ### 重点工作完成情况
            
            **产品工作**
            - {{汇总本周产品相关工作，按项目/任务分类，如果为空则显示"暂无"}}
            
            **项目工作**
            - {{汇总本周项目相关工作，按项目/任务分类，体现进展}}
            
            **其它工作**
            - {{汇总本周其它工作，如果为空则显示"暂无"}}
            
            ### 风险与问题
            - {{汇总本周的风险和问题，合并重复项，标注状态，如果为空则显示"暂无"}}
            
            ### 下周计划
            - {{基于本周工作和次日计划，整理下周重点工作}}
            
            ---
            **统计**：本周工作 {{X}} 天
            **生成时间**: {{当前时间}}
            """),

        # 用户提示词：提供具体的工作记录数据
        ("user", """请根据以下一周的工作记录生成周报：

            【周报周期】
            {start_date} 至 {end_date}
            
            【每日工作记录】
            {daily_records}
            
            ---
            请严格按照系统提示中的格式生成周报。
            注意事项：
            1. 识别相同或相关的工作内容，合并描述并体现进展
            2. 如果某天没有记录，不需要特别说明
            3. 风险问题如果多天重复出现，只列出一次并标注状态
            4. 下周计划应基于本周最后一天的"次日计划"以及整体工作情况整理
        """)
    ])

    llm = create_larget_model()
    chain = weekly_report_prompt | llm

    # 获取日期范围内的工作记录
    work_records = storage.get_work_records_by_date_range(start_date, end_date)

    # 按日期排序
    work_records_sorted = sorted(
        [r for r in work_records if r],  # 过滤空记录
        key=lambda x: x.get("record_date", "")
    )

    # 格式化每日记录
    daily_records_text = _format_daily_records_for_weekly(work_records_sorted)

    # 准备输入数据
    input_data = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily_records": daily_records_text,
    }

    logger.info(f"准备调用 LLM 生成周报，周期: {start_date} 至 {end_date}，记录数: {len(work_records_sorted)}")

    try:
        response = chain.invoke(input_data)
        logger.info(f"LLM 调用成功，返回内容长度: {len(response.content)}")
        return response.content
    except Exception as e:
        logger.error(f"LLM 调用失败: {str(e)}", exc_info=True)
        raise e


def main():
    """测试日报和周报生成功能"""
    # 配置日志以便在直接运行时看到输出
    logging.basicConfig(level=logging.INFO)

    # ========== 测试日报生成 ==========
    print("=" * 50)
    print("测试日报生成")
    print("=" * 50)

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

    daily_record = create_daily_report(work_record)
    print(daily_record)

    # ========== 测试周报生成 ==========
    print("\n" + "=" * 50)
    print("测试周报生成")
    print("=" * 50)

    # 模拟一周的工作记录数据
    test_records = [
        {
            "record_date": "2025-11-25",
            "product": "城市大脑智能中枢：学习中心需求评审",
            "project": "完成登录模块基础框架搭建",
            "others": "参加技术分享会",
            "risks": "数据库选型待定",
            "tomorrow": "继续登录模块开发"
        },
        {
            "record_date": "2025-11-26",
            "product": "城市大脑智能中枢：学习中心UI设计对接",
            "project": "完成登录模块核心逻辑，对接用户认证接口",
            "others": "",
            "risks": "数据库选型待定",
            "tomorrow": "完成登录模块测试"
        },
        {
            "record_date": "2025-11-27",
            "product": "城市大脑智能中枢：能力中心需求梳理",
            "project": "登录模块单元测试完成，修复2个bug",
            "others": "代码评审",
            "risks": "",
            "tomorrow": "开始支付模块开发"
        },
        {
            "record_date": "2025-11-28",
            "product": "",
            "project": "支付模块接口设计，完成支付宝对接",
            "others": "",
            "risks": "支付接口文档不完整，需要和第三方沟通",
            "tomorrow": "继续微信支付对接"
        },
        {
            "record_date": "2025-11-29",
            "product": "城市大脑智能中枢：学习中心开发进度50%",
            "project": "完成微信支付对接，支付模块整体完成80%",
            "others": "周五技术分享：分享LangChain实践",
            "risks": "支付接口文档不完整，已和第三方沟通解决",
            "tomorrow": "完成支付模块剩余功能，开始集成测试"
        },
    ]

    # 保存测试数据到 storage
    for record in test_records:
        record_date = date.fromisoformat(record["record_date"])
        storage.save_work_record(record_date, record)

    # 生成周报
    start_date = date(2025, 11, 25)
    end_date = date(2025, 11, 29)
    weekly_report = create_weekly_report(start_date, end_date)
    print(weekly_report)


if __name__ == "__main__":
    main()
