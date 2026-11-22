from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MODULE_ID = "17_local_api_server"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def policy() -> dict[str, Any]:
    return {
        "policy_version": "dashboard_snapshot_api_policy_v1",
        "runtime": {"local_only": True, "default_host": "127.0.0.1", "default_port": 8765, "allow_host_override": False, "allow_port_override_via_cli": True, "approved_for_public_exposure": False, "approved_for_lan_exposure": False},
        "http_policy": {"read_only": True, "allowed_methods": ["GET", "POST"], "allowed_post_endpoints": ["/api/v1/dashboard/chat"], "disallowed_methods": ["PUT", "PATCH", "DELETE"], "chat_endpoint_modifies_snapshot": False, "chat_endpoint_triggers_pipeline": False},
        "cors_policy": {"enabled_by_default": False, "allow_wildcard_origins": False},
    }


def dashboard_payload(*, primary_type="deterministic", assisted=False, assisted_bad=False, payload_ready=True) -> dict[str, Any]:
    assisted_payload = {"available": assisted, "computed": assisted, "status": "available_validated_assisted_variant" if assisted else "not_available_no_assisted_artifact", "must_not_replace_primary_score": not assisted_bad, "display_disclosure": "Optional variant only."}
    if assisted:
        assisted_payload.update({"score_type": "llm_assisted", "score": 77.0, "label_id": "balanced", "label": "stabilny"})
    return {
        "module_id": "15_build_dashboard_payload",
        "status": "built",
        "metadata": {"latest_date": "2026-01-03", "records_count": 3},
        "current_state": {"date": "2026-01-03", "primary_pws": {"score_type": primary_type, "score": None, "computed": False, "label_id": "insufficient_data", "label": "insufficient_data", "coverage_tier": "insufficient", "display_disclosure": "Primary deterministic PWS."}, "optional_assisted_pws": assisted_payload},
        "time_series": [
            {"date": "2026-01-01", "pws_deterministic": 90.0, "optional_assisted_pws": None},
            {"date": "2026-01-02", "pws_deterministic": 75.34, "optional_assisted_pws": 76.0 if assisted else None},
            {"date": "2026-01-03", "pws_deterministic": None, "optional_assisted_pws": None},
        ],
        "quality_and_coverage": {"records_count": 3},
        "disclosures": {"primary_score": "Deterministic PWS is primary."},
        "ready_for_next_module": payload_ready,
    }


def write_current_snapshot(root: Path, *, missing: str | None = None, invalid_json: str | None = None, primary_type="deterministic", assisted=False, assisted_bad=False, payload_ready=True) -> Path:
    write_json(root / "config/dashboard_snapshot_api_policy_v1.json", policy())
    write_json(root / "config/dashboard_snapshot_policy_v1.json", {"policy_version": "dashboard_snapshot_policy_v1"})
    write_json(root / "config/llm_policy_v1.json", {"policy_version": "llm_policy_v1", "provider": "openai_compatible", "model": "test-local-model", "endpoint": "http://127.0.0.1:11434/v1/chat/completions", "api_key_environment_variable": "OLLAMA_API_KEY"})
    current = root / "data/published/dashboard_snapshots/current"
    payload = dashboard_payload(primary_type=primary_type, assisted=assisted, assisted_bad=assisted_bad, payload_ready=payload_ready)
    status = {"snapshot_id": "dashboard_2026-01-03_20260523T212853925125Z", "snapshot_version": "dashboard_snapshot_v1", "published_at": "2026-05-23T21:28:53Z", "latest_data_date": "2026-01-03", "payload_ready": payload_ready, "primary_pws": payload["current_state"]["primary_pws"], "optional_assisted_pws": payload["current_state"]["optional_assisted_pws"], "records_count": 3}
    manifest = {"snapshot_id": status["snapshot_id"], "primary_score_policy": {"score_type": "deterministic", "preserved_without_modification": True}, "optional_assisted_variant": {"supported": True, "must_not_replace_primary_score": True}, "files": []}
    files = {
        "dashboard_payload.json": payload,
        "dashboard_payload_schema.json": {"schema_version": "dashboard_payload_schema_v1"},
        "dashboard_payload_quality_report.json": {"ready_for_next_module": True},
        "dashboard_payload_lineage.json": {"lineage_version": "dashboard_payload_lineage_v1"},
        "snapshot_manifest.json": manifest,
        "snapshot_status.json": status,
    }
    for name, payload_obj in files.items():
        if name != missing:
            write_json(current / name, payload_obj)
    (current / "dashboard_time_series.csv").parent.mkdir(parents=True, exist_ok=True)
    if missing != "dashboard_time_series.csv":
        (current / "dashboard_time_series.csv").write_text("date,pws_deterministic\n2026-01-01,90\n", encoding="utf-8")
    hashes = {"files": [], "all_required_hashes_verified": True, "all_present_optional_hashes_verified": True}
    for file_path in current.iterdir() if current.exists() else []:
        if file_path.is_file() and file_path.name != "snapshot_source_hashes.json":
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
            hashes["files"].append({"filename": file_path.name, "required": True, "present": True, "source_sha256": digest, "snapshot_sha256": digest, "hash_match": True})
    if missing != "snapshot_source_hashes.json":
        write_json(current / "snapshot_source_hashes.json", hashes)
    if invalid_json:
        (current / invalid_json).write_text("{bad-json", encoding="utf-8")
    return current


def load_ctx(root: Path, api_app_module, **kwargs: Any):
    write_current_snapshot(root, **kwargs)
    return api_app_module.load_snapshot(root)
