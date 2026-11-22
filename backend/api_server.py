
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api_app import DEFAULT_HOST, DEFAULT_PORT, GET_ENDPOINTS, POST_ENDPOINTS, MODULE_ID, POLICY_VERSION, SnapshotContext, create_fastapi_app, load_snapshot

MODULE_VERSION = "1.0.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def artifact_dir(root: Path) -> Path:
    return root / "data" / "pipeline" / MODULE_ID


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Port must be an integer.") from exc
    if port < 1 or port > 65535:
        raise argparse.ArgumentTypeError("Port must be in range 1-65535.")
    return port


def startup_validation(ctx: SnapshotContext) -> dict[str, Any]:
    primary = (ctx.status or {}).get("primary_pws", {})
    assisted = (ctx.status or {}).get("optional_assisted_pws", {})
    validation_status = "valid" if ctx.ready else ctx.validation_status
    return {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "validated_at": now_iso(),
        "validation_status": validation_status,
        "runtime_mode": {"local_only": True, "snapshot_read_only": True, "ephemeral_llm_chat_enabled": True, "host": DEFAULT_HOST, "port": ctx.port, "cors_enabled": False, "public_exposure_approved": False},
        "snapshot": {"directory": "data/published/dashboard_snapshots/current", "available": ctx.snapshot_available, "snapshot_id": ctx.snapshot_id, "latest_data_date": ctx.latest_data_date, "payload_ready": (ctx.status or {}).get("payload_ready")},
        "checks": {"required_files_present": not any(e["code"] == "CURRENT_SNAPSHOT_REQUIRED_FILE_NOT_FOUND" for e in ctx.errors), "json_files_parseable": not any(e["code"] == "CURRENT_SNAPSHOT_JSON_INVALID" for e in ctx.errors), "snapshot_status_ready": (ctx.status or {}).get("payload_ready") is True, "primary_score_is_deterministic": primary.get("score_type") == "deterministic", "optional_assisted_variant_contract_valid": assisted.get("must_not_replace_primary_score", True) is True, "hash_artifact_present": ctx.hashes is not None, "published_hash_verification_status_valid": bool((ctx.hashes or {}).get("all_required_hashes_verified")), "file_hashes_reverified_on_startup": ctx.file_hashes_reverified_on_startup},
        "primary_score": {"score_type": primary.get("score_type"), "preserved_without_modification": True},
        "optional_assisted_variant": {"available": bool(assisted.get("available")), "must_not_replace_primary_score": assisted.get("must_not_replace_primary_score", True)},
        "api_ready_to_serve_snapshot": ctx.ready,
        "errors": ctx.errors,
        "warnings": ctx.warnings,
    }


def api_contract_schema(port: int) -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "schema_version": "dashboard_snapshot_api_schema_v1",
        "policy_version": POLICY_VERSION,
        "api_base_path": "/api/v1",
        "runtime": {"local_only": True, "snapshot_read_only": True, "ephemeral_llm_chat_enabled": True, "default_host": DEFAULT_HOST, "default_port": DEFAULT_PORT, "configured_port": port, "public_exposure_approved": False},
        "source": {"snapshot_directory": "data/published/dashboard_snapshots/current", "snapshot_loaded_at_startup": True, "snapshot_hot_reload_supported": False},
        "endpoints": [
            {"method": "GET", "path": "/api/v1/health", "response_source": "runtime_and_snapshot_startup_validation"},
            {"method": "GET", "path": "/api/v1/snapshot/status", "response_source": "snapshot_status.json"},
            {"method": "GET", "path": "/api/v1/snapshot/manifest", "response_source": "snapshot_manifest.json"},
            {"method": "GET", "path": "/api/v1/dashboard", "response_source": "dashboard_payload.json"},
            {"method": "GET", "path": "/api/v1/dashboard/current-state", "response_source": "dashboard_payload.current_state"},
            {"method": "GET", "path": "/api/v1/dashboard/time-series", "response_source": "dashboard_payload.time_series", "optional_query_parameters": ["date_from", "date_to", "limit"]},
            {"method": "GET", "path": "/api/v1/dashboard/quality", "response_source": "dashboard_payload.quality_and_coverage"},
            {"method": "GET", "path": "/api/v1/dashboard/disclosures", "response_source": "dashboard_payload.disclosures"},
            {"method": "POST", "path": "/api/v1/dashboard/chat", "response_source": "local_llm_with_minimal_dashboard_context", "writes_snapshot": False, "triggers_pipeline": False},
        ],
        "prohibited_methods": ["PUT", "PATCH", "DELETE"],
        "post_endpoints": POST_ENDPOINTS,
        "primary_score_contract": {"score_type": "deterministic", "assisted_score_must_never_replace_primary": True},
        "missing_values_policy": "preserve_null_never_replace_with_zero",
        "recomputation_policy": {"analytical_values_recomputed": False, "pipeline_triggered": False, "llm_called_for_recomputation": False, "llm_chat_runtime_supported": True},
        "privacy_policy": {"private_local_api": True, "raw_source_files_not_served": True, "tokens_and_secrets_not_served": True},
    }


