"""AI 自动化脚本生成服务"""
import json
from app.services.llm_client import get_llm_client
from app.services.prompt_manager import get_prompt
from loguru import logger


async def generate_pytest_script(api_name: str, method: str, base_url: str, path: str, cases: list[dict], llm_config: dict = None) -> dict:
    """生成 Python + Pytest + Requests 脚本"""
    client = get_llm_client(**(llm_config or {}))
    prompt = get_prompt(
        "script_generate_pytest",
        api_name=api_name,
        method=method,
        base_url=base_url,
        path=path,
        cases=json.dumps(cases, ensure_ascii=False, indent=2),
    )
    messages = [
        {"role": "system", "content": "你是自动化测试专家，生成可直接运行的pytest脚本。严格按JSON格式返回。"},
        {"role": "user", "content": prompt},
    ]
    try:
        result = await client.chat_json(messages, temperature=0.2, max_tokens=8192)
        return result
    except Exception as e:
        logger.error(f"Pytest脚本生成失败: {e}")
        raise ValueError(f"脚本生成失败: {str(e)}")


async def generate_playwright_script(url: str, steps: str, llm_config: dict = None) -> dict:
    """生成 Playwright UI 自动化脚本"""
    client = get_llm_client(**(llm_config or {}))
    prompt = get_prompt("script_generate_playwright", url=url, steps=steps)
    messages = [
        {"role": "system", "content": "你是UI自动化测试专家，生成可直接运行的Playwright Python脚本。严格按JSON格式返回。"},
        {"role": "user", "content": prompt},
    ]
    try:
        result = await client.chat_json(messages, temperature=0.2, max_tokens=8192)
        return result
    except Exception as e:
        logger.error(f"Playwright脚本生成失败: {e}")
        raise ValueError(f"脚本生成失败: {str(e)}")
