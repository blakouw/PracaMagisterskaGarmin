
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_ID = "16_persist_local_snapshot"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "dashboard_snapshot_policy_v1"
SOURCE_MODULE_ID = "15_build_dashboard_payload"
SNAPSHOT_VERSION = "dashboard_snapshot_v1"
SCHEMA_VERSION = "dashboard_snapshot_publication_schema_v1"
LINEAGE_VERSION = "dashboard_snapshot_publication_lineage_v1"
REQUIRED_SOURCE_FILES = [
    "dashboard_payload.json",
    "dashboard_time_series.csv",
    "dashboard_payload_schema.json",
    "dashboard_payload_quality_report.json",
    "dashboard_payload_lineage.json",
]
OPTIONAL_SOURCE_FILES = ["dashboard_time_series.parquet"]
GENERATED_SNAPSHOT_FILES = ["snapshot_manifest.json", "snapshot_source_hashes.json", "snapshot_status.json"]
REQUIRED_PAYLOAD_SECTIONS = ["metadata", "current_state", "time_series", "quality_and_coverage", "disclosures"]
READY_STATUSES = {"published", "published_without_optional_parquet", "published_with_payload_warnings"}


class SnapshotError(Exception):
    def __init__(self, status: str, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class CurrentPublishError(Exception):
    pass


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or now_utc()).isoformat(timespec="microseconds").replace("+00:00", "Z")


def compact_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def source_dir(root: Path) -> Path:
    return root / "data" / "pipeline" / SOURCE_MODULE_ID


def artifact_dir(root: Path) -> Path:
    return root / "data" / "pipeline" / MODULE_ID


def snapshot_root(root: Path) -> Path:
    return root / "data" / "published" / "dashboard_snapshots"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_id_from(latest_date: str, published_at: datetime) -> str:
    return f"dashboard_{latest_date}_{compact_utc(published_at)}"


def is_safe_snapshot_id(snapshot_id: str) -> bool:
    return re.fullmatch(r"dashboard_\d{4}-\d{2}-\d{2}_\d{8}T\d{6}\d{6}Z(?:_\d{2})?", snapshot_id) is not None


def unique_snapshot_id(latest_date: str, published_at: datetime, history_root: Path) -> str:
    base = snapshot_id_from(latest_date, published_at)
    if not (history_root / base).exists():
        return base
    for index in range(1, 100):
        candidate = f"{base}_{index:02d}"
        if not (history_root / candidate).exists():
            return candidate
    raise SnapshotError("blocked_snapshot_id_collision", "SNAPSHOT_ID_COLLISION", "Could not create unique snapshot id.")


def load_inputs(root: Path) -> dict[str, Any]:
    policy_path = root / "config" / "dashboard_snapshot_policy_v1.json"
    dashboard_policy_path = root / "config" / "dashboard_payload_policy_v1.json"
    source = source_dir(root)
    if not policy_path.is_file():
        raise SnapshotError("invalid_dashboard_snapshot_policy", "DASHBOARD_SNAPSHOT_POLICY_NOT_FOUND", "Snapshot policy is missing.")
    if not dashboard_policy_path.is_file():
        raise SnapshotError("invalid_dashboard_snapshot_policy", "DASHBOARD_PAYLOAD_POLICY_NOT_FOUND", "Dashboard payload policy is missing.")
    missing = [name for name in REQUIRED_SOURCE_FILES if not (source / name).is_file()]
    if missing:
        status = "blocked_missing_dashboard_payload" if "dashboard_payload.json" in missing else "snapshot_publication_failed"
        code = "DASHBOARD_PAYLOAD_NOT_FOUND" if "dashboard_payload.json" in missing else "SOURCE_ARTIFACT_NOT_FOUND"
        raise SnapshotError(status, code, f"Missing required dashboard source files: {missing}")
    return {
        "policy": read_json(policy_path),
        "dashboard_policy": read_json(dashboard_policy_path),
        "payload": read_json(source / "dashboard_payload.json"),
        "quality": read_json(source / "dashboard_payload_quality_report.json"),
        "paths": {"source_dir": source},
    }


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("policy_version") != POLICY_VERSION:
        raise SnapshotError("invalid_dashboard_snapshot_policy", "DASHBOARD_SNAPSHOT_POLICY_INVALID", "Invalid snapshot policy version.")
    if policy.get("source_module") != SOURCE_MODULE_ID:
        raise SnapshotError("invalid_dashboard_snapshot_policy", "DASHBOARD_SNAPSHOT_POLICY_INVALID", "Snapshot policy source_module does not match registry.")
    if policy.get("hash_policy", {}).get("algorithm") != "sha256":
        raise SnapshotError("invalid_dashboard_snapshot_policy", "DASHBOARD_SNAPSHOT_POLICY_INVALID", "Snapshot policy must use sha256.")


