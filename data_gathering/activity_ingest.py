from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

MODULE_ID = "04_garmin_activity_ingest"
CONTRACT_VERSION = "1.0.0"
POLICY_VERSION = "garmin_activity_ingest_v1"
ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "garmin_activity_ingest_v1.json"
ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID
ACTIVITIES_DIR = ARTIFACT_DIR / "activities"
LOG_FILE = ARTIFACT_DIR / "run_log.txt"
ERRORS_FILE = ARTIFACT_DIR / "errors.json"
INGEST_MANIFEST_FILE = ARTIFACT_DIR / "activity_ingest_manifest.json"
RUN_MANIFEST_FILE = ARTIFACT_DIR / "run_manifest.json"
VALID_ID_PATTERN = re.compile(r"^[0-9]+$")
STATUS_SUCCESS = {
    "skipped_disabled",
    "skipped_dependency_unavailable",
    "skipped_missing_credentials",
    "skipped_no_activity_ids",
    "completed",
    "completed_with_failures",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def append_error(errors: list[dict[str, Any]], code: str, message: str, context: dict[str, Any] | None = None, blocking: bool = True) -> None:
    item: dict[str, Any] = {"code": code, "message": message, "context": context or {}}
    if not blocking:
        item["blocking"] = False
    errors.append(item)


def validate_relative_path(value: str, field_name: str, errors: list[dict[str, Any]]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        append_error(errors, "CONFIGURATION_INVALID", f"{field_name} must be a non-empty relative path.", {"field": field_name})
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        append_error(errors, "CONFIGURATION_INVALID", f"{field_name} must not be absolute.", {"field": field_name})
        return None
    resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        append_error(errors, "CONFIGURATION_INVALID", f"{field_name} points outside the project root.", {"field": field_name})
        return None
    return resolved


def load_and_validate_config() -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not CONFIG_PATH.is_file():
        append_error(errors, "CONFIGURATION_INVALID", "Garmin activity ingest configuration file was not found.", {"path": rel(CONFIG_PATH)})
        return None, errors, warnings
    try:
        config = read_json(CONFIG_PATH)
    except Exception as exc:  # noqa: BLE001
        append_error(errors, "CONFIGURATION_INVALID", f"Garmin activity ingest configuration could not be read: {exc}", {"path": rel(CONFIG_PATH)})
        return None, errors, warnings
    required_values = {
        "policy_version": POLICY_VERSION,
        "optional_module": True,
        "client_library": "garminconnect",
        "credentials_mode": "local_tokenstore_only",
        "previous_project_runtime_dependency_allowed": False,
    }
    for key, expected in required_values.items():
        if config.get(key) != expected:
            append_error(errors, "CONFIGURATION_INVALID", f"{key} must be {expected!r}.", {"field": key})
    if not isinstance(config.get("enabled"), bool):
        append_error(errors, "CONFIGURATION_INVALID", "enabled must be a boolean.", {"field": "enabled"})
    if not isinstance(config.get("manual_activity_ids", []), list):
        append_error(errors, "CONFIGURATION_INVALID", "manual_activity_ids must be a list.", {"field": "manual_activity_ids"})
    if not isinstance(config.get("activity_id_sources", []), list):
        append_error(errors, "CONFIGURATION_INVALID", "activity_id_sources must be a list.", {"field": "activity_id_sources"})
    if not isinstance(config.get("requested_artifacts"), dict):
        append_error(errors, "CONFIGURATION_INVALID", "requested_artifacts must be an object.", {"field": "requested_artifacts"})
    if not isinstance(config.get("failure_policy"), dict):
        append_error(errors, "CONFIGURATION_INVALID", "failure_policy must be an object.", {"field": "failure_policy"})
    if not isinstance(config.get("privacy_rules"), dict):
        append_error(errors, "CONFIGURATION_INVALID", "privacy_rules must be an object.", {"field": "privacy_rules"})
    tokenstore_path = validate_relative_path(str(config.get("local_tokenstore_directory", "")), "local_tokenstore_directory", errors)
    output_path = validate_relative_path(str(config.get("output_directory", "")), "output_directory", errors)
    if output_path and output_path != ACTIVITIES_DIR.resolve():
        append_error(errors, "CONFIGURATION_INVALID", "output_directory must target module 04 activities artifact directory.", {"field": "output_directory"})
    if tokenstore_path is not None and "data/local_secrets/garmin_tokenstore" not in tokenstore_path.as_posix().replace("\\", "/"):
        append_error(errors, "CONFIGURATION_INVALID", "local_tokenstore_directory must be inside data/local_secrets/garmin_tokenstore.", {"field": "local_tokenstore_directory"})
    return (None if errors else config), errors, warnings


def normalize_activity_id(value: Any) -> str | None:
    text = str(value).strip()
    if not text:
        return None
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text if VALID_ID_PATTERN.fullmatch(text) else None


def collect_manual_ids(config: dict[str, Any], warnings: list[str], errors: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for raw_id in config.get("manual_activity_ids", []):
        normalized = normalize_activity_id(raw_id)
        if normalized:
            result.append(normalized)
        else:
            warnings.append("Invalid manual activity ID was skipped.")
            append_error(errors, "ACTIVITY_ID_INVALID", "Invalid manual activity ID was skipped.", {"source": "manual_config"}, blocking=False)
    return result


def find_trimmed_activities_csv(config: dict[str, Any], warnings: list[str]) -> Path | None:
    source = config.get("trimmed_activities_source", {})
    manifest_rel = str(source.get("manifest_path", ""))
    expected_sheet = str(source.get("expected_sheet_name", "Activities"))
    if not manifest_rel:
        warnings.append("Trimmed activities manifest path is not configured.")
        return None
    manifest_path = ROOT / manifest_rel
    if not manifest_path.is_file():
        warnings.append("Trimmed Activities.csv source is not available; manual activity IDs may still be used.")
        return None
    try:
        manifest = read_json(manifest_path)
    except Exception:  # noqa: BLE001
        warnings.append("Trimmed activities manifest could not be read; manual activity IDs may still be used.")
        return None
    for sheet in manifest.get("sheets", []):
        if sheet.get("sheet_name") == expected_sheet and sheet.get("artifact_path"):
            csv_path = ROOT / str(sheet["artifact_path"])
            if csv_path.is_file():
                return csv_path
            warnings.append("Trimmed Activities.csv was referenced but not found.")
            return None
    warnings.append("Trimmed Activities.csv was not produced by module 03.")
    return None


def collect_csv_ids(config: dict[str, Any], warnings: list[str], errors: list[dict[str, Any]]) -> list[str]:
    csv_path = find_trimmed_activities_csv(config, warnings)
    if csv_path is None:
        return []
    column = str(config.get("trimmed_activities_source", {}).get("activity_id_column", "activityId"))
    result: list[str] = []
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if column not in (reader.fieldnames or []):
                warnings.append(f"Trimmed Activities.csv does not contain {column} column.")
                return []
            for row in reader:
                normalized = normalize_activity_id(row.get(column, ""))
                if normalized:
                    result.append(normalized)
                else:
                    warnings.append("Invalid activity ID from trimmed Activities.csv was skipped.")
                    append_error(errors, "ACTIVITY_ID_INVALID", "Invalid activity ID from trimmed Activities.csv was skipped.", {"source": "trimmed_activities_csv"}, blocking=False)
    except Exception:  # noqa: BLE001
        warnings.append("Trimmed Activities.csv could not be read; manual activity IDs may still be used.")
    return result


def collect_activity_ids(config: dict[str, Any], warnings: list[str], errors: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    source_names: list[str] = []
    ids: list[str] = []
    configured_sources = set(config.get("activity_id_sources", []))
    if "manual_config" in configured_sources:
        manual_ids = collect_manual_ids(config, warnings, errors)
        if manual_ids:
            source_names.append("manual_config")
            ids.extend(manual_ids)
    if "trimmed_activities_csv" in configured_sources:
        csv_ids = collect_csv_ids(config, warnings, errors)
        if csv_ids:
            source_names.append("trimmed_activities_csv")
            ids.extend(csv_ids)
    return sorted(set(ids)), source_names


def validate_tokenstore(config: dict[str, Any], errors: list[dict[str, Any]]) -> tuple[bool, Path]:
    tokenstore_dir = ROOT / str(config["local_tokenstore_directory"])
    oauth1_path = tokenstore_dir / "oauth1_token.json"
    oauth2_path = tokenstore_dir / "oauth2_token.json"
    if not tokenstore_dir.is_dir() or not oauth1_path.is_file() or not oauth2_path.is_file():
        append_error(errors, "LOCAL_TOKENSTORE_NOT_FOUND", "Local Garmin tokenstore was not found in the new project secret directory.", {}, blocking=False)
        return False, tokenstore_dir
    try:
        oauth1 = read_json(oauth1_path)
        oauth2 = read_json(oauth2_path)
    except Exception:  # noqa: BLE001
        append_error(errors, "LOCAL_TOKENSTORE_INVALID", "Local Garmin tokenstore JSON could not be read.", {}, blocking=False)
        return False, tokenstore_dir
    missing = []
    for key in ["oauth_token", "oauth_token_secret"]:
        if not isinstance(oauth1, dict) or not str(oauth1.get(key, "")).strip():
            missing.append(f"oauth1_token.json:{key}")
    for key in ["access_token", "refresh_token"]:
        if not isinstance(oauth2, dict) or not str(oauth2.get(key, "")).strip():
            missing.append(f"oauth2_token.json:{key}")
    if missing:
        append_error(errors, "LOCAL_TOKENSTORE_INVALID", "Local Garmin tokenstore is missing required fields.", {"missing_fields": missing}, blocking=False)
        return False, tokenstore_dir
    return True, tokenstore_dir


def make_base_manifest(status: str, warnings: list[str], activity_id_sources: list[str] | None = None, requested_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "policy_version": POLICY_VERSION,
        "status": status,
        "optional_module": True,
        "credentials_checked": False,
        "api_called": False,
        "activity_id_sources": activity_id_sources or [],
        "requested_activity_ids": requested_ids or [],
        "activities": [],
        "warnings": warnings,
        "ready_for_optional_activity_normalization": False,
        "does_not_block_workbook_pipeline": True,
    }


def write_activity_artifact(path: Path, payload: Any, artifact_type: str) -> None:
    if artifact_type in {"details_json", "splits_json"}:
        write_json(path, payload)
    elif isinstance(payload, bytes):
        path.write_bytes(payload)
    elif isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_bytes(bytes(payload))


def download_one_activity(adapter: Any, activity_id: str, requested: dict[str, bool], errors: list[dict[str, Any]]) -> dict[str, Any]:
    activity_dir = ACTIVITIES_DIR / activity_id
    activity_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[dict[str, str]] = []
    local_errors: list[dict[str, Any]] = []
    artifact_specs = [
        ("details_json", "details.json", adapter.get_activity_details, "DETAILS_DOWNLOAD_FAILED"),
        ("splits_json", "splits.json", adapter.get_activity_splits, "SPLITS_DOWNLOAD_FAILED"),
        ("fit_file", "activity.fit", adapter.download_activity_fit, "FIT_DOWNLOAD_FAILED"),
        ("tcx_file", "activity.tcx", adapter.download_activity_tcx, "TCX_DOWNLOAD_FAILED"),
    ]
    requested_count = 0
    for artifact_type, filename, getter, error_code in artifact_specs:
        if not requested.get(artifact_type, False):
            continue
        requested_count += 1
        try:
            payload = getter(activity_id)
            out_path = activity_dir / filename
            write_activity_artifact(out_path, payload, artifact_type)
            downloaded.append({"artifact_type": artifact_type, "relative_path": rel(out_path), "status": "downloaded"})
        except Exception as exc:  # noqa: BLE001
            error = {
                "code": error_code,
                "message": "Failed to download requested Garmin activity artifact.",
                "context": {"activity_id": activity_id, "artifact_type": artifact_type, "reason": str(exc)},
                "blocking": False,
            }
            errors.append(error)
            local_errors.append(error)
    if downloaded and len(downloaded) == requested_count:
        status = "downloaded"
    elif downloaded:
        status = "partially_downloaded"
    else:
        status = "failed"
    manifest = {
        "activity_id": activity_id,
        "status": status,
        "requested_artifacts": requested,
        "downloaded_artifacts": downloaded,
        "errors": local_errors,
        "private_data_notice": "Downloaded activity artifacts may contain private health and location data and must remain local.",
    }
    manifest_path = activity_dir / "download_manifest.json"
    write_json(manifest_path, manifest)
    return {"activity_id": activity_id, "status": status, "manifest_path": rel(manifest_path)}


def run_enabled_ingest(
    config: dict[str, Any],
    warnings: list[str],
    errors: list[dict[str, Any]],
    dependency_available: Callable[[], bool] | None,
    adapter_factory: Callable[[Path], Any] | None,
) -> dict[str, Any]:
    if dependency_available is None or adapter_factory is None:
        from garmin_client_adapter import GarminClientAdapter
        dependency_available = GarminClientAdapter.dependency_available
        adapter_factory = GarminClientAdapter

    if not dependency_available():
        warnings.append("Optional dependency garminconnect is not available. Garmin activity ingest was skipped.")
        return make_base_manifest("skipped_dependency_unavailable", warnings)

    requested_ids, sources = collect_activity_ids(config, warnings, errors)
    if not requested_ids:
        warnings.append("No valid Garmin activity IDs were available for optional ingest.")
        append_error(errors, "NO_ACTIVITY_IDS_AVAILABLE", "No valid Garmin activity IDs were available for optional ingest.", {}, blocking=False)
        return make_base_manifest("skipped_no_activity_ids", warnings, sources, requested_ids)

    credentials_valid, tokenstore_dir = validate_tokenstore(config, errors)
    if not credentials_valid:
        warnings.append("Local Garmin tokenstore is missing or invalid. Optional ingest was skipped.")
        manifest = make_base_manifest("skipped_missing_credentials", warnings, sources, requested_ids)
        manifest["credentials_checked"] = True
        manifest["credentials_valid"] = False
        return manifest

    requested_artifacts = config.get("requested_artifacts", {})
    adapter = adapter_factory(tokenstore_dir)
    activities: list[dict[str, str]] = []
    for activity_id in requested_ids:
        activities.append(download_one_activity(adapter, activity_id, requested_artifacts, errors))
    downloaded_count = sum(1 for item in activities if item["status"] in {"downloaded", "partially_downloaded"})
    failed_count = sum(1 for item in activities if item["status"] == "failed")
    domain_status = "completed" if failed_count == 0 and all(item["status"] == "downloaded" for item in activities) else "completed_with_failures"
    return {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "policy_version": POLICY_VERSION,
        "status": domain_status,
        "optional_module": True,
        "credentials_checked": True,
        "credentials_valid": True,
        "api_called": True,
        "activity_id_sources": sources,
        "requested_activity_ids": requested_ids,
        "activities_requested_count": len(requested_ids),
        "activities_downloaded_count": downloaded_count,
        "activities_failed_count": failed_count,
        "activities": activities,
        "warnings": warnings,
        "ready_for_optional_activity_normalization": downloaded_count > 0,
        "does_not_block_workbook_pipeline": True,
        "private_data_notice": "Downloaded activity artifacts may contain private health and location data and must not be committed to version control.",
    }


def write_outputs(started_at: str, domain_status: str, manifest: dict[str, Any], errors: list[dict[str, Any]], log_lines: list[str]) -> int:
    finished_at = now_iso()
    execution_status = "success" if domain_status in STATUS_SUCCESS else "failed"
    generated = [rel(INGEST_MANIFEST_FILE), rel(RUN_MANIFEST_FILE), rel(LOG_FILE), rel(ERRORS_FILE)]
    write_json(INGEST_MANIFEST_FILE, manifest)
    write_json(ERRORS_FILE, {"module_id": MODULE_ID, "errors": errors})
    log_lines.extend([
        f"finished_at={finished_at}",
        f"execution_status={execution_status}",
        f"domain_status={domain_status}",
        "scope=raw optional activity ingest only; no normalization, no workbook/API merge, no metrics, no LLM",
        "workbook_pipeline_blocked=false",
    ])
    LOG_FILE.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    run_manifest = {
        "module_id": MODULE_ID,
        "module_version": CONTRACT_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": execution_status,
        "domain_status": domain_status,
        "optional_module": True,
        "inputs": ["config/garmin_activity_ingest_v1.json"],
        "generated_artifacts": generated,
        "log_file": rel(LOG_FILE),
        "errors_file": rel(ERRORS_FILE),
        "does_not_block_workbook_pipeline": True,
    }
    write_json(RUN_MANIFEST_FILE, run_manifest)
    return 0 if execution_status == "success" else 1


def execute(
    root: Path | None = None,
    dependency_available: Callable[[], bool] | None = None,
    adapter_factory: Callable[[Path], Any] | None = None,
) -> int:
    global ROOT, CONFIG_PATH, ARTIFACT_DIR, ACTIVITIES_DIR, LOG_FILE, ERRORS_FILE, INGEST_MANIFEST_FILE, RUN_MANIFEST_FILE
    if root is not None:
        ROOT = root
        CONFIG_PATH = ROOT / "config" / "garmin_activity_ingest_v1.json"
        ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID
        ACTIVITIES_DIR = ARTIFACT_DIR / "activities"
        LOG_FILE = ARTIFACT_DIR / "run_log.txt"
        ERRORS_FILE = ARTIFACT_DIR / "errors.json"
        INGEST_MANIFEST_FILE = ARTIFACT_DIR / "activity_ingest_manifest.json"
        RUN_MANIFEST_FILE = ARTIFACT_DIR / "run_manifest.json"

    started_at = now_iso()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVITIES_DIR.mkdir(parents=True, exist_ok=True)
    log_lines = [f"module_id={MODULE_ID}", f"started_at={started_at}"]
    config, errors, warnings = load_and_validate_config()
    if config is None:
        manifest = make_base_manifest("configuration_failed", warnings)
        return write_outputs(started_at, "configuration_failed", manifest, errors, log_lines)

    log_lines.append(f"policy_version={config['policy_version']}")
    log_lines.append(f"enabled={config['enabled']}")
    log_lines.append("previous_project_runtime_dependency_allowed=false")
    log_lines.append("token_values_logged=false")

    if config.get("enabled") is False:
        warnings.append("Garmin activity ingest is disabled in public configuration.")
        manifest = make_base_manifest("skipped_disabled", warnings)
        manifest["enabled"] = False
        log_lines.append("garminconnect_checked=false")
        log_lines.append("credentials_checked=false")
        log_lines.append("api_called=false")
        return write_outputs(started_at, "skipped_disabled", manifest, errors, log_lines)

    try:
        manifest = run_enabled_ingest(config, warnings, errors, dependency_available, adapter_factory)
        manifest["enabled"] = True
        log_lines.append("garminconnect_checked=true")
        log_lines.append(f"credentials_checked={manifest.get('credentials_checked', False)}")
        log_lines.append(f"api_called={manifest.get('api_called', False)}")
        log_lines.append(f"activity_id_sources={manifest.get('activity_id_sources', [])}")
        log_lines.append(f"requested_activity_ids={manifest.get('requested_activity_ids', [])}")
        log_lines.append(f"activities_downloaded_count={manifest.get('activities_downloaded_count', 0)}")
        log_lines.append(f"activities_failed_count={manifest.get('activities_failed_count', 0)}")
        for activity in manifest.get("activities", []):
            log_lines.append(f"activity_manifest={activity.get('manifest_path')}")
        return write_outputs(started_at, str(manifest["status"]), manifest, errors, log_lines)
    except Exception as exc:  # noqa: BLE001
        append_error(errors, "ARTIFACT_WRITE_ERROR", f"Garmin activity ingest failed while writing or downloading artifacts: {exc}")
        manifest = make_base_manifest("artifact_write_failed", warnings)
        return write_outputs(started_at, "artifact_write_failed", manifest, errors, log_lines)


def main() -> int:
    return execute()


if __name__ == "__main__":
    sys.exit(main())
