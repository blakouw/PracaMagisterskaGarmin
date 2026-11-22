from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "09_compute_readiness"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "readiness_policy_v1"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR_REL = Path("data/pipeline/09_compute_readiness")

INPUTS = [
    Path("config/readiness_policy_v1.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics_schema.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json"),
    Path("data/pipeline/08_compute_load_metrics/load_metrics_lineage.json"),
]

GENERATED = [
    "data/pipeline/09_compute_readiness/readiness.json",
    "data/pipeline/09_compute_readiness/readiness.csv",
    "data/pipeline/09_compute_readiness/readiness_schema.json",
    "data/pipeline/09_compute_readiness/readiness_quality_report.json",
    "data/pipeline/09_compute_readiness/readiness_lineage.json",
    "data/pipeline/09_compute_readiness/run_manifest.json",
    "data/pipeline/09_compute_readiness/run_log.txt",
    "data/pipeline/09_compute_readiness/errors.json",
]

COMPONENTS = ["hrv", "stress", "rhr", "load_balance"]
COMPONENT_SCORE_FIELDS = {
    "hrv": "hrv_readiness_score",
    "stress": "stress_readiness_score",
    "rhr": "rhr_readiness_score",
    "load_balance": "load_balance_readiness_score",
}
READINESS_FIELDS = [
    "hrv_readiness_score",
    "hrv_readiness_method",
    "hrv_readiness_input_fields",
    "stress_readiness_score",
    "stress_readiness_method",
    "stress_readiness_input_fields",
    "rhr_delta_used_for_readiness",
    "rhr_readiness_score",
    "rhr_readiness_method",
    "rhr_readiness_input_fields",
    "load_balance_source_metric",
    "load_balance_source_value",
    "load_balance_readiness_score",
    "load_balance_readiness_method",
    "available_readiness_components",
    "missing_readiness_components",
    "available_components_count",
    "available_base_weight_sum",
    "readiness_coverage_ratio",
    "base_component_weights",
    "effective_component_weights",
    "component_contributions",
    "readiness_score",
    "readiness_status",
    "readiness_label_id",
    "readiness_label",
    "readiness_warnings",
]
CSV_FIELDS = [
    "date",
    "hrv_readiness_score",
    "hrv_readiness_method",
    "stress_readiness_score",
    "rhr_readiness_score",
    "rhr_delta_used_for_readiness",
    "load_balance_source_metric",
    "load_balance_source_value",
    "load_balance_readiness_score",
    "available_components_count",
    "available_base_weight_sum",
    "readiness_coverage_ratio",
    "readiness_score",
    "readiness_status",
    "readiness_label_id",
    "readiness_label",
]
FORBIDDEN_RECORD_FIELDS = {
    "LQ",
    "REC",
    "CAP",
    "VS",
    "pws_deterministic",
    "pws_llm_assisted",
    "pws_weights",
    "pws_priority",
    "llm_adjustment",
    "coach_message",
    "training_recommendation",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return parsed if parsed.strftime("%Y-%m-%d") == value else None


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


def positive(value: Any) -> float | None:
    result = number(value)
    return result if result is not None and result > 0 else None


def nonnegative(value: Any) -> float | None:
    result = number(value)
    return result if result is not None and result >= 0 else None


def clip(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def round2(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def round4(value: float | None) -> float | None:
    return None if value is None else round(value, 4)


def validate_policy(policy: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append({"code": "READINESS_POLICY_INVALID", "message": "Unexpected policy_version."})
    if policy.get("score_name") != "readiness_score":
        errors.append({"code": "READINESS_POLICY_INVALID", "message": "score_name must be readiness_score."})
    weights = policy.get("base_weights")
    if not isinstance(weights, dict) or set(weights) != set(COMPONENTS):
        errors.append({"code": "BASE_WEIGHTS_INVALID", "message": "base_weights must define exactly the readiness components."})
    else:
        total = sum(float(weights[k]) for k in COMPONENTS)
        if abs(total - float(policy.get("weights_must_sum_to", 1.0))) > 1e-9:
            errors.append({"code": "BASE_WEIGHTS_INVALID", "message": "base_weights must sum to 1.0."})
    missing_policy = policy.get("missing_component_policy", {})
    if missing_policy.get("do_not_substitute_zero") is not True:
        errors.append({"code": "READINESS_POLICY_INVALID", "message": "Missing components must not be substituted with zero."})
    if missing_policy.get("minimum_available_base_weight_sum_for_final_score") != 0.50:
        errors.append({"code": "READINESS_POLICY_INVALID", "message": "Minimum available base weight sum must be 0.50."})
    if missing_policy.get("minimum_available_components_for_final_score") != 3:
        errors.append({"code": "READINESS_POLICY_INVALID", "message": "Minimum available components must be 3."})
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
            "optional_generated_artifacts": [
                {
                    "path": "data/pipeline/09_compute_readiness/readiness.parquet",
                    "written": parquet_written,
                    "reason_if_not_written": parquet_reason,
                }
            ],
            "log_file": "data/pipeline/09_compute_readiness/run_log.txt",
            "errors_file": "data/pipeline/09_compute_readiness/errors.json",
        },
    )
    write_json(out_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    log_lines.extend([f"Finished at: {finished_at}", f"Execution status: {execution_status}", f"Domain status: {domain_status}"])
    (out_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def clip_with_warning(component: str, field: str, value: float, warnings: list[str], events: list[dict[str, Any]], current_date: str) -> float:
    clipped = clip(value)
    if clipped != value:
        message = f"{field} value was clipped to 0..100 for {component} readiness."
        warnings.append(message)
        events.append({"code": "COMPONENT_VALUE_CLIPPED", "severity": "warning", "date": current_date, "component": component, "field": field, "message": message})
    return clipped


def hrv_component(record: dict[str, Any], current_date: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    warnings: list[str] = []
    last = positive(record.get("hrv_last_night_avg_ms"))
    low = positive(record.get("hrv_baseline_balanced_low_ms"))
    upper = positive(record.get("hrv_baseline_balanced_upper_ms"))
    if last is not None and low is not None and upper is not None and low <= upper:
        if low <= last <= upper:
            value = 100.0
        elif last < low:
            value = 100 * last / low
        else:
            value = max(70, 100 - ((last - upper) / upper) * 100)
        return {"score": round2(clip(value)), "method": "baseline_band", "inputs": ["hrv_last_night_avg_ms", "hrv_baseline_balanced_low_ms", "hrv_baseline_balanced_upper_ms"], "warnings": warnings}
    weekly = positive(record.get("hrv_weekly_avg_ms"))
    if last is not None and weekly is not None:
        events.append({"code": "HRV_WEEKLY_AVERAGE_FALLBACK_USED", "severity": "warning", "date": current_date, "component": "hrv", "message": "HRV weekly average fallback was used."})
        return {"score": round2(clip(100 * last / weekly)), "method": "relative_to_weekly_average", "inputs": ["hrv_last_night_avg_ms", "hrv_weekly_avg_ms"], "warnings": warnings}
    events.append({"code": "COMPONENT_UNAVAILABLE", "severity": "warning", "date": current_date, "component": "hrv", "message": "HRV component unavailable."})
    return {"score": None, "method": "unavailable", "inputs": [], "warnings": warnings}


def direct_component(record: dict[str, Any], source_field: str, component: str, method: str, current_date: str, events: list[dict[str, Any]], inverse: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    value = number(record.get(source_field))
    if value is None:
        events.append({"code": "COMPONENT_UNAVAILABLE", "severity": "warning", "date": current_date, "component": component, "message": f"{component} component unavailable."})
        return {"score": None, "method": "unavailable", "inputs": [], "warnings": warnings}
    raw = 100 - value if inverse else value
    return {"score": round2(clip_with_warning(component, source_field, raw, warnings, events, current_date)), "method": method, "inputs": [source_field], "warnings": warnings}


def rhr_component(record: dict[str, Any], current_date: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    resting = positive(record.get("resting_hr_bpm"))
    baseline = positive(record.get("resting_hr_baseline_bpm"))
    if resting is None or baseline is None:
        events.append({"code": "COMPONENT_UNAVAILABLE", "severity": "warning", "date": current_date, "component": "rhr", "message": "RHR component unavailable."})
        return {"score": None, "method": "unavailable", "inputs": [], "delta": None, "warnings": []}
    delta = resting - baseline
    score = clip(100 - max(0, delta) * 8)
    return {"score": round2(score), "method": "elevation_above_baseline_penalty", "inputs": ["resting_hr_bpm", "resting_hr_baseline_bpm"], "delta": round2(delta), "warnings": []}


def load_balance_component(record: dict[str, Any], current_date: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    source_metric = "acwr_ewma"
    value = positive(record.get("acwr_ewma"))
    if value is None:
        value = positive(record.get("acwr_rolling"))
        source_metric = "acwr_rolling" if value is not None else None
        if value is not None:
            events.append({"code": "LOAD_BALANCE_ROLLING_ACWR_FALLBACK_USED", "severity": "warning", "date": current_date, "component": "load_balance", "message": "Rolling ACWR fallback was used for load balance."})
    if value is None:
        events.append({"code": "COMPONENT_UNAVAILABLE", "severity": "warning", "date": current_date, "component": "load_balance", "message": "Load balance component unavailable."})
        return {"score": None, "method": "unavailable", "source_metric": None, "source_value": None, "warnings": []}
    if value < 0.8:
        score = max(40, 100 - ((0.8 - value) / 0.8) * 60)
    elif value <= 1.3:
        score = 100
    elif value <= 1.5:
        score = 100 - ((value - 1.3) / 0.2) * 40
    else:
        score = max(0, 60 - ((value - 1.5) / 0.5) * 60)
    return {"score": round2(clip(score)), "method": "acwr_piecewise_readiness_contribution", "source_metric": source_metric, "source_value": round4(value), "warnings": []}


def readiness_label(score: float | None) -> tuple[str, str]:
    if score is None:
        return "insufficient_data", "insufficient_data"
    if score < 40:
        return "low", "niska"
    if score < 60:
        return "reduced", "obnizona"
    if score < 80:
        return "moderate", "umiarkowana"
    return "high", "wysoka"


def flatten(record: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (list, dict)):
            flat[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            flat[key] = value
    return flat


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = list(CSV_FIELDS)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            flat = flatten(record)
            writer.writerow({field: "" if flat.get(field) is None else flat.get(field) for field in fields})


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


def build_schema(base_weights: dict[str, float]) -> dict[str, Any]:
    fields = [
        {"name": "hrv_readiness_score", "type": "number", "nullable": True, "base_weight": base_weights["hrv"], "description": "HRV readiness component based on configured baseline or weekly-average comparison."},
        {"name": "stress_readiness_score", "type": "number", "nullable": True, "base_weight": base_weights["stress"], "description": "Inverse average stress contribution."},
        {"name": "rhr_readiness_score", "type": "number", "nullable": True, "base_weight": base_weights["rhr"], "description": "Penalty-based score for resting heart rate elevation above configured baseline."},
        {"name": "load_balance_readiness_score", "type": "number", "nullable": True, "base_weight": base_weights["load_balance"], "description": "Heuristic readiness contribution based on existing ACWR metric from module 08."},
        {"name": "readiness_score", "type": "number", "nullable": True, "description": "Weighted readiness result computed from available components only when minimum availability rules are satisfied."},
    ]
    for field in READINESS_FIELDS:
        if field not in {item["name"] for item in fields}:
            fields.append({"name": field, "type": "audit", "nullable": True, "description": "Readiness audit, method, coverage or lineage field."})
    return {
        "module_id": MODULE_ID,
        "schema_version": "readiness_schema_v1",
        "policy_version": POLICY_VERSION,
        "primary_key": "date",
        "score_field": "readiness_score",
        "score_range": {"minimum": 0, "maximum": 100},
        "missing_component_policy": "null_and_weight_renormalization_only_after_minimum_availability_requirements",
        "minimum_data_requirements": {"minimum_available_base_weight_sum": 0.50, "minimum_available_components": 3},
        "fields": fields,
        "excluded_future_fields": ["LQ", "REC", "CAP", "VS", "pws_deterministic", "pws_llm_assisted", "pws_weights", "pws_priority", "llm_adjustment", "coach_message", "training_recommendation"],
    }


def execute(root: Path | None = None) -> int:
    root = root or ROOT
    out_dir = root / OUT_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    log_lines = [f"Module: {MODULE_ID}", f"Started at: {started_at}", f"Policy version: {POLICY_VERSION}", "Input artifact: data/pipeline/08_compute_load_metrics/load_metrics.json"]
    errors: list[dict[str, Any]] = []

    policy_path = root / "config/readiness_policy_v1.json"
    if not policy_path.exists():
        errors.append({"code": "READINESS_POLICY_NOT_FOUND", "severity": "error", "message": "config/readiness_policy_v1.json is missing."})
        write_run_artifacts(root, started_at, "invalid_readiness_policy", "failed", errors, log_lines)
        return 1
    try:
        policy = read_json(policy_path)
    except Exception as exc:
        errors.append({"code": "READINESS_POLICY_INVALID", "severity": "error", "message": str(exc)})
        write_run_artifacts(root, started_at, "invalid_readiness_policy", "failed", errors, log_lines)
        return 1
    policy_errors = validate_policy(policy)
    if policy_errors:
        errors.extend([{**error, "severity": "error"} for error in policy_errors])
        write_run_artifacts(root, started_at, "invalid_readiness_policy", "failed", errors, log_lines)
        return 1

    missing = [path for path in INPUTS[1:] if not (root / path).exists()]
    if missing:
        errors.append({"code": "LOAD_METRICS_NOT_FOUND", "severity": "error", "message": "Required module 08 artifacts are missing.", "missing_inputs": [path.as_posix() for path in missing]})
        write_run_artifacts(root, started_at, "blocked_missing_load_metrics", "failed", errors, log_lines)
        return 1

    try:
        load_metrics = read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics.json")
        read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics_schema.json")
        read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json")
        read_json(root / "data/pipeline/08_compute_load_metrics/load_metrics_lineage.json")
    except Exception as exc:
        errors.append({"code": "LOAD_METRICS_NOT_FOUND", "severity": "error", "message": f"Could not read module 08 artifacts: {exc}"})
        write_run_artifacts(root, started_at, "blocked_missing_load_metrics", "failed", errors, log_lines)
        return 1

    if load_metrics.get("ready_for_next_module") is not True:
        errors.append({"code": "LOAD_METRICS_NOT_READY", "severity": "error", "message": "load_metrics.json is not ready for next module."})
        write_run_artifacts(root, started_at, "blocked_load_metrics_not_ready", "failed", errors, log_lines)
        return 1

    records = load_metrics.get("records")
    if not isinstance(records, list):
        errors.append({"code": "LOAD_METRICS_NOT_FOUND", "severity": "error", "message": "load_metrics records must be a list."})
        write_run_artifacts(root, started_at, "blocked_missing_load_metrics", "failed", errors, log_lines)
        return 1

    seen: set[str] = set()
    dated_records: list[tuple[str, dict[str, Any]]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or "date" not in record:
            errors.append({"code": "DATE_FIELD_MISSING", "severity": "error", "row_index": index, "message": "Missing date."})
            continue
        parsed = parse_date(record.get("date"))
        if parsed is None:
            errors.append({"code": "DATE_VALUE_INVALID", "severity": "error", "row_index": index, "date": record.get("date"), "message": "Invalid date."})
            continue
        date_key = parsed.strftime("%Y-%m-%d")
        if date_key in seen:
            errors.append({"code": "DUPLICATE_DATE_FOUND", "severity": "error", "date": date_key, "message": "Duplicate readiness date."})
            continue
        seen.add(date_key)
        dated_records.append((date_key, record))
    if errors:
        domain = "blocked_duplicate_dates" if any(error["code"] == "DUPLICATE_DATE_FOUND" for error in errors) else "readiness_computation_failed"
        write_run_artifacts(root, started_at, domain, "failed", errors, log_lines)
        return 1

    dated_records.sort(key=lambda item: item[0])
    base_weights = {key: float(value) for key, value in policy["base_weights"].items()}
    minimum_weight = float(policy["missing_component_policy"]["minimum_available_base_weight_sum_for_final_score"])
    minimum_components = int(policy["missing_component_policy"]["minimum_available_components_for_final_score"])
    output_records: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    for current_date, record in dated_records:
        event_count_before = len(events)
        components = {
            "hrv": hrv_component(record, current_date, events),
            "stress": direct_component(record, "avg_stress", "stress", "inverse_average_stress", current_date, events, inverse=True),
            "rhr": rhr_component(record, current_date, events),
            "load_balance": load_balance_component(record, current_date, events),
        }
        available = [name for name in COMPONENTS if components[name]["score"] is not None]
        missing_components = [name for name in COMPONENTS if name not in available]
        available_weight_sum = sum(base_weights[name] for name in available)
        coverage = available_weight_sum
        effective_weights: dict[str, float] = {}
        contributions: dict[str, float] = {}
        readiness_score = None
        readiness_status = "insufficient_data"
        if len(available) >= minimum_components and available_weight_sum >= minimum_weight:
            readiness_status = "computed"
            for name in available:
                effective_weights[name] = round4(base_weights[name] / available_weight_sum)
                contributions[name] = round4(float(components[name]["score"]) * (base_weights[name] / available_weight_sum))
            readiness_score = round2(sum(contributions.values()))
        else:
            events.append({"code": "INSUFFICIENT_COMPONENT_COVERAGE", "severity": "warning", "date": current_date, "message": "Readiness score unavailable because minimum component coverage was not met."})

        label_id, label = readiness_label(readiness_score)
        row = {"date": current_date}
        row.update(
            {
                "hrv_readiness_score": components["hrv"]["score"],
                "hrv_readiness_method": components["hrv"]["method"],
                "hrv_readiness_input_fields": components["hrv"]["inputs"],
                "stress_readiness_score": components["stress"]["score"],
                "stress_readiness_method": components["stress"]["method"],
                "stress_readiness_input_fields": components["stress"]["inputs"],
                "rhr_delta_used_for_readiness": components["rhr"].get("delta"),
                "rhr_readiness_score": components["rhr"]["score"],
                "rhr_readiness_method": components["rhr"]["method"],
                "rhr_readiness_input_fields": components["rhr"]["inputs"],
                "load_balance_source_metric": components["load_balance"].get("source_metric"),
                "load_balance_source_value": components["load_balance"].get("source_value"),
                "load_balance_readiness_score": components["load_balance"]["score"],
                "load_balance_readiness_method": components["load_balance"]["method"],
                "available_readiness_components": available,
                "missing_readiness_components": missing_components,
                "available_components_count": len(available),
                "available_base_weight_sum": round4(available_weight_sum),
                "readiness_coverage_ratio": round4(coverage),
                "base_component_weights": base_weights,
                "effective_component_weights": effective_weights,
                "component_contributions": contributions,
                "readiness_score": readiness_score,
                "readiness_status": readiness_status,
                "readiness_label_id": label_id,
                "readiness_label": label,
                "readiness_warnings": [event["message"] for event in events[event_count_before:] if event.get("date") == current_date and event.get("message")],
            }
        )
        for forbidden in FORBIDDEN_RECORD_FIELDS:
            if forbidden in row:
                raise RuntimeError(f"Forbidden future field leaked into readiness output: {forbidden}")
        output_records.append(row)

    parquet_written, parquet_reason = try_write_parquet(out_dir / "readiness.parquet", output_records)
    if not parquet_written:
        code = "PARQUET_DEPENDENCY_UNAVAILABLE" if parquet_reason and parquet_reason.startswith("PARQUET_DEPENDENCY_UNAVAILABLE") else "PARQUET_WRITE_FAILED"
        events.append({"code": code, "severity": "warning", "message": parquet_reason})

    def method_counts(component: str) -> dict[str, int]:
        field = f"{component}_readiness_method"
        counts: dict[str, int] = {}
        if component == "load_balance":
            for row in output_records:
                key = row.get("load_balance_source_metric") or "unavailable"
                counts[key] = counts.get(key, 0) + 1
            return counts
        for row in output_records:
            key = row.get(field, "unavailable")
            counts[key] = counts.get(key, 0) + 1
        return counts

    component_availability: dict[str, Any] = {}
    for name in COMPONENTS:
        field = COMPONENT_SCORE_FIELDS[name]
        available_count = sum(1 for row in output_records if row.get(field) is not None)
        item = {
            "available_count": available_count,
            "missing_count": len(output_records) - available_count,
            "coverage_ratio": round4(available_count / len(output_records)) if output_records else 0,
        }
        if name in {"hrv", "load_balance"}:
            item["methods_used"] = method_counts(name)
        component_availability[name] = item

    computed_count = sum(1 for row in output_records if row.get("readiness_score") is not None)
    insufficient_count = len(output_records) - computed_count
    label_counts: dict[str, int] = {"low": 0, "reduced": 0, "moderate": 0, "high": 0, "insufficient_data": 0}
    for row in output_records:
        label_counts[row["readiness_label_id"]] = label_counts.get(row["readiness_label_id"], 0) + 1
    days_with_renormalized = [row["date"] for row in output_records if row["readiness_score"] is not None and row["available_base_weight_sum"] < 1.0]
    clipped_days = sorted({event.get("date") for event in events if event.get("code") == "COMPONENT_VALUE_CLIPPED" and event.get("date")})
    warning_days = sorted({event.get("date") for event in events if event.get("date")})

    if insufficient_count:
        status = "computed_with_insufficient_data_days"
    elif days_with_renormalized:
        status = "computed_with_partial_component_coverage"
    elif events:
        status = "computed_with_warnings"
    else:
        status = "computed"

    date_range = {"first_date": dated_records[0][0] if dated_records else None, "last_date": dated_records[-1][0] if dated_records else None}
    readiness = {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "status": status,
        "source_artifact": "data/pipeline/08_compute_load_metrics/load_metrics.json",
        "score_name": "readiness_score",
        "score_range": {"minimum": 0, "maximum": 100},
        "score_interpretation": "Short-term daily training readiness decision-support indicator.",
        "limitations": [
            "Readiness is not a medical diagnosis.",
            "Readiness is not an injury prediction.",
            "Readiness is not a professional training prescription.",
        ],
        "base_component_weights": base_weights,
        "minimum_data_requirements": {"minimum_available_base_weight_sum": minimum_weight, "minimum_available_components": minimum_components},
        "records_count": len(output_records),
        "date_range": date_range,
        "records": output_records,
        "missing_component_policy": "preserve_as_null_and_renormalize_available_weights_only_if_minimum_coverage_is_satisfied",
        "pws_computed": False,
        "llm_used": False,
        "ready_for_next_module": True,
        "private_data_notice": "Readiness records contain private health and training data and must not be committed to version control.",
    }
    quality_report = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "records_count": len(output_records),
        "score_availability": {
            "computed_score_count": computed_count,
            "insufficient_data_count": insufficient_count,
            "coverage_ratio": round4(computed_count / len(output_records)) if output_records else 0,
        },
        "component_availability": component_availability,
        "readiness_label_counts": label_counts,
        "days_with_renormalized_weights": days_with_renormalized,
        "days_with_clipped_component_values": clipped_days,
        "days_with_component_warnings": warning_days,
        "parquet_output": {"requested": True, "written": parquet_written, "warning": parquet_reason},
        "pws_computed": False,
        "llm_used": False,
        "warnings": [
            "Readiness is a decision-support indicator and not a medical diagnosis.",
            "Missing component values were preserved as null and were not replaced with zero.",
            "Final readiness was not calculated for days that did not meet minimum component availability requirements.",
        ] + [event["message"] for event in events if event.get("message")],
        "ready_for_next_module": True,
    }
    lineage = {
        "module_id": MODULE_ID,
        "lineage_version": "readiness_lineage_v1",
        "source_artifacts": [
            {"module_id": "08_compute_load_metrics", "artifact_path": "data/pipeline/08_compute_load_metrics/load_metrics.json", "role": "daily_input_with_health_signals_and_load_metrics"},
            {"module_id": "08_compute_load_metrics", "artifact_path": "data/pipeline/08_compute_load_metrics/load_metrics_quality_report.json", "role": "input_quality_reference"},
        ],
        "component_lineage": [
            {"component": "hrv", "output_field": "hrv_readiness_score", "base_weight": base_weights["hrv"], "preferred_inputs": ["hrv_last_night_avg_ms", "hrv_baseline_balanced_low_ms", "hrv_baseline_balanced_upper_ms"], "fallback_inputs": ["hrv_last_night_avg_ms", "hrv_weekly_avg_ms"], "transformation": "configured_baseline_or_weekly_relative_score"},
            {"component": "stress", "output_field": "stress_readiness_score", "base_weight": base_weights["stress"], "inputs": ["avg_stress"], "transformation": "inverse_average_stress"},
            {"component": "rhr", "output_field": "rhr_readiness_score", "base_weight": base_weights["rhr"], "inputs": ["resting_hr_bpm", "resting_hr_baseline_bpm"], "transformation": "penalty_for_elevation_above_baseline"},
            {"component": "load_balance", "output_field": "load_balance_readiness_score", "base_weight": base_weights["load_balance"], "preferred_input": "acwr_ewma", "fallback_input": "acwr_rolling", "transformation": "configured_piecewise_acwr_contribution"},
        ],
        "final_score_transformation": "weighted_average_of_available_components_after_minimum_coverage_check_and_weight_renormalization",
        "forbidden_calculation_confirmation": {
            "pws_components_computed": False,
            "pws_weights_computed": False,
            "pws_score_computed": False,
            "llm_used": False,
            "medical_diagnosis_generated": False,
            "training_prescription_generated": False,
        },
    }

    write_json(out_dir / "readiness.json", readiness)
    write_csv(out_dir / "readiness.csv", output_records)
    write_json(out_dir / "readiness_schema.json", build_schema(base_weights))
    write_json(out_dir / "readiness_quality_report.json", quality_report)
    write_json(out_dir / "readiness_lineage.json", lineage)
    log_lines.extend(
        [
            f"Input records: {len(output_records)}",
            f"Date range: {date_range['first_date']}..{date_range['last_date']}",
            f"Components and base weights: {json.dumps(base_weights, sort_keys=True)}",
            f"Minimum requirements: components>={minimum_components}, weight_sum>={minimum_weight}",
            f"Computed readiness days: {computed_count}",
            f"Insufficient data days: {insufficient_count}",
            f"Component coverage: {json.dumps(component_availability, sort_keys=True)}",
            f"HRV baseline days: {method_counts('hrv').get('baseline_band', 0)}",
            f"HRV weekly fallback days: {method_counts('hrv').get('relative_to_weekly_average', 0)}",
            f"Load balance acwr_ewma days: {method_counts('load_balance').get('acwr_ewma', 0)}",
            f"Load balance acwr_rolling days: {method_counts('load_balance').get('acwr_rolling', 0)}",
            f"Renormalized weight days: {len(days_with_renormalized)}",
            f"Clipping warnings: {len(clipped_days)}",
            f"Readiness label counts: {json.dumps(label_counts, sort_keys=True)}",
            "JSON written: true",
            "CSV written: true",
            f"Parquet written: {str(parquet_written).lower()}",
            "Missing components remained null and were not replaced with zero.",
            "PWS was not computed.",
            "LLM was not used.",
            "Readiness is not a medical diagnosis or professional training prescription.",
        ]
    )
    write_run_artifacts(root, started_at, status, "success", events, log_lines, parquet_written, parquet_reason)
    return 0


def main() -> int:
    return execute()


if __name__ == "__main__":
    raise SystemExit(main())
