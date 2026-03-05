"""AI 测试报告生成服务"""
import json
from app.services.llm_client import get_llm_client
from app.services.prompt_manager import get_prompt
from loguru import logger


async def generate_test_report(project_name: str, iteration_name: str, execution_data: dict, defect_data: dict, llm_config: dict = None) -> dict:
    """AI 生成测试报告"""
    client = get_llm_client(**(llm_config or {}))
    test_scope = f"项目 {project_name} 迭代 {iteration_name} 全量测试"
    prompt = get_prompt(
        "report_generate",
        project_name=project_name,
        iteration_name=iteration_name,
        test_scope=test_scope,
        execution_data=json.dumps(execution_data, ensure_ascii=False),
        defect_data=json.dumps(defect_data, ensure_ascii=False),
    )
    messages = [
        {"role": "system", "content": "你是测试经理，请生成专业的测试报告。严格按JSON格式返回。"},
        {"role": "user", "content": prompt},
    ]
    try:
        result = await client.chat_json(messages, temperature=0.5)
        return result
    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        raise ValueError(f"AI报告生成失败: {str(e)}")
