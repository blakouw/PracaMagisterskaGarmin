from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REAL_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = REAL_ROOT / "pipeline" / "13_validate_llm_weight_influence"


def load_openai_variant():
    path = MODULE_DIR / "openai_variant.py"
    module_dir = str(MODULE_DIR)
    sys.path.insert(0, module_dir)
    previous_main = sys.modules.pop("main", None)
    try:
        spec = importlib.util.spec_from_file_location("module13_openai_variant", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(module_dir)
        sys.modules.pop("main", None)
        if previous_main is not None:
            sys.modules["main"] = previous_main


class CapturingOpenAIClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    def complete_json(self, system_instruction, structured_context, response_schema):
        self.calls.append((system_instruction, structured_context, response_schema))
        return self.response


def prepare_policy(fake_root: Path) -> None:
    source = REAL_ROOT / "config" / "openai_pws_policy_v1.json"
    (fake_root / "config" / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_openai_uses_exact_same_bounded_context_and_local_validation(fake_root: Path):
    prepare_policy(fake_root)
    module = load_openai_variant()
    client = CapturingOpenAIClient({
        "decision": "propose_adjustment",
        "reason_summary": "Synthetic bounded comparison.",
        "proposed_weight_deltas": {"LQ": -0.01, "REC": 0.0, "CAP": 0.01, "VS": 0.0},
    })

    assert module.run(["--enable-openai", "--date", "2026-01-01"], root=fake_root, injected_client=client) == 0
    assert len(client.calls) == 1

    _, context, response_schema = client.calls[0]
    local_policy = read_json(fake_root / "config" / "llm_assisted_pws_policy_v1.json")
    assert set(context) == set(local_policy["allowed_context_fields"])
    assert set(context).isdisjoint(local_policy["forbidden_context_fields"])
    assert response_schema == read_json(fake_root / "config" / "llm_weight_adjustment_prompt_v1.json")["required_response_schema"]

    output = read_json(fake_root / "data" / "pipeline" / module.MODULE_ID / "openai_assisted_pws.json")
    record = output["record"]
    assert output["must_not_replace_primary_score"] is True
    assert output["must_not_replace_local_llm_variant"] is True
    assert record["pws_deterministic"] == 90.0
    assert record["pws_openai_assisted_computed"] is True
    assert record["validated_llm_adjusted_weights"] != record["pws_deterministic_weights"]
    assert sum(record["validated_llm_adjusted_weights"].values()) == 1.0


def test_openai_is_opt_in_and_dry_run_never_calls_provider(fake_root: Path):
    prepare_policy(fake_root)
    module = load_openai_variant()
    client = CapturingOpenAIClient({})

    assert module.run(["--dry-run"], root=fake_root, injected_client=client) == 0
    assert client.calls == []
    output = read_json(fake_root / "data" / "pipeline" / module.MODULE_ID / "openai_assisted_pws.json")
    assert output["computed_count"] == 0
    assert all(record["pws_openai_assisted"] is None for record in output["records"])


def test_single_date_rerun_preserves_cached_history(fake_root: Path):
    prepare_policy(fake_root)
    module = load_openai_variant()
    client = CapturingOpenAIClient({
        "decision": "propose_adjustment",
        "reason_summary": "Synthetic bounded comparison.",
        "proposed_weight_deltas": {"LQ": -0.01, "REC": 0.0, "CAP": 0.01, "VS": 0.0},
    })
    assert module.run(["--enable-openai"], root=fake_root, injected_client=client) == 0
    first = read_json(fake_root / "data" / "pipeline" / module.MODULE_ID / "openai_assisted_pws.json")
    assert [record["date"] for record in first["records"]] == ["2026-01-01", "2026-01-02"]

    assert module.run(["--enable-openai", "--date", "2026-01-01"], root=fake_root, injected_client=client) == 0
    second = read_json(fake_root / "data" / "pipeline" / module.MODULE_ID / "openai_assisted_pws.json")
    assert [record["date"] for record in second["records"]] == ["2026-01-01", "2026-01-02"]
    assert all(record["pws_openai_assisted_computed"] is True for record in second["records"])


def test_openai_audit_contains_no_credentials_or_hidden_reasoning(fake_root: Path):
    prepare_policy(fake_root)
    module = load_openai_variant()
    client = CapturingOpenAIClient({
        "decision": "propose_adjustment",
        "reason_summary": "Synthetic bounded comparison.",
        "proposed_weight_deltas": {"LQ": 0.0, "REC": -0.01, "CAP": 0.0, "VS": 0.01},
    })
    assert module.run(["--enable-openai", "--date", "2026-01-01"], root=fake_root, injected_client=client) == 0
    audit_path = fake_root / "data" / "pipeline" / module.MODULE_ID / "openai_conversations" / "2026-01-01.json"
    audit_text = audit_path.read_text(encoding="utf-8")
    audit = json.loads(audit_text)
    assert "OPENAI_API_KEY" not in audit_text
    assert "test-key" not in audit_text
    assert audit["hidden_reasoning_requested_or_stored"] is False
    assert audit["raw_private_data_sent"] is False

