from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "12_compute_pws_score"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "pws_score_policy_v1"
COMPONENTS = ["LQ", "REC", "CAP", "VS"]
SCORE_FIELDS = {"LQ": "lq_score", "REC": "rec_score", "CAP": "cap_score", "VS": "vs_score"}
STATUS_FIELDS = {"LQ": "lq_status", "REC": "rec_status", "CAP": "cap_status", "VS": "vs_status"}
CSV_FIELDS = [
    "date", "lq_score", "rec_score", "cap_score", "vs_score",
    "weight_lq", "weight_rec", "weight_cap", "weight_vs",
    "contribution_lq", "contribution_rec", "contribution_cap", "contribution_vs",
    "pws_available_components_count", "pws_available_base_weight_sum", "pws_coverage_ratio",
    "pws_coverage_tier", "pws_computed_from_partial_coverage", "weights_ready_for_final_pws",
    "pws_deterministic", "pws_deterministic_computed", "pws_status", "pws_label_id", "pws_label",
    "llm_adjustment_eligible", "pws_llm_assisted_computed", "llm_used"
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def valid_score(value: Any) -> bool:
    return is_number(value) and 0 <= float(value) <= 100


def validate_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def add_error(errors: list[dict[str, Any]], code: str, message: str, *, severity: str = "error", date: str | None = None, component: str | None = None) -> None:
    item: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if date:
        item["date"] = date
    if component:
        item["component"] = component
    errors.append(item)


def label_for(score: float | None) -> tuple[str, str]:
    if score is None:
        return "insufficient_data", "insufficient_data"
    if score < 40:
        return "low", "niski"
    if score < 60:
        return "reduced", "obnizony"
    if score < 80:
        return "balanced", "stabilny"
    return "strong", "wysoki"


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append("policy_version must be pws_score_policy_v1")
    if policy.get("score_name") != "pws_deterministic":
        errors.append("score_name must be pws_deterministic")
    if set(policy.get("components", {})) != set(COMPONENTS):
        errors.append("components must define LQ, REC, CAP and VS")
    weight_policy = policy.get("input_weight_policy", {})
    if weight_policy.get("allowed_weight_source_only") != "11_compute_pws_weights.deterministic_effective_weights":
        errors.append("deterministic_effective_weights from module 11 must be the only weight source")
    if weight_policy.get("must_not_recompute_weights") is not True or weight_policy.get("must_not_modify_weights") is not True:
        errors.append("policy must forbid recomputing or modifying weights")
    if abs(float(weight_policy.get("must_validate_effective_weight_sum_to", -1)) - 1.0) > 1e-12:
        errors.append("effective weight sum target must be 1.0")
    if float(weight_policy.get("weight_sum_tolerance", -1)) != 0.000001:
        errors.append("weight_sum_tolerance must be 0.000001")
    if policy.get("future_llm_assisted_path", {}).get("implemented_in_this_module") is not False:
        errors.append("LLM-assisted path must not be implemented in module 12")
    return errors


def load_artifact(root: Path, path_text: str, missing_code: str, not_ready_code: str, errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    path = root / path_text
    if not path.is_file():
        add_error(errors, missing_code, f"Missing required artifact: {path_text}")
        return None
    payload = read_json(path)
    if payload.get("ready_for_next_module") is not True:
        add_error(errors, not_ready_code, f"Artifact is not ready for next module: {path_text}")
        return None
    return payload


def validate_unique_dates(records: list[dict[str, Any]], errors: list[dict[str, Any]]) -> bool:
    seen: set[str] = set()
    ok = True
    for record in records:
        date = record.get("date")
        if "date" not in record:
            add_error(errors, "DATE_FIELD_MISSING", "Record is missing date field.")
            ok = False
        elif not validate_date(date):
            add_error(errors, "DATE_VALUE_INVALID", f"Invalid date value: {date}", date=str(date))
            ok = False
        elif date in seen:
            add_error(errors, "DUPLICATE_DATE_FOUND", f"Duplicate date found: {date}", date=date)
            ok = False
        else:
            seen.add(date)
    return ok


def component_scores_from_component_record(record: dict[str, Any] | None) -> dict[str, Any]:
    if record is None:
        return {component: None for component in COMPONENTS}
    return {component: (float(record.get(SCORE_FIELDS[component])) if valid_score(record.get(SCORE_FIELDS[component])) else None) for component in COMPONENTS}


def component_statuses(record: dict[str, Any] | None, weight_record: dict[str, Any]) -> dict[str, Any]:
    if record is None:
        return weight_record.get("component_source_statuses", {component: None for component in COMPONENTS})
    return {component: record.get(STATUS_FIELDS[component], weight_record.get("component_source_statuses", {}).get(component)) for component in COMPONENTS}


def weights_valid(weights: Any) -> bool:
    return isinstance(weights, dict) and set(weights) == set(COMPONENTS) and all(is_number(value) and float(value) >= 0 for value in weights.values())


def compare_scores(date: str, component_scores: dict[str, Any], weight_record: dict[str, Any], errors: list[dict[str, Any]], warnings: list[str]) -> None:
    copied = weight_record.get("component_scores", {})
    if not isinstance(copied, dict):
        return
    for component in COMPONENTS:
        copied_score = copied.get(component)
        source_score = component_scores[component]
        if copied_score is None and source_score is None:
            continue
        if not (is_number(copied_score) and is_number(source_score) and abs(float(copied_score) - float(source_score)) <= 1e-9):
            message = f"{component} score differs between module 10 and module 11 audit copy."
            add_error(errors, "COMPONENT_SCORE_MISMATCH", message, severity="warning", date=date, component=component)
            warnings.append(message)


def coverage_tier(ready: bool, count: int) -> str:
    if not ready:
        return "insufficient"
    return "full" if count == 4 else "partial_eligible"


def compute_record(weight_record: dict[str, Any], component_record: dict[str, Any] | None, policy: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    date = weight_record["date"]
    warnings: list[str] = []
    scores = component_scores_from_component_record(component_record)
    statuses = component_statuses(component_record, weight_record)
    available = list(weight_record.get("available_components", []))
    missing = list(weight_record.get("missing_components", []))
    count = int(weight_record.get("available_components_count", len(available)))
    base_weight_sum = float(weight_record.get("available_base_weight_sum", 0.0) or 0.0)
    ready = weight_record.get("weights_ready_for_final_pws") is True
    tier = coverage_tier(ready, count)
    computed = False
    pws_value: float | None = None
    contributions: dict[str, float] = {}
    weights = weight_record.get("deterministic_effective_weights")
    pws_status = "not_computed_insufficient_component_coverage"

    if component_record is None:
        add_error(errors, "MISSING_COMPONENT_RECORD_FOR_WEIGHT_DATE", "No module 10 component record exists for weight date.", severity="warning", date=date)
        warnings.append("PWS was not computed because module 10 component record is missing for this date.")
        pws_status = "not_computed_input_contract_violation"
        ready = False
        tier = "insufficient"
    else:
        compare_scores(date, scores, weight_record, errors, warnings)

    if weight_record.get("final_pws_computed") is not False or weight_record.get("llm_adjustment_applied") is not False:
        add_error(errors, "UNEXPECTED_LLM_ADJUSTMENT_IN_INPUT", "Module 11 input indicates final PWS or LLM adjustment was already applied.", severity="warning", date=date)
        warnings.append("Input contract warning: module 11 indicated final PWS or LLM adjustment state inconsistent with module 12 expectations.")
        pws_status = "not_computed_input_contract_violation"
        ready = False
        tier = "insufficient"

    if ready:
        tolerance = float(policy["input_weight_policy"]["weight_sum_tolerance"])
        if not weights_valid(weights):
            add_error(errors, "DETERMINISTIC_WEIGHTS_MISSING_FOR_ELIGIBLE_DATE", "deterministic_effective_weights are missing or malformed for eligible date.", severity="warning", date=date)
            warnings.append("PWS was not computed because deterministic effective weights are missing or malformed.")
            pws_status = "not_computed_input_contract_violation"
        elif abs(sum(float(weights[component]) for component in COMPONENTS) - 1.0) > tolerance:
            add_error(errors, "DETERMINISTIC_WEIGHT_SUM_INVALID", "deterministic_effective_weights do not sum to 1.0 within tolerance.", severity="warning", date=date)
            warnings.append("PWS was not computed because deterministic effective weights do not sum to 1.0.")
            pws_status = "not_computed_input_contract_violation"
        else:
            valid = True
            raw_sum = 0.0
            for component in COMPONENTS:
                weight = float(weights[component])
                score = scores[component]
                if weight > tolerance and not valid_score(score):
                    add_error(errors, "POSITIVE_WEIGHT_FOR_MISSING_COMPONENT", "Positive deterministic weight was assigned to a missing or invalid component score.", severity="warning", date=date, component=component)
                    warnings.append(f"PWS was not computed because {component} has positive weight but missing or invalid score.")
                    valid = False
                contribution = 0.0 if score is None else float(score) * weight
                contributions[component] = round(contribution, 4)
                raw_sum += contribution
            if valid:
                pws_value = round(raw_sum, 2)
                computed = True
                pws_status = "computed_full_coverage" if tier == "full" else "computed_partial_eligible_coverage"
                if tier == "partial_eligible":
                    warning = "Deterministic PWS was computed from an eligible but partial component set. Missing components were not replaced with zero."
                    warnings.append(warning)
                    add_error(errors, "PWS_COMPUTED_FROM_PARTIAL_ELIGIBLE_COVERAGE", warning, severity="warning", date=date)
    else:
        warning = "PWS was not computed because configured minimum component coverage requirements were not satisfied."
        if warning not in warnings:
            warnings.append(warning)
        add_error(errors, "PWS_NOT_COMPUTED_INSUFFICIENT_COMPONENT_COVERAGE", warning, severity="warning", date=date)

    label_id, label = label_for(pws_value)
    return {
        "date": date,
        "pws_component_scores": scores,
        "pws_component_statuses": statuses,
        "pws_deterministic_weights": weights if computed else (weights if ready and weights_valid(weights) else None),
        "pws_weighted_contributions": contributions if computed else {},
        "pws_available_components": available,
        "pws_missing_components": missing,
        "pws_available_components_count": count,
        "pws_available_base_weight_sum": base_weight_sum,
        "pws_coverage_ratio": round(base_weight_sum, 6),
        "pws_coverage_tier": tier,
        "pws_computed_from_partial_coverage": computed and tier == "partial_eligible",
        "weights_ready_for_final_pws": weight_record.get("weights_ready_for_final_pws") is True,
        "weights_readiness_status": weight_record.get("weights_readiness_status"),
        "pws_deterministic": pws_value,
        "pws_deterministic_computed": computed,
        "pws_status": pws_status,
        "pws_label_id": label_id,
        "pws_label": label,
        "llm_adjustment_eligible": bool(weight_record.get("llm_adjustment_eligible")),
        "pws_llm_assisted": None,
        "pws_llm_assisted_computed": False,
        "future_llm_assisted_path_status": "eligible_but_not_executed" if computed and weight_record.get("llm_adjustment_eligible") is True else "not_eligible_or_not_available",
        "llm_adjustment_applied": False,
        "llm_used": False,
        "pws_warnings": warnings,
    }


def flat_row(record: dict[str, Any]) -> dict[str, Any]:
    weights = record.get("pws_deterministic_weights") or {}
    contrib = record.get("pws_weighted_contributions") or {}
    scores = record.get("pws_component_scores") or {}
    row = {
        "date": record["date"],
        "lq_score": scores.get("LQ"),
        "rec_score": scores.get("REC"),
        "cap_score": scores.get("CAP"),
        "vs_score": scores.get("VS"),
        "weight_lq": weights.get("LQ"),
        "weight_rec": weights.get("REC"),
        "weight_cap": weights.get("CAP"),
        "weight_vs": weights.get("VS"),
        "contribution_lq": contrib.get("LQ"),
        "contribution_rec": contrib.get("REC"),
        "contribution_cap": contrib.get("CAP"),
        "contribution_vs": contrib.get("VS"),
        "pws_available_components_count": record["pws_available_components_count"],
        "pws_available_base_weight_sum": record["pws_available_base_weight_sum"],
        "pws_coverage_ratio": record["pws_coverage_ratio"],
        "pws_coverage_tier": record["pws_coverage_tier"],
        "pws_computed_from_partial_coverage": record["pws_computed_from_partial_coverage"],
        "weights_ready_for_final_pws": record["weights_ready_for_final_pws"],
        "pws_deterministic": record["pws_deterministic"],
        "pws_deterministic_computed": record["pws_deterministic_computed"],
        "pws_status": record["pws_status"],
        "pws_label_id": record["pws_label_id"],
        "pws_label": record["pws_label"],
        "llm_adjustment_eligible": record["llm_adjustment_eligible"],
        "pws_llm_assisted_computed": record["pws_llm_assisted_computed"],
        "llm_used": record["llm_used"],
    }
    return row


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: "" if value is None else value for key, value in flat_row(record).items()})


def try_write_parquet(path: Path, records: list[dict[str, Any]]) -> tuple[bool, str | None]:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        return False, "PARQUET_DEPENDENCY_UNAVAILABLE"
    try:
        pd.DataFrame([flat_row(record) for record in records], columns=CSV_FIELDS).to_parquet(path, index=False)
        return True, None
    except Exception:
        return False, "PARQUET_WRITE_FAILED"


def build_schema() -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "schema_version": "pws_score_schema_v1",
        "policy_version": POLICY_VERSION,
        "primary_key": "date",
        "score_field": "pws_deterministic",
        "score_range": {"minimum": 0, "maximum": 100},
        "weight_source": "11_compute_pws_weights.deterministic_effective_weights",
        "formula": "sum(component_score * deterministic_effective_weight for available weighted components)",
        "components": COMPONENTS,
        "missing_values_policy": "missing_scores_remain_null_and_are_never_replaced_with_zero",
        "coverage_policy": {
            "full": "all four components available",
            "partial_eligible": "configured weighting eligibility passed with one missing component",
            "insufficient": "configured weighting eligibility failed and PWS is not computed",
        },
        "fields": [
            {"name": "pws_deterministic", "type": "number", "nullable": True, "description": "Final deterministic PWS computed only from validated deterministic effective weights."},
            {"name": "pws_deterministic_computed", "type": "boolean", "nullable": False, "description": "Whether a numeric deterministic PWS exists for the day."},
            {"name": "pws_deterministic_weights", "type": "object", "nullable": True, "description": "Validated deterministic effective weights copied from module 11 without modification."},
            {"name": "pws_weighted_contributions", "type": "object", "nullable": False, "description": "Auditable weighted contributions of each available component."},
            {"name": "pws_coverage_tier", "type": "string", "nullable": False, "description": "Completeness tier of the score input component set."},
            {"name": "pws_llm_assisted", "type": "number", "nullable": True, "description": "Reserved future field. Must remain null in this module."},
            {"name": "llm_used", "type": "boolean", "nullable": False, "description": "Must remain false in this deterministic module."},
        ],
        "csv_flattening": "Nested score, weight and contribution objects are flattened into per-component columns.",
        "excluded_future_outputs": ["llm_adjusted_weights", "priority_component", "priority_recommendation", "coach_message", "training_recommendation", "medical_diagnosis", "injury_prediction"],
    }


