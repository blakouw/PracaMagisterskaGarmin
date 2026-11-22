from __future__ import annotations

import csv
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "08_compute_load_metrics"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "load_metrics_policy_v1"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR_REL = Path("data/pipeline/08_compute_load_metrics")

INPUTS = [
    Path("config/load_metrics_policy_v1.json"),
    Path("data/pipeline/07_build_daily_features/daily_features.json"),
    Path("data/pipeline/07_build_daily_features/daily_features_schema.json"),
    Path("data/pipeline/07_build_daily_features/daily_features_quality_report.json"),
    Path("data/pipeline/07_build_daily_features/daily_features_lineage.json"),
]
ACTIVITIES_INPUT = Path("data/pipeline/06_normalize_activities/activities_normalized.json")

GENERATED = [
    "data/pipeline/08_compute_load_metrics/load_metrics.json",
    "data/pipeline/08_compute_load_metrics/load_metrics.csv",
    "data/pipeline/08_compute_load_metrics/load_metrics_schema.json",
    "data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json",
    "data/pipeline/08_compute_load_metrics/load_metrics_lineage.json",
    "data/pipeline/08_compute_load_metrics/run_manifest.json",
    "data/pipeline/08_compute_load_metrics/run_log.txt",
    "data/pipeline/08_compute_load_metrics/errors.json",
]

METRIC_FIELDS = [
    "load_active_kcal",
    "load_session_rpe",
    "load_value",
    "load_source",
    "session_rpe_activity_count",
    "session_rpe_evaluated_activity_count",
    "session_rpe_coverage_complete",
    "acute_rolling_7d",
    "acute_rolling_7d_coverage_days",
    "acute_rolling_7d_required_days",
    "acute_rolling_7d_complete",
    "chronic_rolling_28d",
    "chronic_rolling_28d_coverage_days",
    "chronic_rolling_28d_required_days",
    "chronic_rolling_28d_complete",
    "acwr_rolling",
    "acwr_rolling_zone_id",
    "acwr_rolling_zone_label",
    "acute_ewma_7d",
    "chronic_ewma_28d",
    "acwr_ewma",
    "acwr_ewma_zone_id",
    "acwr_ewma_zone_label",
    "ewma_sequence_id",
    "ewma_sequence_day_index",
    "ewma_sequence_restarted_on_date",
    "ewma_sequence_has_acute_history_7d",
    "ewma_sequence_has_chronic_history_28d",
    "weekly_load_sum_7d",
    "weekly_load_mean_7d",
    "weekly_load_population_std_7d",
    "monotony_7d",
    "strain_7d",
    "load_metric_warnings",
]

FORBIDDEN = {
    "rhr_delta",
    "ln_rmssd",
    "readiness",
    "readiness_label",
    "LQ",
    "REC",
    "CAP",
    "VS",
    "pws_score",
    "pws_weights",
    "pws_priority",
    "llm_adjustment",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    if parsed.isoformat() != value:
        return None
    return parsed


def as_nonnegative_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and value.strip():
        try:
            number = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def rounded(value: Any, digits: int = 6) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        return round(value, digits)
    return value


def date_range(start: date, end: date) -> list[date]:
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]


def zone_for(value: float | None, zones: list[dict[str, Any]] | None = None) -> dict[str, str | None]:
    if value is None:
        return {"zone_id": None, "label": None}
    if value < 0.8:
        return {"zone_id": "underload", "label": "niedobor"}
    if value <= 1.3:
        return {"zone_id": "optimal", "label": "optimum"}
    if value <= 1.5:
        return {"zone_id": "caution", "label": "ostroznie"}
    return {"zone_id": "risk", "label": "ryzyko"}