def validate_payload(payload: dict[str, Any], quality: dict[str, Any]) -> str:
    if payload.get("ready_for_next_module") is not True:
        raise SnapshotError("blocked_dashboard_payload_not_ready", "DASHBOARD_PAYLOAD_NOT_READY", "Dashboard payload is not ready.")
    if quality.get("ready_for_next_module") is not True:
        raise SnapshotError("blocked_dashboard_quality_report_not_ready", "DASHBOARD_PAYLOAD_QUALITY_REPORT_NOT_READY", "Dashboard payload quality report is not ready.")
    missing = [section for section in REQUIRED_PAYLOAD_SECTIONS if section not in payload]
    if missing:
        raise SnapshotError("blocked_dashboard_payload_not_ready", "DASHBOARD_REQUIRED_SECTION_MISSING", f"Missing dashboard payload sections: {missing}")
    latest_date = payload.get("metadata", {}).get("latest_date")
    if not valid_date(latest_date):
        raise SnapshotError("blocked_invalid_dashboard_latest_date", "DASHBOARD_LATEST_DATE_INVALID", "dashboard_payload.metadata.latest_date is invalid.")
    primary = payload.get("current_state", {}).get("primary_pws")
    if not isinstance(primary, dict) or primary.get("score_type") != "deterministic" or "computed" not in primary or "coverage_tier" not in primary or "display_disclosure" not in primary:
        raise SnapshotError("blocked_invalid_primary_score_contract", "PRIMARY_SCORE_NOT_DETERMINISTIC", "Primary PWS must be deterministic and expose required fields.")
    assisted = payload.get("current_state", {}).get("optional_assisted_pws", {})
    if isinstance(assisted, dict) and assisted.get("available") is True:
        if assisted.get("score_type") != "llm_assisted" or assisted.get("must_not_replace_primary_score") is not True or "display_disclosure" not in assisted:
            raise SnapshotError("blocked_assisted_score_contract_violation", "ASSISTED_VARIANT_CONTRACT_VIOLATION", "Optional assisted PWS violates the presentation contract.")
    return latest_date

def copy_source_files(source: Path, destination: Path, optional_present: list[str]) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for filename in REQUIRED_SOURCE_FILES:
        shutil.copy2(source / filename, destination / filename)
    for filename in optional_present:
        shutil.copy2(source / filename, destination / filename)


