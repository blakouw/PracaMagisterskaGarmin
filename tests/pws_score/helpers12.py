from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / "algorithms/pws_score.py"


def load_module():
    spec = importlib.util.spec_from_file_location("module12_main", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def component_record(date: str, lq=100.0, rec=86.76, cap=92.4, vs=91.35) -> dict[str, Any]:
    return {
        "date": date,
        "lq_score": lq,
        "lq_status": "computed" if lq is not None else "unavailable",
        "rec_score": rec,
        "rec_status": "computed" if rec is not None else "unavailable_insufficient_readiness_data",
        "cap_score": cap,
        "cap_status": "computed" if cap is not None else "unavailable_insufficient_calendar_history",
        "vs_score": vs,
        "vs_status": "computed" if vs is not None else "insufficient_vital_signal_coverage",
    }


def weight_record(
    date: str,
    *,
    lq=100.0,
    rec=86.76,
    cap=92.4,
    vs=91.35,
    weights: dict[str, float] | None = None,
    ready: bool = True,
    available: list[str] | None = None,
    missing: list[str] | None = None,
) -> dict[str, Any]:
    if weights is None:
        weights = {"LQ": 0.2, "REC": 0.35, "CAP": 0.15, "VS": 0.3}
    scores = {"LQ": lq, "REC": rec, "CAP": cap, "VS": vs}
    if available is None:
        available = [component for component, score in scores.items() if score is not None]
    if missing is None:
        missing = [component for component in ["LQ", "REC", "CAP", "VS"] if component not in available]
    base_weights = {"LQ": 0.2, "REC": 0.35, "CAP": 0.15, "VS": 0.3}
    available_sum = sum(base_weights[component] for component in available)
    return {
        "date": date,
        "component_scores": scores,
        "component_source_statuses": {component: ("computed" if scores[component] is not None else "unavailable") for component in scores},
        "available_components": available,
        "missing_components": missing,
        "available_components_count": len(available),
        "available_base_weight_sum": round(available_sum, 6),
        "weights_ready_for_final_pws": ready,
        "weights_readiness_status": "ready" if ready and len(available) == 4 else ("ready_partial_component_coverage" if ready else "insufficient_component_coverage"),
        "deterministic_effective_weights": weights if ready else None,
        "llm_adjustment_eligible": ready,
        "llm_adjustment_applied": False,
        "final_pws_computed": False,
    }


def full_fixture_records():
    return [component_record("2026-01-01")], [weight_record("2026-01-01")]


def setup_root(tmp_path: Path, components=None, weights=None, *, components_ready=True, weights_ready=True, policy=True) -> Path:
    root = tmp_path / "root"
    root.mkdir(parents=True)
    (root / "config").mkdir()
    if policy:
        shutil.copy2(PROJECT_ROOT / "config/pws_score_policy_v1.json", root / "config/pws_score_policy_v1.json")
    for filename in ["pws_policy_v1.json", "pws_components_policy_v1.json", "pws_weights_policy_v1.json", "llm_policy_v1.json"]:
        shutil.copy2(PROJECT_ROOT / "config" / filename, root / "config" / filename)
    if components is not None:
        art = root / "data/pipeline/10_compute_pws_components"
        write_json(art / "pws_components.json", {"module_id": "10_compute_pws_components", "records": components, "ready_for_next_module": components_ready})
        write_json(art / "pws_components_schema.json", {})
        write_json(art / "pws_components_quality_report.json", {})
        write_json(art / "pws_components_lineage.json", {})
    if weights is not None:
        art = root / "data/pipeline/11_compute_pws_weights"
        write_json(art / "pws_weights.json", {"module_id": "11_compute_pws_weights", "records": weights, "ready_for_next_module": weights_ready})
        write_json(art / "pws_weights_schema.json", {})
        write_json(art / "pws_weights_quality_report.json", {})
        write_json(art / "pws_weights_lineage.json", {})
        write_json(art / "pws_weight_guardrails.json", {"module_id": "11_compute_pws_weights", "guardrails_version": "pws_weight_guardrails_v1"})
    return root


def run_module(root: Path) -> int:
    return load_module().run(root)


def output(root: Path) -> Path:
    return root / "data/pipeline/12_compute_pws_score/pws_score.json"


def first_record(root: Path) -> dict[str, Any]:
    return read_json(output(root))["records"][0]
