from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "16_persist_local_snapshot"
SOURCE_MODULE = "15_build_dashboard_payload"

def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def policy_payload() -> dict[str, Any]:
    return {
        "policy_version": "dashboard_snapshot_policy_v1",
        "source_module": SOURCE_MODULE,
        "required_source_files": ["dashboard_payload.json", "dashboard_time_series.csv", "dashboard_payload_schema.json", "dashboard_payload_quality_report.json", "dashboard_payload_lineage.json"],
        "optional_source_files": ["dashboard_time_series.parquet"],
        "hash_policy": {"algorithm": "sha256"},
        "publication_policy": {"use_staging_before_publish": True, "preserve_history_if_current_publish_fails": True},
    }


def payload_fixture(*, ready=True, quality_ready=True, latest_date="2026-01-03", primary_type="deterministic", assisted_available=False, assisted_replaces=False, include_sections=True, primary_score=None) -> tuple[dict[str, Any], dict[str, Any]]:
    primary = {
        "score_type": primary_type,
        "score_field": "pws_deterministic",
        "score": primary_score,
        "computed": primary_score is not None,
        "status": "not_computed_insufficient_component_coverage" if primary_score is None else "computed_full_coverage",
        "label_id": "insufficient_data" if primary_score is None else "balanced",
        "label": "insufficient_data" if primary_score is None else "stabilny",
        "coverage_tier": "insufficient" if primary_score is None else "full",
        "display_disclosure": "Primary deterministic PWS calculated from validated deterministic component weights.",
    }
    assisted = {
        "available": assisted_available,
        "computed": assisted_available,
        "status": "available_validated_assisted_variant" if assisted_available else "not_available_no_assisted_artifact",
        "must_not_replace_primary_score": not assisted_replaces,
        "display_disclosure": "Optional variant only.",
    }
    if assisted_available:
        assisted.update({"score_type": "llm_assisted", "score": 74.0, "label_id": "balanced", "label": "stabilny"})
    payload = {
        "module_id": SOURCE_MODULE,
        "status": "built",
        "metadata": {"latest_date": latest_date, "records_count": 1},
        "current_state": {"date": latest_date, "primary_pws": primary, "optional_assisted_pws": assisted},
        "time_series": [{"date": latest_date, "pws_deterministic": primary_score}],
        "quality_and_coverage": {"records_count": 1},
        "disclosures": {"primary_score": "Deterministic PWS is primary."},
        "ready_for_next_module": ready,
    }
    if not include_sections:
        payload.pop("time_series")
    quality = {"module_id": SOURCE_MODULE, "status": "built", "ready_for_next_module": quality_ready}
    return payload, quality


def write_dashboard_fixture(root: Path, **kwargs: Any) -> Path:
    parquet = bool(kwargs.pop("parquet", False))
    source = root / "data" / "pipeline" / SOURCE_MODULE
    payload, quality = payload_fixture(**kwargs)
    write_json(root / "config" / "dashboard_snapshot_policy_v1.json", policy_payload())
    write_json(root / "config" / "dashboard_payload_policy_v1.json", {"policy_version": "dashboard_payload_policy_v1"})
    write_json(source / "dashboard_payload.json", payload)
    write_json(source / "dashboard_payload_quality_report.json", quality)
    write_json(source / "dashboard_payload_schema.json", {"schema_version": "dashboard_payload_schema_v1"})
    write_json(source / "dashboard_payload_lineage.json", {"lineage_version": "dashboard_payload_lineage_v1"})
    (source / "dashboard_time_series.csv").parent.mkdir(parents=True, exist_ok=True)
    (source / "dashboard_time_series.csv").write_text("date,pws_deterministic\n%s,\n" % payload["metadata"].get("latest_date", "2026-01-03"), encoding="utf-8")
    if parquet:
        (source / "dashboard_time_series.parquet").write_bytes(b"PAR1safe-fixture")
    return source


def run_module(root: Path, module) -> str:
    module.STARTED_AT = module.iso()
    try:
        status, _snapshot_id = module.publish_snapshot(root)
        return status
    except module.SnapshotError as exc:
        module.write_module_artifacts(root, exc.status, module.STARTED_AT, module.iso(), [{"severity": "error", "code": exc.code, "message": exc.message}], None, None, None, [], None, False, False, False)
        return exc.status


def read_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def publication(root: Path) -> dict[str, Any]:
    return read_json_file(root / "data" / "pipeline" / MODULE_ID / "snapshot_publication.json")


def current(root: Path) -> Path:
    return root / "data" / "published" / "dashboard_snapshots" / "current"


def history_dir(root: Path, snapshot_id: str) -> Path:
    return root / "data" / "published" / "dashboard_snapshots" / "history" / snapshot_id
