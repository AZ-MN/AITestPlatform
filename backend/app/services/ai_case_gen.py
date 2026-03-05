"""AI 测试用例生成服务"""
import json
from typing import Optional
from app.services.llm_client import get_llm_client
from app.services.prompt_manager import get_prompt
from loguru import logger


async def parse_requirement(content: str, llm_config: dict = None) -> dict:
    """解析需求文档，提取功能点、业务规则、测试点"""
    client = get_llm_client(**(llm_config or {}))
    prompt = get_prompt("requirement_parse", content=content)
    messages = [
        {"role": "system", "content": "你是一名资深软件测试工程师，擅长需求分析和测试设计。"},
        {"role": "user", "content": prompt},
    ]
    try:
        result = await client.chat_json(messages)
        return result
    except Exception as e:
        logger.error(f"需求解析失败: {e}")
        return {
            "功能点列表": [],
            "业务规则": [],
            "可测性问题": [f"解析失败: {str(e)}"],
            "测试点清单": [],
        }


async def generate_test_cases(requirement_text: str, llm_config: dict = None) -> list[dict]:
    """根据需求文本生成测试用例列表"""
    client = get_llm_client(**(llm_config or {}))
    prompt = get_prompt("testcase_generate", requirement=requirement_text)
    messages = [
        {"role": "system", "content": "你是一名资深软件测试工程师，擅长测试用例设计。请严格按照JSON格式返回结果。"},
        {"role": "user", "content": prompt},
    ]
    try:
        result = await client.chat_json(messages, temperature=0.5)
        cases = result.get("test_cases", [])
        logger.info(f"生成测试用例 {len(cases)} 条")
        return cases
    except Exception as e:
        logger.error(f"测试用例生成失败: {e}")
        raise ValueError(f"AI生成失败，请稍后重试: {str(e)}")