def validate_policy(policy: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "Unexpected policy_version."})
    if policy.get("daily_load_source_field") != "session_rpe_with_active_kcal_fallback":
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "daily_load_source_field must define the approved session-RPE/fallback model."})
    if policy.get("daily_load_normalized_field") != "load_value":
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "daily_load_normalized_field must be load_value."})
    selection = policy.get("daily_load_selection_policy", {})
    if selection.get("preferred_source") != "session_rpe" or selection.get("fallback_source") != "active_kcal":
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "Preferred and fallback load sources are invalid."})
    session_rpe = policy.get("session_rpe_policy", {})
    if session_rpe.get("rpe_field") != "perceived_effort_rpe" or session_rpe.get("duration_field") != "duration_seconds":
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "session-RPE input fields are invalid."})
    date_policy = policy.get("date_axis_policy", {})
    if date_policy.get("window_unit") != "calendar_days":
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "Windows must use calendar_days."})
    if date_policy.get("missing_calendar_dates_policy") != "do_not_impute_and_do_not_assume_zero":
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "Missing calendar dates must not be imputed."})
    rolling = policy.get("rolling_load_metrics", {})
    if rolling.get("acute_rolling_7d", {}).get("window_days") != 7:
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "acute_rolling_7d must use 7 days."})
    if rolling.get("chronic_rolling_28d", {}).get("window_days") != 28:
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "chronic_rolling_28d must use 28 days."})
    ewma = policy.get("ewma_load_metrics", {})
    if ewma.get("acute_ewma", {}).get("alpha") != 0.25:
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "acute EWMA alpha must be 0.25."})
    if round(float(ewma.get("chronic_ewma", {}).get("alpha", -1)), 12) != round(2 / 29, 12):
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "chronic EWMA alpha must be 2/29."})
    if "readiness" in policy.get("prohibited_calculations", []) and "pws_score" in policy.get("prohibited_calculations", []):
        return errors
    errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "message": "Forbidden future calculations must be listed."})
    return errors