def build_lineage() -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "lineage_version": "pws_score_lineage_v1",
        "source_artifacts": [
            {"module_id": "10_compute_pws_components", "artifact_path": "data/pipeline/10_compute_pws_components/pws_components.json", "role": "component_score_source"},
            {"module_id": "11_compute_pws_weights", "artifact_path": "data/pipeline/11_compute_pws_weights/pws_weights.json", "role": "deterministic_effective_weight_source"},
            {"module_id": "11_compute_pws_weights", "artifact_path": "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json", "role": "future_llm_boundary_reference"},
        ],
        "score_transformation": {
            "output_field": "pws_deterministic",
            "formula": "sum(component_score * deterministic_effective_weight for available weighted components)",
            "weights_source": "deterministic_effective_weights",
            "weights_recomputed": False,
            "weights_modified": False,
        },
        "component_lineage": [{"component": component, "score_field": SCORE_FIELDS[component], "origin_module": "10_compute_pws_components"} for component in COMPONENTS],
        "future_llm_boundary": {
            "deterministic_score_field": "pws_deterministic",
            "future_llm_assisted_score_field": "pws_llm_assisted",
            "llm_called_in_this_module": False,
            "llm_assisted_score_computed_in_this_module": False,
            "deterministic_score_must_never_be_overwritten": True,
        },
        "forbidden_calculation_confirmation": {
            "llm_used": False,
            "llm_weight_adjustment_applied": False,
            "medical_diagnosis_generated": False,
            "injury_prediction_generated": False,
            "training_prescription_generated": False,
        },
    }


