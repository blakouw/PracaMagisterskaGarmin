from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_ID = "15_build_dashboard_payload"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "dashboard_payload_policy_v1"
DETERMINISTIC_ID = "12_compute_pws_score"
ASSISTED_ID = "13_validate_llm_weight_influence"
COMPONENTS = ["LQ", "REC", "CAP", "VS"]
READY_STATUSES = {
    "built",
    "built_with_optional_assisted_variant",
    "built_without_optional_assisted_artifact",
    "built_with_optional_assisted_skipped",
    "built_with_partial_source_coverage",
    "built_with_warnings",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("records", [])
    return value if isinstance(value, list) else []


def index_records(source: str, payload: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for record in records(payload):
        date = record.get("date")
        if date is None:
            errors.append({"severity": "error", "code": "DATE_FIELD_MISSING", "source": source})
            continue
        if not valid_date(date):
            errors.append({"severity": "error", "code": "DATE_VALUE_INVALID", "source": source, "date": date})
            continue
        if date in out:
            errors.append({"severity": "error", "code": "DUPLICATE_DATE_FOUND", "source": source, "date": date})
            continue
        out[date] = record
    return out


def load_inputs(root: Path, errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    required = {
        "policy": root / "config" / "dashboard_payload_policy_v1.json",
        "load_metrics": root / "data" / "pipeline" / "08_compute_load_metrics" / "load_metrics.json",
        "load_metrics_quality": root / "data" / "pipeline" / "08_compute_load_metrics" / "load_metrics_quality_report.json",
        "readiness": root / "data" / "pipeline" / "09_compute_readiness" / "readiness.json",
        "readiness_quality": root / "data" / "pipeline" / "09_compute_readiness" / "readiness_quality_report.json",
        "pws_components": root / "data" / "pipeline" / "10_compute_pws_components" / "pws_components.json",
        "pws_components_quality": root / "data" / "pipeline" / "10_compute_pws_components" / "pws_components_quality_report.json",
        "pws_weights": root / "data" / "pipeline" / "11_compute_pws_weights" / "pws_weights.json",
        "pws_weights_quality": root / "data" / "pipeline" / "11_compute_pws_weights" / "pws_weights_quality_report.json",
        "pws_score": root / "data" / "pipeline" / DETERMINISTIC_ID / "pws_score.json",
        "pws_score_quality": root / "data" / "pipeline" / DETERMINISTIC_ID / "pws_score_quality_report.json",
    }
    missing_code = {
        "policy": "DASHBOARD_PAYLOAD_POLICY_NOT_FOUND",
        "load_metrics": "LOAD_METRICS_NOT_FOUND",
        "readiness": "READINESS_NOT_FOUND",
        "pws_components": "PWS_COMPONENTS_NOT_FOUND",
        "pws_weights": "PWS_WEIGHTS_NOT_FOUND",
        "pws_score": "DETERMINISTIC_PWS_NOT_FOUND",
    }
    for key, path in required.items():
        if not path.is_file():
            errors.append({"severity": "error", "code": missing_code.get(key, "REQUIRED_SOURCE_NOT_FOUND"), "message": f"Missing required input: {rel(root, path)}"})
            return None
    optional = {
        "daily_features": root / "data" / "pipeline" / "07_build_daily_features" / "daily_features.json",
        "assisted": root / "data" / "pipeline" / ASSISTED_ID / "llm_assisted_pws.json",
        "assisted_quality": root / "data" / "pipeline" / ASSISTED_ID / "llm_assisted_pws_quality_report.json",
        "assisted_validation": root / "data" / "pipeline" / ASSISTED_ID / "llm_validation_report.json",
        "openai_assisted": root / "data" / "pipeline" / ASSISTED_ID / "openai_assisted_pws.json",
        "openai_assisted_quality": root / "data" / "pipeline" / ASSISTED_ID / "openai_assisted_pws_quality_report.json",
    }
    try:
        loaded = {key: read_json(path) for key, path in required.items()}
        for key, path in optional.items():
            loaded[key] = read_json(path) if path.is_file() else None
        loaded["paths"] = required | optional
        return loaded
    except json.JSONDecodeError as exc:
        errors.append({"severity": "error", "code": "REQUIRED_SOURCE_INVALID_JSON", "message": str(exc)})
        return None


def source_ready(payload: dict[str, Any]) -> bool:
    return payload.get("ready_for_next_module") is True


def validate_inputs(data: dict[str, Any], errors: list[dict[str, Any]]) -> bool:
    if data["policy"].get("policy_version") != POLICY_VERSION:
        errors.append({"severity": "error", "code": "DASHBOARD_PAYLOAD_POLICY_INVALID", "message": "Invalid dashboard payload policy version."})
        return False
    ok = True
    for key in ["load_metrics", "readiness", "pws_components", "pws_weights", "pws_score"]:
        if not source_ready(data[key]):
            errors.append({"severity": "error", "code": "REQUIRED_SOURCE_NOT_READY", "source": key})
            ok = False
    if not records(data["pws_score"]):
        errors.append({"severity": "error", "code": "DETERMINISTIC_PWS_NOT_FOUND", "message": "Deterministic PWS contains no records."})
        ok = False
    return ok


def field(record: dict[str, Any] | None, *names: str) -> Any:
    if not isinstance(record, dict):
        return None
    for name in names:
        if name in record:
            return record.get(name)
    return None


def load_metric(record: dict[str, Any] | None, name: str) -> Any:
    aliases = {
        "acwr_ewma": ["acwr_ewma", "ewma_acwr", "load_acwr_ewma"],
        "acwr_rolling": ["acwr_rolling", "rolling_acwr"],
        "acute_ewma_7d": ["acute_ewma_7d", "acute_load_ewma_7d"],
        "chronic_ewma_28d": ["chronic_ewma_28d", "chronic_load_ewma_28d"],
        "monotony_7d": ["monotony_7d"],
        "strain_7d": ["strain_7d"],
    }
    return field(record, *aliases[name])


def source_metric(feature: dict[str, Any] | None, readiness: dict[str, Any] | None, load: dict[str, Any] | None, name: str) -> Any:
    aliases = {
        "resting_hr_bpm": ["resting_hr_bpm", "resting_hr_avg_bpm"],
        "resting_hr_baseline_bpm": ["resting_hr_baseline_bpm"],
        "sleep_seconds": ["sleep_seconds"],
        "deep_sleep_seconds": ["deep_sleep_seconds"],
        "light_sleep_seconds": ["light_sleep_seconds"],
        "rem_sleep_seconds": ["rem_sleep_seconds"],
        "awake_sleep_seconds": ["awake_sleep_seconds"],
        "hrv_last_night_avg_ms": ["hrv_last_night_avg_ms"],
        "hrv_weekly_avg_ms": ["hrv_weekly_avg_ms"],
        "avg_sleep_spo2": ["avg_sleep_spo2"],
        "avg_sleep_respiration": ["avg_sleep_respiration"],
        "avg_stress": ["avg_stress"],
        "max_stress": ["max_stress"],
        "activity_duration_weighted_average_hr_bpm": ["activity_duration_weighted_average_hr_bpm"],
        "activity_maximum_hr_bpm": ["activity_maximum_hr_bpm"],
        "activity_total_duration_seconds": ["activity_total_duration_seconds"],
        "activity_total_distance_km": ["activity_total_distance_km"],
        "steps": ["steps"],
        "weight_kg": ["weight_kg"],
        "rhr_readiness_score": ["rhr_readiness_score"],
        "hrv_readiness_score": ["hrv_readiness_score"],
        "stress_readiness_score": ["stress_readiness_score"],
        "load_balance_readiness_score": ["load_balance_readiness_score"],
    }
    for record in (readiness, load, feature):
        value = field(record, *aliases[name])
        if value is not None:
            return value
    return None


def source_metric_section(feature: dict[str, Any] | None, readiness: dict[str, Any] | None, load: dict[str, Any] | None) -> dict[str, Any]:
    names = [
        "resting_hr_bpm", "resting_hr_baseline_bpm", "sleep_seconds", "deep_sleep_seconds",
        "light_sleep_seconds", "rem_sleep_seconds", "awake_sleep_seconds", "hrv_last_night_avg_ms",
        "hrv_weekly_avg_ms", "avg_sleep_spo2", "avg_sleep_respiration", "avg_stress", "max_stress",
        "activity_duration_weighted_average_hr_bpm", "activity_maximum_hr_bpm",
        "activity_total_duration_seconds", "activity_total_distance_km", "steps", "weight_kg",
        "rhr_readiness_score", "hrv_readiness_score", "stress_readiness_score",
        "load_balance_readiness_score",
    ]
    return {name: source_metric(feature, readiness, load, name) for name in names}


def readiness_section(record: dict[str, Any] | None) -> dict[str, Any]:
    score = field(record, "readiness_score", "score")
    return {
        "score": score,
        "score_field": "readiness_score",
        "computed": is_number(score),
        "status": field(record, "readiness_status", "status") or ("computed" if is_number(score) else "unavailable"),
        "label_id": field(record, "readiness_label_id", "label_id"),
        "label": field(record, "readiness_label", "label"),
        "coverage_ratio": field(record, "readiness_coverage_ratio", "coverage_ratio", "source_coverage_ratio"),
        "available_components": field(record, "available_readiness_components", "available_components") or [],
        "missing_components": field(record, "missing_readiness_components", "missing_components") or [],
        "display_disclosure": "Short-term daily readiness indicator. It is not the same as PWS.",
    }


def components_section(component_record: dict[str, Any] | None, score_record: dict[str, Any]) -> dict[str, Any]:
    available = score_record.get("pws_available_components") or field(component_record, "available_components") or []
    missing = score_record.get("pws_missing_components") or field(component_record, "missing_components") or []
    coverage = score_record.get("pws_coverage_ratio")
    return {
        "LQ": {"name": "Load Quality", "score": field(component_record, "lq_score"), "status": field(component_record, "lq_status")},
        "REC": {"name": "Recovery", "score": field(component_record, "rec_score"), "status": field(component_record, "rec_status")},
        "CAP": {"name": "Capacity", "score": field(component_record, "cap_score"), "status": field(component_record, "cap_status")},
        "VS": {"name": "Vital Stability", "score": field(component_record, "vs_score"), "status": field(component_record, "vs_status")},
        "available_components": available,
        "missing_components": missing,
        "coverage_ratio": coverage,
        "known_overlaps": [
            "LQ and REC may both contain ACWR exposure through readiness load balance.",
            "REC and VS may both rely on HRV and RHR under different interpretations.",
        ],
    }


def weights_section(weight_record: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "base_weights": field(weight_record, "base_component_weights"),
        "deterministic_effective_weights": field(weight_record, "deterministic_effective_weights"),
        "weights_ready_for_final_pws": field(weight_record, "weights_ready_for_final_pws"),
        "weights_readiness_status": field(weight_record, "weights_readiness_status"),
        "movement_limits_applied": field(weight_record, "deterministic_movement_limits_applied"),
        "overlap_controls_applied": field(weight_record, "overlap_controls_applied") or [],
        "llm_adjustment_eligible": field(weight_record, "llm_adjustment_eligible"),
        "display_disclosure": "Deterministic weights are validated upstream and are displayed without modification.",
    }


def load_section(record: dict[str, Any] | None) -> dict[str, Any]:
    out = {name: load_metric(record, name) for name in ["acwr_ewma", "acwr_rolling", "acute_ewma_7d", "chronic_ewma_28d", "monotony_7d", "strain_7d"]}
    out["display_disclosure"] = "Load metrics are presented as analytical context and are not injury predictions."
    return out


def assisted_record_status(record: dict[str, Any] | None, source_status: str | None = None) -> str:
    if not record:
        return "not_available_llm_path_skipped"
    if record.get("pws_llm_assisted_computed") is True:
        if record.get("proposal_interpretation_mode") == "permissive_simplex_normalization":
            return "available_assisted_variant_with_normalization_warnings"
        if record.get("llm_adjustment_applied") is True:
            return "available_validated_assisted_variant"
        return "available_no_adjustment_same_as_deterministic"
    record_status = record.get("llm_assisted_status")
    if record_status == "proposal_rejected":
        return "not_available_proposal_rejected"
    if record_status in {"error_llm_no_assisted_score_delivered", "llm_request_failed"}:
        return "error_llm_no_assisted_score_delivered"
    if record.get("llm_called") is True:
        return "error_llm_no_assisted_score_delivered"
    if source_status == "completed_no_adjustment_proposed":
        return "not_available_no_adjustment_proposed"
    if source_status == "completed_proposal_rejected":
        return "not_available_proposal_rejected"
    if source_status in {"llm_response_invalid", "llm_request_failed"}:
        return "error_llm_no_assisted_score_delivered"
    return "not_available_llm_path_skipped"


def assisted_info(assisted: dict[str, Any] | None, validation: dict[str, Any] | None) -> dict[str, Any]:
    if not assisted:
        return {
            "artifact_present": False,
            "status": "not_available_no_assisted_artifact",
            "record": None,
            "records": [],
            "records_by_date": {},
            "validation": validation,
        }
    records = assisted.get("records") if isinstance(assisted.get("records"), list) else []
    records = [record for record in records if isinstance(record, dict)]
    compatibility_record = assisted.get("record") if isinstance(assisted.get("record"), dict) else None
    if not records and compatibility_record:
        records = [compatibility_record]
    records.sort(key=lambda record: str(record.get("date") or ""))
    records_by_date = {
        record["date"]: record
        for record in records
        if isinstance(record.get("date"), str)
    }
    source_status = assisted.get("status")
    statuses = [assisted_record_status(record, source_status) for record in records]
    if "available_assisted_variant_with_normalization_warnings" in statuses:
        mapped = "available_assisted_variant_with_normalization_warnings"
    elif "available_validated_assisted_variant" in statuses:
        mapped = "available_validated_assisted_variant"
    elif "available_no_adjustment_same_as_deterministic" in statuses:
        mapped = "available_no_adjustment_same_as_deterministic"
    elif "error_llm_no_assisted_score_delivered" in statuses:
        mapped = "error_llm_no_assisted_score_delivered"
    elif "not_available_no_adjustment_proposed" in statuses:
        mapped = "not_available_no_adjustment_proposed"
    elif "not_available_proposal_rejected" in statuses:
        mapped = "not_available_proposal_rejected"
    else:
        mapped = "not_available_llm_path_skipped"
    return {
        "artifact_present": True,
        "status": mapped,
        "source_status": source_status,
        "record": records[-1] if records else compatibility_record,
        "records": records,
        "records_by_date": records_by_date,
        "validation": validation,
    }


ASSISTED_AVAILABLE_STATUSES = {"available_validated_assisted_variant", "available_assisted_variant_with_normalization_warnings", "available_no_adjustment_same_as_deterministic"}


def optional_assisted_section(info: dict[str, Any], current_date: str) -> dict[str, Any]:
    record = info.get("records_by_date", {}).get(current_date)
    status = assisted_record_status(record, info.get("source_status")) if record else (
        "not_available_for_current_date" if info.get("artifact_present") else info.get("status")
    )
    if status in ASSISTED_AVAILABLE_STATUSES and record:
        no_adjustment = status == "available_no_adjustment_same_as_deterministic"
        normalized_with_warnings = status == "available_assisted_variant_with_normalization_warnings"
        return {
            "available": True,
            "score_type": "llm_assisted",
            "score_field": "pws_llm_assisted",
            "score": record.get("pws_llm_assisted"),
            "computed": True,
            "status": status,
            "analysis_status": status,
            "label_id": record.get("pws_llm_assisted_label_id"),
            "label": record.get("pws_llm_assisted_label"),
            "delta_from_deterministic": record.get("pws_llm_assisted_delta_from_deterministic"),
            "validated_adjusted_weights": record.get("validated_llm_adjusted_weights"),
            "raw_proposed_weight_deltas": record.get("llm_proposed_weight_deltas"),
            "effective_weight_deltas": record.get("llm_effective_weight_deltas"),
            "proposal_interpretation_mode": record.get("proposal_interpretation_mode"),
            "validation_warnings": record.get("llm_guardrail_violations") or [],
            "conversation_log_path": f"data/pipeline/{ASSISTED_ID}/llm_conversations/{record.get('date')}.json",
            "llm_response_decision": record.get("llm_response_decision"),
            "llm_reason_summary": record.get("llm_reason_summary"),
            "llm_tool_execution": record.get("llm_tool_execution"),
            "llm_error": None,
            "must_not_replace_primary_score": True,
            "display_disclosure": "LLM returned a validated no-adjustment decision, so the assisted comparison is recorded with the same score as deterministic PWS." if no_adjustment else ("Optional LLM-assisted variant calculated from a preserved raw proposal after deterministic normalization to valid available weights. Guardrail findings remain visible as warnings." if normalized_with_warnings else "Optional LLM-assisted variant calculated separately after validated bounded weight adjustment. The deterministic PWS remains the primary score."),
        }
    disclosures = {
        "not_available_no_assisted_artifact": "Optional LLM-assisted analysis has not been executed or no artifact is available.",
        "not_available_llm_path_skipped": "Optional LLM-assisted analysis was skipped or did not run.",
        "not_available_no_adjustment_proposed": "No optional assisted score exists because the LLM did not propose a validated weight adjustment.",
        "not_available_proposal_rejected": "No optional assisted score exists because the proposed weight adjustment failed deterministic validation.",
        "not_available_for_current_date": "Optional assisted analysis is not available for the currently displayed date.",
        "error_llm_no_assisted_score_delivered": "LLM did not deliver a validated assisted PWS value.",
    }
    return {
        "available": False,
        "computed": False,
        "status": status,
        "analysis_status": status,
        "llm_response_decision": record.get("llm_response_decision") if record else None,
        "llm_reason_summary": record.get("llm_reason_summary") if record else None,
        "llm_tool_execution": record.get("llm_tool_execution") if record else None,
        "llm_error": "LLM did not deliver assisted PWS values." if status == "error_llm_no_assisted_score_delivered" else None,
        "must_not_replace_primary_score": True,
        "display_disclosure": disclosures.get(status, "Optional assisted score is not available."),
    }


def external_assisted_section(info: dict[str, Any], current_date: str) -> dict[str, Any]:
    section = optional_assisted_section(info, current_date)
    record = info.get("records_by_date", {}).get(current_date)
    section.update({
        "score_type": "external_llm_assisted" if section.get("available") else None,
        "score_field": "pws_openai_assisted" if section.get("available") else None,
        "provider": (record or {}).get("provider", "openai"),
        "model": (record or {}).get("model"),
        "must_not_replace_local_llm_variant": True,
    })
    if record:
        section["conversation_log_path"] = f"data/pipeline/{ASSISTED_ID}/openai_conversations/{record.get('date')}.json"
    return section


def primary_pws_section(score_record: dict[str, Any]) -> dict[str, Any]:
    computed = score_record.get("pws_deterministic_computed") is True
    return {
        "score_type": "deterministic",
        "score_field": "pws_deterministic",
        "score": score_record.get("pws_deterministic"),
        "computed": computed,
        "status": score_record.get("pws_status"),
        "label_id": score_record.get("pws_label_id"),
        "label": score_record.get("pws_label"),
        "coverage_ratio": score_record.get("pws_coverage_ratio"),
        "coverage_tier": score_record.get("pws_coverage_tier"),
        "computed_from_partial_coverage": score_record.get("pws_computed_from_partial_coverage"),
        "available_components": score_record.get("pws_available_components") or [],
        "missing_components": score_record.get("pws_missing_components") or [],
        "weighted_contributions": score_record.get("pws_weighted_contributions") or {},
        "display_disclosure": "Primary deterministic PWS calculated from validated deterministic component weights." if computed else "Deterministic PWS is unavailable for this date because minimum component coverage requirements were not satisfied.",
    }


def row_for(date: str, score: dict[str, Any], readiness: dict[str, Any] | None, components: dict[str, Any] | None, weights: dict[str, Any] | None, load: dict[str, Any] | None, feature: dict[str, Any] | None, assisted_info_payload: dict[str, Any], external_assisted_info_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    deterministic_weights = score.get("pws_deterministic_weights") or field(weights, "deterministic_effective_weights") or {}
    assisted_record = assisted_info_payload.get("records_by_date", {}).get(date)
    assisted_available = bool(assisted_record and assisted_record.get("pws_llm_assisted_computed") is True)
    assisted_weights = assisted_record.get("validated_llm_adjusted_weights") if assisted_available else None
    external_record = (external_assisted_info_payload or {}).get("records_by_date", {}).get(date)
    external_available = bool(external_record and external_record.get("pws_openai_assisted_computed") is True)
    external_weights = external_record.get("validated_llm_adjusted_weights") if external_available else None
    source_metrics = source_metric_section(feature, readiness, load)
    return {
        "date": date,
        "pws_deterministic": score.get("pws_deterministic"),
        "pws_deterministic_computed": score.get("pws_deterministic_computed"),
        "pws_label_id": score.get("pws_label_id"),
        "pws_label": score.get("pws_label"),
        "pws_coverage_ratio": score.get("pws_coverage_ratio"),
        "pws_coverage_tier": score.get("pws_coverage_tier"),
        "pws_computed_from_partial_coverage": score.get("pws_computed_from_partial_coverage"),
        "readiness_score": field(readiness, "readiness_score", "score"),
        "readiness_status": field(readiness, "readiness_status", "status"),
        "readiness_label_id": field(readiness, "readiness_label_id", "label_id"),
        "readiness_label": field(readiness, "readiness_label", "label"),
        "readiness_coverage_ratio": field(readiness, "readiness_coverage_ratio", "coverage_ratio", "source_coverage_ratio"),
        "lq_score": field(components, "lq_score"),
        "rec_score": field(components, "rec_score"),
        "cap_score": field(components, "cap_score"),
        "vs_score": field(components, "vs_score"),
        "weight_lq": deterministic_weights.get("LQ") if isinstance(deterministic_weights, dict) else None,
        "weight_rec": deterministic_weights.get("REC") if isinstance(deterministic_weights, dict) else None,
        "weight_cap": deterministic_weights.get("CAP") if isinstance(deterministic_weights, dict) else None,
        "weight_vs": deterministic_weights.get("VS") if isinstance(deterministic_weights, dict) else None,
        "local_llm_weight_lq": assisted_weights.get("LQ") if isinstance(assisted_weights, dict) else None,
        "local_llm_weight_rec": assisted_weights.get("REC") if isinstance(assisted_weights, dict) else None,
        "local_llm_weight_cap": assisted_weights.get("CAP") if isinstance(assisted_weights, dict) else None,
        "local_llm_weight_vs": assisted_weights.get("VS") if isinstance(assisted_weights, dict) else None,
        "openai_weight_lq": external_weights.get("LQ") if isinstance(external_weights, dict) else None,
        "openai_weight_rec": external_weights.get("REC") if isinstance(external_weights, dict) else None,
        "openai_weight_cap": external_weights.get("CAP") if isinstance(external_weights, dict) else None,
        "openai_weight_vs": external_weights.get("VS") if isinstance(external_weights, dict) else None,
        "acwr_ewma": load_metric(load, "acwr_ewma"),
        "acwr_rolling": load_metric(load, "acwr_rolling"),
        "acute_ewma_7d": load_metric(load, "acute_ewma_7d"),
        "chronic_ewma_28d": load_metric(load, "chronic_ewma_28d"),
        "monotony_7d": load_metric(load, "monotony_7d"),
        "strain_7d": load_metric(load, "strain_7d"),
        **source_metrics,
        "optional_assisted_pws": assisted_record.get("pws_llm_assisted") if assisted_available else None,
        "optional_assisted_label_id": assisted_record.get("pws_llm_assisted_label_id") if assisted_available else None,
        "optional_assisted_delta_from_deterministic": assisted_record.get("pws_llm_assisted_delta_from_deterministic") if assisted_available else None,
        "external_assisted_pws": external_record.get("pws_openai_assisted") if external_available else None,
        "external_assisted_label_id": external_record.get("pws_llm_assisted_label_id") if external_available else None,
        "external_assisted_delta_from_deterministic": external_record.get("pws_llm_assisted_delta_from_deterministic") if external_available else None,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "date", "pws_deterministic", "pws_deterministic_computed", "pws_label_id", "pws_label",
        "pws_coverage_ratio", "pws_coverage_tier", "pws_computed_from_partial_coverage",
        "readiness_score", "readiness_status", "readiness_label_id", "readiness_label", "readiness_coverage_ratio",
        "lq_score", "rec_score", "cap_score", "vs_score", "weight_lq", "weight_rec", "weight_cap", "weight_vs",
        "local_llm_weight_lq", "local_llm_weight_rec", "local_llm_weight_cap", "local_llm_weight_vs",
        "openai_weight_lq", "openai_weight_rec", "openai_weight_cap", "openai_weight_vs",
        "acwr_ewma", "acwr_rolling", "acute_ewma_7d", "chronic_ewma_28d", "monotony_7d", "strain_7d",
        "resting_hr_bpm", "resting_hr_baseline_bpm", "sleep_seconds", "deep_sleep_seconds", "light_sleep_seconds",
        "rem_sleep_seconds", "awake_sleep_seconds", "hrv_last_night_avg_ms", "hrv_weekly_avg_ms",
        "avg_sleep_spo2", "avg_sleep_respiration", "avg_stress", "max_stress",
        "activity_duration_weighted_average_hr_bpm", "activity_maximum_hr_bpm", "activity_total_duration_seconds",
        "activity_total_distance_km", "steps", "weight_kg", "rhr_readiness_score",
        "hrv_readiness_score", "stress_readiness_score", "load_balance_readiness_score",
        "optional_assisted_pws", "optional_assisted_label_id", "optional_assisted_delta_from_deterministic",
        "external_assisted_pws", "external_assisted_label_id", "external_assisted_delta_from_deterministic",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in fields})


def try_write_parquet(path: Path, rows: list[dict[str, Any]]) -> tuple[bool, str | None]:
    try:
        import pandas as pd  # type: ignore
        frame = pd.DataFrame(rows)
        frame.to_parquet(path, index=False)
        return True, None
    except ImportError:
        return False, "PARQUET_DEPENDENCY_UNAVAILABLE"
    except Exception as exc:
        return False, f"PARQUET_WRITE_FAILED: {exc}"


def count_labels(rows: list[dict[str, Any]]) -> dict[str, int]:
    out = {"low": 0, "reduced": 0, "balanced": 0, "strong": 0, "insufficient_data": 0}
    for row in rows:
        key = row.get("pws_label_id") or "insufficient_data"
        if key not in out:
            out[key] = 0
        out[key] += 1
    return out


def build(root: Path) -> tuple[int, str]:
    started = now_iso()
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    artifact_dir.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    data = load_inputs(root, errors)
    if data is None:
        status = "blocked_missing_deterministic_pws" if any(e["code"] == "DETERMINISTIC_PWS_NOT_FOUND" for e in errors) else "blocked_missing_required_source"
        write_failure(root, started, status, errors)
        return 1, status
    if not validate_inputs(data, errors):
        status = "invalid_dashboard_payload_policy" if any(e["code"] == "DASHBOARD_PAYLOAD_POLICY_INVALID" for e in errors) else "blocked_required_source_not_ready"
        write_failure(root, started, status, errors)
        return 1, status
    indexes = {
        "load_metrics": index_records("load_metrics", data["load_metrics"], errors),
        "readiness": index_records("readiness", data["readiness"], errors),
        "pws_components": index_records("pws_components", data["pws_components"], errors),
        "pws_weights": index_records("pws_weights", data["pws_weights"], errors),
        "pws_score": index_records("pws_score", data["pws_score"], errors),
        "daily_features": index_records("daily_features", data["daily_features"], errors) if isinstance(data.get("daily_features"), dict) else {},
    }
    if any(e["code"] == "DUPLICATE_DATE_FOUND" for e in errors):
        write_failure(root, started, "blocked_duplicate_dates", errors)
        return 1, "blocked_duplicate_dates"
    axis = sorted(indexes["pws_score"])
    latest = axis[-1]
    assisted = assisted_info(data.get("assisted"), data.get("assisted_validation"))
    external_assisted = assisted_info(data.get("openai_assisted"), None)
    time_series = [
        row_for(
            date,
            indexes["pws_score"][date],
            indexes["readiness"].get(date),
            indexes["pws_components"].get(date),
            indexes["pws_weights"].get(date),
            indexes["load_metrics"].get(date),
            indexes["daily_features"].get(date),
            assisted,
            external_assisted,
        )
        for date in axis
    ]
    latest_score = indexes["pws_score"][latest]
    current = {
        "date": latest,
        "primary_pws": primary_pws_section(latest_score),
        "optional_assisted_pws": optional_assisted_section(assisted, latest),
        "external_assisted_pws": external_assisted_section(external_assisted, latest),
        "readiness": readiness_section(indexes["readiness"].get(latest)),
        "pws_components": components_section(indexes["pws_components"].get(latest), latest_score),
        "pws_weights": weights_section(indexes["pws_weights"].get(latest)),
        "load_metrics": load_section(indexes["load_metrics"].get(latest)),
        "coverage": {
            "pws_coverage_tier": latest_score.get("pws_coverage_tier"),
            "pws_coverage_ratio": latest_score.get("pws_coverage_ratio"),
            "pws_computed_from_partial_coverage": latest_score.get("pws_computed_from_partial_coverage"),
            "readiness_coverage_ratio": field(indexes["readiness"].get(latest), "readiness_coverage_ratio", "coverage_ratio", "source_coverage_ratio"),
            "pws_components_coverage_ratio": latest_score.get("pws_coverage_ratio"),
            "missing_pws_components": latest_score.get("pws_missing_components") or [],
            "missing_readiness_components": field(indexes["readiness"].get(latest), "missing_readiness_components", "missing_components") or [],
        },
        "source_statuses": {},
        "disclosures": current_disclosures(latest_score),
    }
    required_sources = {
        name: {"present": True, "ready": source_ready(data[name]), "artifact_status": data[name].get("status")}
        for name in ["load_metrics", "readiness", "pws_components", "pws_weights", "pws_score"]
    }
    metadata = {
        "payload_version": "dashboard_payload_v1",
        "date_axis_source": "pws_deterministic",
        "records_count": len(axis),
        "date_range": {"first_date": axis[0], "last_date": axis[-1]},
        "latest_date": latest,
        "primary_score_type": "deterministic",
        "optional_assisted_variant_supported": True,
        "external_assisted_variant_supported": True,
        "source_modules": source_modules(data, assisted, external_assisted),
        "additional_daily_signal_fields": [
            "resting_hr_bpm", "sleep_seconds", "hrv_last_night_avg_ms", "avg_sleep_spo2",
            "avg_sleep_respiration", "avg_stress",
            "activity_duration_weighted_average_hr_bpm", "activity_maximum_hr_bpm",
        ],
    }
    join_validation = join_quality(axis, indexes, assisted)
    quality = quality_section(time_series, indexes, assisted, latest, current, data, join_validation)
    quality["optional_sources"]["pws_openai_assisted"] = {
        "present": external_assisted["artifact_present"],
        "status": external_assisted.get("source_status"),
        "analysis_status": external_assisted.get("status"),
        "assisted_score_available": any(record.get("pws_openai_assisted_computed") is True for record in external_assisted.get("records", [])),
        "assisted_dates": sorted(date for date, record in external_assisted.get("records_by_date", {}).items() if record.get("pws_openai_assisted_computed") is True),
    }
    quality["presentation_availability"]["external_assisted_score_count"] = sum(1 for row in time_series if row.get("external_assisted_pws") is not None)
    quality["presentation_availability"]["current_state_external_assisted_pws_available"] = current["external_assisted_pws"].get("available") is True
    parquet_path = artifact_dir / "dashboard_time_series.parquet"
    parquet_written, parquet_warning = try_write_parquet(parquet_path, time_series)
    if parquet_warning:
        errors.append({"severity": "warning", "code": parquet_warning.split(":")[0], "message": parquet_warning})
    quality["parquet_output"] = {"requested": True, "written": parquet_written, "warning": parquet_warning}
    payload = {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "status": select_status(assisted, time_series),
        "payload_type": "local_dashboard_presentation_payload",
        "generated_at": now_iso(),
        "metadata": metadata,
        "current_state": current,
        "time_series": time_series,
        "quality_and_coverage": quality,
        "disclosures": disclosures(),
        "ready_for_next_module": True,
        "private_data_notice": "Dashboard payload contains private derived health, activity and wellness information and must not be committed to version control.",
    }
    domain_status = payload["status"]
    write_json(artifact_dir / "dashboard_payload.json", payload)
    write_csv(artifact_dir / "dashboard_time_series.csv", time_series)
    write_json(artifact_dir / "dashboard_payload_schema.json", schema())
    write_json(artifact_dir / "dashboard_payload_quality_report.json", {**quality, "module_id": MODULE_ID, "policy_version": POLICY_VERSION, "status": domain_status, "ready_for_next_module": True})
    write_json(artifact_dir / "dashboard_payload_lineage.json", lineage(assisted, external_assisted))
    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    generated = [
        f"data/pipeline/{MODULE_ID}/dashboard_payload.json",
        f"data/pipeline/{MODULE_ID}/dashboard_time_series.csv",
        f"data/pipeline/{MODULE_ID}/dashboard_payload_schema.json",
        f"data/pipeline/{MODULE_ID}/dashboard_payload_quality_report.json",
        f"data/pipeline/{MODULE_ID}/dashboard_payload_lineage.json",
        f"data/pipeline/{MODULE_ID}/run_manifest.json",
        f"data/pipeline/{MODULE_ID}/run_log.txt",
        f"data/pipeline/{MODULE_ID}/errors.json",
    ]
    manifest = {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started,
        "finished_at": now_iso(),
        "execution_status": "success",
        "domain_status": domain_status,
        "inputs": [
            "config/dashboard_payload_policy_v1.json",
            "data/pipeline/08_compute_load_metrics/load_metrics.json",
            "data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json",
            "data/pipeline/09_compute_readiness/readiness.json",
            "optional: data/pipeline/07_build_daily_features/daily_features.json",
            "data/pipeline/09_compute_readiness/readiness_quality_report.json",
            "data/pipeline/10_compute_pws_components/pws_components.json",
            "data/pipeline/10_compute_pws_components/pws_components_quality_report.json",
            "data/pipeline/11_compute_pws_weights/pws_weights.json",
            "data/pipeline/11_compute_pws_weights/pws_weights_quality_report.json",
            f"data/pipeline/{DETERMINISTIC_ID}/pws_score.json",
            f"data/pipeline/{DETERMINISTIC_ID}/pws_score_quality_report.json",
            f"optional: data/pipeline/{ASSISTED_ID}/llm_assisted_pws.json",
            f"optional: data/pipeline/{ASSISTED_ID}/openai_assisted_pws.json",
        ],
        "generated_artifacts": generated,
        "optional_generated_artifacts": [{"path": f"data/pipeline/{MODULE_ID}/dashboard_time_series.parquet", "written": parquet_written, "reason_if_not_written": parquet_warning}],
        "primary_score_source": "pws_deterministic",
        "optional_assisted_score_included": current["optional_assisted_pws"].get("available") is True,
        "external_assisted_score_included": current["external_assisted_pws"].get("available") is True,
        "analytical_values_recomputed": False,
        "llm_called": False,
        "log_file": f"data/pipeline/{MODULE_ID}/run_log.txt",
        "errors_file": f"data/pipeline/{MODULE_ID}/errors.json",
    }
    write_json(artifact_dir / "run_manifest.json", manifest)
    write_log(artifact_dir / "run_log.txt", started, domain_status, payload, quality, assisted, parquet_written, parquet_warning)
    return 0, domain_status


def select_status(assisted: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    if assisted["status"] in ASSISTED_AVAILABLE_STATUSES:
        return "built_with_optional_assisted_variant"
    if not assisted["artifact_present"]:
        return "built_without_optional_assisted_artifact"
    if assisted["artifact_present"]:
        return "built_with_optional_assisted_skipped"
    if any(row.get("pws_coverage_tier") != "full" for row in rows):
        return "built_with_partial_source_coverage"
    return "built"


def source_modules(data: dict[str, Any], assisted: dict[str, Any], external_assisted: dict[str, Any]) -> dict[str, Any]:
    daily_features = data.get("daily_features") if isinstance(data.get("daily_features"), dict) else None
    return {
        "daily_features": {"module_id": "07_build_daily_features", "artifact_present": daily_features is not None, "artifact_status": daily_features.get("status") if daily_features else None, "ready_for_next_module": source_ready(daily_features) if daily_features else None, "optional": True},
        "load_metrics": {"module_id": "08_compute_load_metrics", "artifact_status": data["load_metrics"].get("status"), "ready_for_next_module": source_ready(data["load_metrics"])},
        "readiness": {"module_id": "09_compute_readiness", "artifact_status": data["readiness"].get("status"), "ready_for_next_module": source_ready(data["readiness"])},
        "pws_components": {"module_id": "10_compute_pws_components", "artifact_status": data["pws_components"].get("status"), "ready_for_next_module": source_ready(data["pws_components"])},
        "pws_weights": {"module_id": "11_compute_pws_weights", "artifact_status": data["pws_weights"].get("status"), "ready_for_next_module": source_ready(data["pws_weights"])},
        "pws_deterministic": {"module_id": DETERMINISTIC_ID, "artifact_status": data["pws_score"].get("status"), "ready_for_next_module": source_ready(data["pws_score"])},
        "pws_llm_assisted": {"module_id": ASSISTED_ID, "artifact_present": assisted["artifact_present"], "artifact_status": assisted.get("source_status"), "ready_for_next_module": True, "optional": True},
        "pws_openai_assisted": {"module_id": ASSISTED_ID, "artifact_present": external_assisted["artifact_present"], "artifact_status": external_assisted.get("source_status"), "ready_for_next_module": True, "optional": True},
    }


def join_quality(axis: list[str], indexes: dict[str, dict[str, dict[str, Any]]], assisted: dict[str, Any]) -> dict[str, list[str]]:
    axis_set = set(axis)
    out = {}
    for key in ["load_metrics", "readiness", "pws_components", "pws_weights"]:
        out[f"missing_{key}_dates_on_primary_axis"] = [date for date in axis if date not in indexes[key]]
        out[f"orphan_{key}_dates"] = sorted(set(indexes[key]) - axis_set)
    out["orphan_assisted_dates"] = sorted(
        date for date in assisted.get("records_by_date", {}) if date not in axis_set
    )
    return out


def quality_section(rows: list[dict[str, Any]], indexes: dict[str, dict[str, dict[str, Any]]], assisted: dict[str, Any], latest: str, current: dict[str, Any], data: dict[str, Any], join_validation: dict[str, list[str]]) -> dict[str, Any]:
    computed = sum(1 for row in rows if row.get("pws_deterministic_computed") is True)
    tiers: dict[str, int] = {}
    for row in rows:
        tier = row.get("pws_coverage_tier") or "unknown"
        tiers[tier] = tiers.get(tier, 0) + 1
    component_availability = {}
    for component, field_name in [("LQ", "lq_score"), ("REC", "rec_score"), ("CAP", "cap_score"), ("VS", "vs_score")]:
        count = sum(1 for rec in indexes["pws_components"].values() if rec.get(field_name) is not None)
        component_availability[component] = {"available_count": count, "coverage_ratio": round(count / len(rows), 4) if rows else None}
    return {
        "records_count": len(rows),
        "latest_date": latest,
        "required_sources": {key: {"present": True, "ready": source_ready(data[key])} for key in ["load_metrics", "readiness", "pws_components", "pws_weights", "pws_score"]},
        "optional_sources": {"pws_llm_assisted": {"present": assisted["artifact_present"], "status": assisted.get("source_status"), "analysis_status": assisted.get("status"), "assisted_score_available": any(record.get("pws_llm_assisted_computed") is True for record in assisted.get("records", [])), "assisted_dates": sorted(date for date, record in assisted.get("records_by_date", {}).items() if record.get("pws_llm_assisted_computed") is True), "latest_assisted_date": max(assisted.get("records_by_date", {}), default=None)}},
        "join_validation": join_validation,
        "presentation_availability": {"primary_pws_computed_count": computed, "primary_pws_unavailable_count": len(rows) - computed, "optional_assisted_score_count": sum(1 for row in rows if row.get("optional_assisted_pws") is not None), "current_state_primary_pws_available": current["primary_pws"]["computed"], "current_state_optional_assisted_pws_available": current["optional_assisted_pws"].get("available") is True},
        "coverage_tiers": tiers,
        "pws_label_counts": count_labels(rows),
        "readiness_availability": {"computed_count": sum(1 for row in rows if row.get("readiness_score") is not None), "insufficient_data_count": sum(1 for row in rows if row.get("readiness_score") is None)},
        "component_availability": component_availability,
        "weight_availability": {"weights_ready_for_final_pws_count": sum(1 for rec in indexes["pws_weights"].values() if rec.get("weights_ready_for_final_pws") is True), "weights_not_ready_for_final_pws_count": sum(1 for rec in indexes["pws_weights"].values() if rec.get("weights_ready_for_final_pws") is not True)},
        "recomputation_confirmation": {"load_metrics_recomputed": False, "readiness_recomputed": False, "pws_components_recomputed": False, "pws_weights_recomputed": False, "pws_deterministic_recomputed": False, "pws_llm_assisted_recomputed": False, "llm_called": False},
        "warnings": [
            "Dashboard payload is a presentation artifact and does not recalculate analytical values.",
            "Deterministic PWS remains the primary score.",
            "Optional LLM-assisted PWS is exposed only as a separately labelled comparison variant when available.",
            "PWS and readiness are not medical diagnoses, injury predictions or professional training prescriptions.",
        ],
    }


def current_disclosures(score_record: dict[str, Any]) -> list[str]:
    out = [
        "Deterministic PWS is the primary auditable score.",
        "Optional LLM-assisted PWS, when available, is a separate comparison variant and never replaces deterministic PWS.",
        "PWS and readiness are heuristic decision-support indicators and are not medical diagnoses, injury predictions or professional training prescriptions.",
        "Missing values remain null and are not replaced with zero.",
    ]
    if score_record.get("pws_computed_from_partial_coverage") is True:
        out.append("This deterministic PWS value was calculated from an eligible but incomplete component set. Interpret it with its disclosed coverage limitation.")
    return out


def disclosures() -> dict[str, Any]:
    return {
        "primary_score": "Deterministic PWS is the primary auditable product score.",
        "optional_assisted_score": "An LLM-assisted score, when available, is a separately labelled optional comparison variant based on a validated bounded weight adjustment and never replaces deterministic PWS.",
        "external_assisted_score": "An external OpenAI-assisted score, when available, uses the same bounded context and deterministic validation as the local LLM variant and never replaces deterministic PWS.",
        "coverage": "A score calculated from partial eligible component coverage must be presented together with its coverage limitation.",
        "missing_values": "Missing values remain null and are never replaced with zero.",
        "readiness": "Readiness is a short-term daily indicator and is not the same as PWS.",
        "load_metrics": "Load metrics and ACWR are analytical context and are not injury predictions.",
        "medical_limitation": "PWS and related metrics are not medical diagnoses, injury predictions or professional training prescriptions.",
        "privacy": "The payload contains private derived health and training information and must remain local unless a later approved privacy policy explicitly defines otherwise.",
        "no_recommendations_generated": True,
        "no_medical_diagnosis_generated": True,
        "no_llm_called_in_this_module": True,
    }


def schema() -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "schema_version": "dashboard_payload_schema_v1",
        "policy_version": POLICY_VERSION,
        "payload_type": "local_dashboard_presentation_payload",
        "primary_score": {"field": "current_state.primary_pws.score", "source": "pws_deterministic", "score_type": "deterministic", "nullable": True, "description": "Primary auditable PWS score copied from the deterministic PWS artifact."},
        "optional_assisted_score": {"field": "current_state.optional_assisted_pws.score", "source": "pws_llm_assisted", "score_type": "llm_assisted_optional_variant", "nullable": True, "must_not_replace_primary": True, "description": "Optional comparison variant available only when validated LLM-assisted PWS was calculated upstream."},
        "external_assisted_score": {"field": "current_state.external_assisted_pws.score", "source": "pws_openai_assisted", "score_type": "external_llm_assisted_optional_variant", "nullable": True, "must_not_replace_primary": True, "description": "Optional OpenAI comparison variant calculated upstream from the same bounded context and local validation rules."},
        "top_level_sections": ["metadata", "current_state", "time_series", "quality_and_coverage", "disclosures"],
        "date_axis_source": "deterministic_pws_records",
        "current_state_date_rule": "latest_date_on_deterministic_pws_axis",
        "missing_values_policy": "preserve_null_never_replace_with_zero",
        "recomputation_policy": {"recompute_load_metrics": False, "recompute_readiness": False, "recompute_pws_components": False, "recompute_pws_weights": False, "recompute_pws_deterministic": False, "recompute_pws_llm_assisted": False, "call_llm": False},
        "privacy_policy": {"private_local_payload": True, "gitignored": True, "raw_health_sources_excluded": True, "secrets_excluded": True},
        "forbidden_fields": ["medical_diagnosis", "injury_prediction", "training_prescription", "coach_message", "tokens", "credentials", "raw_garmin_api_payloads", "raw_workbook_data"],
    }


def lineage(assisted: dict[str, Any], external_assisted: dict[str, Any]) -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "lineage_version": "dashboard_payload_lineage_v1",
        "source_artifacts": [
            {"module_id": "07_build_daily_features", "artifact_path": "data/pipeline/07_build_daily_features/daily_features.json", "role": "daily_signal_presentation_source", "optional": True},
            {"module_id": "08_compute_load_metrics", "artifact_path": "data/pipeline/08_compute_load_metrics/load_metrics.json", "role": "load_metrics_presentation_source"},
            {"module_id": "09_compute_readiness", "artifact_path": "data/pipeline/09_compute_readiness/readiness.json", "role": "readiness_presentation_source"},
            {"module_id": "10_compute_pws_components", "artifact_path": "data/pipeline/10_compute_pws_components/pws_components.json", "role": "pws_component_presentation_source"},
            {"module_id": "11_compute_pws_weights", "artifact_path": "data/pipeline/11_compute_pws_weights/pws_weights.json", "role": "deterministic_weight_presentation_source"},
            {"module_id": DETERMINISTIC_ID, "artifact_path": f"data/pipeline/{DETERMINISTIC_ID}/pws_score.json", "role": "primary_deterministic_pws_source"},
            {"module_id": ASSISTED_ID, "artifact_path": f"data/pipeline/{ASSISTED_ID}/llm_assisted_pws.json", "role": "optional_assisted_variant_source", "optional": True, "present": assisted["artifact_present"]},
            {"module_id": ASSISTED_ID, "artifact_path": f"data/pipeline/{ASSISTED_ID}/openai_assisted_pws.json", "role": "optional_external_assisted_variant_source", "optional": True, "present": external_assisted["artifact_present"]},
        ],
        "payload_mapping": {
            "current_state.primary_pws": "copied_from_deterministic_pws_latest_date",
            "current_state.optional_assisted_pws": "copied_from_validated_optional_assisted_artifact_when_available_for_latest_date",
            "current_state.external_assisted_pws": "copied_from_validated_optional_openai_artifact_when_available_for_latest_date",
            "current_state.readiness": "copied_from_readiness_record_by_date",
            "current_state.pws_components": "copied_from_pws_components_record_by_date",
            "current_state.pws_weights": "copied_from_pws_weights_record_by_date",
            "current_state.load_metrics": "copied_from_load_metrics_record_by_date",
            "time_series": "joined_presentation_projection_on_deterministic_pws_date_axis",
            "time_series.daily_signals": "copied_from_daily_features_readiness_or_load_records_by_date_when_available",
        },
        "transformation_policy": {"joins_by_date_only": True, "presentation_projection_only": True, "latest_record_selection_only": True, "availability_counting_only": True, "analytical_recomputation_performed": False},
        "primary_and_assisted_boundary": {"deterministic_pws_is_primary": True, "assisted_pws_is_optional_only": True, "assisted_pws_may_replace_primary": False},
        "forbidden_action_confirmation": {"llm_called": False, "pws_recomputed": False, "weights_recomputed": False, "readiness_recomputed": False, "medical_diagnosis_generated": False, "injury_prediction_generated": False, "training_prescription_generated": False, "coaching_message_generated": False},
    }


def write_failure(root: Path, started: str, status: str, errors: list[dict[str, Any]]) -> None:
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    artifact_dir.mkdir(parents=True, exist_ok=True)
    finished = now_iso()
    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    write_json(artifact_dir / "run_manifest.json", {"module_id": MODULE_ID, "module_version": MODULE_VERSION, "policy_version": POLICY_VERSION, "started_at": started, "finished_at": finished, "execution_status": "failed", "domain_status": status, "generated_artifacts": [f"data/pipeline/{MODULE_ID}/run_manifest.json", f"data/pipeline/{MODULE_ID}/run_log.txt", f"data/pipeline/{MODULE_ID}/errors.json"], "primary_score_source": "pws_deterministic", "analytical_values_recomputed": False, "llm_called": False, "log_file": f"data/pipeline/{MODULE_ID}/run_log.txt", "errors_file": f"data/pipeline/{MODULE_ID}/errors.json"})
    (artifact_dir / "run_log.txt").write_text(f"module_id={MODULE_ID}\nstarted_at={started}\nfinished_at={finished}\ndomain_status={status}\nanalytical_values_recomputed=false\nllm_called=false\n", encoding="utf-8")


def write_log(path: Path, started: str, status: str, payload: dict[str, Any], quality: dict[str, Any], assisted: dict[str, Any], parquet_written: bool, parquet_warning: str | None) -> None:
    current = payload["current_state"]
    lines = [
        f"module_id={MODULE_ID}",
        f"started_at={started}",
        f"policy_version={POLICY_VERSION}",
        "required_inputs=load_metrics, readiness, pws_components, pws_weights, pws_score",
        f"optional_assisted_artifact_present={assisted['artifact_present']}",
        f"records_count={payload['metadata']['records_count']}",
        f"date_range={payload['metadata']['date_range']}",
        f"latest_date={payload['metadata']['latest_date']}",
        f"current_state_primary_pws_available={current['primary_pws']['computed']}",
        f"current_state_optional_assisted_pws_available={current['optional_assisted_pws'].get('available')}",
        f"primary_pws_computed_count={quality['presentation_availability']['primary_pws_computed_count']}",
        f"primary_pws_unavailable_count={quality['presentation_availability']['primary_pws_unavailable_count']}",
        f"coverage_tiers={quality['coverage_tiers']}",
        f"readiness_computed_count={quality['readiness_availability']['computed_count']}",
        f"component_availability={quality['component_availability']}",
        f"weight_availability={quality['weight_availability']}",
        f"time_series_records={len(payload['time_series'])}",
        f"optional_assisted_score_count={quality['presentation_availability']['optional_assisted_score_count']}",
        "deterministic_pws_is_primary=true",
        "assisted_pws_never_replaces_primary=true",
        "analytical_values_recomputed=false",
        "llm_called=false",
        "coaching_or_recommendations_generated=false",
        f"json_csv_written=true",
        f"parquet_written={parquet_written}",
        f"parquet_warning={parquet_warning}",
        "payload_private_local_data=true",
        f"finished_at={now_iso()}",
        f"domain_status={status}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    code, _status = build(root_dir())
    return code


if __name__ == "__main__":
    sys.exit(main())
