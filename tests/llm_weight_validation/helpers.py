from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "13_validate_llm_weight_influence"


class FakeLLM:
    def __init__(self, module, parsed: dict[str, Any] | None = None, raw: str = "", parse_error: str | None = None):
        self.module = module
        self.parsed = parsed
        self.raw = raw or json.dumps(parsed or {})
        self.parse_error = parse_error
        self.calls = 0

    def complete_json(self, system_instruction, structured_context, temperature=0):
        self.calls += 1
        return self.module.LLMClientResult(raw_text=self.raw, parsed_json=self.parsed, parse_error=self.parse_error)


def read_output(root: Path, name="llm_assisted_pws.json"):
    return json.loads((root / "data" / "pipeline" / MODULE_ID / name).read_text(encoding="utf-8"))