def quality_report(ctx: SnapshotContext, domain_status: str) -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": domain_status,
        "local_only": True,
        "snapshot_read_only": True,
        "ephemeral_llm_chat_enabled": True,
        "snapshot_validation": {"snapshot_available": ctx.snapshot_available, "snapshot_valid": ctx.ready, "snapshot_id": ctx.snapshot_id, "latest_data_date": ctx.latest_data_date},
        "endpoint_contract": {"get_endpoints_count": len(GET_ENDPOINTS), "post_endpoints": POST_ENDPOINTS, "write_endpoints_count": 0, "llm_chat_endpoint_count": len(POST_ENDPOINTS), "pipeline_trigger_endpoints_count": 0, "auth_endpoints_count": 0, "garmin_token_endpoints_count": 0},
        "presentation_contract": {"deterministic_pws_remains_primary": True, "optional_assisted_pws_remains_separate": True, "missing_values_preserved_as_null": True},
        "security_boundary": {"bind_host": DEFAULT_HOST, "public_exposure_approved": False, "lan_exposure_approved": False, "cors_wildcard_enabled": False, "authentication_implemented": False, "important_note": "No authentication is implemented because this stage is strictly local-only. Do not expose it outside localhost."},
        "forbidden_action_confirmation": {"pipeline_triggered": False, "metrics_recomputed": False, "llm_called_for_recomputation": False, "frontend_implemented": False, "auth_profile_api_implemented": False, "garmin_token_pipeline_implemented": False, "medical_diagnosis_generated": False, "training_prescription_generated": False},
        "warnings": ["The API serves private derived wellness data and must remain bound to localhost.", "The API is read-only and does not implement authentication or public deployment security.", "Restart the API process after publishing a new snapshot."],
        "ready_for_next_module": domain_status in {"ready_to_serve_local_snapshot", "validated_only"},
    }


def api_lineage() -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "lineage_version": "dashboard_snapshot_api_lineage_v1",
        "source_artifacts": [
            {"module_id": "16_persist_local_snapshot", "artifact_path": "data/published/dashboard_snapshots/current/dashboard_payload.json", "role": "dashboard_payload_runtime_source"},
            {"module_id": "16_persist_local_snapshot", "artifact_path": "data/published/dashboard_snapshots/current/snapshot_status.json", "role": "snapshot_status_runtime_source"},
            {"module_id": "16_persist_local_snapshot", "artifact_path": "data/published/dashboard_snapshots/current/snapshot_manifest.json", "role": "snapshot_manifest_runtime_source"},
        ],
        "runtime_transformation": {"operation": "serve_immutable_in_memory_view_of_validated_current_snapshot_and_ephemeral_local_llm_chat", "snapshot_loaded_at_startup": True, "snapshot_modified": False, "analytical_values_recomputed": False, "pipeline_triggered": False},
        "endpoint_mapping": {"/api/v1/snapshot/status": "snapshot_status.json", "/api/v1/snapshot/manifest": "snapshot_manifest.json", "/api/v1/dashboard": "dashboard_payload.json", "/api/v1/dashboard/current-state": "dashboard_payload.current_state", "/api/v1/dashboard/time-series": "dashboard_payload.time_series_with_optional_read_only_filtering", "/api/v1/dashboard/quality": "dashboard_payload.quality_and_coverage", "/api/v1/dashboard/disclosures": "dashboard_payload.disclosures", "/api/v1/dashboard/chat": "local_llm_answer_from_minimal_dashboard_context"},
        "primary_and_assisted_boundary": {"deterministic_pws_preserved_as_primary": True, "optional_assisted_pws_preserved_only_as_optional_variant": True, "api_may_replace_primary_score": False},
        "forbidden_action_confirmation": {"llm_called_for_recomputation": False, "metrics_recomputed": False, "snapshot_modified": False, "write_endpoint_implemented": False, "authentication_implemented": False, "garmin_token_pipeline_implemented": False, "frontend_implemented": False, "medical_diagnosis_generated": False, "training_prescription_generated": False},
    }

