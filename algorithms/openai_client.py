from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from llm_client import LLMClientError, LLMClientResult


class OpenAIResponsesClient:
    """Minimal Responses API adapter for the external PWS comparison path."""

    def __init__(self, model: str, endpoint: str, api_key: str, timeout_seconds: int = 90) -> None:
        self.model = model
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def complete_json(
        self,
        system_instruction: str,
        structured_context: dict[str, Any],
        response_schema: dict[str, Any],
    ) -> LLMClientResult:
        payload = {
            "model": self.model,
            "store": False,
            "input": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": json.dumps(structured_context, ensure_ascii=False, sort_keys=True),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "pws_weight_proposal",
                    "strict": True,
                    "schema": response_schema,
                }
            },
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
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

        raw_text = self._extract_output_text(response_payload)
        try:
            return LLMClientResult(raw_text=raw_text, parsed_json=json.loads(raw_text))
        except json.JSONDecodeError as exc:
            return LLMClientResult(raw_text=raw_text, parsed_json=None, parse_error=str(exc))

    @staticmethod
    def _extract_output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct
        for item in payload.get("output", []):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    text = content.get("text")
                    if isinstance(text, str) and text.strip():
                        return text
        raise LLMClientError("OpenAI response did not contain output text")