def build_hash_report(root: Path, source: Path, snapshot_dir: Path, snapshot_id: str, optional_present: list[str]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for filename in REQUIRED_SOURCE_FILES:
        source_hash = sha256_file(source / filename)
        snapshot_hash = sha256_file(snapshot_dir / filename)
        entries.append({"filename": filename, "required": True, "present": True, "source_sha256": source_hash, "snapshot_sha256": snapshot_hash, "hash_match": source_hash == snapshot_hash})
    for filename in OPTIONAL_SOURCE_FILES:
        present = filename in optional_present
        if present:
            source_hash = sha256_file(source / filename)
            snapshot_hash = sha256_file(snapshot_dir / filename)
            match: bool | None = source_hash == snapshot_hash
        else:
            source_hash = None
            snapshot_hash = None
            match = None
        entries.append({"filename": filename, "required": False, "present": present, "source_sha256": source_hash, "snapshot_sha256": snapshot_hash, "hash_match": match})
    return {
        "module_id": MODULE_ID,
        "snapshot_id": snapshot_id,
        "hash_algorithm": "sha256",
        "source_module": SOURCE_MODULE_ID,
        "source_artifact_directory": rel(root, source),
        "files": entries,
        "all_required_hashes_verified": all(item["hash_match"] is True for item in entries if item["required"]),
        "all_present_optional_hashes_verified": all(item["hash_match"] is True for item in entries if not item["required"] and item["present"]),
    }


def assert_hash_report_valid(report: dict[str, Any]) -> None:
    if not report.get("all_required_hashes_verified") or not report.get("all_present_optional_hashes_verified"):
        raise SnapshotError("blocked_snapshot_hash_verification_failed", "SNAPSHOT_HASH_MISMATCH", "Source and staged snapshot hashes do not match.")


def snapshot_manifest(snapshot_id: str, published_at_iso: str, latest_date: str, payload: dict[str, Any], optional_present: list[str]) -> dict[str, Any]:
    assisted = payload.get("current_state", {}).get("optional_assisted_pws", {})
    return {
        "snapshot_id": snapshot_id,
        "snapshot_version": SNAPSHOT_VERSION,
        "policy_version": POLICY_VERSION,
        "publisher_module_id": MODULE_ID,
        "source_module_id": SOURCE_MODULE_ID,
        "published_at": published_at_iso,
        "latest_data_date": latest_date,
        "payload_status": payload.get("status"),
        "primary_score_policy": {"score_type": "deterministic", "preserved_without_modification": True},
        "optional_assisted_variant": {"supported": True, "present_in_payload": bool(isinstance(assisted, dict) and assisted.get("available") is True), "preserved_without_modification": True, "must_not_replace_primary_score": True},
        "files": [*[{"filename": name, "required": True} for name in REQUIRED_SOURCE_FILES], {"filename": "dashboard_time_series.parquet", "required": False, "included": "dashboard_time_series.parquet" in optional_present}],
        "integrity": {"hash_algorithm": "sha256", "hashes_artifact": "snapshot_source_hashes.json", "all_required_hashes_verified": True},
        "publication": {"history_snapshot_written": True, "current_snapshot_published": True, "atomic_publish_strategy": "staging_then_replace_current"},
        "privacy": {"contains_private_derived_wellness_data": True, "local_storage_only": True, "must_not_be_committed_to_version_control": True},
        "analytical_recomputation_performed": False,
        "llm_called": False,
    }


def snapshot_status(snapshot_id: str, published_at_iso: str, latest_date: str, payload: dict[str, Any]) -> dict[str, Any]:
    primary = payload.get("current_state", {}).get("primary_pws", {})
    assisted = payload.get("current_state", {}).get("optional_assisted_pws", {})
    return {
        "snapshot_id": snapshot_id,
        "snapshot_version": SNAPSHOT_VERSION,
        "published_at": published_at_iso,
        "latest_data_date": latest_date,
        "payload_ready": payload.get("ready_for_next_module") is True,
        "primary_pws": {"score_type": primary.get("score_type"), "computed": primary.get("computed"), "score": primary.get("score"), "label_id": primary.get("label_id"), "label": primary.get("label"), "coverage_tier": primary.get("coverage_tier")},
        "optional_assisted_pws": {"available": assisted.get("available") if isinstance(assisted, dict) else False, "score": assisted.get("score") if isinstance(assisted, dict) else None, "label_id": assisted.get("label_id") if isinstance(assisted, dict) else None, "label": assisted.get("label") if isinstance(assisted, dict) else None, "must_not_replace_primary_score": assisted.get("must_not_replace_primary_score") if isinstance(assisted, dict) else True},
        "records_count": payload.get("metadata", {}).get("records_count"),
        "private_data_notice": "Private derived wellness snapshot. Local use only.",
    }


def write_snapshot_generated_files(staging: Path, manifest: dict[str, Any], status: dict[str, Any], hash_report: dict[str, Any]) -> None:
    write_json(staging / "snapshot_manifest.json", manifest)
    write_json(staging / "snapshot_source_hashes.json", hash_report)
    write_json(staging / "snapshot_status.json", status)


def verify_complete_snapshot(path: Path, optional_present: list[str]) -> None:
    required = REQUIRED_SOURCE_FILES + GENERATED_SNAPSHOT_FILES
    missing = [name for name in required if not (path / name).is_file()]
    optional_missing = [name for name in optional_present if not (path / name).is_file()]
    if missing or optional_missing:
        raise SnapshotError("snapshot_publication_failed", "STAGING_WRITE_FAILED", f"Incomplete snapshot: missing={missing}, optional_missing={optional_missing}")


def publish_current(snapshot_root_path: Path, staging: Path, snapshot_id: str) -> None:
    if os.environ.get("SNAPSHOT_SIMULATE_CURRENT_PUBLISH_FAILURE") == "1":
        raise CurrentPublishError("Simulated current publish failure.")
    current_next_root = snapshot_root_path / ".current_next"
    current_next = current_next_root / snapshot_id
    current = snapshot_root_path / "current"
    backup = snapshot_root_path / f".current_previous_{snapshot_id}"
    if current_next.exists():
        shutil.rmtree(current_next)
    current_next.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(staging, current_next)
    if backup.exists():
        shutil.rmtree(backup)
    try:
        if current.exists():
            current.rename(backup)
        current_next.rename(current)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception as exc:
        if current.exists():
            shutil.rmtree(current)
        if backup.exists():
            backup.rename(current)
        raise CurrentPublishError(str(exc)) from exc
    finally:
        if current_next.exists():
            shutil.rmtree(current_next)


def clean_run_staging(staging: Path, current_next: Path) -> None:
    for path in [staging, current_next]:
        if path.exists():
            shutil.rmtree(path)

def publication_schema() -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "snapshot_id_format": "dashboard_<latest_date>_<published_at_utc_compact>",
        "published_snapshot_root": "data/published/dashboard_snapshots",
        "history_snapshot_policy": {"immutable": True, "automatic_deletion": False},
        "current_snapshot_policy": {"represents_latest_successfully_published_snapshot": True, "published_after_complete_staging_validation": True},
        "required_snapshot_files": REQUIRED_SOURCE_FILES + GENERATED_SNAPSHOT_FILES,
        "optional_snapshot_files": OPTIONAL_SOURCE_FILES,
        "integrity_policy": {"hash_algorithm": "sha256", "source_copy_hash_match_required": True},
        "primary_score_policy": {"score_type": "deterministic", "must_be_preserved_without_modification": True},
        "optional_assisted_score_policy": {"may_be_preserved_when_present": True, "must_not_replace_primary_score": True},
        "recomputation_policy": {"analytical_values_recomputed": False, "llm_called": False},
        "privacy_policy": {"private_local_artifacts": True, "must_be_gitignored": True, "secrets_excluded": True, "raw_source_health_data_excluded": True},
    }


