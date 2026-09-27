"""Клиент LLM (Ollama или OpenAI-совместимый API) с fallback.

Клиент реализован на stdlib (`urllib`), без внешних SDK. Если провайдер
недоступен (нет сервера, нет ключа, сеть, таймаут) — `generate` возвращает
`None`, и агенты переключаются на rule-based скоринг.
"""

from __future__ import annotations

import json
import re
import urllib.request

from ai_recruiter.config import config


class LLMClient:
    """Минимальный клиент с поддержкой Ollama и OpenAI-совместимого API."""

    def __init__(self) -> None:
        self.provider = config.llm_provider
        self.model = (
            config.ollama_model if self.provider == "ollama" else config.openai_model
        )

    def is_configured(self) -> bool:
        if self.provider == "openai":
            return bool(config.openai_api_key)
        return True

    def generate(self, prompt: str) -> str | None:
        """Возвращает текст ответа или None при любой ошибке."""
        if not self.is_configured():
            return None
        try:
            if self.provider == "ollama":
                return self._ollama(prompt)
            if self.provider == "openai":
                return self._openai(prompt)
        except Exception:  # noqa: BLE001 — любая ошибка => fallback
            return None
        return None

    def complete_json(self, prompt: str) -> dict | None:
        """Просит LLM вернуть JSON и парсит его. None при неудаче."""
        text = self.generate(prompt)
        if not text:
            return None
        return extract_json(text)

    def _ollama(self, prompt: str) -> str:
        url = config.ollama_base_url.rstrip("/") + "/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        data = self._post_json(url, payload)
        return data.get("response", "")

    def _openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {config.openai_api_key}"}
        data = self._post_json(url, payload, headers=headers)
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
        headers = dict(headers or {})
        headers.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers=headers
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))


def extract_json(text: str) -> dict | None:
    """Извлекает первый JSON-объект из произвольного текста ответа LLM."""
    if not text:
        return None
    start = text.find("{")
    if start == -1:
        return None
    for end in range(len(text), start, -1):
        if text[end - 1] == "}":
            candidate = text[start:end]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return None


# Разовый экземпляр для использования агентами (можно переопределить в тестах).
client = LLMClient()


__all__ = ["LLMClient", "extract_json", "client"]
