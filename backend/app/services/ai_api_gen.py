"""AI 接口测试用例生成服务"""
import json
from app.services.llm_client import get_llm_client
from app.services.prompt_manager import get_prompt
from loguru import logger


async def generate_api_cases(api_info: dict, llm_config: dict = None) -> list[dict]:
    """根据接口定义生成 API 测试用例"""
    client = get_llm_client(**(llm_config or {}))
    prompt = get_prompt(
        "api_case_generate",
        name=api_info.get("name", ""),
        method=api_info.get("method", "GET"),
        path=api_info.get("path", ""),
        description=api_info.get("description", ""),
        params=json.dumps(api_info.get("query_params", {}), ensure_ascii=False),
        body_schema=json.dumps(api_info.get("body_schema", {}), ensure_ascii=False),
        response_schema=json.dumps(api_info.get("response_schema", {}), ensure_ascii=False),
    )
    messages = [
        {"role": "system", "content": "你是API测试专家，请严格按JSON格式返回测试用例。"},
        {"role": "user", "content": prompt},
    ]
    try:
        result = await client.chat_json(messages, temperature=0.3)
        cases = result.get("cases", [])
        logger.info(f"API用例生成: {len(cases)} 条")
        return cases
    except Exception as e:
        logger.error(f"API用例生成失败: {e}")
        raise ValueError(f"AI生成失败: {str(e)}")


async def parse_swagger(swagger_json: dict) -> list[dict]:
    """解析 Swagger/OpenAPI 文档，返回接口定义列表"""
    apis = []
    paths = swagger_json.get("paths", {})
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                continue
            api = {
                "name": operation.get("summary", path),
                "method": method.upper(),
                "path": path,
                "description": operation.get("description", ""),
                "module": operation.get("tags", ["默认"])[0] if operation.get("tags") else "默认",
                "query_params": {},
                "body_schema": {},
                "response_schema": {},
            }
            # 解析参数
            for param in operation.get("parameters", []):
                if param.get("in") == "query":
                    api["query_params"][param["name"]] = {
                        "type": param.get("schema", {}).get("type", "string"),
                        "required": param.get("required", False),
                        "description": param.get("description", ""),
                    }
            # 解析请求体
            if "requestBody" in operation:
                content = operation["requestBody"].get("content", {})
                for content_type, schema_info in content.items():
                    api["body_schema"] = schema_info.get("schema", {})
                    break
            apis.append(api)
    return apis