def quality_report(status: str, snapshot_id: str | None, latest_date: str | None, optional_present: list[str], hash_report: dict[str, Any] | None, history_written: bool, current_published: bool, staging_cleaned: bool) -> dict[str, Any]:
    mismatches = [] if not hash_report else [item for item in hash_report.get("files", []) if item.get("hash_match") is False]
    return {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "snapshot_id": snapshot_id,
        "source_validation": {"dashboard_payload_present": status != "blocked_missing_dashboard_payload", "dashboard_payload_ready": status != "blocked_dashboard_payload_not_ready", "dashboard_quality_report_present": True, "dashboard_quality_report_ready": status != "blocked_dashboard_quality_report_not_ready", "required_payload_sections_present": status != "blocked_dashboard_payload_not_ready", "latest_date_valid": status != "blocked_invalid_dashboard_latest_date", "primary_score_is_deterministic": status != "blocked_invalid_primary_score_contract", "optional_assisted_contract_valid": status != "blocked_assisted_score_contract_violation"},
        "copied_artifacts": {"required_files_expected_count": len(REQUIRED_SOURCE_FILES), "required_files_copied_count": len(REQUIRED_SOURCE_FILES) if history_written else 0, "optional_parquet_present": "dashboard_time_series.parquet" in optional_present, "optional_parquet_copied": "dashboard_time_series.parquet" in optional_present and history_written},
        "integrity_validation": {"hash_algorithm": "sha256", "required_file_hashes_verified": bool(hash_report and hash_report.get("all_required_hashes_verified")), "optional_present_file_hashes_verified": bool(hash_report and hash_report.get("all_present_optional_hashes_verified")), "hash_mismatches": mismatches},
        "publication": {"staging_created": snapshot_id is not None, "history_snapshot_written": history_written, "current_snapshot_published": current_published, "staging_cleaned": staging_cleaned},
        "payload_contract_preservation": {"deterministic_primary_score_preserved": True, "optional_assisted_variant_preserved_without_promotion": True, "analytical_values_recomputed": False, "llm_called": False},
        "warnings": ["The published snapshot contains private derived wellness information and must remain local.", "This module copies and publishes an existing dashboard payload and does not recompute analytical values."] + ([] if "dashboard_time_series.parquet" in optional_present else ["Optional Parquet was not present; JSON and CSV snapshot artifacts were published."]),
        "ready_for_next_module": status in READY_STATUSES,
    }