def domain_status(records: list[dict[str, Any]], errors: list[dict[str, Any]]) -> str:
    warnings = [error for error in errors if error.get("severity") == "warning"]
    if any(record["pws_status"] == "not_computed_input_contract_violation" for record in records):
        return "computed_with_input_contract_warnings"
    if any(record["pws_coverage_tier"] == "partial_eligible" and record["pws_deterministic_computed"] for record in records):
        return "computed_with_partial_coverage"
    if any(not record["pws_deterministic_computed"] for record in records):
        return "computed_with_unavailable_score_days"
    if warnings:
        return "computed_with_input_contract_warnings"
    return "computed"


def build_quality(records: list[dict[str, Any]], status: str, errors: list[dict[str, Any]], orphan_dates: list[str], parquet_written: bool, parquet_warning: str | None) -> dict[str, Any]:
    count = len(records)
    computed_count = sum(1 for record in records if record["pws_deterministic_computed"])
    labels: dict[str, int] = {key: 0 for key in ["low", "reduced", "balanced", "strong", "insufficient_data"]}
    tiers: dict[str, int] = {key: 0 for key in ["full", "partial_eligible", "insufficient"]}
    for record in records:
        labels[record["pws_label_id"]] = labels.get(record["pws_label_id"], 0) + 1
        tiers[record["pws_coverage_tier"]] = tiers.get(record["pws_coverage_tier"], 0) + 1
    return {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "records_count": count,
        "score_availability": {
            "pws_deterministic_computed_count": computed_count,
            "pws_deterministic_unavailable_count": count - computed_count,
            "coverage_ratio": round(computed_count / count, 4) if count else 0,
        },
        "coverage_tiers": tiers,
        "label_counts": labels,
        "input_contract_validation": {
            "weight_sum_violations": [error for error in errors if error["code"] == "DETERMINISTIC_WEIGHT_SUM_INVALID"],
            "positive_weight_for_missing_component_violations": [error for error in errors if error["code"] == "POSITIVE_WEIGHT_FOR_MISSING_COMPONENT"],
            "component_score_mismatches_between_modules": [error for error in errors if error["code"] == "COMPONENT_SCORE_MISMATCH"],
            "missing_component_records_for_weight_dates": [error for error in errors if error["code"] == "MISSING_COMPONENT_RECORD_FOR_WEIGHT_DATE"],
            "orphan_component_dates": orphan_dates,
        },
        "weight_source_validation": {
            "deterministic_effective_weights_used_only": True,
            "weights_recomputed_in_this_module": False,
            "weights_modified_in_this_module": False,
        },
        "llm_path": {
            "guardrails_reference_available": True,
            "llm_adjustment_eligible_dates_count": sum(1 for record in records if record["llm_adjustment_eligible"]),
            "llm_called": False,
            "llm_adjustment_applied": False,
            "pws_llm_assisted_computed": False,
        },
        "parquet_output": {"requested": True, "written": parquet_written, "warning": parquet_warning},
        "warnings": [
            "PWS is a deterministic decision-support indicator and is not a medical diagnosis or professional training prescription.",
            "Numeric PWS values computed from partial eligible coverage expose that limitation explicitly.",
            "No LLM was called and no LLM-assisted score was calculated.",
        ],
        "ready_for_next_module": True,
    }


