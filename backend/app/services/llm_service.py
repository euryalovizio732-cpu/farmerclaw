"""LLM 抽象层 — 支持 DashScope (通义千问/豆包) 及 OpenAI 兼容 API

复用自 CrossClaw LLM Service，精简版本。
"""

import json
import re
import time
import hashlib
import threading
from collections import OrderedDict
from typing import Any, Optional

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from app.config import get_settings

settings = get_settings()


class _LLMResponseCache:
    def __init__(self, max_entries: int = 256, ttl_seconds: int = 1800):
        self._max = max_entries
        self._ttl = ttl_seconds
        self._store: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._lock = threading.Lock()

    def _key(self, system: str, user: str, model: str) -> str:
        raw = f"{model}\x00{system}\x00{user}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, system: str, user: str, model: str) -> Optional[str]:
        key = self._key(system, user, model)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            exp, val = entry
            if time.monotonic() > exp:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return val

    def set(self, system: str, user: str, model: str, value: str) -> None:
        key = self._key(system, user, model)
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, value)
            self._store.move_to_end(key)
            while len(self._store) > self._max:
                self._store.popitem(last=False)


_cache = _LLMResponseCache()


class LLMService:
    """统一 LLM 调用入口 — 优先 DashScope，回退 OpenAI"""

    def __init__(self):
        self._model = settings.llm_model
        self._api_key = settings.dashscope_api_key
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _call_dashscope(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        try:
            import dashscope
            from dashscope import Generation

            dashscope.api_key = self._api_key
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            extra = {"result_format": "message"}

            if json_mode:
                extra["result_format"] = "message"
            response = Generation.call(
                model=self._model,
                messages=messages,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                **extra,
            )
            if response.status_code != 200:
                raise RuntimeError(f"DashScope error: {response.code} {response.message}")
            choice = response.output.choices[0]
            finish = getattr(choice, "finish_reason", "")
            if finish == "length":
                logger.warning("DashScope 输出被截断(length)，考虑增加max_tokens或减少输出字段")
            return choice.message.content.strip()
        except ImportError:
            logger.warning("dashscope 未安装，尝试 OpenAI 兼容接口")
            return self._call_openai_compatible(system_prompt, user_prompt, json_mode)

    def _call_openai_compatible(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        from openai import OpenAI

        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        client = OpenAI(api_key=self._api_key, base_url=base_url)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()

    def chat(self, system_prompt: str, user_prompt: str, use_cache: bool = True) -> str:
        """同步文本对话"""
        if use_cache:
            cached = _cache.get(system_prompt, user_prompt, self._model)
            if cached:
                logger.debug("LLM cache hit")
                return cached
        try:
            result = self._call_dashscope(system_prompt, user_prompt)
        except RetryError as exc:
            logger.error("LLM 调用失败（重试耗尽）: {}", exc)
            raise RuntimeError("AI服务暂时不可用，请稍后重试") from exc

        if use_cache:
            _cache.set(system_prompt, user_prompt, self._model, result)
        return result

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict | list:
        """调用 LLM 并解析返回的 JSON（支持对象和数组），强制启用json_mode"""
        try:
            raw = self._call_dashscope(
                system_prompt,
                user_prompt + "\n\n请严格按照JSON格式返回，不要添加任何说明文字或Markdown标记。",
                json_mode=True,
            )
        except RetryError as exc:
            logger.error("LLM 调用失败（重试耗尽）: {}", exc)
            raise RuntimeError("AI服务暂时不可用，请稍后重试") from exc
        cleaned = self._extract_json(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # 第二次尝试：修复常见问题（末尾逗号、单引号）
            repaired = self._repair_json(cleaned)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                logger.warning("LLM 返回非标准 JSON，原始内容: {}", raw[:400])
                return {"raw_output": raw}

    @staticmethod
    def _extract_json(text: str) -> str:
        """从 LLM 原始输出中提取 JSON 字符串"""
        # 1. 剥离 Markdown 代码块 ``` ... ``` 或 ```json ... ```
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()

        # 2. 优先匹配数组 [...]，再匹配对象 {...}
        arr_match = re.search(r"\[[\s\S]*\]", text)
        obj_match = re.search(r"\{[\s\S]*\}", text)

        if arr_match and obj_match:
            # 两者都有，取先出现的
            if arr_match.start() < obj_match.start():
                return arr_match.group(0)
            return obj_match.group(0)
        if arr_match:
            return arr_match.group(0)
        if obj_match:
            return obj_match.group(0)
        return text.strip()

    @staticmethod
    def _repair_json(text: str) -> str:
        """修复常见 JSON 语法错误"""
        # 末尾逗号（对象和数组）
        text = re.sub(r",\s*([}\]])", r"\1", text)
        # 单引号→双引号（简单情况）
        text = text.replace("'", '"')
        return text


llm_service = LLMService()