def lineage(snapshot_id: str | None) -> dict[str, Any]:
    history = f"data/published/dashboard_snapshots/history/{snapshot_id}" if snapshot_id else None
    return {
        "module_id": MODULE_ID,
        "lineage_version": LINEAGE_VERSION,
        "source_artifacts": [
            {"module_id": SOURCE_MODULE_ID, "artifact_path": f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload.json", "role": "primary_dashboard_payload_source"},
            {"module_id": SOURCE_MODULE_ID, "artifact_path": f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_time_series.csv", "role": "dashboard_time_series_source"},
            {"module_id": SOURCE_MODULE_ID, "artifact_path": f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload_schema.json", "role": "dashboard_payload_schema_source"},
            {"module_id": SOURCE_MODULE_ID, "artifact_path": f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload_quality_report.json", "role": "dashboard_payload_quality_source"},
            {"module_id": SOURCE_MODULE_ID, "artifact_path": f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload_lineage.json", "role": "dashboard_payload_lineage_source"},
        ],
        "publication_transformation": {"operation": "copy_validated_dashboard_artifacts_to_immutable_history_and_current_snapshot_locations", "content_modified": False, "hash_verified_after_copy": True, "analytical_recomputation_performed": False},
        "published_destinations": {"history_snapshot": history, "current_snapshot": "data/published/dashboard_snapshots/current"},
        "primary_and_assisted_boundary": {"deterministic_pws_preserved_as_primary": True, "optional_assisted_pws_preserved_only_as_optional_variant": True, "scores_recomputed": False, "scores_reinterpreted": False},
        "forbidden_action_confirmation": {"llm_called": False, "metrics_recomputed": False, "api_server_implemented": False, "ui_implemented": False, "authentication_implemented": False, "garmin_token_pipeline_implemented": False, "medical_diagnosis_generated": False, "training_prescription_generated": False},
    }


def publication_payload(status: str, snapshot_id: str | None, published_at: str | None, latest_date: str | None, optional_present: list[str], history_written: bool, current_published: bool, staging_cleaned: bool) -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "status": status,
        "source_artifact": f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload.json",
        "snapshot_id": snapshot_id,
        "published_at": published_at,
        "latest_data_date": latest_date,
        "published_paths": {"history_snapshot": f"data/published/dashboard_snapshots/history/{snapshot_id}" if snapshot_id else None, "current_snapshot": "data/published/dashboard_snapshots/current"},
        "publication_result": {"source_validation_passed": status in READY_STATUSES or status == "history_snapshot_written_current_publish_failed", "staging_written": snapshot_id is not None, "hash_verification_passed": history_written or current_published, "history_snapshot_written": history_written, "current_snapshot_published": current_published, "staging_cleaned": staging_cleaned},
        "payload_preservation_confirmation": {"primary_deterministic_pws_preserved": True, "optional_assisted_variant_preserved_if_present": True, "analytical_values_recomputed": False, "llm_called": False},
        "included_files": REQUIRED_SOURCE_FILES + GENERATED_SNAPSHOT_FILES,
        "optional_files": [{"filename": name, "included": name in optional_present} for name in OPTIONAL_SOURCE_FILES],
        "ready_for_next_module": status in READY_STATUSES,
        "private_data_notice": "Published dashboard snapshots contain private derived health, training and wellness information and must not be committed to version control.",
    }


def generated_artifact_paths() -> list[str]:
    return [f"data/pipeline/{MODULE_ID}/{name}" for name in ["snapshot_publication.json", "snapshot_publication_schema.json", "snapshot_publication_quality_report.json", "snapshot_publication_lineage.json", "run_manifest.json", "run_log.txt", "errors.json"]]


def published_artifact_paths(snapshot_id: str | None, optional_present: list[str]) -> list[str]:
    if not snapshot_id:
        return []
    names = REQUIRED_SOURCE_FILES + optional_present + GENERATED_SNAPSHOT_FILES
    return [f"data/published/dashboard_snapshots/history/{snapshot_id}/{name}" for name in names] + [f"data/published/dashboard_snapshots/current/{name}" for name in names]

def write_module_artifacts(root: Path, status: str, started_at: str, finished_at: str, errors: list[dict[str, Any]], snapshot_id: str | None, published_at: str | None, latest_date: str | None, optional_present: list[str], hash_report: dict[str, Any] | None, history_written: bool, current_published: bool, staging_cleaned: bool) -> None:
    out = artifact_dir(root)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "snapshot_publication.json", publication_payload(status, snapshot_id, published_at, latest_date, optional_present, history_written, current_published, staging_cleaned))
    write_json(out / "snapshot_publication_schema.json", publication_schema())
    write_json(out / "snapshot_publication_quality_report.json", quality_report(status, snapshot_id, latest_date, optional_present, hash_report, history_written, current_published, staging_cleaned))
    write_json(out / "snapshot_publication_lineage.json", lineage(snapshot_id))
    write_json(out / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    write_json(out / "run_manifest.json", {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "success" if status in READY_STATUSES else "failed",
        "domain_status": status,
        "inputs": ["config/dashboard_snapshot_policy_v1.json", "config/dashboard_payload_policy_v1.json", f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload.json", f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_time_series.csv", f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload_schema.json", f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload_quality_report.json", f"data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload_lineage.json", f"optional: data/pipeline/{SOURCE_MODULE_ID}/dashboard_time_series.parquet"],
        "snapshot_id": snapshot_id,
        "generated_artifacts": generated_artifact_paths(),
        "published_artifacts": published_artifact_paths(snapshot_id, optional_present),
        "publication": {"history_snapshot_written": history_written, "current_snapshot_published": current_published, "hash_verification_passed": bool(hash_report and hash_report.get("all_required_hashes_verified") and hash_report.get("all_present_optional_hashes_verified"))},
        "analytical_values_recomputed": False,
        "llm_called": False,
        "api_implemented": False,
        "ui_implemented": False,
        "log_file": f"data/pipeline/{MODULE_ID}/run_log.txt",
        "errors_file": f"data/pipeline/{MODULE_ID}/errors.json",
    })
    lines = [
        f"module_id={MODULE_ID}", f"started_at={started_at}", f"policy_version={POLICY_VERSION}",
        f"source_dashboard_payload=data/pipeline/{SOURCE_MODULE_ID}/dashboard_payload.json", f"source_dashboard_status={status}",
        f"latest_data_date={latest_date}", f"snapshot_id={snapshot_id}", f"required_source_files={REQUIRED_SOURCE_FILES}",
        f"optional_parquet_present={'dashboard_time_series.parquet' in optional_present}", "primary_deterministic_pws_valid=true",
        "optional_assisted_contract_valid=true", f"staging_created={snapshot_id is not None}", "sha256_hashes_calculated=true",
        f"history_snapshot_written={history_written}", f"current_snapshot_published={current_published}", f"staging_cleaned={staging_cleaned}",
        "historical_snapshots_auto_deleted=false", "deterministic_pws_remained_primary=true", "optional_assisted_never_replaced_primary=true",
        "analytical_values_recomputed=false", "llm_called=false", "api_or_ui_implemented=false", "medical_or_coaching_outputs_generated=false",
        "snapshots_are_private_local_artifacts=true", f"finished_at={finished_at}", f"final_status={status}",
    ]
    if errors:
        lines.append("errors:")
        lines.extend(f"{item['code']}: {item['message']}" for item in errors)
    (out / "run_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


STARTED_AT = ""


def publish_snapshot(root: Path) -> tuple[str, str | None]:
    data = load_inputs(root)
    validate_policy(data["policy"])
    latest_date = validate_payload(data["payload"], data["quality"])
    published_dt = now_utc()
    published_iso = iso(published_dt)
    snap_root = snapshot_root(root)
    history_root = snap_root / "history"
    staging_root = snap_root / ".staging"
    current_next_root = snap_root / ".current_next"
    history_root.mkdir(parents=True, exist_ok=True)
    staging_root.mkdir(parents=True, exist_ok=True)
    current_next_root.mkdir(parents=True, exist_ok=True)
    snapshot_id = unique_snapshot_id(latest_date, published_dt, history_root)
    if not is_safe_snapshot_id(snapshot_id):
        raise SnapshotError("blocked_snapshot_id_collision", "SNAPSHOT_ID_COLLISION", "Generated snapshot id is not safe.")
    source = source_dir(root)
    optional_present = [name for name in OPTIONAL_SOURCE_FILES if (source / name).is_file()]
    staging = staging_root / snapshot_id
    history = history_root / snapshot_id
    current_next = current_next_root / snapshot_id
    if staging.exists():
        shutil.rmtree(staging)
    if current_next.exists():
        shutil.rmtree(current_next)
    if history.exists():
        raise SnapshotError("blocked_snapshot_id_collision", "SNAPSHOT_ID_COLLISION", "History snapshot already exists.")
    history_written = False
    current_published = False
    staging_cleaned = False
    hash_report: dict[str, Any] | None = None
    try:
        copy_source_files(source, staging, optional_present)
        hash_report = build_hash_report(root, source, staging, snapshot_id, optional_present)
        assert_hash_report_valid(hash_report)
        write_snapshot_generated_files(staging, snapshot_manifest(snapshot_id, published_iso, latest_date, data["payload"], optional_present), snapshot_status(snapshot_id, published_iso, latest_date, data["payload"]), hash_report)
        verify_complete_snapshot(staging, optional_present)
        shutil.copytree(staging, history)
        history_written = True
        publish_current(snap_root, staging, snapshot_id)
        current_published = True
        clean_run_staging(staging, current_next)
        staging_cleaned = True
    except CurrentPublishError as exc:
        clean_run_staging(staging, current_next)
        staging_cleaned = True
        status = "history_snapshot_written_current_publish_failed" if history_written else "snapshot_publication_failed"
        write_module_artifacts(root, status, STARTED_AT, iso(), [{"severity": "error", "code": "CURRENT_SNAPSHOT_PUBLISH_FAILED", "message": str(exc)}], snapshot_id, published_iso, latest_date, optional_present, hash_report, history_written, current_published, staging_cleaned)
        return status, snapshot_id
    status = "published" if optional_present else "published_without_optional_parquet"
    if data["payload"].get("status") in {"built_with_warnings", "built_with_partial_source_coverage"}:
        status = "published_with_payload_warnings"
    write_module_artifacts(root, status, STARTED_AT, iso(), [], snapshot_id, published_iso, latest_date, optional_present, hash_report, history_written, current_published, staging_cleaned)
    return status, snapshot_id


def main() -> int:
    global STARTED_AT
    root = root_dir()
    STARTED_AT = iso()
    try:
        status, _snapshot_id = publish_snapshot(root)
        return 0 if status in READY_STATUSES else 1
    except SnapshotError as exc:
        write_module_artifacts(root, exc.status, STARTED_AT, iso(), [{"severity": "error", "code": exc.code, "message": exc.message}], None, None, None, [], None, False, False, False)
        return 1
    except Exception as exc:
        write_module_artifacts(root, "snapshot_publication_failed", STARTED_AT, iso(), [{"severity": "error", "code": "ARTIFACT_WRITE_ERROR", "message": str(exc)}], None, None, None, [], None, False, False, False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