def write_run_artifacts(
    root: Path,
    started_at: str,
    domain_status: str,
    execution_status: str,
    errors: list[dict[str, Any]],
    log_lines: list[str],
    parquet_written: bool = False,
    parquet_reason: str | None = None,
) -> None:
    out_dir = root / OUT_DIR_REL
    finished_at = utc_now()
    manifest = {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": execution_status,
        "domain_status": domain_status,
        "inputs": [p.as_posix() for p in INPUTS] + [f"optional: {ACTIVITIES_INPUT.as_posix()}"],
        "generated_artifacts": GENERATED,
        "optional_generated_artifacts": [
            {
                "path": "data/pipeline/08_compute_load_metrics/load_metrics.parquet",
                "written": parquet_written,
                "reason_if_not_written": parquet_reason,
            }
        ],
        "log_file": "data/pipeline/08_compute_load_metrics/run_log.txt",
        "errors_file": "data/pipeline/08_compute_load_metrics/errors.json",
    }
    write_json(out_dir / "run_manifest.json", manifest)
    write_json(out_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    log_lines.extend(
        [
            f"Finished at: {finished_at}",
            f"Execution status: {execution_status}",
            f"Domain status: {domain_status}",
        ]
    )
    (out_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def contiguous_sequences(sorted_dates: list[date]) -> list[dict[str, Any]]:
    if not sorted_dates:
        return []
    sequences: list[dict[str, Any]] = []
    start = prev = sorted_dates[0]
    seq_id = 1
    for current in sorted_dates[1:]:
        if (current - prev).days != 1:
            sequences.append(
                {
                    "sequence_id": seq_id,
                    "first_date": start.isoformat(),
                    "last_date": prev.isoformat(),
                    "days_count": (prev - start).days + 1,
                }
            )
            seq_id += 1
            start = current
        prev = current
    sequences.append(
        {
            "sequence_id": seq_id,
            "first_date": start.isoformat(),
            "last_date": prev.isoformat(),
            "days_count": (prev - start).days + 1,
        }
    )
    return sequences


def availability(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    available = [record for record in records if record.get(field) is not None]
    return {
        "available_count": len(available),
        "unavailable_count": len(records) - len(available),
        "first_available_date": available[0]["date"] if available else None,
    }


def zone_counts(records: list[dict[str, Any]], prefix: str) -> dict[str, int]:
    counts = {"underload": 0, "optimal": 0, "caution": 0, "risk": 0, "unavailable": 0}
    for record in records:
        zone = record.get(f"{prefix}_zone_id")
        if zone in counts and zone != "unavailable":
            counts[zone] += 1
        else:
            counts["unavailable"] += 1
    return counts


def load_activities_by_date(root: Path, warnings: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], bool]:
    path = root / ACTIVITIES_INPUT
    if not path.is_file():
        return {}, False
    try:
        payload = read_json(path)
    except Exception as exc:
        warnings.append({"code": "RPE_ACTIVITY_SOURCE_INVALID", "severity": "warning", "message": f"Normalized activity artifact could not be read; active_kcal fallback was used: {exc.__class__.__name__}."})
        return {}, False
    records = payload.get("activities")
    if not isinstance(records, list):
        warnings.append({"code": "RPE_ACTIVITY_SOURCE_INVALID", "severity": "warning", "message": "Normalized activity artifact has no activities list; active_kcal fallback was used."})
        return {}, False
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        parsed_date = parse_iso_date(record.get("date"))
        if parsed_date is None:
            continue
        grouped.setdefault(parsed_date.isoformat(), []).append(record)
    return grouped, True


def select_daily_load(active_kcal: float, activities: list[dict[str, Any]]) -> dict[str, Any]:
    activity_count = len(activities)
    session_loads: list[float] = []
    for activity in activities:
        duration_seconds = as_nonnegative_number(activity.get("duration_seconds"))
        rpe = as_nonnegative_number(activity.get("perceived_effort_rpe"))
        if duration_seconds is None or duration_seconds <= 0 or rpe is None or rpe > 10:
            continue
        session_loads.append((duration_seconds / 60.0) * rpe)
    evaluated_count = len(session_loads)
    complete = activity_count > 0 and evaluated_count == activity_count
    session_rpe = sum(session_loads) if complete else None
    return {
        "load_active_kcal": active_kcal,
        "load_session_rpe": session_rpe,
        "load_value": session_rpe if complete else active_kcal,
        "load_source": "session_rpe" if complete else "active_kcal_fallback",
        "session_rpe_activity_count": activity_count,
        "session_rpe_evaluated_activity_count": evaluated_count,
        "session_rpe_coverage_complete": complete,
    }


def flatten_for_tabular(record: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (list, dict)):
            flat[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            flat[key] = value
    return flat


def write_csv(path: Path, records: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            flat = flatten_for_tabular(record)
            writer.writerow({field: "" if flat.get(field) is None else flat.get(field) for field in fields})


def try_write_parquet(path: Path, records: list[dict[str, Any]], fields: list[str]) -> tuple[bool, str | None]:
    try:
        import pandas as pd  # type: ignore
        import pyarrow  # noqa: F401  # type: ignore
    except Exception as exc:
        return False, f"PARQUET_DEPENDENCY_UNAVAILABLE: {exc.__class__.__name__}"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame([{field: flatten_for_tabular(record).get(field) for field in fields} for record in records])
        frame.to_parquet(path, index=False)
        return True, None
    except Exception as exc:
        return False, f"PARQUET_WRITE_FAILED: {exc.__class__.__name__}: {exc}"


def build_schema(fields: list[str], base_fields: list[str]) -> dict[str, Any]:
    schema_fields: list[dict[str, Any]] = []
    for field in base_fields:
        schema_fields.append(
            {
                "name": field,
                "type": "inherited",
                "nullable": field != "date",
                "origin": "07_build_daily_features",
                "transformation": "copied_without_semantic_change",
                "description": "Base daily feature field copied from module 07.",
            }
        )
    descriptions = {
        "load_active_kcal": ("number", False, "copied_reference_value", "Daily active kilocalories retained as the fallback and audit reference."),
        "load_session_rpe": ("number", True, "sum_rpe_times_duration_minutes", "Daily session-RPE when every activity has valid duration and RPE."),
        "load_value": ("number", False, "policy_selected_daily_load", "Selected daily load: complete session-RPE when available, otherwise active_kcal."),
        "load_source": ("string", False, "policy_source_label", "Source selected for load_value."),
        "session_rpe_activity_count": ("integer", False, "count_daily_activities", "Activities found for the day."),
        "session_rpe_evaluated_activity_count": ("integer", False, "count_valid_rpe_duration_pairs", "Activities contributing to session-RPE."),
        "session_rpe_coverage_complete": ("boolean", False, "compare_evaluated_and_total_activity_counts", "True only when every activity can contribute to session-RPE."),
        "acute_rolling_7d": ("number", True, "mean_over_complete_7_calendar_day_window", "Rolling seven-day mean of load_value; null until full coverage exists."),
        "chronic_rolling_28d": ("number", True, "mean_over_complete_28_calendar_day_window", "Rolling twenty-eight-day mean of load_value; null until full coverage exists."),
        "acwr_rolling": ("number", True, "acute_rolling_7d_divided_by_chronic_rolling_28d", "Dashboard-oriented rolling ACWR ratio."),
        "acute_ewma_7d": ("number", True, "ewma_alpha_0_25_over_contiguous_sequence", "Analytical acute EWMA load."),
        "chronic_ewma_28d": ("number", True, "ewma_alpha_2_divided_by_29_over_contiguous_sequence", "Analytical chronic EWMA load."),
        "acwr_ewma": ("number", True, "acute_ewma_7d_divided_by_chronic_ewma_28d", "Analytical EWMA-based ACWR ratio."),
        "monotony_7d": ("number", True, "mean_divided_by_population_standard_deviation_over_complete_7_day_window", "Seven-day load monotony; undefined when window variance is zero."),
        "strain_7d": ("number", True, "weekly_load_sum_multiplied_by_monotony_7d", "Seven-day strain derived from load proxy and monotony."),
    }
    for field in METRIC_FIELDS:
        kind, nullable, transformation, description = descriptions.get(
            field,
            ("mixed", True, "load_metric_supporting_field", "Supporting load metric availability, coverage or audit field."),
        )
        schema_fields.append(
            {
                "name": field,
                "type": kind,
                "nullable": nullable,
                "origin": MODULE_ID,
                "transformation": transformation,
                "description": description,
            }
        )
    return {
        "module_id": MODULE_ID,
        "schema_version": "load_metrics_schema_v1",
        "policy_version": POLICY_VERSION,
        "primary_key": "date",
        "load_source_field": "load_value",
        "load_source_interpretation": "session_rpe_preferred_with_active_kcal_fallback",
        "date_window_policy": "calendar_days_complete_coverage_required_for_rolling_metrics",
        "missing_values_policy": "do_not_impute_and_do_not_assume_zero",
        "fields": schema_fields,
        "excluded_future_fields": sorted(FORBIDDEN),
    }


def execute(root: Path | None = None) -> int:
    root = root or ROOT
    out_dir = root / OUT_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    log_lines = [
        f"Module: {MODULE_ID}",
        f"Started at: {started_at}",
        f"Policy version: {POLICY_VERSION}",
        "Input artifact: data/pipeline/07_build_daily_features/daily_features.json",
    ]
    errors: list[dict[str, Any]] = []

    policy_path = root / "config/load_metrics_policy_v1.json"
    if not policy_path.exists():
        errors.append({"code": "LOAD_METRICS_POLICY_NOT_FOUND", "severity": "error", "message": "config/load_metrics_policy_v1.json is missing."})
        write_run_artifacts(root, started_at, "invalid_load_policy", "failed", errors, log_lines)
        return 1
    try:
        policy = read_json(policy_path)
    except Exception as exc:
        errors.append({"code": "LOAD_METRICS_POLICY_INVALID", "severity": "error", "message": str(exc)})
        write_run_artifacts(root, started_at, "invalid_load_policy", "failed", errors, log_lines)
        return 1
    policy_errors = validate_policy(policy)
    if policy_errors:
        for err in policy_errors:
            err["severity"] = "error"
        errors.extend(policy_errors)
        write_run_artifacts(root, started_at, "invalid_load_policy", "failed", errors, log_lines)
        return 1

    missing = [path for path in INPUTS[1:] if not (root / path).exists()]
    if missing:
        errors.append(
            {
                "code": "DAILY_FEATURES_NOT_FOUND",
                "severity": "error",
                "message": "Required module 07 artifacts are missing.",
                "missing_inputs": [path.as_posix() for path in missing],
            }
        )
        write_run_artifacts(root, started_at, "blocked_missing_daily_features", "failed", errors, log_lines)
        return 1

    try:
        daily_features = read_json(root / "data/pipeline/07_build_daily_features/daily_features.json")
        read_json(root / "data/pipeline/07_build_daily_features/daily_features_schema.json")
        read_json(root / "data/pipeline/07_build_daily_features/daily_features_quality_report.json")
        read_json(root / "data/pipeline/07_build_daily_features/daily_features_lineage.json")
    except Exception as exc:
        errors.append({"code": "DAILY_FEATURES_NOT_FOUND", "severity": "error", "message": f"Could not read module 07 artifacts: {exc}"})
        write_run_artifacts(root, started_at, "blocked_missing_daily_features", "failed", errors, log_lines)
        return 1

    if daily_features.get("ready_for_next_module") is not True:
        errors.append({"code": "DAILY_FEATURES_NOT_READY", "severity": "error", "message": "daily_features.json is not ready for next module."})
        write_run_artifacts(root, started_at, "blocked_daily_features_not_ready", "failed", errors, log_lines)
        return 1

    input_records = daily_features.get("records")
    if not isinstance(input_records, list):
        errors.append({"code": "DAILY_FEATURES_NOT_FOUND", "severity": "error", "message": "daily_features.json records must be a list."})
        write_run_artifacts(root, started_at, "blocked_missing_daily_features", "failed", errors, log_lines)
        return 1

    seen_dates: set[str] = set()
    warning_entries: list[dict[str, Any]] = []
    activities_by_date, activity_source_available = load_activities_by_date(root, warning_entries)
    parsed_rows: list[tuple[date, float, dict[str, Any], dict[str, Any]]] = []
    for index, record in enumerate(input_records):
        if not isinstance(record, dict):
            errors.append({"code": "DATE_FIELD_MISSING", "severity": "error", "row_index": index, "message": "Feature record is not an object."})
            continue
        parsed_date = parse_iso_date(record.get("date"))
        if parsed_date is None:
            errors.append({"code": "DATE_VALUE_INVALID" if "date" in record else "DATE_FIELD_MISSING", "severity": "error", "row_index": index, "message": "Invalid or missing date."})
            continue
        if parsed_date.isoformat() in seen_dates:
            errors.append({"code": "DUPLICATE_DATE_FOUND", "severity": "error", "date": parsed_date.isoformat(), "message": "Duplicate daily feature date."})
            continue
        seen_dates.add(parsed_date.isoformat())
        if "active_kcal" not in record:
            errors.append({"code": "ACTIVE_KCAL_FIELD_MISSING", "severity": "error", "date": parsed_date.isoformat(), "message": "active_kcal is missing."})
            continue
        raw_load = record.get("active_kcal")
        load = as_nonnegative_number(raw_load)
        if load is None:
            code = "ACTIVE_KCAL_NEGATIVE" if isinstance(raw_load, (int, float)) and raw_load < 0 else "ACTIVE_KCAL_INVALID"
            errors.append({"code": code, "severity": "error", "date": parsed_date.isoformat(), "message": "active_kcal must be a nonnegative number and cannot be null."})
            continue
        load_audit = select_daily_load(load, activities_by_date.get(parsed_date.isoformat(), []))
        parsed_rows.append((parsed_date, float(load_audit["load_value"]), record, load_audit))

    if errors:
        domain_status = "blocked_duplicate_dates" if any(e["code"] == "DUPLICATE_DATE_FOUND" for e in errors) else "blocked_invalid_load_source"
        write_run_artifacts(root, started_at, domain_status, "failed", errors, log_lines)
        return 1

    parsed_rows.sort(key=lambda item: item[0])
    dates = [item[0] for item in parsed_rows]
    loads = {item[0]: item[1] for item in parsed_rows}
    records_by_date = {item[0]: item[2] for item in parsed_rows}
    sequences = contiguous_sequences(dates)
    missing_dates = [] if not dates else [d.isoformat() for d in date_range(dates[0], dates[-1]) if d not in loads]

    output_records: list[dict[str, Any]] = []
    alpha_acute = float(policy["ewma_load_metrics"]["acute_ewma"]["alpha"])
    alpha_chronic = float(policy["ewma_load_metrics"]["chronic_ewma"]["alpha"])
    prev_date: date | None = None
    seq_id = 0
    seq_start: date | None = None
    seq_index = 0
    acute_prev: float | None = None
    chronic_prev: float | None = None
    ewma_restarts = 0

    for current_date, load, source_record, load_audit in parsed_rows:
        warnings: list[str] = []
        if prev_date is None or (current_date - prev_date).days != 1:
            seq_id += 1
            seq_index = 1
            seq_start = current_date
            acute_prev = load
            chronic_prev = load
            if prev_date is not None:
                ewma_restarts += 1
                warning_entries.append(
                    {
                        "code": "EWMA_SEQUENCE_RESTARTED",
                        "severity": "warning",
                        "date": current_date.isoformat(),
                        "message": "EWMA sequence restarted after a calendar gap.",
                    }
                )
        else:
            seq_index += 1
            acute_prev = alpha_acute * load + (1 - alpha_acute) * float(acute_prev)
            chronic_prev = alpha_chronic * load + (1 - alpha_chronic) * float(chronic_prev)

        def complete_window(window_days: int) -> tuple[list[float], int, bool]:
            wanted = [current_date - timedelta(days=offset) for offset in range(window_days - 1, -1, -1)]
            values = [loads[d] for d in wanted if d in loads]
            return values, len(values), len(values) == window_days

        acute_values, acute_coverage, acute_complete = complete_window(7)
        chronic_values, chronic_coverage, chronic_complete = complete_window(28)
        acute_rolling = sum(acute_values) / 7 if acute_complete else None
        chronic_rolling = sum(chronic_values) / 28 if chronic_complete else None
        acwr_rolling = None
        if acute_rolling is not None and chronic_rolling is not None:
            if chronic_rolling > 0:
                acwr_rolling = acute_rolling / chronic_rolling
            else:
                warning_entries.append(
                    {
                        "code": "CHRONIC_LOAD_ZERO_ACWR_UNAVAILABLE",
                        "severity": "warning",
                        "date": current_date.isoformat(),
                        "message": "Rolling ACWR is unavailable because chronic load equals zero.",
                    }
                )
        rolling_zone = zone_for(acwr_rolling, policy.get("acwr_zones"))

        acwr_ewma = None
        if chronic_prev is not None and chronic_prev > 0:
            acwr_ewma = float(acute_prev) / float(chronic_prev)
        elif chronic_prev == 0:
            warning_entries.append(
                {
                    "code": "CHRONIC_LOAD_ZERO_ACWR_UNAVAILABLE",
                    "severity": "warning",
                    "date": current_date.isoformat(),
                    "message": "EWMA ACWR is unavailable because chronic EWMA load equals zero.",
                }
            )
        ewma_zone = zone_for(acwr_ewma, policy.get("acwr_zones"))

        weekly_values = acute_values
        weekly_sum = weekly_mean = weekly_std = monotony = strain = None
        if acute_complete:
            weekly_sum = sum(weekly_values)
            weekly_mean = weekly_sum / 7
            weekly_std = math.sqrt(sum((value - weekly_mean) ** 2 for value in weekly_values) / 7)
            if weekly_std > 0:
                monotony = weekly_mean / weekly_std
                strain = weekly_sum * monotony
            else:
                warnings.append("Monotony is undefined because seven-day load standard deviation equals zero.")
                warning_entries.append(
                    {
                        "code": "MONOTONY_ZERO_STANDARD_DEVIATION",
                        "severity": "warning",
                        "date": current_date.isoformat(),
                        "message": "Monotony is undefined because seven-day load standard deviation equals zero.",
                    }
                )

        output = dict(source_record)
        output.update(
            {
                "load_active_kcal": rounded(load_audit["load_active_kcal"]),
                "load_session_rpe": rounded(load_audit["load_session_rpe"]),
                "load_value": rounded(load_audit["load_value"]),
                "load_source": load_audit["load_source"],
                "session_rpe_activity_count": load_audit["session_rpe_activity_count"],
                "session_rpe_evaluated_activity_count": load_audit["session_rpe_evaluated_activity_count"],
                "session_rpe_coverage_complete": load_audit["session_rpe_coverage_complete"],
                "acute_rolling_7d": rounded(acute_rolling),
                "acute_rolling_7d_coverage_days": acute_coverage,
                "acute_rolling_7d_required_days": 7,
                "acute_rolling_7d_complete": acute_complete,
                "chronic_rolling_28d": rounded(chronic_rolling),
                "chronic_rolling_28d_coverage_days": chronic_coverage,
                "chronic_rolling_28d_required_days": 28,
                "chronic_rolling_28d_complete": chronic_complete,
                "acwr_rolling": rounded(acwr_rolling),
                "acwr_rolling_zone_id": rolling_zone["zone_id"],
                "acwr_rolling_zone_label": rolling_zone["label"],
                "acute_ewma_7d": rounded(acute_prev),
                "chronic_ewma_28d": rounded(chronic_prev),
                "acwr_ewma": rounded(acwr_ewma),
                "acwr_ewma_zone_id": ewma_zone["zone_id"],
                "acwr_ewma_zone_label": ewma_zone["label"],
                "ewma_sequence_id": seq_id,
                "ewma_sequence_day_index": seq_index,
                "ewma_sequence_restarted_on_date": seq_start.isoformat() if seq_start else None,
                "ewma_sequence_has_acute_history_7d": seq_index >= 7,
                "ewma_sequence_has_chronic_history_28d": seq_index >= 28,
                "weekly_load_sum_7d": rounded(weekly_sum),
                "weekly_load_mean_7d": rounded(weekly_mean),
                "weekly_load_population_std_7d": rounded(weekly_std),
                "monotony_7d": rounded(monotony),
                "strain_7d": rounded(strain),
                "load_metric_warnings": warnings,
            }
        )
        output_records.append(output)
        prev_date = current_date

    base_fields = list(input_records[0].keys()) if input_records else []
    fields = base_fields + [field for field in METRIC_FIELDS if field not in base_fields]
    for forbidden in FORBIDDEN:
        if forbidden in fields:
            raise RuntimeError(f"Forbidden future field leaked into module 08 output: {forbidden}")

    parquet_written, parquet_reason = try_write_parquet(out_dir / "load_metrics.parquet", output_records, fields)
    parquet_warning = None
    if not parquet_written:
        code = "PARQUET_DEPENDENCY_UNAVAILABLE" if parquet_reason and parquet_reason.startswith("PARQUET_DEPENDENCY_UNAVAILABLE") else "PARQUET_WRITE_FAILED"
        parquet_warning = parquet_reason
        warning_entries.append({"code": code, "severity": "warning", "message": parquet_reason})

    metric_availability = {
        "acute_rolling_7d": availability(output_records, "acute_rolling_7d"),
        "chronic_rolling_28d": availability(output_records, "chronic_rolling_28d"),
        "acwr_rolling": availability(output_records, "acwr_rolling"),
        "acwr_ewma": availability(output_records, "acwr_ewma"),
        "monotony_7d": {
            **availability(output_records, "monotony_7d"),
            "undefined_zero_variance_dates": [w["date"] for w in warning_entries if w.get("code") == "MONOTONY_ZERO_STANDARD_DEVIATION"],
        },
        "strain_7d": availability(output_records, "strain_7d"),
        "acute_ewma_7d": availability(output_records, "acute_ewma_7d"),
        "chronic_ewma_28d": availability(output_records, "chronic_ewma_28d"),
    }

    status = "computed"
    if missing_dates:
        status = "computed_with_calendar_gaps"
    elif any(metric_availability[name]["unavailable_count"] for name in ("acute_rolling_7d", "chronic_rolling_28d", "acwr_rolling")):
        status = "computed_with_incomplete_windows"
    elif warning_entries:
        status = "computed_with_warnings"

    records_count = len(output_records)
    date_range_payload = {
        "first_date": dates[0].isoformat() if dates else None,
        "last_date": dates[-1].isoformat() if dates else None,
    }
    load_metrics = {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "status": status,
        "source_artifact": "data/pipeline/07_build_daily_features/daily_features.json",
        "optional_activity_source_artifact": ACTIVITIES_INPUT.as_posix(),
        "load_source_field": "load_value",
        "load_model_description": "Complete daily session-RPE is preferred; active_kcal is retained as an explicit fallback when any activity lacks RPE or duration.",
        "load_model_limitations": [
            "session-RPE and active kilocalories are different proxy units, and source changes are explicitly labelled per day.",
            "The fallback prevents missing RPE from becoming zero load but does not make the two proxies physiologically equivalent.",
            "This is not TRIMP or a medical or injury-risk model.",
        ],
        "records_count": records_count,
        "date_range": date_range_payload,
        "metrics_computed": [
            "load_active_kcal",
            "load_session_rpe",
            "load_value",
            "load_source",
            "acute_rolling_7d",
            "chronic_rolling_28d",
            "acwr_rolling",
            "acute_ewma_7d",
            "chronic_ewma_28d",
            "acwr_ewma",
            "weekly_load_sum_7d",
            "weekly_load_mean_7d",
            "weekly_load_population_std_7d",
            "monotony_7d",
            "strain_7d",
        ],
        "records": output_records,
        "missing_values_policy": "do_not_impute_and_do_not_assume_zero",
        "rolling_window_policy": "calendar_days_with_complete_required_coverage",
        "derived_readiness_or_pws_computed": False,
        "ready_for_next_module": True,
        "private_data_notice": "Load metric records contain private health and training data and must not be committed to version control.",
    }
    quality_report = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "records_count": records_count,
        "load_source": {
            "field": "load_value",
            "preferred_source": "session_rpe",
            "fallback_source": "active_kcal",
            "normalized_activity_source_available": activity_source_available,
            "session_rpe_days_count": sum(1 for record in output_records if record.get("load_source") == "session_rpe"),
            "active_kcal_fallback_days_count": sum(1 for record in output_records if record.get("load_source") == "active_kcal_fallback"),
            "valid_values_count": records_count,
            "invalid_values_count": 0,
            "null_values_count": 0,
            "proxy_limitation_acknowledged": True,
        },
        "calendar_axis_quality": {
            "first_date": date_range_payload["first_date"],
            "last_date": date_range_payload["last_date"],
            "expected_calendar_days_in_range": (dates[-1] - dates[0]).days + 1 if dates else 0,
            "available_record_days": records_count,
            "missing_calendar_dates": missing_dates,
            "contiguous_sequences": sequences,
        },
        "metric_availability": metric_availability,
        "acwr_zone_counts": {
            "rolling": zone_counts(output_records, "acwr_rolling"),
            "ewma": zone_counts(output_records, "acwr_ewma"),
        },
        "parquet_output": {
            "requested": True,
            "written": parquet_written,
            "warning": parquet_warning,
        },
        "forbidden_metrics_computed": False,
        "warnings": [
            "Complete daily session-RPE is preferred; active kilocalories are used as a labelled fallback when RPE coverage is incomplete.",
            "The preferred and fallback sources use different proxy units; this limitation is retained in quality and lineage artifacts.",
            "Rolling windows require complete calendar-day coverage and missing days were not replaced with zero.",
            "ACWR zones are descriptive heuristic labels and not medical or injury-risk diagnoses.",
        ] + [entry["message"] for entry in warning_entries if entry.get("message")],
        "ready_for_next_module": True,
    }
    lineage = {
        "module_id": MODULE_ID,
        "lineage_version": "load_metrics_lineage_v1",
        "source_artifacts": [
            {
                "module_id": "07_build_daily_features",
                "artifact_path": "data/pipeline/07_build_daily_features/daily_features.json",
                "role": "base_daily_feature_source",
            },
            {
                "module_id": "07_build_daily_features",
                "artifact_path": "data/pipeline/07_build_daily_features/daily_features_quality_report.json",
                "role": "input_quality_reference",
            },
            {
                "module_id": "06_normalize_activities",
                "artifact_path": ACTIVITIES_INPUT.as_posix(),
                "role": "optional_rpe_and_duration_source",
            },
        ],
        "load_source": {
            "preferred_input_fields": ["perceived_effort_rpe", "duration_seconds"],
            "fallback_input_field": "active_kcal",
            "output_field": "load_value",
            "selection_rule": "use sum(perceived_effort_rpe * duration_seconds / 60) only when every activity on the day has both values; otherwise use active_kcal",
            "rationale": "RPE is used when complete while missing evaluations preserve the previous explicit active-kilocalorie proxy.",
        },
        "metric_groups": [
            {
                "group_name": "dashboard_rolling_load",
                "fields": ["acute_rolling_7d", "chronic_rolling_28d", "acwr_rolling", "acwr_rolling_zone_id", "acwr_rolling_zone_label"],
                "method": "complete_calendar_window_rolling_means_and_ratio",
            },
            {
                "group_name": "analytical_ewma_load",
                "fields": ["acute_ewma_7d", "chronic_ewma_28d", "acwr_ewma", "acwr_ewma_zone_id", "acwr_ewma_zone_label"],
                "method": "ewma_over_contiguous_valid_calendar_sequences",
            },
            {
                "group_name": "weekly_variability",
                "fields": ["weekly_load_sum_7d", "weekly_load_mean_7d", "weekly_load_population_std_7d", "monotony_7d", "strain_7d"],
                "method": "complete_seven_calendar_day_window",
            },
        ],
        "forbidden_calculation_confirmation": {
            "readiness_computed": False,
            "pws_components_computed": False,
            "pws_weights_computed": False,
            "pws_score_computed": False,
            "llm_used": False,
        },
    }

    write_json(out_dir / "load_metrics.json", load_metrics)
    write_csv(out_dir / "load_metrics.csv", output_records, fields)
    write_json(out_dir / "load_metrics_schema.json", build_schema(fields, base_fields))
    write_json(out_dir / "load_metrics_quality_report.json", quality_report)
    write_json(out_dir / "load_metrics_lineage.json", lineage)

    nonblocking_errors = warning_entries
    errors_for_file = [{**entry, "severity": entry.get("severity", "warning")} for entry in nonblocking_errors]
    log_lines.extend(
        [
            f"Input records: {records_count}",
            f"Date range: {date_range_payload['first_date']}..{date_range_payload['last_date']}",
            f"Load source: session-RPE days={sum(1 for record in output_records if record.get('load_source') == 'session_rpe')}; active_kcal fallback days={sum(1 for record in output_records if record.get('load_source') == 'active_kcal_fallback')}",
            "session-RPE is used only with complete per-day activity evaluation coverage; fallback use is explicit.",
            f"Calendar gaps found: {len(missing_dates)}",
            f"Contiguous sequences: {len(sequences)}",
            f"acute_rolling_7d available: {metric_availability['acute_rolling_7d']['available_count']}",
            f"chronic_rolling_28d available: {metric_availability['chronic_rolling_28d']['available_count']}",
            f"acwr_rolling available: {metric_availability['acwr_rolling']['available_count']}",
            f"acute_ewma_7d available: {metric_availability['acute_ewma_7d']['available_count']}",
            f"chronic_ewma_28d available: {metric_availability['chronic_ewma_28d']['available_count']}",
            f"acwr_ewma available: {metric_availability['acwr_ewma']['available_count']}",
            f"monotony_7d available: {metric_availability['monotony_7d']['available_count']}",
            f"strain_7d available: {metric_availability['strain_7d']['available_count']}",
            f"EWMA restarts: {ewma_restarts}",
            f"Monotony zero standard deviation count: {len(metric_availability['monotony_7d']['undefined_zero_variance_dates'])}",
            f"JSON written: true",
            f"CSV written: true",
            f"Parquet written: {str(parquet_written).lower()}",
            "Missing dates were not filled with zero load.",
            "Readiness and PWS were not computed.",
            "LLM was not used.",
        ]
    )
    write_run_artifacts(root, started_at, status, "success", errors_for_file, log_lines, parquet_written, parquet_reason)
    return 0


def main() -> int:
    return execute()


if __name__ == "__main__":
    raise SystemExit(main())