def write_failure(root: Path, artifact_dir: Path, started_at: str, status: str, errors: list[dict[str, Any]]) -> None:
    finished_at = now_iso()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    (artifact_dir / "run_log.txt").write_text(
        "\n".join([f"module_id={MODULE_ID}", f"started_at={started_at}", f"finished_at={finished_at}", f"domain_status={status}", "execution_status=failed", "llm_used=false"]) + "\n",
        encoding="utf-8",
    )
    write_json(artifact_dir / "run_manifest.json", {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "failed",
        "domain_status": status,
        "generated_artifacts": [
            "data/pipeline/12_compute_pws_score/run_manifest.json",
            "data/pipeline/12_compute_pws_score/run_log.txt",
            "data/pipeline/12_compute_pws_score/errors.json",
        ],
        "deterministic_pws_computed": False,
        "llm_called": False,
        "llm_adjustment_applied": False,
        "llm_assisted_pws_computed": False,
        "log_file": "data/pipeline/12_compute_pws_score/run_log.txt",
        "errors_file": "data/pipeline/12_compute_pws_score/errors.json",
    })


def run(root: Path | None = None) -> int:
    root = root or project_root()
    started_at = now_iso()
    artifact_dir = root / "data/pipeline/12_compute_pws_score"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    required_files = [
        ("config/pws_score_policy_v1.json", "PWS_SCORE_POLICY_NOT_FOUND"),
        ("data/pipeline/10_compute_pws_components/pws_components_schema.json", "PWS_COMPONENTS_NOT_FOUND"),
        ("data/pipeline/10_compute_pws_components/pws_components_quality_report.json", "PWS_COMPONENTS_NOT_FOUND"),
        ("data/pipeline/10_compute_pws_components/pws_components_lineage.json", "PWS_COMPONENTS_NOT_FOUND"),
        ("data/pipeline/11_compute_pws_weights/pws_weights_schema.json", "PWS_WEIGHTS_NOT_FOUND"),
        ("data/pipeline/11_compute_pws_weights/pws_weights_quality_report.json", "PWS_WEIGHTS_NOT_FOUND"),
        ("data/pipeline/11_compute_pws_weights/pws_weights_lineage.json", "PWS_WEIGHTS_NOT_FOUND"),
        ("data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json", "PWS_WEIGHT_GUARDRAILS_NOT_FOUND"),
    ]
    for path_text, code in required_files:
        if not (root / path_text).is_file():
            add_error(errors, code, f"Missing required input: {path_text}")
    policy = None
    policy_path = root / "config/pws_score_policy_v1.json"
    if policy_path.is_file():
        try:
            policy = read_json(policy_path)
            for message in validate_policy(policy):
                add_error(errors, "PWS_SCORE_POLICY_INVALID", message)
        except Exception as exc:
            add_error(errors, "PWS_SCORE_POLICY_INVALID", str(exc))
    if errors:
        status = "invalid_pws_score_policy" if any(error["code"].startswith("PWS_SCORE_POLICY") for error in errors) else ("blocked_missing_pws_weights" if any("WEIGHTS" in error["code"] or "GUARDRAILS" in error["code"] for error in errors) else "blocked_missing_pws_components")
        write_failure(root, artifact_dir, started_at, status, errors)
        return 1

    components_payload = load_artifact(root, "data/pipeline/10_compute_pws_components/pws_components.json", "PWS_COMPONENTS_NOT_FOUND", "PWS_COMPONENTS_NOT_READY", errors)
    weights_payload = load_artifact(root, "data/pipeline/11_compute_pws_weights/pws_weights.json", "PWS_WEIGHTS_NOT_FOUND", "PWS_WEIGHTS_NOT_READY", errors)
    if errors:
        status = "blocked_inputs_not_ready" if any(error["code"].endswith("_NOT_READY") for error in errors) else ("blocked_missing_pws_weights" if any("WEIGHTS" in error["code"] for error in errors) else "blocked_missing_pws_components")
        write_failure(root, artifact_dir, started_at, status, errors)
        return 1
    component_records = components_payload.get("records", [])
    weight_records = weights_payload.get("records", [])
    if not isinstance(component_records, list) or not isinstance(weight_records, list):
        add_error(errors, "PWS_WEIGHTS_NOT_READY", "Input records must be lists.")
        write_failure(root, artifact_dir, started_at, "blocked_inputs_not_ready", errors)
        return 1
    if not (validate_unique_dates(component_records, errors) and validate_unique_dates(weight_records, errors)):
        write_failure(root, artifact_dir, started_at, "blocked_duplicate_dates" if any(error["code"] == "DUPLICATE_DATE_FOUND" for error in errors) else "blocked_inputs_not_ready", errors)
        return 1
    components_by_date = {record["date"]: record for record in component_records}
    weights_by_date = {record["date"]: record for record in weight_records}
    orphan_component_dates = sorted(set(components_by_date) - set(weights_by_date))
    for date in orphan_component_dates:
        add_error(errors, "ORPHAN_COMPONENT_DATE_FOUND", "Module 10 contains a component date that is absent from module 11 weights.", severity="warning", date=date)
    records = [compute_record(record, components_by_date.get(record["date"]), policy, errors) for record in sorted(weight_records, key=lambda item: item["date"])]
    parquet_written, parquet_warning = try_write_parquet(artifact_dir / "pws_score.parquet", records)
    if parquet_warning:
        add_error(errors, parquet_warning, "Parquet output was not written; JSON and CSV outputs are authoritative.", severity="warning")
    status = domain_status(records, errors)
    date_range = {"first_date": records[0]["date"] if records else None, "last_date": records[-1]["date"] if records else None}
    output = {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "status": status,
        "source_artifacts": {
            "pws_components": "data/pipeline/10_compute_pws_components/pws_components.json",
            "pws_weights": "data/pipeline/11_compute_pws_weights/pws_weights.json",
            "pws_weight_guardrails": "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json",
        },
        "score_name": "pws_deterministic",
        "score_range": {"minimum": 0, "maximum": 100},
        "score_interpretation": "Deterministic Personal Wellness Score decision-support indicator.",
        "limitations": [
            "PWS is not a medical diagnosis.",
            "PWS is not an injury prediction.",
            "PWS is not a professional training prescription.",
            "Scores computed from partial eligible component coverage must expose that limitation.",
        ],
        "formula": "sum(component_score * deterministic_effective_weight for available weighted components)",
        "weight_source": "11_compute_pws_weights.deterministic_effective_weights",
        "records_count": len(records),
        "date_range": date_range,
        "records": records,
        "deterministic_path_computed": any(record["pws_deterministic_computed"] for record in records),
        "llm_assisted_path_computed": False,
        "llm_used": False,
        "ready_for_next_module": True,
        "private_data_notice": "PWS records contain private derived health, activity and training information and must not be committed to version control.",
    }
    write_json(artifact_dir / "pws_score.json", output)
    write_csv(artifact_dir / "pws_score.csv", records)
    write_json(artifact_dir / "pws_score_schema.json", build_schema())
    quality = build_quality(records, status, errors, orphan_component_dates, parquet_written, parquet_warning)
    write_json(artifact_dir / "pws_score_quality_report.json", quality)
    write_json(artifact_dir / "pws_score_lineage.json", build_lineage())
    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    finished_at = now_iso()
    generated = [
        "data/pipeline/12_compute_pws_score/pws_score.json",
        "data/pipeline/12_compute_pws_score/pws_score.csv",
        "data/pipeline/12_compute_pws_score/pws_score_schema.json",
        "data/pipeline/12_compute_pws_score/pws_score_quality_report.json",
        "data/pipeline/12_compute_pws_score/pws_score_lineage.json",
        "data/pipeline/12_compute_pws_score/run_manifest.json",
        "data/pipeline/12_compute_pws_score/run_log.txt",
        "data/pipeline/12_compute_pws_score/errors.json",
    ]
    write_json(artifact_dir / "run_manifest.json", {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "success",
        "domain_status": status,
        "inputs": CONTRACT_INPUTS,
        "generated_artifacts": generated,
        "optional_generated_artifacts": [{"path": "data/pipeline/12_compute_pws_score/pws_score.parquet", "written": parquet_written, "reason_if_not_written": parquet_warning}],
        "deterministic_pws_computed": any(record["pws_deterministic_computed"] for record in records),
        "llm_called": False,
        "llm_adjustment_applied": False,
        "llm_assisted_pws_computed": False,
        "log_file": "data/pipeline/12_compute_pws_score/run_log.txt",
        "errors_file": "data/pipeline/12_compute_pws_score/errors.json",
    })
    label_counts = quality["label_counts"]
    log_lines = [
        f"module_id={MODULE_ID}",
        f"started_at={started_at}",
        f"finished_at={finished_at}",
        f"policy_version={POLICY_VERSION}",
        "component_source=data/pipeline/10_compute_pws_components/pws_components.json",
        "weight_source=data/pipeline/11_compute_pws_weights/pws_weights.json deterministic_effective_weights only",
        "weights_recomputed=false weights_modified=false",
        f"records_count={len(records)} date_range={date_range}",
        f"pws_deterministic_computed_count={quality['score_availability']['pws_deterministic_computed_count']}",
        f"pws_unavailable_count={quality['score_availability']['pws_deterministic_unavailable_count']}",
        f"coverage_tiers={quality['coverage_tiers']}",
        f"label_counts={label_counts}",
        f"component_score_mismatch_count={len(quality['input_contract_validation']['component_score_mismatches_between_modules'])}",
        f"weight_sum_violation_count={len(quality['input_contract_validation']['weight_sum_violations'])}",
        f"positive_weight_for_missing_component_count={len(quality['input_contract_validation']['positive_weight_for_missing_component_violations'])}",
        "Missing components were not replaced with zero.",
        "pws_deterministic is the primary auditable score path.",
        "pws_llm_assisted was not computed. LLM was not called.",
        f"json_csv_written=true parquet_written={parquet_written} parquet_warning={parquet_warning}",
        "PWS is not a medical diagnosis or training prescription.",
        f"domain_status={status}",
    ]
    (artifact_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return 0


CONTRACT_INPUTS = [
    "config/pws_score_policy_v1.json",
    "config/pws_policy_v1.json",
    "config/pws_components_policy_v1.json",
    "config/pws_weights_policy_v1.json",
    "config/llm_policy_v1.json",
    "data/pipeline/10_compute_pws_components/pws_components.json",
    "data/pipeline/10_compute_pws_components/pws_components_schema.json",
    "data/pipeline/10_compute_pws_components/pws_components_quality_report.json",
    "data/pipeline/10_compute_pws_components/pws_components_lineage.json",
    "data/pipeline/11_compute_pws_weights/pws_weights.json",
    "data/pipeline/11_compute_pws_weights/pws_weights_schema.json",
    "data/pipeline/11_compute_pws_weights/pws_weights_quality_report.json",
    "data/pipeline/11_compute_pws_weights/pws_weights_lineage.json",
    "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json",
]


def main() -> int:
    try:
        return run()
    except Exception as exc:
        root = project_root()
        write_failure(root, root / "data/pipeline/12_compute_pws_score", now_iso(), "pws_score_computation_failed", [{"severity": "error", "code": "PWS_SCORE_COMPUTATION_FAILED", "message": str(exc)}])
        return 1


if __name__ == "__main__":
    sys.exit(main())
