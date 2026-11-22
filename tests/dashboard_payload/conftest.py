from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REAL_ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "15_build_dashboard_payload"
ASSISTED_ID = "13_validate_llm_weight_influence"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def load_module():
    path = REAL_ROOT / "pipeline" / MODULE_ID / "main.py"
    spec = importlib.util.spec_from_file_location("module15_main", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def module15():
    return load_module()


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    for rel in [
        "config",
        "data/pipeline/08_compute_load_metrics",
        "data/pipeline/09_compute_readiness",
        "data/pipeline/10_compute_pws_components",
        "data/pipeline/11_compute_pws_weights",
        "data/pipeline/12_compute_pws_score",
        f"data/pipeline/{ASSISTED_ID}",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "config/dashboard_payload_policy_v1.json").write_text((REAL_ROOT / "config/dashboard_payload_policy_v1.json").read_text(encoding="utf-8"), encoding="utf-8")
    write_module_artifacts(root)
    return root


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def artifact(root: Path, module: str, name: str, payload: Any) -> None:
    write_json(root / "data" / "pipeline" / module / name, payload)


def base_payload(module_id: str, records: list[dict[str, Any]], status="computed") -> dict[str, Any]:
    return {"module_id": module_id, "status": status, "ready_for_next_module": True, "records": records}


def write_module_artifacts(root: Path) -> None:
    dates = ["2026-01-01", "2026-01-02", "2026-01-03"]
    load = [
        {"date": d, "acwr_ewma": i + 1.01, "acwr_rolling": i + 1.02, "acute_ewma_7d": 100 + i, "chronic_ewma_28d": 200 + i, "monotony_7d": 2 + i, "strain_7d": 300 + i}
        for i, d in enumerate(dates)
    ]
    readiness = [
        {"date": "2026-01-01", "readiness_score": 86.0, "readiness_status": "computed", "readiness_label_id": "high", "readiness_label": "wysoka", "readiness_coverage_ratio": 1.0, "available_readiness_components": ["sleep"], "missing_readiness_components": []},
        {"date": "2026-01-02", "readiness_score": 70.0, "readiness_status": "computed", "readiness_label_id": "medium", "readiness_label": "srednia", "readiness_coverage_ratio": 0.8, "available_readiness_components": ["sleep"], "missing_readiness_components": ["stress"]},
        {"date": "2026-01-03", "readiness_score": None, "readiness_status": "insufficient_data", "readiness_label_id": "insufficient_data", "readiness_label": "insufficient_data", "readiness_coverage_ratio": 0.2, "available_readiness_components": [], "missing_readiness_components": ["sleep"]},
    ]
    components = [
        {"date": "2026-01-01", "lq_score": 100.0, "lq_status": "computed", "rec_score": 86.0, "rec_status": "computed", "cap_score": 90.0, "cap_status": "computed", "vs_score": 88.0, "vs_status": "computed"},
        {"date": "2026-01-02", "lq_score": 74.0, "lq_status": "computed", "rec_score": 70.0, "rec_status": "computed", "cap_score": None, "cap_status": "missing", "vs_score": 83.0, "vs_status": "computed"},
        {"date": "2026-01-03", "lq_score": 81.0, "lq_status": "computed", "rec_score": None, "rec_status": "missing", "cap_score": None, "cap_status": "missing", "vs_score": 88.0, "vs_status": "computed"},
    ]
    weights = [
        {"date": "2026-01-01", "base_component_weights": {"LQ": .2, "REC": .35, "CAP": .15, "VS": .3}, "deterministic_effective_weights": {"LQ": .2, "REC": .35, "CAP": .15, "VS": .3}, "weights_ready_for_final_pws": True, "weights_readiness_status": "ready", "deterministic_movement_limits_applied": False, "overlap_controls_applied": [], "llm_adjustment_eligible": True},
        {"date": "2026-01-02", "base_component_weights": {"LQ": .2, "REC": .35, "CAP": .15, "VS": .3}, "deterministic_effective_weights": {"LQ": .259268, "REC": .409986, "CAP": 0.0, "VS": .330746}, "weights_ready_for_final_pws": True, "weights_readiness_status": "ready_partial_component_coverage", "deterministic_movement_limits_applied": False, "overlap_controls_applied": [], "llm_adjustment_eligible": True},
        {"date": "2026-01-03", "base_component_weights": {"LQ": .2, "REC": .35, "CAP": .15, "VS": .3}, "deterministic_effective_weights": None, "weights_ready_for_final_pws": False, "weights_readiness_status": "insufficient_component_coverage", "deterministic_movement_limits_applied": False, "overlap_controls_applied": [], "llm_adjustment_eligible": False},
    ]
    pws = [
        pws_record("2026-01-01", 90.0, True, "strong", "wysoki", "full", False, ["LQ","REC","CAP","VS"], []),
        pws_record("2026-01-02", 75.34, True, "balanced", "stabilny", "partial_eligible", True, ["LQ","REC","VS"], ["CAP"]),
        pws_record("2026-01-03", None, False, "insufficient_data", "insufficient_data", "insufficient", False, ["LQ","VS"], ["REC","CAP"]),
    ]
    artifact(root, "08_compute_load_metrics", "load_metrics.json", base_payload("08_compute_load_metrics", load))
    artifact(root, "08_compute_load_metrics", "load_metrics_quality_report.json", {"ready_for_next_module": True, "status": "computed"})
    artifact(root, "09_compute_readiness", "readiness.json", base_payload("09_compute_readiness", readiness))
    artifact(root, "09_compute_readiness", "readiness_quality_report.json", {"ready_for_next_module": True, "status": "computed"})
    artifact(root, "10_compute_pws_components", "pws_components.json", base_payload("10_compute_pws_components", components))
    artifact(root, "10_compute_pws_components", "pws_components_quality_report.json", {"ready_for_next_module": True, "status": "computed"})
    artifact(root, "11_compute_pws_weights", "pws_weights.json", base_payload("11_compute_pws_weights", weights))
    artifact(root, "11_compute_pws_weights", "pws_weights_quality_report.json", {"ready_for_next_module": True, "status": "computed"})
    artifact(root, "12_compute_pws_score", "pws_score.json", base_payload("12_compute_pws_score", pws, status="computed_with_partial_coverage"))
    artifact(root, "12_compute_pws_score", "pws_score_quality_report.json", {"ready_for_next_module": True, "status": "computed_with_partial_coverage"})


def pws_record(date, score, computed, label_id, label, tier, partial, available, missing):
    scores = {
        "2026-01-01": {"LQ": 100.0, "REC": 86.0, "CAP": 90.0, "VS": 88.0},
        "2026-01-02": {"LQ": 74.0, "REC": 70.0, "CAP": None, "VS": 83.0},
        "2026-01-03": {"LQ": 81.0, "REC": None, "CAP": None, "VS": 88.0},
    }[date]
    weights = {"LQ": .2, "REC": .35, "CAP": .15, "VS": .3} if date == "2026-01-01" else ({"LQ": .259268, "REC": .409986, "CAP": 0.0, "VS": .330746} if date == "2026-01-02" else None)
    return {
        "date": date,
        "pws_component_scores": scores,
        "pws_deterministic_weights": weights,
        "pws_weighted_contributions": {"LQ": 1.0} if computed else {},
        "pws_available_components": available,
        "pws_missing_components": missing,
        "pws_available_components_count": len(available),
        "pws_available_base_weight_sum": 1.0 if tier == "full" else (0.85 if tier == "partial_eligible" else 0.5),
        "pws_coverage_ratio": 1.0 if tier == "full" else (0.85 if tier == "partial_eligible" else 0.5),
        "pws_coverage_tier": tier,
        "pws_computed_from_partial_coverage": partial,
        "pws_deterministic": score,
        "pws_deterministic_computed": computed,
        "pws_status": "computed_full_coverage" if tier == "full" else ("computed_partial_eligible_coverage" if computed else "not_computed_insufficient_component_coverage"),
        "pws_label_id": label_id,
        "pws_label": label,
        "llm_adjustment_eligible": computed,
    }


def write_assisted(root: Path, status="completed_assisted_score_computed", date="2026-01-03", computed=True):
    record = {
        "date": date,
        "pws_deterministic": 75.34 if date == "2026-01-02" else 90.0,
        "pws_llm_assisted": 89.9 if computed else None,
        "pws_llm_assisted_computed": computed,
        "pws_llm_assisted_label_id": "strong" if computed else None,
        "pws_llm_assisted_label": "wysoki" if computed else None,
        "pws_llm_assisted_delta_from_deterministic": -0.1 if computed else None,
        "validated_llm_adjusted_weights": {"LQ": .19, "REC": .35, "CAP": .16, "VS": .3} if computed else None,
        "llm_adjustment_applied": computed,
    }
    artifact(root, ASSISTED_ID, "llm_assisted_pws.json", {"module_id": ASSISTED_ID, "status": status, "ready_for_next_module": True, "record": record})
    artifact(root, ASSISTED_ID, "llm_assisted_pws_quality_report.json", {"status": status, "ready_for_next_module": True})
    artifact(root, ASSISTED_ID, "llm_validation_report.json", {"validation_status": "accepted" if computed and status == "completed_assisted_score_computed" else "not_applicable"})


def read_output(root: Path, name="dashboard_payload.json"):
    return json.loads((root / "data" / "pipeline" / MODULE_ID / name).read_text(encoding="utf-8"))


def run_module(module15, root: Path):
    return module15.build(root)[0]