def write_runtime_artifacts(root: Path, ctx: SnapshotContext, started_at: str, validation_finished_at: str, execution_mode: str, server_started: bool, domain_status: str) -> None:
    out = artifact_dir(root)
    out.mkdir(parents=True, exist_ok=True)
    errors = ctx.errors
    write_json(out / "api_startup_validation.json", startup_validation(ctx))
    write_json(out / "api_contract_schema.json", api_contract_schema(ctx.port))
    write_json(out / "api_quality_report.json", quality_report(ctx, domain_status))
    write_json(out / "api_lineage.json", api_lineage())
    write_json(out / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    write_json(out / "run_manifest.json", {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "validation_finished_at": validation_finished_at,
        "execution_mode": execution_mode,
        "execution_status": "success" if domain_status in {"ready_to_serve_local_snapshot", "validated_only"} else "failed",
        "domain_status": domain_status,
        "runtime": {"local_only": True, "snapshot_read_only": True, "ephemeral_llm_chat_enabled": True, "host": DEFAULT_HOST, "port": ctx.port, "server_started": server_started},
        "inputs": ["config/dashboard_snapshot_api_policy_v1.json", "config/dashboard_snapshot_policy_v1.json", "data/published/dashboard_snapshots/current/dashboard_payload.json", "data/published/dashboard_snapshots/current/snapshot_manifest.json", "data/published/dashboard_snapshots/current/snapshot_status.json", "data/published/dashboard_snapshots/current/snapshot_source_hashes.json"],
        "generated_artifacts": [f"data/pipeline/{MODULE_ID}/api_startup_validation.json", f"data/pipeline/{MODULE_ID}/api_contract_schema.json", f"data/pipeline/{MODULE_ID}/api_quality_report.json", f"data/pipeline/{MODULE_ID}/api_lineage.json", f"data/pipeline/{MODULE_ID}/run_manifest.json", f"data/pipeline/{MODULE_ID}/run_log.txt", f"data/pipeline/{MODULE_ID}/errors.json"],
        "snapshot_loaded": ctx.ready,
        "snapshot_id": ctx.snapshot_id,
        "analytical_values_recomputed": False,
        "pipeline_triggered": False,
        "llm_called_during_startup": False,
        "ephemeral_llm_chat_endpoint_implemented": True,
        "write_endpoints_implemented": False,
        "authentication_implemented": False,
        "frontend_implemented": False,
        "log_file": f"data/pipeline/{MODULE_ID}/run_log.txt",
        "errors_file": f"data/pipeline/{MODULE_ID}/errors.json",
    })
    lines = [
        f"module_id={MODULE_ID}", f"policy_version={POLICY_VERSION}", f"execution_mode={execution_mode}", f"started_at={started_at}",
        "local_only=true", "snapshot_read_only=true", "ephemeral_llm_chat_enabled=true", f"host={DEFAULT_HOST}", f"port={ctx.port}", "public_exposure_approved=false",
        "authentication_implemented=false", "current_snapshot_directory=data/published/dashboard_snapshots/current", f"snapshot_available={ctx.snapshot_available}",
        f"snapshot_id={ctx.snapshot_id}", f"latest_data_date={ctx.latest_data_date}", f"snapshot_validation_status={ctx.validation_status}",
        "primary_score_is_deterministic=true", f"optional_assisted_available={bool((ctx.status or {}).get('optional_assisted_pws', {}).get('available'))}",
        "optional_assisted_never_replaces_primary=true", f"get_endpoints={GET_ENDPOINTS}", "write_endpoints_created=false",
        "pipeline_triggered_by_api=false", "snapshot_loaded_at_startup=true", "hot_reload_supported=false", "restart_required_after_new_snapshot=true",
        "analytical_values_recomputed=false", "llm_called_during_startup=false", "llm_chat_endpoint=/api/v1/dashboard/chat", "frontend_implemented=false", "auth_profile_api_implemented=false", "garmin_token_pipeline_implemented=false",
        "private_derived_data_served_locally=true", f"validation_finished_at={validation_finished_at}", f"domain_status={domain_status}",
    ]
    if errors:
        lines.append("errors:")
        lines.extend(f"{item['code']}: {item['message']}" for item in errors)
    (out / "run_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve local read-only dashboard snapshot API.")
    parser.add_argument("--port", type=validate_port, default=DEFAULT_PORT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--verify-file-hashes-on-startup", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    root = root_dir()
    started_at = now_iso()
    try:
        args = parse_args(argv if argv is not None else sys.argv[1:])
    except SystemExit:
        ctx = SnapshotContext(root=root)
        ctx.errors.append({"code": "INVALID_PORT_ARGUMENT", "message": "Invalid CLI arguments."})
        write_runtime_artifacts(root, ctx, started_at, now_iso(), "validate_only", False, "api_startup_failed")
        return 2
    ctx = load_snapshot(root, port=args.port, verify_file_hashes=args.verify_file_hashes_on_startup)
    validation_finished_at = now_iso()
    if args.validate_only:
        domain_status = "validated_only" if ctx.ready else ctx.validation_status
        write_runtime_artifacts(root, ctx, started_at, validation_finished_at, "validate_only", False, domain_status)
        return 0 if ctx.ready else 1

    domain_status = "ready_to_serve_local_snapshot" if ctx.ready else "degraded_snapshot_unavailable"
    write_runtime_artifacts(root, ctx, started_at, validation_finished_at, "serve", ctx.ready, domain_status)
    try:
        import uvicorn
    except ImportError:
        ctx.errors.append({"code": "API_STARTUP_DEPENDENCY_MISSING", "message": "uvicorn is not installed. Install requirements.txt before serving."})
        write_runtime_artifacts(root, ctx, started_at, validation_finished_at, "serve", False, "api_startup_failed")
        return 1
    try:
        app = create_fastapi_app(ctx)
    except RuntimeError as exc:
        ctx.errors.append({"code": "API_STARTUP_DEPENDENCY_MISSING", "message": str(exc)})
        write_runtime_artifacts(root, ctx, started_at, validation_finished_at, "serve", False, "api_startup_failed")
        return 1
    uvicorn.run(app, host=DEFAULT_HOST, port=args.port, access_log=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
