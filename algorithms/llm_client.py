from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMClientResult:
    raw_text: str
    parsed_json: dict[str, Any] | None
    parse_error: str | None = None


class LLMClientError(RuntimeError):
    pass


class ConfiguredLLMClient:
    """Small provider adapter. Tests pass a fake client and never use the network."""

    def __init__(self, provider: str, model: str, endpoint: str, api_key: str, timeout_seconds: int = 60) -> None:
        self.provider = provider
        self.model = model
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def complete_json(self, system_instruction: str, structured_context: dict[str, Any], temperature: float = 0) -> LLMClientResult:
        if self.provider not in {"openai", "openai_compatible"}:
            raise LLMClientError(f"Unsupported LLM provider: {self.provider}")
        payload = {
            "model": self.model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": json.dumps(structured_context, ensure_ascii=False, sort_keys=True)},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LLMClientError(str(exc)) from exc
        try:
            raw_text = response_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("Provider response did not contain choices[0].message.content") from exc
        try:
            parsed = json.loads(raw_text)
            return LLMClientResult(raw_text=raw_text, parsed_json=parsed)
        except json.JSONDecodeError as exc:
            return LLMClientResult(raw_text=raw_text, parsed_json=None, parse_error=str(exc))
