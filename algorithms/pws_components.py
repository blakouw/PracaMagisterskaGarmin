from __future__ import annotations

import csv
import json
import math
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "10_compute_pws_components"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "pws_components_policy_v1"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR_REL = Path("data/pipeline/10_compute_pws_components")

INPUTS = [
    Path("config/pws_components_policy_v1.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics_schema.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics_lineage.json"),
    Path("data/pipeline/09_compute_readiness/readiness.json"),
    Path("data/pipeline/09_compute_readiness/readiness_schema.json"),
    Path("data/pipeline/09_compute_readiness/readiness_quality_report.json"),
    Path("data/pipeline/09_compute_readiness/readiness_lineage.json"),
]
GENERATED = [
    "data/pipeline/10_compute_pws_components/pws_components.json",
    "data/pipeline/10_compute_pws_components/pws_components.csv",
    "data/pipeline/10_compute_pws_components/pws_components_schema.json",
    "data/pipeline/10_compute_pws_components/pws_components_quality_report.json",
    "data/pipeline/10_compute_pws_components/pws_components_lineage.json",
    "data/pipeline/10_compute_pws_components/run_manifest.json",
    "data/pipeline/10_compute_pws_components/run_log.txt",
    "data/pipeline/10_compute_pws_components/errors.json",
]
CSV_FIELDS = [
    "date",
    "lq_score",
    "lq_status",
    "lq_source_metric",
    "lq_source_value",
    "rec_score",
    "rec_status",
    "rec_source_metric",
    "rec_source_coverage_ratio",
    "cap_score",
    "cap_status",
    "cap_recent_duration_seconds_7d",
    "cap_baseline_weekly_equivalent_seconds",
    "cap_recent_to_baseline_ratio",
    "cap_window_complete",
    "vs_score",
    "vs_status",
    "vs_rhr_stability_score",
    "vs_hrv_stability_score",
    "vs_spo2_stability_score",
    "vs_respiration_stability_score",
    "vs_available_signal_count",
    "vs_coverage_ratio",
    "available_pws_components_count",
    "pws_components_coverage_ratio",
    "final_pws_computed",
    "pws_weights_computed",
    "llm_used",
]
FORBIDDEN = {
    "pws_score",
    "pws_deterministic",
    "pws_llm_assisted",
    "pws_weights",
    "effective_pws_weights",
    "dynamic_weights",
    "priority_component",
    "priority_recommendation",
    "llm_adjustment",
    "coach_message",
}
OVERLAPS = [
    {
        "components": ["LQ", "REC"],
        "reason": "REC may already contain a limited ACWR-based load-balance contribution through readiness.",
        "handling": "Disclosed only. Resolution belongs to the later PWS weighting module.",
    },
    {
        "components": ["REC", "VS"],
        "reason": "Both components may use HRV and RHR, but REC measures readiness while VS measures stability against personal baseline.",
        "handling": "Disclosed only. Resolution belongs to the later PWS weighting module.",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str) and value.strip():
        try:
            result = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def nonnegative(value: Any) -> float | None:
    result = number(value)
    return result if result is not None and result >= 0 else None


def clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def round2(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def round6(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def date_window(current: date, days: int, include_current: bool = True) -> list[date]:
    if include_current:
        return [current - timedelta(days=offset) for offset in range(days - 1, -1, -1)]
    return [current - timedelta(days=offset) for offset in range(days, 0, -1)]


def write_run_artifacts(root: Path, started_at: str, domain_status: str, execution_status: str, errors: list[dict[str, Any]], log_lines: list[str], parquet_written: bool = False, parquet_reason: str | None = None) -> None:
    out_dir = root / OUT_DIR_REL
    finished_at = utc_now()
    write_json(
        out_dir / "run_manifest.json",
        {
            "module_id": MODULE_ID,
            "module_version": MODULE_VERSION,
            "policy_version": POLICY_VERSION,
            "started_at": started_at,
            "finished_at": finished_at,
            "execution_status": execution_status,
            "domain_status": domain_status,
            "inputs": [path.as_posix() for path in INPUTS],
            "generated_artifacts": GENERATED,
            "optional_generated_artifacts": [{"path": "data/pipeline/10_compute_pws_components/pws_components.parquet", "written": parquet_written, "reason_if_not_written": parquet_reason}],
            "log_file": "data/pipeline/10_compute_pws_components/run_log.txt",
            "errors_file": "data/pipeline/10_compute_pws_components/errors.json",
        },
    )
    write_json(out_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    log_lines.extend([f"Finished at: {finished_at}", f"Execution status: {execution_status}", f"Domain status: {domain_status}"])
    (out_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def validate_policy(policy: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append({"code": "PWS_COMPONENTS_POLICY_INVALID", "message": "Unexpected policy version."})
    if policy.get("missing_values_policy", {}).get("do_not_replace_missing_with_zero") is not True:
        errors.append({"code": "PWS_COMPONENTS_POLICY_INVALID", "message": "Missing components must not be replaced with zero."})
    components = policy.get("components", {})
    for name in ["LQ", "REC", "CAP", "VS"]:
        if name not in components:
            errors.append({"code": "PWS_COMPONENTS_POLICY_INVALID", "message": f"Missing component policy for {name}."})
    vs_weights = components.get("VS", {}).get("signal_weights", {})
    if vs_weights and abs(sum(float(v) for v in vs_weights.values()) - 1.0) > 1e-9:
        errors.append({"code": "PWS_COMPONENTS_POLICY_INVALID", "message": "VS signal weights must sum to 1.0."})
    return errors


def validate_records(records: Any, source_name: str) -> tuple[list[tuple[date, dict[str, Any]]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    parsed: list[tuple[date, dict[str, Any]]] = []
    seen: set[str] = set()
    if not isinstance(records, list):
        return [], [{"code": f"{source_name.upper()}_NOT_FOUND", "severity": "error", "message": f"{source_name} records must be a list."}]
    for index, record in enumerate(records):
        if not isinstance(record, dict) or "date" not in record:
            errors.append({"code": "DATE_FIELD_MISSING", "severity": "error", "source": source_name, "row_index": index, "message": "Missing date."})
            continue
        parsed_date = parse_date(record.get("date"))
        if parsed_date is None:
            errors.append({"code": "DATE_VALUE_INVALID", "severity": "error", "source": source_name, "row_index": index, "date": record.get("date"), "message": "Invalid date."})
            continue
        key = parsed_date.isoformat()
        if key in seen:
            errors.append({"code": "DUPLICATE_DATE_FOUND", "severity": "error", "source": source_name, "date": key, "message": "Duplicate date."})
            continue
        seen.add(key)
        parsed.append((parsed_date, record))
    parsed.sort(key=lambda item: item[0])
    return parsed, errors


def acwr_piecewise(value: float) -> float:
    if value < 0.8:
        return max(40, 100 - ((0.8 - value) / 0.8) * 60)
    if value <= 1.3:
        return 100
    if value <= 1.5:
        return 100 - ((value - 1.3) / 0.2) * 40
    return max(0, 60 - ((value - 1.5) / 0.5) * 60)


def compute_lq(record: dict[str, Any], current_date: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    metric = "acwr_ewma"
    value = nonnegative(record.get("acwr_ewma"))
    method = "acwr_piecewise_load_quality"
    if value is None:
        value = nonnegative(record.get("acwr_rolling"))
        metric = "acwr_rolling" if value is not None else None
        method = "acwr_piecewise_load_quality_fallback" if value is not None else "unavailable"
        if value is not None:
            events.append({"code": "LQ_ROLLING_ACWR_FALLBACK_USED", "severity": "warning", "date": current_date, "message": "LQ used rolling ACWR fallback."})
    if value is None:
        events.append({"code": "LQ_UNAVAILABLE", "severity": "warning", "date": current_date, "message": "LQ unavailable because no ACWR metric is available."})
        return {"score": None, "status": "unavailable", "source_metric": None, "source_value": None, "method": "unavailable", "warnings": ["No ACWR metric available."]}
    return {"score": round2(clip(acwr_piecewise(value))), "status": "computed", "source_metric": metric, "source_value": round6(value), "method": method, "warnings": []}


def compute_rec(readiness: dict[str, Any] | None, current_date: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    if readiness is None:
        events.append({"code": "REC_UNAVAILABLE_READINESS_SCORE", "severity": "warning", "date": current_date, "message": "No readiness record for date."})
        return {"score": None, "status": "unavailable_insufficient_readiness_data", "source_value": None, "source_status": None, "coverage": None, "warnings": ["No readiness record for date."]}
    score = number(readiness.get("readiness_score"))
    if score is None or not (0 <= score <= 100):
        events.append({"code": "REC_UNAVAILABLE_READINESS_SCORE", "severity": "warning", "date": current_date, "message": "Readiness score unavailable."})
        return {"score": None, "status": "unavailable_insufficient_readiness_data", "source_value": None, "source_status": readiness.get("readiness_status"), "coverage": readiness.get("readiness_coverage_ratio"), "warnings": ["Readiness score unavailable."]}
    return {"score": round2(score), "status": "computed", "source_value": round2(score), "source_status": readiness.get("readiness_status"), "coverage": readiness.get("readiness_coverage_ratio"), "warnings": []}


def compute_cap(current: date, by_date: dict[date, dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    recent_dates = date_window(current, 7, include_current=True)
    baseline_dates = [current - timedelta(days=offset) for offset in range(27, 6, -1)]
    all_dates = baseline_dates + recent_dates
    warnings: list[str] = []
    coverage = 0
    values: dict[date, float] = {}
    for day in all_dates:
        if day not in by_date:
            warnings.append("CAP requires a complete 28 calendar day window.")
            events.append({"code": "CAP_INSUFFICIENT_HISTORY", "severity": "warning", "date": current.isoformat(), "message": "CAP has insufficient calendar history."})
            return {
                "score": None,
                "status": "unavailable_insufficient_calendar_history",
                "recent": None,
                "baseline": None,
                "weekly_equivalent": None,
                "ratio": None,
                "coverage": coverage,
                "complete": False,
                "warnings": warnings,
            }
        value = nonnegative(by_date[day].get("activity_total_duration_seconds"))
        if value is None:
            warnings.append("CAP activity duration data is incomplete.")
            events.append({"code": "CAP_ACTIVITY_DURATION_INCOMPLETE", "severity": "warning", "date": current.isoformat(), "message": "CAP activity duration data is incomplete."})
            return {
                "score": None,
                "status": "unavailable_incomplete_activity_duration_data",
                "recent": None,
                "baseline": None,
                "weekly_equivalent": None,
                "ratio": None,
                "coverage": coverage,
                "complete": False,
                "warnings": warnings,
            }
        coverage += 1
        values[day] = value
    recent = sum(values[day] for day in recent_dates)
    baseline = sum(values[day] for day in baseline_dates)
    weekly = baseline / 3
    if weekly <= 0:
        warnings.append("CAP baseline activity duration is zero.")
        events.append({"code": "CAP_ZERO_BASELINE_ACTIVITY_DURATION", "severity": "warning", "date": current.isoformat(), "message": "CAP baseline activity duration is zero."})
        return {"score": None, "status": "unavailable_zero_baseline_activity_duration", "recent": round6(recent), "baseline": round6(baseline), "weekly_equivalent": round6(weekly), "ratio": None, "coverage": coverage, "complete": True, "warnings": warnings}
    ratio = recent / weekly
    return {"score": round2(clip(100 * ratio)), "status": "computed", "recent": round6(recent), "baseline": round6(baseline), "weekly_equivalent": round6(weekly), "ratio": round6(ratio), "coverage": coverage, "complete": True, "warnings": warnings}


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def signal_stability(current_value: float, history: list[float], field: str, mode: str, floor: float) -> dict[str, Any]:
    baseline = median(history)
    mad = median([abs(value - baseline) for value in history])
    scaled_mad = 1.4826 * mad
    effective_scale = max(scaled_mad, floor)
    if mode == "rhr":
        adverse = max(0, current_value - baseline)
    elif mode in {"hrv", "spo2"}:
        adverse = max(0, baseline - current_value)
    else:
        adverse = abs(current_value - baseline)
    units = adverse / effective_scale
    score = clip(100 - 20 * units)
    return {
        "score": round2(score),
        "current_value": round6(current_value),
        "baseline_median": round6(baseline),
        "scaled_mad": round6(scaled_mad),
        "effective_scale": round6(effective_scale),
        "baseline_observations": len(history),
        "method": "prior_28d_median_mad_personal_baseline",
    }


def compute_vs(current: date, by_date: dict[date, dict[str, Any]], policy: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    vs_policy = policy["components"]["VS"]
    weights = {key: float(value) for key, value in vs_policy["signal_weights"].items()}
    floors = {key: float(value) for key, value in vs_policy["scale_floors"].items()}
    signal_defs = {
        "rhr_stability": ("resting_hr_bpm", "rhr", floors["resting_hr_bpm"]),
        "hrv_stability": ("hrv_last_night_avg_ms", "hrv", floors["hrv_last_night_avg_ms"]),
        "spo2_stability": ("avg_sleep_spo2", "spo2", floors["avg_sleep_spo2"]),
        "respiration_stability": ("avg_sleep_respiration", "respiration", floors["avg_sleep_respiration"]),
    }
    history_days = date_window(current, 28, include_current=False)
    details: dict[str, dict[str, Any]] = {}
    available: list[str] = []
    warnings: list[str] = []
    for signal, (field, mode, floor) in signal_defs.items():
        current_value = number(by_date[current].get(field))
        history = [number(by_date[day].get(field)) for day in history_days if day in by_date and number(by_date[day].get(field)) is not None]
        if current_value is None:
            details[signal] = {"score": None, "source_field": field, "current_value": None, "warnings": ["Current signal value unavailable."]}
            events.append({"code": "VS_SIGNAL_VALUE_INVALID", "severity": "warning", "date": current.isoformat(), "signal": signal, "message": "VS current signal value unavailable."})
            continue
        if len(history) < int(vs_policy["minimum_baseline_observations"]):
            details[signal] = {"score": None, "source_field": field, "current_value": round6(current_value), "baseline_observations": len(history), "warnings": ["Insufficient baseline observations."]}
            events.append({"code": "VS_BASELINE_INSUFFICIENT", "severity": "warning", "date": current.isoformat(), "signal": signal, "message": "VS baseline has insufficient observations."})
            continue
        result = signal_stability(current_value, [float(value) for value in history if value is not None], field, mode, floor)
        result["source_field"] = field
        result["warnings"] = []
        details[signal] = result
        available.append(signal)
    available_weight = sum(weights[signal] for signal in available)
    missing = [signal for signal in signal_defs if signal not in available]
    effective: dict[str, float] = {}
    contributions: dict[str, float] = {}
    score = None
    status = "insufficient_vital_signal_coverage"
    if len(available) >= int(vs_policy["minimum_available_signals"]) and available_weight >= float(vs_policy["minimum_available_weight_sum"]):
        status = "computed"
        for signal in available:
            effective[signal] = round6(weights[signal] / available_weight)
            contributions[signal] = round6(float(details[signal]["score"]) * (weights[signal] / available_weight))
        score = round2(sum(contributions.values()))
    else:
        events.append({"code": "VS_INSUFFICIENT_SIGNAL_COVERAGE", "severity": "warning", "date": current.isoformat(), "message": "VS has insufficient available signal coverage."})
        warnings.append("VS has insufficient available signal coverage.")
    return {
        "score": score,
        "status": status,
        "available": available,
        "missing": missing,
        "available_count": len(available),
        "available_weight_sum": round6(available_weight),
        "coverage_ratio": round6(available_weight),
        "base_weights": weights,
        "effective_weights": effective,
        "contributions": contributions,
        "details": details,
        "warnings": warnings,
    }


def flatten(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (dict, list)):
            out[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            out[key] = value
    return out


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for record in records:
            flat = flatten(record)
            writer.writerow({field: "" if flat.get(field) is None else flat.get(field) for field in CSV_FIELDS})


def try_write_parquet(path: Path, records: list[dict[str, Any]]) -> tuple[bool, str | None]:
    try:
        import pandas as pd  # type: ignore
        import pyarrow  # noqa: F401  # type: ignore
    except Exception as exc:
        return False, f"PARQUET_DEPENDENCY_UNAVAILABLE: {exc.__class__.__name__}"
    try:
        frame = pd.DataFrame([{field: flatten(record).get(field) for field in CSV_FIELDS} for record in records])
        frame.to_parquet(path, index=False)
        return True, None
    except Exception as exc:
        return False, f"PARQUET_WRITE_FAILED: {exc.__class__.__name__}: {exc}"


def build_schema() -> dict[str, Any]:
    fields = [
        {"name": "lq_score", "component": "LQ", "type": "number", "nullable": True, "description": "Load Quality score derived from existing ACWR metric, preferring EWMA ACWR."},
        {"name": "rec_score", "component": "REC", "type": "number", "nullable": True, "description": "Recovery score inherited directly from deterministic readiness_score."},
        {"name": "cap_score", "component": "CAP", "type": "number", "nullable": True, "description": "Observed performed-capacity proxy based on recent seven-day activity duration relative to prior twenty-one-day weekly-equivalent baseline."},
        {"name": "vs_score", "component": "VS", "type": "number", "nullable": True, "description": "Vital Stability score derived from available physiological signals relative to personal historical baselines."},
    ]
    return {
        "module_id": MODULE_ID,
        "schema_version": "pws_components_schema_v1",
        "policy_version": POLICY_VERSION,
        "primary_key": "date",
        "component_score_range": {"minimum": 0, "maximum": 100},
        "missing_values_policy": "unavailable_component_scores_remain_null",
        "fields": fields,
        "component_scope_notes": {
            "LQ": "Monotony and strain are retained as context only and do not affect LQ in version 1.",
            "REC": "REC does not recompute readiness; it inherits readiness_score when available.",
            "CAP": "CAP is a duration-based performed-capacity proxy and is not an absolute fitness measure.",
            "VS": "VS measures deviations from personal baseline and is not a medical assessment.",
        },
        "excluded_future_fields": sorted(FORBIDDEN),
    }


def execute(root: Path | None = None) -> int:
    root = root or ROOT
    out_dir = root / OUT_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    log_lines = [f"Module: {MODULE_ID}", f"Started at: {started_at}", f"Policy version: {POLICY_VERSION}", "Inputs: module 08 load metrics and module 09 readiness"]
    errors: list[dict[str, Any]] = []

    policy_path = root / "config/pws_components_policy_v1.json"
    if not policy_path.exists():
        errors.append({"code": "PWS_COMPONENTS_POLICY_NOT_FOUND", "severity": "error", "message": "config/pws_components_policy_v1.json is missing."})
        write_run_artifacts(root, started_at, "invalid_pws_components_policy", "failed", errors, log_lines)
        return 1
    try:
        policy = read_json(policy_path)
    except Exception as exc:
        errors.append({"code": "PWS_COMPONENTS_POLICY_INVALID", "severity": "error", "message": str(exc)})
        write_run_artifacts(root, started_at, "invalid_pws_components_policy", "failed", errors, log_lines)
        return 1
    policy_errors = validate_policy(policy)
    if policy_errors:
        errors.extend([{**error, "severity": "error"} for error in policy_errors])
        write_run_artifacts(root, started_at, "invalid_pws_components_policy", "failed", errors, log_lines)
        return 1

    missing_load = [path for path in INPUTS[1:5] if not (root / path).exists()]
    missing_readiness = [path for path in INPUTS[5:] if not (root / path).exists()]
    if missing_load:
        errors.append({"code": "LOAD_METRICS_NOT_FOUND", "severity": "error", "missing_inputs": [path.as_posix() for path in missing_load], "message": "Required module 08 artifacts are missing."})
        write_run_artifacts(root, started_at, "blocked_missing_load_metrics", "failed", errors, log_lines)
        return 1
    if missing_readiness:
        errors.append({"code": "READINESS_NOT_FOUND", "severity": "error", "missing_inputs": [path.as_posix() for path in missing_readiness], "message": "Required module 09 artifacts are missing."})
        write_run_artifacts(root, started_at, "blocked_missing_readiness", "failed", errors, log_lines)
        return 1

    try:
        load_metrics = read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics.json")
        read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics_schema.json")
        read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json")
        read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics_lineage.json")
        readiness = read_json(root / "data/pipeline/09_compute_readiness/readiness.json")
        read_json(root / "data/pipeline/09_compute_readiness/readiness_schema.json")
        read_json(root / "data/pipeline/09_compute_readiness/readiness_quality_report.json")
        read_json(root / "data/pipeline/09_compute_readiness/readiness_lineage.json")
    except Exception as exc:
        errors.append({"code": "ARTIFACT_WRITE_ERROR", "severity": "error", "message": f"Could not read inputs: {exc}"})
        write_run_artifacts(root, started_at, "pws_component_computation_failed", "failed", errors, log_lines)
        return 1

    if load_metrics.get("ready_for_next_module") is not True:
        errors.append({"code": "LOAD_METRICS_NOT_READY", "severity": "error", "message": "load_metrics.json is not ready."})
        write_run_artifacts(root, started_at, "blocked_load_metrics_not_ready", "failed", errors, log_lines)
        return 1
    if readiness.get("ready_for_next_module") is not True:
        errors.append({"code": "READINESS_NOT_READY", "severity": "error", "message": "readiness.json is not ready."})
        write_run_artifacts(root, started_at, "blocked_readiness_not_ready", "failed", errors, log_lines)
        return 1

    load_records, load_errors = validate_records(load_metrics.get("records"), "load_metrics")
    readiness_records, readiness_errors = validate_records(readiness.get("records"), "readiness")
    errors.extend(load_errors + readiness_errors)
    if errors:
        write_run_artifacts(root, started_at, "blocked_duplicate_dates" if any(e["code"] == "DUPLICATE_DATE_FOUND" for e in errors) else "pws_component_computation_failed", "failed", errors, log_lines)
        return 1

    load_by_date = {day: record for day, record in load_records}
    readiness_by_date = {day: record for day, record in readiness_records}
    orphan_readiness_dates = sorted(day.isoformat() for day in readiness_by_date if day not in load_by_date)
    events: list[dict[str, Any]] = []
    for orphan in orphan_readiness_dates:
        events.append({"code": "ORPHAN_READINESS_DATE_FOUND", "severity": "warning", "date": orphan, "message": "Readiness date is not present in load metrics axis."})
    for overlap in OVERLAPS:
        events.append({"code": "KNOWN_COMPONENT_SIGNAL_OVERLAP", "severity": "warning", "components": overlap["components"], "message": overlap["reason"]})

    output_records: list[dict[str, Any]] = []
    for current, load_record in load_records:
        current_str = current.isoformat()
        event_count = len(events)
        readiness_record = readiness_by_date.get(current)
        lq = compute_lq(load_record, current_str, events)
        rec = compute_rec(readiness_record, current_str, events)
        cap = compute_cap(current, load_by_date, events)
        vs = compute_vs(current, load_by_date, policy, events)
        row = {
            "date": current_str,
            "acwr_ewma": load_record.get("acwr_ewma"),
            "acwr_rolling": load_record.get("acwr_rolling"),
            "monotony_7d": load_record.get("monotony_7d"),
            "strain_7d": load_record.get("strain_7d"),
            "readiness_score": readiness_record.get("readiness_score") if readiness_record else None,
            "readiness_status": readiness_record.get("readiness_status") if readiness_record else None,
            "readiness_coverage_ratio": readiness_record.get("readiness_coverage_ratio") if readiness_record else None,
            "activity_total_duration_seconds": load_record.get("activity_total_duration_seconds"),
            "resting_hr_bpm": load_record.get("resting_hr_bpm"),
            "hrv_last_night_avg_ms": load_record.get("hrv_last_night_avg_ms"),
            "avg_sleep_spo2": load_record.get("avg_sleep_spo2"),
            "avg_sleep_respiration": load_record.get("avg_sleep_respiration"),
            "lq_score": lq["score"],
            "lq_status": lq["status"],
            "lq_source_metric": lq["source_metric"],
            "lq_source_value": lq["source_value"],
            "lq_method": lq["method"],
            "lq_context_monotony_7d": load_record.get("monotony_7d"),
            "lq_context_strain_7d": load_record.get("strain_7d"),
            "lq_warnings": lq["warnings"],
            "rec_score": rec["score"],
            "rec_status": rec["status"],
            "rec_source_metric": "readiness_score",
            "rec_source_value": rec["source_value"],
            "rec_method": "identity_from_readiness_score" if rec["score"] is not None else "unavailable",
            "rec_source_readiness_status": rec["source_status"],
            "rec_source_coverage_ratio": rec["coverage"],
            "rec_warnings": rec["warnings"],
            "cap_score": cap["score"],
            "cap_status": cap["status"],
            "cap_method": "recent_7d_activity_duration_relative_to_prior_21d_weekly_equivalent",
            "cap_recent_duration_seconds_7d": cap["recent"],
            "cap_baseline_duration_seconds_21d": cap["baseline"],
            "cap_baseline_weekly_equivalent_seconds": cap["weekly_equivalent"],
            "cap_recent_to_baseline_ratio": cap["ratio"],
            "cap_window_required_days": 28,
            "cap_window_coverage_days": cap["coverage"],
            "cap_window_complete": cap["complete"],
            "cap_warnings": cap["warnings"],
            "vs_score": vs["score"],
            "vs_status": vs["status"],
            "vs_rhr_stability_score": vs["details"].get("rhr_stability", {}).get("score"),
            "vs_hrv_stability_score": vs["details"].get("hrv_stability", {}).get("score"),
            "vs_spo2_stability_score": vs["details"].get("spo2_stability", {}).get("score"),
            "vs_respiration_stability_score": vs["details"].get("respiration_stability", {}).get("score"),
            "vs_signal_details": vs["details"],
            "vs_available_signals": vs["available"],
            "vs_missing_signals": vs["missing"],
            "vs_available_signal_count": vs["available_count"],
            "vs_available_base_weight_sum": vs["available_weight_sum"],
            "vs_coverage_ratio": vs["coverage_ratio"],
            "vs_base_signal_weights": vs["base_weights"],
            "vs_effective_signal_weights": vs["effective_weights"],
            "vs_signal_contributions": vs["contributions"],
            "vs_warnings": vs["warnings"],
        }
        component_map = {"LQ": row["lq_score"], "REC": row["rec_score"], "CAP": row["cap_score"], "VS": row["vs_score"]}
        available = [name for name, value in component_map.items() if value is not None]
        missing = [name for name in component_map if name not in available]
        row.update(
            {
                "available_pws_components": available,
                "missing_pws_components": missing,
                "available_pws_components_count": len(available),
                "pws_components_coverage_ratio": round6(len(available) / 4),
                "known_component_overlaps": [
                    "LQ and REC may both contain load-balance signal exposure through ACWR.",
                    "REC and VS may both use HRV and RHR signals for different interpretations.",
                ],
                "component_warnings": [event["message"] for event in events[event_count:] if event.get("date") == current_str and event.get("message")],
                "final_pws_computed": False,
                "pws_weights_computed": False,
                "llm_used": False,
            }
        )
        for forbidden in FORBIDDEN:
            if forbidden in row:
                raise RuntimeError(f"Forbidden future field leaked into PWS components output: {forbidden}")
        output_records.append(row)

    parquet_written, parquet_reason = try_write_parquet(out_dir / "pws_components.parquet", output_records)
    if not parquet_written:
        code = "PARQUET_DEPENDENCY_UNAVAILABLE" if parquet_reason and parquet_reason.startswith("PARQUET_DEPENDENCY_UNAVAILABLE") else "PARQUET_WRITE_FAILED"
        events.append({"code": code, "severity": "warning", "message": parquet_reason})

    def available_count(field: str) -> int:
        return sum(1 for record in output_records if record.get(field) is not None)

    component_availability = {
        "LQ": {
            "available_count": available_count("lq_score"),
            "missing_count": len(output_records) - available_count("lq_score"),
            "coverage_ratio": round6(available_count("lq_score") / len(output_records)) if output_records else 0,
            "methods_used": {
                "acwr_ewma": sum(1 for row in output_records if row.get("lq_source_metric") == "acwr_ewma"),
                "acwr_rolling": sum(1 for row in output_records if row.get("lq_source_metric") == "acwr_rolling"),
                "unavailable": sum(1 for row in output_records if row.get("lq_score") is None),
            },
        },
        "REC": {
            "available_count": available_count("rec_score"),
            "missing_count": len(output_records) - available_count("rec_score"),
            "coverage_ratio": round6(available_count("rec_score") / len(output_records)) if output_records else 0,
            "methods_used": {
                "identity_from_readiness_score": sum(1 for row in output_records if row.get("rec_score") is not None),
                "unavailable": sum(1 for row in output_records if row.get("rec_score") is None),
            },
        },
        "CAP": {
            "available_count": available_count("cap_score"),
            "missing_count": len(output_records) - available_count("cap_score"),
            "coverage_ratio": round6(available_count("cap_score") / len(output_records)) if output_records else 0,
            "unavailable_reasons": {
                "insufficient_calendar_history": sum(1 for row in output_records if row.get("cap_status") == "unavailable_insufficient_calendar_history"),
                "incomplete_activity_duration_data": sum(1 for row in output_records if row.get("cap_status") == "unavailable_incomplete_activity_duration_data"),
                "zero_baseline_activity_duration": sum(1 for row in output_records if row.get("cap_status") == "unavailable_zero_baseline_activity_duration"),
            },
        },
        "VS": {
            "available_count": available_count("vs_score"),
            "missing_count": len(output_records) - available_count("vs_score"),
            "coverage_ratio": round6(available_count("vs_score") / len(output_records)) if output_records else 0,
            "subsignal_availability": {
                "rhr_stability": available_count("vs_rhr_stability_score"),
                "hrv_stability": available_count("vs_hrv_stability_score"),
                "spo2_stability": available_count("vs_spo2_stability_score"),
                "respiration_stability": available_count("vs_respiration_stability_score"),
            },
        },
    }
    coverage_counts = {str(i): sum(1 for row in output_records if row["available_pws_components_count"] == i) for i in range(5)}
    if all(row["available_pws_components_count"] == 4 for row in output_records):
        status = "computed"
    elif any(row["available_pws_components_count"] == 0 for row in output_records):
        status = "computed_with_unavailable_components"
    elif any(row["available_pws_components_count"] < 4 for row in output_records):
        status = "computed_with_partial_component_coverage"
    elif events:
        status = "computed_with_warnings"
    else:
        status = "computed"

    date_range = {"first_date": load_records[0][0].isoformat() if load_records else None, "last_date": load_records[-1][0].isoformat() if load_records else None}
    payload = {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "status": status,
        "source_artifacts": {"load_metrics": "data/pipeline/08_compute_load_metrics/load_metrics.json", "readiness": "data/pipeline/09_compute_readiness/readiness.json"},
        "component_definitions": {"LQ": "Load Quality", "REC": "Recovery", "CAP": "Capacity", "VS": "Vital Stability"},
        "component_score_range": {"minimum": 0, "maximum": 100},
        "records_count": len(output_records),
        "date_range": date_range,
        "known_component_overlaps": OVERLAPS,
        "records": output_records,
        "missing_values_policy": "preserve_unavailable_components_as_null",
        "final_pws_computed": False,
        "pws_weights_computed": False,
        "llm_used": False,
        "ready_for_next_module": True,
        "private_data_notice": "PWS component records contain private health, activity and training data and must not be committed to version control.",
    }
    quality = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "records_count": len(output_records),
        "component_availability": component_availability,
        "daily_component_coverage": {
            "all_four_components_available_count": coverage_counts["4"],
            "three_components_available_count": coverage_counts["3"],
            "two_components_available_count": coverage_counts["2"],
            "one_component_available_count": coverage_counts["1"],
            "zero_components_available_count": coverage_counts["0"],
        },
        "orphan_readiness_dates": orphan_readiness_dates,
        "known_component_overlaps": [
            {"components": overlap["components"], "reason": overlap["reason"], "requires_later_weighting_attention": True} for overlap in OVERLAPS
        ],
        "parquet_output": {"requested": True, "written": parquet_written, "warning": parquet_reason},
        "final_pws_computed": False,
        "pws_weights_computed": False,
        "llm_used": False,
        "warnings": [
            "Component scores are heuristic decision-support measures and are not medical diagnoses.",
            "Missing component values were preserved as null and were not replaced with zero.",
            "Known signal overlaps are disclosed but intentionally not resolved in this module.",
        ] + [event["message"] for event in events if event.get("message")],
        "ready_for_next_module": True,
    }
    lineage = {
        "module_id": MODULE_ID,
        "lineage_version": "pws_components_lineage_v1",
        "source_artifacts": [
            {"module_id": "08_compute_load_metrics", "artifact_path": "data/pipeline/08_compute_load_metrics/load_metrics.json", "role": "load_metrics_and_base_daily_fields_source"},
            {"module_id": "09_compute_readiness", "artifact_path": "data/pipeline/09_compute_readiness/readiness.json", "role": "readiness_source_for_REC"},
        ],
        "component_lineage": [
            {"component": "LQ", "output_field": "lq_score", "preferred_input": "acwr_ewma", "fallback_input": "acwr_rolling", "context_only_inputs": ["monotony_7d", "strain_7d"], "transformation": "configured_piecewise_acwr_quality_score"},
            {"component": "REC", "output_field": "rec_score", "input": "readiness_score", "transformation": "identity_from_existing_readiness"},
            {"component": "CAP", "output_field": "cap_score", "input": "activity_total_duration_seconds", "transformation": "recent_7_day_duration_relative_to_prior_21_day_weekly_equivalent_baseline"},
            {"component": "VS", "output_field": "vs_score", "inputs": ["resting_hr_bpm", "hrv_last_night_avg_ms", "avg_sleep_spo2", "avg_sleep_respiration"], "transformation": "weighted_available_signal_stability_scores_against_prior_28_day_personal_baselines"},
        ],
        "known_component_overlaps": [{"components": overlap["components"], "resolution_stage": "future_pws_weighting_module"} for overlap in OVERLAPS],
        "forbidden_calculation_confirmation": {
            "final_pws_computed": False,
            "pws_weights_computed": False,
            "dynamic_weights_computed": False,
            "llm_used": False,
            "medical_diagnosis_generated": False,
            "training_prescription_generated": False,
        },
    }
    write_json(out_dir / "pws_components.json", payload)
    write_csv(out_dir / "pws_components.csv", output_records)
    write_json(out_dir / "pws_components_schema.json", build_schema())
    write_json(out_dir / "pws_components_quality_report.json", quality)
    write_json(out_dir / "pws_components_lineage.json", lineage)
    errors_for_file = events
    log_lines.extend(
        [
            f"Input load records: {len(load_records)}",
            f"Input readiness records: {len(readiness_records)}",
            f"Date range: {date_range['first_date']}..{date_range['last_date']}",
            "Computed components only: LQ, REC, CAP, VS",
            f"LQ available days: {component_availability['LQ']['available_count']}",
            f"REC available days: {component_availability['REC']['available_count']}",
            f"CAP available days: {component_availability['CAP']['available_count']}",
            f"VS available days: {component_availability['VS']['available_count']}",
            f"All four components days: {coverage_counts['4']}",
            f"Partial coverage days: {len(output_records) - coverage_counts['4']}",
            f"LQ acwr_rolling fallback count: {component_availability['LQ']['methods_used']['acwr_rolling']}",
            f"REC unavailable count: {component_availability['REC']['missing_count']}",
            f"CAP insufficient history count: {component_availability['CAP']['unavailable_reasons']['insufficient_calendar_history']}",
            f"VS unavailable count: {component_availability['VS']['missing_count']}",
            "Known overlaps disclosed: LQ/REC and REC/VS",
            "JSON written: true",
            "CSV written: true",
            f"Parquet written: {str(parquet_written).lower()}",
            "Missing components remained null and were not replaced with zero.",
            "Final PWS and PWS weights were not computed.",
            "LLM was not used.",
            "Components are not medical diagnoses or training prescriptions.",
        ]
    )
    write_run_artifacts(root, started_at, status, "success", errors_for_file, log_lines, parquet_written, parquet_reason)
    return 0


def main() -> int:
    return execute()


if __name__ == "__main__":
    raise SystemExit(main())
