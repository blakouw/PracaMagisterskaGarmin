from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REAL_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = REAL_ROOT / "pipeline" / "13_validate_llm_weight_influence"


def load_client_module():
    module_dir = str(MODULE_DIR)
    sys.path.insert(0, module_dir)
    try:
        spec = importlib.util.spec_from_file_location("module13_openai_client", MODULE_DIR / "openai_client.py")
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(module_dir)


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        proposal = {
            "decision": "propose_adjustment",
            "reason_summary": "Synthetic response.",
            "proposed_weight_deltas": {"LQ": -0.01, "REC": 0.0, "CAP": 0.01, "VS": 0.0},
        }
        return json.dumps({"output_text": json.dumps(proposal)}).encode("utf-8")


def test_responses_api_request_is_strict_non_persistent_and_bounded(monkeypatch):
    module = load_client_module()
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    client = module.OpenAIResponsesClient(
        model="test-model",
        endpoint="https://api.openai.com/v1/responses",
        api_key="synthetic-test-key",
        timeout_seconds=12,
    )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"decision": {"type": "string"}},
        "required": ["decision"],
    }
    result = client.complete_json("Bounded system instruction", {"date": "2026-01-01"}, schema)

    payload = captured["payload"]
    assert payload["store"] is False
    assert payload["model"] == "test-model"
    assert payload["input"] == [
        {"role": "system", "content": "Bounded system instruction"},
        {"role": "user", "content": '{"date": "2026-01-01"}'},
    ]
    assert payload["text"]["format"] == {
        "type": "json_schema",
        "name": "pws_weight_proposal",
        "strict": True,
        "schema": schema,
    }
    assert captured["authorization"] == "Bearer synthetic-test-key"
    assert captured["timeout"] == 12
    assert result.parsed_json["decision"] == "propose_adjustment"

