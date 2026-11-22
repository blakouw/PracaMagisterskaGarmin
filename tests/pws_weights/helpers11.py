from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / "pipeline/11_compute_pws_weights/main.py"


def load_module():
    spec = importlib.util.spec_from_file_location("module11_main", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def component_record(
    date: str,
    lq: float | None = 100.0,
    rec: float | None = 86.0,
    cap: float | None = 90.0,
    vs: float | None = 88.0,
    *,
    lq_source_metric: str | None = "acwr_ewma",
    rec_coverage: float | None = 1.0,
    cap_window_complete: bool | None = True,
    vs_coverage: float | None = 1.0,
) -> dict[str, Any]:
    return {
        "date": date,
        "lq_score": lq,
        "lq_status": "computed" if lq is not None else "unavailable",
        "lq_source_metric": lq_source_metric,
        "rec_score": rec,
        "rec_status": "computed" if rec is not None else "unavailable_insufficient_readiness_data",
        "rec_source_coverage_ratio": rec_coverage,
        "cap_score": cap,
        "cap_status": "computed" if cap is not None else "unavailable_insufficient_calendar_history",
        "cap_window_complete": cap_window_complete,
        "vs_score": vs,
        "vs_status": "computed" if vs is not None else "insufficient_vital_signal_coverage",
        "vs_coverage_ratio": vs_coverage,
        "known_component_overlaps": [
            "LQ and REC may both contain load-balance signal exposure through ACWR.",
            "REC and VS may both use HRV and RHR signals for different interpretations.",
        ],
    }


def setup_root(tmp_path: Path, records: list[dict[str, Any]] | None = None, *, ready: bool = True, policy: bool = True) -> Path:
    root = tmp_path / "root"
    root.mkdir(parents=True)
    (root / "config").mkdir()
    if policy:
        shutil.copy2(PROJECT_ROOT / "config/pws_weights_policy_v1.json", root / "config/pws_weights_policy_v1.json")
    for filename in ["pws_policy_v1.json", "llm_policy_v1.json", "pws_components_policy_v1.json"]:
        shutil.copy2(PROJECT_ROOT / "config" / filename, root / "config" / filename)
    if records is not None:
        artifact_dir = root / "data/pipeline/10_compute_pws_components"
        artifact_dir.mkdir(parents=True)
        write_json(artifact_dir / "pws_components.json", {
            "module_id": "10_compute_pws_components",
            "policy_version": "pws_components_policy_v1",
            "status": "computed",
            "records": records,
            "ready_for_next_module": ready,
        })
        write_json(artifact_dir / "pws_components_schema.json", {"module_id": "10_compute_pws_components"})
        write_json(artifact_dir / "pws_components_quality_report.json", {"module_id": "10_compute_pws_components"})
        write_json(artifact_dir / "pws_components_lineage.json", {"module_id": "10_compute_pws_components"})
    return root


def run_module(root: Path) -> int:
    return load_module().run(root)


def output(root: Path) -> Path:
    return root / "data/pipeline/11_compute_pws_weights/pws_weights.json"


def first_record(root: Path) -> dict[str, Any]:
    return read_json(output(root))["records"][0]


def errors(root: Path) -> dict[str, Any]:
    return read_json(root / "data/pipeline/11_compute_pws_weights/errors.json")
