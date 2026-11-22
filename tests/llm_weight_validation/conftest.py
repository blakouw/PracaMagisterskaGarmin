from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


REAL_ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "13_validate_llm_weight_influence"
COMPONENTS = ["LQ", "REC", "CAP", "VS"]


def load_module():
    path = REAL_ROOT / "algorithms/llm_weight_validation.py"
    spec = importlib.util.spec_from_file_location("module13_main", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def module13():
    return load_module()


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


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    for rel in [
        "config",
        "pipeline/13_validate_llm_weight_influence",
        "data/pipeline/10_compute_pws_components",
        "data/pipeline/11_compute_pws_weights",
        "data/pipeline/12_compute_pws_score",
        "data/local_context",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)
    policy = "llm_assisted_pws_policy_v1.json"
    prompt = "llm_weight_adjustment_prompt_v1.json"
    (root / "config" / policy).write_bytes((REAL_ROOT / "config" / policy).read_bytes())
    (root / "config" / prompt).write_bytes((REAL_ROOT / "ai_prompts" / prompt).read_bytes())
    (root / "config" / "llm_policy_v1.json").write_text(json.dumps({
        "provider": "openai",
        "model": "test-model",
        "endpoint": "https://example.invalid/v1/chat/completions",
        "api_key_environment_variable": "OPENAI_API_KEY",
    }), encoding="utf-8")
    (root / "config" / "pws_score_policy_v1.json").write_text(json.dumps({"policy_version": "pws_score_policy_v1"}), encoding="utf-8")
    components_records = [
        {"date": "2026-01-01", "lq_score": 100.0, "rec_score": 86.0, "cap_score": 90.0, "vs_score": 88.0},
        {"date": "2026-01-02", "lq_score": 74.0, "rec_score": 70.0, "cap_score": None, "vs_score": 83.0},
        {"date": "2026-01-03", "lq_score": 81.0, "rec_score": None, "cap_score": None, "vs_score": 88.0},
    ]
    write_artifact(root, "10_compute_pws_components", "pws_components.json", {"ready_for_next_module": True, "records": components_records})
    write_artifact(root, "10_compute_pws_components", "pws_components_schema.json", {"schema": "test"})
    weight_records = [
        {"date": "2026-01-01", "deterministic_effective_weights": {"LQ": 0.2, "REC": 0.35, "CAP": 0.15, "VS": 0.3}, "overlap_disclosures": ["LQ/REC overlap", "REC/VS overlap"]},
        {"date": "2026-01-02", "deterministic_effective_weights": {"LQ": 0.259268, "REC": 0.409986, "CAP": 0.0, "VS": 0.330746}, "overlap_disclosures": ["partial overlap disclosed"]},
        {"date": "2026-01-03", "deterministic_effective_weights": None},
    ]
    write_artifact(root, "11_compute_pws_weights", "pws_weights.json", {"ready_for_next_module": True, "records": weight_records})
    write_artifact(root, "11_compute_pws_weights", "pws_weights_schema.json", {"schema": "test"})
    write_artifact(root, "11_compute_pws_weights", "pws_weight_guardrails.json", guardrails())
    records = [
        pws_record("2026-01-01", {"LQ": 100.0, "REC": 86.0, "CAP": 90.0, "VS": 88.0}, {"LQ": 0.2, "REC": 0.35, "CAP": 0.15, "VS": 0.3}, ["LQ", "REC", "CAP", "VS"], [], 90.0, "strong", "wysoki"),
        pws_record("2026-01-02", {"LQ": 74.0, "REC": 70.0, "CAP": None, "VS": 83.0}, {"LQ": 0.259268, "REC": 0.409986, "CAP": 0.0, "VS": 0.330746}, ["LQ", "REC", "VS"], ["CAP"], 75.34, "balanced", "stabilny"),
        insufficient_record("2026-01-03"),
    ]
    score_payload = {"module_id": "12_compute_pws_score", "ready_for_next_module": True, "records": records}
    write_artifact(root, "12_compute_pws_score", "pws_score.json", score_payload)
    write_artifact(root, "12_compute_pws_score", "pws_score_schema.json", {"schema": "test"})
    write_artifact(root, "12_compute_pws_score", "pws_score_quality_report.json", {"ready_for_next_module": True})
    write_artifact(root, "12_compute_pws_score", "pws_score_lineage.json", {"lineage": "test"})
    return root


def write_artifact(root: Path, module: str, name: str, payload: Any) -> None:
    path = root / "data" / "pipeline" / module / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def pws_record(date, scores, weights, available, missing, score, label_id, label):
    return {
        "date": date,
        "pws_component_scores": scores,
        "pws_component_statuses": {c: ("computed" if scores.get(c) is not None else "missing") for c in COMPONENTS},
        "pws_deterministic_weights": weights,
        "pws_available_components": available,
        "pws_missing_components": missing,
        "pws_available_components_count": len(available),
        "pws_available_base_weight_sum": 1.0 if len(available) == 4 else 0.85,
        "pws_coverage_ratio": 1.0 if len(available) == 4 else 0.85,
        "pws_coverage_tier": "full" if len(available) == 4 else "partial_eligible",
        "pws_deterministic": score,
        "pws_deterministic_computed": True,
        "pws_label_id": label_id,
        "pws_label": label,
        "llm_adjustment_eligible": True,
        "pws_llm_assisted": None,
        "pws_llm_assisted_computed": False,
        "llm_adjustment_applied": False,
        "llm_used": False,
    }


def insufficient_record(date):
    return {
        "date": date,
        "pws_component_scores": {"LQ": 81.0, "REC": None, "CAP": None, "VS": 88.0},
        "pws_component_statuses": {"LQ": "computed", "REC": "missing", "CAP": "missing", "VS": "computed"},
        "pws_deterministic_weights": None,
        "pws_available_components": ["LQ", "VS"],
        "pws_missing_components": ["REC", "CAP"],
        "pws_available_components_count": 2,
        "pws_available_base_weight_sum": 0.5,
        "pws_coverage_ratio": 0.5,
        "pws_coverage_tier": "insufficient",
        "pws_deterministic": None,
        "pws_deterministic_computed": False,
        "pws_label_id": "insufficient_data",
        "pws_label": "insufficient_data",
        "llm_adjustment_eligible": False,
        "pws_llm_assisted": None,
        "pws_llm_assisted_computed": False,
        "llm_adjustment_applied": False,
        "llm_used": False,
    }


def guardrails():
    return {
        "module_id": "11_compute_pws_weights",
        "future_llm_adjustment": {
            "maximum_absolute_delta_per_component": 0.1,
            "maximum_total_positive_weight_shift": 0.1,
            "maximum_total_absolute_delta": 0.2,
            "weights_must_sum_to": 1.0,
            "no_negative_weights": True,
            "unavailable_component_weight_must_remain_zero": True,
            "must_reapply_overlap_controls_after_proposal": True,
        },
    }


@pytest.fixture
def no_adjustment(module13):
    return FakeLLM(module13, {"decision": "no_adjustment", "reason_summary": "No change.", "proposed_weight_deltas": {"LQ": 0.0, "REC": 0.0, "CAP": 0.0, "VS": 0.0}})
