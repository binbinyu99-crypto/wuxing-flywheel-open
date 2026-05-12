"""
五行飞轮 LLM 路由器
支持多模型路由，每个Agent可使用不同的LLM提供商。
"""

import os
import httpx
import json
import asyncio
from typing import Optional

# 模型路由配置
DEFAULT_ROUTING = {
    "qinglong": "deepseek",
    "zhuque": "deepseek",
    "diting": "kimi",
    "baihu": "deepseek",
    "xuanwu": "deepseek",
    "verifier": "kimi",
}

# 提供商配置
PROVIDERS = {
    "deepseek": {
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "model": "deepseek-chat",
    },
    "openai": {
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": "gpt-4o",
    },
    "kimi": {
        "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
        "api_key": os.getenv("KIMI_API_KEY", ""),
        "model": "moonshot-v1-128k",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "model": "claude-sonnet-4-20250514",
    },
}

# 连接池
_client = httpx.AsyncClient(timeout=120.0, limits=httpx.Limits(max_connections=20))
_semaphore = asyncio.Semaphore(16)


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model_key: str = "deepseek",
    temperature: float = 0.7,
    max_tokens: int = 16384,
) -> dict:
    """
    调用LLM，返回 {"text": "...", "model": "...", "tokens": N}
    """
    provider = PROVIDERS.get(model_key, PROVIDERS["deepseek"])

    if not provider["api_key"]:
        return {"text": f"[ERROR] No API key configured for {model_key}", "model": model_key, "tokens": 0}

    headers = {
        "Authorization": f"Bearer {provider['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": provider["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with _semaphore:
        try:
            response = await _client.post(
                f"{provider['base_url']}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            text = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)

            return {"text": text, "model": provider["model"], "tokens": tokens}

        except Exception as e:
            return {"text": f"[ERROR] LLM call failed: {str(e)}", "model": model_key, "tokens": 0}


def get_routing() -> dict:
    """获取当前模型路由配置"""
    return DEFAULT_ROUTING.copy()
