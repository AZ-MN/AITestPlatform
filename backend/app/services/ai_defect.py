"""AI 缺陷分析服务"""
from app.services.llm_client import get_llm_client
from app.services.prompt_manager import get_prompt
from loguru import logger


async def analyze_defect(description: str, llm_config: dict = None) -> dict:
    """AI 分析缺陷：结构化、分类、根因分析、修复建议"""
    client = get_llm_client(**(llm_config or {}))
    prompt = get_prompt("defect_analyze", description=description)
    messages = [
        {"role": "system", "content": "你是资深测试工程师，专注缺陷分析。请严格按JSON格式返回。"},
        {"role": "user", "content": prompt},
    ]
    try:
        result = await client.chat_json(messages, temperature=0.3)
        return result
    except Exception as e:
        logger.error(f"缺陷分析失败: {e}")
        return {
            "structured": {"title": description[:100], "steps_to_reproduce": "", "actual_result": "", "expected_result": ""},
            "category": "functional",
            "severity_suggestion": "normal",
            "root_cause_analysis": f"AI分析失败: {str(e)}",
            "fix_suggestion": "请人工分析",
            "keywords": [],
        }


async def find_similar_defects(keywords: list[str], existing_defects: list[dict]) -> list[int]:
    """基于关键词匹配相似缺陷"""
    similar_ids = []
    for defect in existing_defects:
        title = defect.get("title", "").lower()
        score = sum(1 for kw in keywords if kw.lower() in title)
        if score >= 2:
            similar_ids.append(defect["id"])
    return similar_ids[:5]
