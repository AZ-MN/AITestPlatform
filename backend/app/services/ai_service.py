"""
AI 多模型适配器：统一封装 OpenAI / Claude / 通义千问 / 智谱 / DeepSeek 等供应商
"""
import json
import re
from typing import List, Dict, Optional, AsyncIterator
from app.core.config import settings


class AIServiceError(Exception):
    pass


class AIAdapter:
    """统一 AI 调用接口"""

    def __init__(self, provider: str = None, api_key: str = None,
                 api_base_url: str = None, model: str = None, temperature: float = 0.3):
        self.provider = provider or settings.DEFAULT_AI_PROVIDER
        self.temperature = temperature

        # 根据供应商选择配置
        if self.provider == "openai":
            self.api_key = api_key or settings.OPENAI_API_KEY
            self.api_base_url = api_base_url or settings.OPENAI_BASE_URL
            self.model = model or settings.OPENAI_DEFAULT_MODEL
        elif self.provider == "anthropic":
            self.api_key = api_key or settings.ANTHROPIC_API_KEY
            self.api_base_url = api_base_url
            self.model = model or settings.ANTHROPIC_DEFAULT_MODEL
        elif self.provider == "tongyi":
            self.api_key = api_key or settings.TONGYI_API_KEY
            self.api_base_url = api_base_url or settings.TONGYI_BASE_URL
            self.model = model or settings.TONGYI_DEFAULT_MODEL
        elif self.provider == "zhipu":
            self.api_key = api_key or settings.ZHIPU_API_KEY
            self.api_base_url = api_base_url or settings.ZHIPU_BASE_URL
            self.model = model or settings.ZHIPU_DEFAULT_MODEL
        elif self.provider == "deepseek":
            self.api_key = api_key or settings.DEEPSEEK_API_KEY
            self.api_base_url = api_base_url or settings.DEEPSEEK_BASE_URL
            self.model = model or settings.DEEPSEEK_DEFAULT_MODEL
        else:
            self.api_key = api_key
            self.api_base_url = api_base_url
            self.model = model or "gpt-4o"

    async def chat(self, system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
        """统一的 chat 接口"""
        if self.provider == "anthropic":
            return await self._call_anthropic(system_prompt, user_message, max_tokens)
        else:
            # openai-compatible：tongyi/zhipu/deepseek 均支持 openai SDK 格式
            return await self._call_openai_compatible(system_prompt, user_message, max_tokens)

    async def _call_openai_compatible(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        if not self.api_key:
            raise AIServiceError(f"未配置 {self.provider} API Key，请在设置页面添加模型配置")
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.api_base_url)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise AIServiceError(f"{self.provider} 调用失败: {str(e)}")

    async def _call_anthropic(self, system_prompt: str, user_message: str, max_tokens: int) -> str:
        if not self.api_key:
            raise AIServiceError("未配置 Anthropic API Key")
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            message = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return message.content[0].text
        except Exception as e:
            raise AIServiceError(f"Anthropic 调用失败: {str(e)}")


# ──────────────────────────────────────────────────────────────
#  测试用例生成专用 Prompt
# ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT_CASE_GEN = """你是一位资深测试架构师，精通等价类划分、边界值分析、错误推测法、因果图法、场景法等经典测试设计方法。
你的职责是根据用户给出的需求点，生成标准化、覆盖全面的测试用例。

【输出格式要求】
必须严格返回 JSON 数组，每个元素为一条测试用例对象，字段如下：
{
  "module": "所属模块",
  "title": "用例标题（简洁描述测试场景，不超过60字）",
  "case_level": "P0/P1/P2/P3",
  "test_type": "functional/api/unit/regression",
  "stage": "smoke/integration/system/regression",
  "preconditions": "前置条件（字符串）",
  "steps": [
    {"step": 1, "action": "操作描述", "expected": "预期结果"}
  ],
  "remarks": "备注（可为空字符串）"
}

【用例等级说明】
- P0：核心业务流程，冒烟测试必须覆盖
- P1：主要功能场景，高优先级
- P2：边界值/异常场景，中优先级
- P3：兼容性/低频场景，低优先级

【覆盖场景要求】
每个需求点必须覆盖：正常流程、异常输入、边界条件、权限控制（如适用）

【约束】
- 不得输出 JSON 以外的任何文字
- steps 数组每项都必须有明确的 action 和 expected
- 避免重复用例
"""

SYSTEM_PROMPT_REQ_PARSE = """你是一位资深业务分析师，擅长从需求文档中提取结构化需求点。
根据输入的需求文档内容，提取所有需求点，以 JSON 数组格式返回：
[
  {
    "id": "REQ-001",
    "title": "需求标题（简洁，不超过40字）",
    "description": "需求详细描述",
    "priority": "P0/P1/P2/P3",
    "module": "所属模块",
    "conditions": ["前置条件1", "前置条件2"],
    "rules": ["业务规则1", "业务规则2"]
  }
]
注意：只返回 JSON，不要包含任何其他文字。
"""

SYSTEM_PROMPT_API_CASE = """你是一位资深接口测试工程师。
根据输入的接口信息，生成完整的接口测试用例，以 JSON 数组格式返回：
[
  {
    "module": "接口所属模块",
    "title": "用例标题",
    "case_level": "P0/P1/P2/P3",
    "test_type": "api",
    "stage": "integration",
    "preconditions": "前置条件",
    "steps": [
      {
        "step": 1,
        "action": "发送请求：METHOD URL，请求体：{...}",
        "expected": "HTTP状态码：200，响应体包含：{...}"
      }
    ],
    "remarks": ""
  }
]
覆盖：正向用例、参数缺失、参数越界、未授权、错误参数类型、并发场景（如适用）。
只返回 JSON 数组，不包含任何其他文字。
"""


def build_case_gen_prompt(req_points: List[Dict], test_type: str,
                           granularity: str, cover_scenarios: List[str],
                           custom_instructions: str = "") -> str:
    granularity_desc = {"coarse": "粗颗粒度（按业务流程）", "medium": "中颗粒度（按功能点）", "fine": "细颗粒度（按单一场景）"}
    scenario_map = {
        "normal": "正常流程",
        "exception": "异常/错误场景",
        "boundary": "边界值",
        "permission": "权限控制",
        "compatibility": "兼容性",
        "security": "数据安全",
    }
    scenarios_desc = "、".join(scenario_map.get(s, s) for s in cover_scenarios)

    prompt = f"""请根据以下需求点，生成{granularity_desc.get(granularity, '中颗粒度')}的测试用例。
测试类型：{test_type}
覆盖场景：{scenarios_desc}
"""
    if custom_instructions:
        prompt += f"补充说明：{custom_instructions}\n"

    prompt += "\n需求点清单：\n"
    for rp in req_points:
        prompt += f"\n【{rp.get('id', 'REQ')}】{rp.get('title', '')}\n"
        prompt += f"  描述：{rp.get('description', '')}\n"
        if rp.get('module'):
            prompt += f"  模块：{rp.get('module')}\n"
        if rp.get('rules'):
            prompt += f"  业务规则：{'; '.join(str(r) for r in rp['rules'])}\n"
        if rp.get('conditions'):
            prompt += f"  前置条件：{'; '.join(str(c) for c in rp['conditions'])}\n"

    return prompt


def parse_ai_json_response(raw: str) -> list:
    """安全解析 AI 返回的 JSON，处理 markdown 代码块等情况"""
    # 去除 markdown 代码块
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # 尝试直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 尝试提取第一个 JSON 数组
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return []
