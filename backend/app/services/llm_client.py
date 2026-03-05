"""统一LLM客户端 - 支持 OpenAI 兼容格式、通义千问、文心一言等"""
import time
import json
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from app.core.config import settings


class LLMClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model = model or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """发送聊天请求，返回文本结果"""
        start_time = time.time()
        try:
            kwargs = dict(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"LLM call success | model={self.model} | duration={duration_ms}ms | tokens={response.usage.total_tokens}")
            return content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def chat_json(self, messages: list[dict], **kwargs) -> dict:
        """发送请求并解析 JSON 结果"""
        content = await self.chat(messages, json_mode=True, **kwargs)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            raise ValueError(f"无法解析LLM返回的JSON: {content[:200]}")

    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        """流式输出"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 全局默认客户端
_default_client: Optional[LLMClient] = None


def get_llm_client(api_key: str = None, base_url: str = None, model: str = None) -> LLMClient:
    global _default_client
    if api_key or base_url or model:
        return LLMClient(api_key=api_key, base_url=base_url, model=model)
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
