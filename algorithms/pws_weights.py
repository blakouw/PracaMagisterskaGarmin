from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "11_compute_pws_weights"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "pws_weights_policy_v1"
COMPONENTS = ["LQ", "REC", "CAP", "VS"]
SCORE_FIELDS = {"LQ": "lq_score", "REC": "rec_score", "CAP": "cap_score", "VS": "vs_score"}
STATUS_FIELDS = {"LQ": "lq_status", "REC": "rec_status", "CAP": "cap_status", "VS": "vs_status"}
CSV_FIELDS = [
    "date",
    "lq_score",
    "rec_score",
    "cap_score",
    "vs_score",
    "lq_available",
    "rec_available",
    "cap_available",
    "vs_available",
    "available_components_count",
    "available_base_weight_sum",
    "base_weight_lq",
    "base_weight_rec",
    "base_weight_cap",
    "base_weight_vs",
    "base_available_weight_lq",
    "base_available_weight_rec",
    "base_available_weight_cap",
    "base_available_weight_vs",
    "reliability_factor_lq",
    "reliability_factor_rec",
    "reliability_factor_cap",
    "reliability_factor_vs",
    "urgency_factor_lq",
    "urgency_factor_rec",
    "urgency_factor_cap",
    "urgency_factor_vs",
    "deterministic_effective_weight_lq",
    "deterministic_effective_weight_rec",
    "deterministic_effective_weight_cap",
    "deterministic_effective_weight_vs",
    "deterministic_total_absolute_weight_change",
    "overlap_controls_applied_count",
    "weights_ready_for_final_pws",
    "weights_readiness_status",
    "llm_adjustment_eligible",
    "llm_adjustment_applied",
    "final_pws_computed",
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


def clip(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def round_or_none(value: Any, places: int = 6) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        rounded = {key: round_or_none(item, places) for key, item in value.items()}
        if set(rounded) == set(COMPONENTS) and all(is_number(item) for item in rounded.values()):
            total = sum(float(item) for item in rounded.values())
            if abs(total - 1.0) <= 10 ** (-(places - 1)):
                residual = round(1.0 - total, places)
                target = max(COMPONENTS, key=lambda component: rounded[component])
                rounded[target] = round(float(rounded[target]) + residual, places)
        return rounded
    if is_number(value):
        return round(float(value), places)
    return value


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


def status_is_computed(status: Any) -> bool:
    return status == "computed"


def add_error(errors: list[dict[str, Any]], code: str, message: str, *, severity: str = "error", date: str | None = None, component: str | None = None) -> None:
    item: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if date is not None:
        item["date"] = date
    if component is not None:
        item["component"] = component
    errors.append(item)


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append("policy_version must be pws_weights_policy_v1")
    base = policy.get("base_weights", {})
    expected = {"LQ": 0.20, "REC": 0.35, "CAP": 0.15, "VS": 0.30}
    if set(base) != set(COMPONENTS):
        errors.append("base_weights must define LQ, REC, CAP and VS")
    for component, value in expected.items():
        if abs(float(base.get(component, -1)) - value) > 1e-9:
            errors.append(f"{component} base_weight must be {value}")
    if abs(sum(float(base.get(component, 0)) for component in COMPONENTS) - 1.0) > 1e-9:
        errors.append("base weights must sum to 1.0")
    eligibility = policy.get("eligibility_for_future_final_pws", {})
    if eligibility.get("minimum_available_components") != 3:
        errors.append("minimum_available_components must be 3")
    if abs(float(eligibility.get("minimum_available_base_weight_sum", -1)) - 0.65) > 1e-9:
        errors.append("minimum_available_base_weight_sum must be 0.65")
    if set(eligibility.get("must_include_at_least_one_component_from", [])) != {"REC", "VS"}:
        errors.append("eligibility must require REC or VS")
    urgency = policy.get("deterministic_adjustment", {}).get("urgency_factor", {})
    if urgency.get("target_component_score") != 80 or abs(float(urgency.get("sensitivity", -1)) - 0.5) > 1e-9:
        errors.append("urgency factor policy must use target 80 and sensitivity 0.50")
    movement = policy.get("deterministic_adjustment", {}).get("movement_limits", {})
    if abs(float(movement.get("maximum_absolute_change_from_base_available_weight_per_component", -1)) - 0.07) > 1e-9:
        errors.append("per-component movement limit must be 0.07")
    if abs(float(movement.get("maximum_total_absolute_change_across_all_components", -1)) - 0.20) > 1e-9:
        errors.append("total movement limit must be 0.20")
    llm_limits = policy.get("future_llm_adjustment_guardrails", {}).get("adjustment_limits", {})
    required_llm_limits = {
        "maximum_absolute_delta_per_component": 0.20,
        "maximum_total_positive_weight_shift": 0.20,
        "maximum_total_absolute_delta": 0.40,
        "weights_must_sum_to": 1.0,
    }
    for key, expected_value in required_llm_limits.items():
        if abs(float(llm_limits.get(key, -1)) - expected_value) > 1e-9:
            errors.append(f"LLM guardrail {key} must be {expected_value}")
    if llm_limits.get("unavailable_component_weight_must_remain_zero") is not True:
        errors.append("LLM guardrails must keep unavailable component weights at zero")
    return errors


def load_records(root: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    path = root / "data/pipeline/10_compute_pws_components/pws_components.json"
    if not path.is_file():
        add_error(errors, "PWS_COMPONENTS_NOT_FOUND", "Required module 10 artifact pws_components.json is missing.")
        return None, [], errors
    payload = read_json(path)
    if payload.get("ready_for_next_module") is not True:
        add_error(errors, "PWS_COMPONENTS_NOT_READY", "pws_components.json is not ready for next module.")
        return payload, [], errors
    records = payload.get("records")
    if not isinstance(records, list):
        add_error(errors, "PWS_COMPONENTS_NOT_READY", "pws_components.json records must be a list.")
        return payload, [], errors
    seen: set[str] = set()
    for record in records:
        date = record.get("date")
        if "date" not in record:
            add_error(errors, "DATE_FIELD_MISSING", "Record is missing date field.")
        elif not validate_date(date):
            add_error(errors, "DATE_VALUE_INVALID", f"Invalid date value: {date}")
        elif date in seen:
            add_error(errors, "DUPLICATE_DATE_FOUND", f"Duplicate date found: {date}", date=date)
        else:
            seen.add(date)
    if errors:
        return payload, [], errors
    return payload, sorted(records, key=lambda item: item["date"]), []


def component_availability(record: dict[str, Any], base_weights: dict[str, float]) -> tuple[dict[str, bool], dict[str, Any], dict[str, Any]]:
    availability: dict[str, bool] = {}
    scores: dict[str, Any] = {}
    statuses: dict[str, Any] = {}
    for component in COMPONENTS:
        score = record.get(SCORE_FIELDS[component])
        status = record.get(STATUS_FIELDS[component])
        scores[component] = float(score) if valid_score(score) else None
        statuses[component] = status
        availability[component] = valid_score(score) and status_is_computed(status)
    return availability, scores, statuses


def calculate_base_available_weights(availability: dict[str, bool], base_weights: dict[str, float]) -> tuple[float, dict[str, float]]:
    available_sum = sum(base_weights[component] for component in COMPONENTS if availability[component])
    if available_sum <= 0:
        return 0.0, {component: 0.0 for component in COMPONENTS}
    return available_sum, {
        component: (base_weights[component] / available_sum if availability[component] else 0.0)
        for component in COMPONENTS
    }


def eligibility(availability: dict[str, bool], available_weight_sum: float, policy: dict[str, Any]) -> tuple[bool, str, list[str]]:
    cfg = policy["eligibility_for_future_final_pws"]
    reasons: list[str] = []
    count = sum(1 for value in availability.values() if value)
    if count < cfg["minimum_available_components"]:
        reasons.append("minimum_available_components_not_satisfied")
    if available_weight_sum + 1e-12 < cfg["minimum_available_base_weight_sum"]:
        reasons.append("minimum_available_base_weight_sum_not_satisfied")
    if not any(availability[item] for item in cfg["must_include_at_least_one_component_from"]):
        reasons.append("missing_required_recovery_or_vital_component")
    if reasons:
        return False, "insufficient_component_coverage", reasons
    return True, ("ready" if count == 4 else "ready_partial_component_coverage"), []


def reliability_for(component: str, record: dict[str, Any]) -> tuple[float, str, list[str]]:
    warnings: list[str] = []
    if component == "LQ":
        source = record.get("lq_source_metric")
        if source == "acwr_ewma":
            return 1.0, "preferred_ewma_acwr_source", warnings
        if source == "acwr_rolling":
            return 0.85, "rolling_acwr_fallback_source", warnings
        warnings.append("LQ score exists but source metric is unknown; conservative reliability factor applied.")
        return 0.75, "unknown_source_conservative_fallback", warnings
    if component == "REC":
        coverage = record.get("rec_source_coverage_ratio")
        if is_number(coverage):
            return clip(float(coverage), 0.50, 1.00), "readiness_coverage_reliability", warnings
        warnings.append("REC score exists but readiness coverage metadata is missing; conservative reliability factor applied.")
        return 0.75, "readiness_coverage_missing_conservative_fallback", warnings
    if component == "CAP":
        if record.get("cap_status") == "computed" and record.get("cap_window_complete") is True:
            return 1.0, "computed_complete_window_reliability", warnings
        warnings.append("CAP score exists but complete window metadata could not be confirmed; conservative reliability factor applied.")
        return 0.75, "cap_window_metadata_missing_conservative_fallback", warnings
    if component == "VS":
        coverage = record.get("vs_coverage_ratio")
        if is_number(coverage):
            return clip(float(coverage), 0.50, 1.00), "vital_signal_coverage_reliability", warnings
        warnings.append("VS score exists but vital signal coverage metadata is missing; conservative reliability factor applied.")
        return 0.75, "vital_signal_coverage_missing_conservative_fallback", warnings
    raise ValueError(component)


def urgency_factor(score: float, target: float = 80.0, sensitivity: float = 0.50) -> float:
    return clip(1 + sensitivity * max(0.0, (target - score) / target), 1.0, 1.5)


def normalize_weights(weights: dict[str, float], available: dict[str, bool]) -> dict[str, float]:
    total = sum(weights[component] for component in COMPONENTS if available[component])
    if total <= 0:
        return {component: 0.0 for component in COMPONENTS}
    return {component: (weights[component] / total if available[component] else 0.0) for component in COMPONENTS}


def rebalance_deltas(base: dict[str, float], deltas: dict[str, float], available: dict[str, bool], per_limit: float) -> dict[str, float]:
    adjusted = dict(deltas)
    for _ in range(20):
        residual = sum(adjusted[component] for component in COMPONENTS)
        if abs(residual) <= 1e-12:
            break
        if residual > 0:
            candidates = [component for component in COMPONENTS if available[component] and adjusted[component] > -per_limit + 1e-12]
            capacity = {component: adjusted[component] + per_limit for component in candidates}
            sign = -1.0
        else:
            candidates = [component for component in COMPONENTS if available[component] and adjusted[component] < per_limit - 1e-12]
            capacity = {component: per_limit - adjusted[component] for component in candidates}
            sign = 1.0
        total_capacity = sum(capacity.values())
        if not candidates or total_capacity <= 1e-12:
            break
        amount = abs(residual)
        for component in candidates:
            move = min(capacity[component], amount * capacity[component] / total_capacity)
            adjusted[component] += sign * move
    return adjusted


def limit_movement(candidate: dict[str, float], base: dict[str, float], available: dict[str, bool], per_limit: float = 0.07, total_limit: float = 0.20) -> tuple[dict[str, float], bool]:
    deltas = {
        component: (candidate[component] - base[component] if available[component] else 0.0)
        for component in COMPONENTS
    }
    limited_applied = False
    for component in COMPONENTS:
        if not available[component]:
            continue
        clipped = clip(deltas[component], -per_limit, per_limit)
        if abs(clipped - deltas[component]) > 1e-12:
            limited_applied = True
        deltas[component] = clipped
    deltas = rebalance_deltas(base, deltas, available, per_limit)
    total_abs = sum(abs(deltas[component]) for component in COMPONENTS if available[component])
    if total_abs > total_limit + 1e-12:
        scale = total_limit / total_abs
        deltas = {component: (deltas[component] * scale if available[component] else 0.0) for component in COMPONENTS}
        limited_applied = True
    weights = {
        component: (max(0.0, base[component] + deltas[component]) if available[component] else 0.0)
        for component in COMPONENTS
    }
    weights = normalize_weights(weights, available)
    return weights, limited_applied


def apply_pair_cap(weights: dict[str, float], pair: list[str], cap: float, targets: list[str]) -> tuple[dict[str, float], bool, dict[str, Any] | None]:
    combined = weights[pair[0]] + weights[pair[1]]
    if combined <= cap + 1e-12:
        return weights, False, None
    excess = combined - cap
    new_weights = dict(weights)
    for component in pair:
        reduction = excess * (weights[component] / combined)
        new_weights[component] -= reduction
    target_total = sum(weights[component] for component in targets)
    if target_total <= 0:
        for component in targets:
            new_weights[component] += excess / len(targets)
    else:
        for component in targets:
            new_weights[component] += excess * (weights[component] / target_total)
    action = {
        "components": pair,
        "maximum_combined_effective_weight": cap,
        "excess_redistributed": excess,
        "redistribution_targets": targets,
    }
    return new_weights, True, action


def apply_overlap_controls(weights: dict[str, float], availability: dict[str, bool]) -> tuple[dict[str, float], list[str], list[dict[str, Any]], list[str]]:
    disclosures = [
        "LQ and REC may both contain ACWR exposure through readiness load balance.",
        "REC and VS may both rely on HRV and RHR under different interpretations.",
    ]
    if not all(availability.values()):
        disclosures.append("Overlap is present but full-component overlap cap was not applied because one or more components are unavailable.")
        return weights, [], [], disclosures
    actions: list[dict[str, Any]] = []
    applied_ids: list[str] = []
    weights, applied, action = apply_pair_cap(weights, ["LQ", "REC"], 0.55, ["CAP", "VS"])
    if applied and action:
        action["overlap_id"] = "LQ_REC_load_balance_overlap"
        actions.append(action)
        applied_ids.append("LQ_REC_load_balance_overlap")
    weights, applied, action = apply_pair_cap(weights, ["REC", "VS"], 0.65, ["LQ", "CAP"])
    if applied and action:
        action["overlap_id"] = "REC_VS_recovery_vital_overlap"
        actions.append(action)
        applied_ids.append("REC_VS_recovery_vital_overlap")
    weights = normalize_weights(weights, {component: True for component in COMPONENTS})
    return weights, applied_ids, actions, disclosures


def compute_record(source: dict[str, Any], policy: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    date = source["date"]
    base_weights = {component: float(policy["base_weights"][component]) for component in COMPONENTS}
    availability, scores, statuses = component_availability(source, base_weights)
    available_components = [component for component in COMPONENTS if availability[component]]
    missing_components = [component for component in COMPONENTS if not availability[component]]
    available_sum, base_available = calculate_base_available_weights(availability, base_weights)
    ready, readiness_status, readiness_reasons = eligibility(availability, available_sum, policy)
    record: dict[str, Any] = {
        "date": date,
        "component_scores": scores,
        "component_source_statuses": statuses,
        "base_component_weights": base_weights,
        "component_availability": availability,
        "available_components": available_components,
        "missing_components": missing_components,
        "available_components_count": len(available_components),
        "available_base_weight_sum": available_sum,
        "base_available_weights": base_available,
        "weights_ready_for_final_pws": ready,
        "weights_readiness_status": readiness_status,
        "weights_readiness_reasons": readiness_reasons,
        "component_reliability_factors": {component: None for component in COMPONENTS},
        "component_reliability_methods": {component: None for component in COMPONENTS},
        "component_reliability_warnings": {component: [] for component in COMPONENTS},
        "component_urgency_factors": {component: None for component in COMPONENTS},
        "raw_deterministic_weights": None,
        "candidate_deterministic_weights": None,
        "movement_limited_weights": None,
        "deterministic_weight_deltas_from_base_available": None,
        "deterministic_total_absolute_weight_change": None,
        "deterministic_movement_limits_applied": False,
        "overlap_controls_applied": [],
        "overlap_control_actions": [],
        "overlap_disclosures": [
            "LQ and REC may both contain ACWR exposure through readiness load balance.",
            "REC and VS may both rely on HRV and RHR under different interpretations.",
        ],
        "deterministic_effective_weights": None,
        "llm_adjustment_eligible": False,
        "llm_adjustment_applied": False,
        "final_pws_computed": False,
        "weight_warnings": [],
    }

    for component in missing_components:
        add_error(errors, "COMPONENT_UNAVAILABLE", f"{component} is unavailable and will be excluded from weighting.", severity="warning", date=date, component=component)

    if not ready:
        record["weight_warnings"].append("Deterministic effective weights were not produced because minimum component availability requirements were not satisfied.")
        add_error(errors, "INSUFFICIENT_COMPONENT_COVERAGE_FOR_FUTURE_PWS", "Date does not satisfy future final PWS eligibility requirements.", severity="warning", date=date)
        return round_or_none(record)

    raw: dict[str, float] = {component: 0.0 for component in COMPONENTS}
    for component in COMPONENTS:
        if not availability[component]:
            continue
        factor, method, warnings = reliability_for(component, source)
        record["component_reliability_factors"][component] = factor
        record["component_reliability_methods"][component] = method
        record["component_reliability_warnings"][component] = warnings
        if factor < 1.0:
            add_error(errors, "RELIABILITY_FACTOR_FALLBACK_USED", f"{component} reliability factor below one.", severity="warning", date=date, component=component)
        for warning in warnings:
            add_error(errors, "RELIABILITY_METADATA_MISSING", warning, severity="warning", date=date, component=component)
        urgency = urgency_factor(float(scores[component]))
        record["component_urgency_factors"][component] = urgency
        if urgency > 1.0:
            add_error(errors, "URGENCY_FACTOR_APPLIED", f"{component} urgency factor above one.", severity="warning", date=date, component=component)
        raw[component] = base_available[component] * factor * urgency

    candidate = normalize_weights(raw, availability)
    movement_limited, movement_applied = limit_movement(
        candidate,
        base_available,
        availability,
        float(policy["deterministic_adjustment"]["movement_limits"]["maximum_absolute_change_from_base_available_weight_per_component"]),
        float(policy["deterministic_adjustment"]["movement_limits"]["maximum_total_absolute_change_across_all_components"]),
    )
    if movement_applied:
        add_error(errors, "DETERMINISTIC_MOVEMENT_LIMIT_APPLIED", "Deterministic movement limit applied.", severity="warning", date=date)
    overlap_weights, overlap_ids, overlap_actions, disclosures = apply_overlap_controls(movement_limited, availability)
    if overlap_ids:
        add_error(errors, "OVERLAP_CONTROL_APPLIED", "Overlap controls applied.", severity="warning", date=date)
    elif not all(availability.values()):
        add_error(errors, "OVERLAP_DISCLOSED_NOT_CAPPED_PARTIAL_COMPONENT_SET", "Overlap disclosed but full caps not applied for partial component set.", severity="warning", date=date)

    deltas = {component: overlap_weights[component] - base_available[component] for component in COMPONENTS}
    record.update({
        "raw_deterministic_weights": raw,
        "candidate_deterministic_weights": candidate,
        "movement_limited_weights": movement_limited,
        "deterministic_weight_deltas_from_base_available": deltas,
        "deterministic_total_absolute_weight_change": sum(abs(value) for value in deltas.values()),
        "deterministic_movement_limits_applied": movement_applied,
        "overlap_controls_applied": overlap_ids,
        "overlap_control_actions": overlap_actions,
        "overlap_disclosures": disclosures,
        "deterministic_effective_weights": overlap_weights,
        "llm_adjustment_eligible": True,
    })
    return round_or_none(record)


def build_guardrails(policy: dict[str, Any]) -> dict[str, Any]:
    limits = policy["future_llm_adjustment_guardrails"]["adjustment_limits"]
    return {
        "module_id": MODULE_ID,
        "guardrails_version": "pws_weight_guardrails_v1",
        "policy_version": POLICY_VERSION,
        "deterministic_path": {
            "always_available_when_component_eligibility_is_satisfied": True,
            "weights_field": "deterministic_effective_weights",
            "must_never_be_overwritten_by_llm": True,
        },
        "future_llm_adjustment": {
            "enabled_for_future_module": True,
            "executed_in_this_module": False,
            "allowed_role": "propose_evidence_proportional_explainable_reprioritization_within_hard_constraints",
            "required_input_weight_field": "deterministic_effective_weights",
            "eligibility_field": "llm_adjustment_eligible",
            "maximum_absolute_delta_per_component": limits["maximum_absolute_delta_per_component"],
            "maximum_total_positive_weight_shift": limits["maximum_total_positive_weight_shift"],
            "maximum_total_absolute_delta": limits["maximum_total_absolute_delta"],
            "weights_must_sum_to": limits["weights_must_sum_to"],
            "no_negative_weights": True,
            "unavailable_component_weight_must_remain_zero": True,
            "must_reapply_overlap_controls_after_proposal": True,
            "must_preserve_deterministic_weights_separately": True,
            "must_store_llm_proposal_separately": True,
            "must_store_adjustment_reason": True,
            "must_store_validation_result": True,
        },
        "allowed_future_llm_context_fields": [
            "date",
            "available_components",
            "missing_components",
            "component_scores",
            "component_source_statuses",
            "component_coverage_information",
            "deterministic_effective_weights",
            "overlap_disclosures",
            "explicitly_approved_user_goal_context",
        ],
        "forbidden_future_llm_actions": [
            "modify_component_scores",
            "assign_weight_to_unavailable_component",
            "replace_missing_component_score_with_zero",
            "override_weights_ready_for_final_pws_false",
            "remove_or_overwrite_deterministic_weights",
            "bypass_overlap_controls",
            "exceed_adjustment_limits",
            "generate_medical_diagnosis",
            "predict_injury",
            "produce_unbounded_training_prescription",
            "calculate_final_pws_without_later_validation",
        ],
        "privacy_policy": {
            "minimum_structured_context_only_by_default": True,
            "do_not_send_tokens_or_secrets": True,
            "do_not_send_raw_fit_or_tcx": True,
            "do_not_send_full_raw_api_payloads_by_default": True,
        },
        "notes": [
            "No LLM is called in module 11.",
            "The deterministic weight path remains authoritative and auditable.",
            "Any future LLM-assisted variant must be clearly labeled separately from deterministic output.",
        ],
    }


def build_schema(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "schema_version": "pws_weights_schema_v1",
        "policy_version": POLICY_VERSION,
        "primary_key": "date",
        "components": COMPONENTS,
        "base_component_weights": policy["base_weights"],
        "future_final_pws_eligibility_requirements": policy["eligibility_for_future_final_pws"],
        "fields": [
            {"name": "component_scores", "type": "object", "nullable": False, "description": "Input PWS component scores copied from module 10, preserving missing scores as null."},
            {"name": "base_component_weights", "type": "object", "nullable": False, "description": "Stable product-level base weights before daily availability or deterministic adjustments."},
            {"name": "base_available_weights", "type": "object", "nullable": False, "description": "Base weights renormalized only over components available for the day. Zero for unavailable components means exclusion, not zero quality."},
            {"name": "component_reliability_factors", "type": "object", "nullable": True, "description": "Factors reducing influence of components supported by fallback or partial coverage."},
            {"name": "component_urgency_factors", "type": "object", "nullable": True, "description": "Bounded factors moderately increasing attention to low available component scores."},
            {"name": "candidate_deterministic_weights", "type": "object", "nullable": True, "description": "Reliability and urgency adjusted weights before movement and overlap controls."},
            {"name": "deterministic_effective_weights", "type": "object", "nullable": True, "description": "Final deterministic component weights after reliability, urgency, movement and overlap controls. Null when future final PWS eligibility fails."},
            {"name": "weights_ready_for_final_pws", "type": "boolean", "nullable": False, "description": "Whether a future deterministic PWS module may use the effective weights for this date."},
            {"name": "llm_adjustment_eligible", "type": "boolean", "nullable": False, "description": "Whether a future optional LLM module may propose a bounded adjustment for this date. No LLM call occurs here."},
            {"name": "llm_adjustment_applied", "type": "boolean", "nullable": False, "description": "Always false in module 11."},
            {"name": "final_pws_computed", "type": "boolean", "nullable": False, "description": "Always false in module 11."},
        ],
        "csv_flattening": "Nested weight and factor fields are flattened into deterministic per-component columns. Missing effective weights for ineligible days remain blank.",
        "excluded_future_fields": [
            "pws_score",
            "pws_deterministic",
            "pws_llm_assisted",
            "llm_adjusted_weights",
            "priority_component",
            "priority_recommendation",
            "coach_message",
            "training_recommendation",
        ],
    }


def build_lineage(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "module_id": MODULE_ID,
        "lineage_version": "pws_weights_lineage_v1",
        "source_artifacts": [
            {"module_id": "10_compute_pws_components", "artifact_path": "data/pipeline/10_compute_pws_components/pws_components.json", "role": "component_scores_and_component_coverage_source"},
            {"module_id": "10_compute_pws_components", "artifact_path": "data/pipeline/10_compute_pws_components/pws_components_quality_report.json", "role": "component_quality_reference"},
        ],
        "base_weight_rationale": {
            "LQ": {"weight": 0.20, "reason": "Load Quality matters but must not dominate recovery and vital stability."},
            "REC": {"weight": 0.35, "reason": "Recovery is the strongest short-term wellness signal in the configured model."},
            "CAP": {"weight": 0.15, "reason": "Capacity is a duration-based proxy and must not reward excessive activity volume."},
            "VS": {"weight": 0.30, "reason": "Vital Stability protects the model from ignoring meaningful physiological deviations."},
        },
        "deterministic_weighting_stages": [
            {"stage": "availability_renormalization", "description": "Exclude unavailable component scores from future weighting without treating them as zero quality."},
            {"stage": "reliability_adjustment", "description": "Moderately reduce influence of scores based on fallback sources or partial coverage."},
            {"stage": "urgency_adjustment", "description": "Moderately increase attention to weaker available components below configured target score."},
            {"stage": "movement_limits", "description": "Prevent unstable or excessive daily weight shifts."},
            {"stage": "overlap_controls", "description": "Limit combined influence of known overlapping component pairs when all components are available."},
        ],
        "future_llm_boundary": {
            "guardrails_artifact": "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json",
            "llm_called_in_this_module": False,
            "llm_adjustment_applied_in_this_module": False,
            "future_adjustment_must_remain_separate_from_deterministic_weights": True,
        },
        "forbidden_calculation_confirmation": {
            "final_pws_computed": False,
            "llm_used": False,
            "medical_diagnosis_generated": False,
            "injury_prediction_generated": False,
            "training_prescription_generated": False,
        },
    }


def flat_row(record: dict[str, Any]) -> dict[str, Any]:
    row = {
        "date": record["date"],
        "lq_score": record["component_scores"]["LQ"],
        "rec_score": record["component_scores"]["REC"],
        "cap_score": record["component_scores"]["CAP"],
        "vs_score": record["component_scores"]["VS"],
        "lq_available": record["component_availability"]["LQ"],
        "rec_available": record["component_availability"]["REC"],
        "cap_available": record["component_availability"]["CAP"],
        "vs_available": record["component_availability"]["VS"],
        "available_components_count": record["available_components_count"],
        "available_base_weight_sum": record["available_base_weight_sum"],
        "deterministic_total_absolute_weight_change": record["deterministic_total_absolute_weight_change"],
        "overlap_controls_applied_count": len(record["overlap_controls_applied"]),
        "weights_ready_for_final_pws": record["weights_ready_for_final_pws"],
        "weights_readiness_status": record["weights_readiness_status"],
        "llm_adjustment_eligible": record["llm_adjustment_eligible"],
        "llm_adjustment_applied": record["llm_adjustment_applied"],
        "final_pws_computed": record["final_pws_computed"],
    }
    for component, suffix in [("LQ", "lq"), ("REC", "rec"), ("CAP", "cap"), ("VS", "vs")]:
        row[f"base_weight_{suffix}"] = record["base_component_weights"][component]
        row[f"base_available_weight_{suffix}"] = record["base_available_weights"][component]
        row[f"reliability_factor_{suffix}"] = record["component_reliability_factors"][component]
        row[f"urgency_factor_{suffix}"] = record["component_urgency_factors"][component]
        effective = record["deterministic_effective_weights"]
        row[f"deterministic_effective_weight_{suffix}"] = None if effective is None else effective[component]
    return round_or_none(row)


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: ("" if value is None else value) for key, value in flat_row(record).items()})


def try_write_parquet(path: Path, records: list[dict[str, Any]]) -> tuple[bool, str | None]:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        return False, "PARQUET_DEPENDENCY_UNAVAILABLE"
    try:
        rows = [flat_row(record) for record in records]
        pd.DataFrame(rows, columns=CSV_FIELDS).to_parquet(path, index=False)
        return True, None
    except Exception:
        return False, "PARQUET_WRITE_FAILED"


def domain_status(records: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> str:
    if any(record["overlap_controls_applied"] for record in records):
        return "computed_with_overlap_controls"
    if any(not record["weights_ready_for_final_pws"] for record in records):
        return "computed_with_ineligible_days"
    if any(record["available_components_count"] < 4 for record in records):
        return "computed_with_partial_component_coverage"
    if warnings:
        return "computed_with_warnings"
    return "computed"


def build_quality(records: list[dict[str, Any]], policy: dict[str, Any], status: str, parquet_written: bool, parquet_warning: str | None) -> dict[str, Any]:
    count = len(records)
    availability = {}
    for component in COMPONENTS:
        available_count = sum(1 for record in records if record["component_availability"][component])
        availability[component] = {
            "available_count": available_count,
            "missing_count": count - available_count,
            "coverage_ratio": round(available_count / count, 6) if count else 0,
        }
    ready_count = sum(1 for record in records if record["weights_ready_for_final_pws"])
    reliability_below = [record["date"] for record in records if any((value is not None and value < 1.0) for value in record["component_reliability_factors"].values())]
    urgency_above = [record["date"] for record in records if any((value is not None and value > 1.0) for value in record["component_urgency_factors"].values())]
    movement = [record["date"] for record in records if record["deterministic_movement_limits_applied"]]
    overlap = [record["date"] for record in records if record["overlap_controls_applied"]]
    partial_overlap = [record["date"] for record in records if "Overlap is present but full-component overlap cap was not applied because one or more components are unavailable." in record["overlap_disclosures"]]
    return {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "records_count": count,
        "base_component_weights": policy["base_weights"],
        "component_availability": availability,
        "weight_readiness": {
            "weights_ready_for_final_pws_count": ready_count,
            "weights_not_ready_for_final_pws_count": count - ready_count,
            "llm_adjustment_eligible_count": sum(1 for record in records if record["llm_adjustment_eligible"]),
        },
        "deterministic_adjustment_usage": {
            "days_with_reliability_factor_below_one": reliability_below,
            "days_with_urgency_factor_above_one": urgency_above,
            "days_with_movement_limits_applied": movement,
            "days_with_overlap_controls_applied": overlap,
        },
        "overlap_controls": {
            "known_overlaps": ["LQ_REC_load_balance_overlap", "REC_VS_recovery_vital_overlap"],
            "full_component_overlap_cap_applied_count": len(overlap),
            "partial_component_overlap_disclosed_count": len(partial_overlap),
        },
        "future_llm_guardrails": {
            "guardrails_written": True,
            "llm_called": False,
            "actual_llm_adjustments_applied": False,
        },
        "parquet_output": {
            "requested": True,
            "written": parquet_written,
            "warning": parquet_warning,
        },
        "final_pws_computed": False,
        "warnings": [
            "Unavailable component scores were preserved as null and were not interpreted as zero quality.",
            "Deterministic weights were produced only for dates satisfying configured future-PWS eligibility requirements.",
            "No LLM was called. Guardrails were published only for a future optional bounded adjustment stage.",
        ],
        "ready_for_next_module": True,
    }


def write_failure_outputs(root: Path, artifact_dir: Path, started_at: str, domain_status_value: str, errors: list[dict[str, Any]]) -> None:
    finished_at = now_iso()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    errors_path = artifact_dir / "errors.json"
    log_path = artifact_dir / "run_log.txt"
    manifest_path = artifact_dir / "run_manifest.json"
    write_json(errors_path, {"module_id": MODULE_ID, "errors": errors})
    log_path.write_text(
        "\n".join([
            f"module_id={MODULE_ID}",
            f"started_at={started_at}",
            f"finished_at={finished_at}",
            f"policy_version={POLICY_VERSION}",
            f"domain_status={domain_status_value}",
            "execution_status=failed",
            "final_pws_computed=false",
            "llm_called=false",
        ]) + "\n",
        encoding="utf-8",
    )
    write_json(manifest_path, {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "failed",
        "domain_status": domain_status_value,
        "inputs": [
            "config/pws_weights_policy_v1.json",
            "data/pipeline/10_compute_pws_components/pws_components.json",
            "data/pipeline/10_compute_pws_components/pws_components_schema.json",
            "data/pipeline/10_compute_pws_components/pws_components_quality_report.json",
            "data/pipeline/10_compute_pws_components/pws_components_lineage.json",
        ],
        "generated_artifacts": [rel(root, manifest_path), rel(root, log_path), rel(root, errors_path)],
        "final_pws_computed": False,
        "llm_called": False,
        "llm_adjustment_applied": False,
        "log_file": rel(root, log_path),
        "errors_file": rel(root, errors_path),
    })


def run(root: Path | None = None) -> int:
    root = root or project_root()
    started_at = now_iso()
    artifact_dir = root / "data/pipeline/11_compute_pws_weights"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    required = [
        root / "config/pws_weights_policy_v1.json",
        root / "config/pws_components_policy_v1.json",
        root / "data/pipeline/10_compute_pws_components/pws_components_schema.json",
        root / "data/pipeline/10_compute_pws_components/pws_components_quality_report.json",
        root / "data/pipeline/10_compute_pws_components/pws_components_lineage.json",
    ]
    for path in required:
        if not path.is_file():
            code = "PWS_WEIGHTS_POLICY_NOT_FOUND" if path.name == "pws_weights_policy_v1.json" else "PWS_COMPONENTS_NOT_FOUND"
            add_error(errors, code, f"Required input is missing: {rel(root, path)}")
    policy_path = root / "config/pws_weights_policy_v1.json"
    policy: dict[str, Any] | None = None
    if policy_path.is_file():
        try:
            policy = read_json(policy_path)
            for message in validate_policy(policy):
                add_error(errors, "PWS_WEIGHTS_POLICY_INVALID", message)
        except Exception as exc:
            add_error(errors, "PWS_WEIGHTS_POLICY_INVALID", str(exc))
    if errors:
        status = "invalid_pws_weights_policy" if any(error["code"].startswith("PWS_WEIGHTS_POLICY") for error in errors) else "blocked_missing_pws_components"
        write_failure_outputs(root, artifact_dir, started_at, status, errors)
        return 1

    components_payload, input_records, input_errors = load_records(root)
    if input_errors:
        status = "blocked_pws_components_not_ready" if any(error["code"] == "PWS_COMPONENTS_NOT_READY" for error in input_errors) else "blocked_missing_pws_components"
        if any(error["code"] == "DUPLICATE_DATE_FOUND" for error in input_errors):
            status = "blocked_duplicate_dates"
        write_failure_outputs(root, artifact_dir, started_at, status, input_errors)
        return 1

    records = [compute_record(record, policy, errors) for record in input_records]
    warnings = [error for error in errors if error.get("severity") == "warning"]
    parquet_path = artifact_dir / "pws_weights.parquet"
    parquet_written, parquet_warning = try_write_parquet(parquet_path, records)
    if parquet_warning:
        add_error(errors, parquet_warning, "Parquet output was not written; JSON and CSV outputs are authoritative.", severity="warning")
    status = domain_status(records, warnings)
    ready_for_next = status in {"computed", "computed_with_partial_component_coverage", "computed_with_ineligible_days", "computed_with_overlap_controls", "computed_with_warnings"}
    date_range = {
        "first_date": records[0]["date"] if records else None,
        "last_date": records[-1]["date"] if records else None,
    }
    guardrails = build_guardrails(policy)
    output_payload = {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "status": status,
        "source_artifact": "data/pipeline/10_compute_pws_components/pws_components.json",
        "component_definitions": {"LQ": "Load Quality", "REC": "Recovery", "CAP": "Capacity", "VS": "Vital Stability"},
        "base_component_weights": policy["base_weights"],
        "weighting_strategy": {
            "availability_handling": "renormalize_base_weights_across_available_components_only",
            "deterministic_adjustment": "reliability_and_urgency_adjustment_with_movement_limits",
            "overlap_handling": "bounded_combined_weight_caps_when_full_component_redistribution_is_feasible",
            "future_llm_handling": "publish_guardrails_only_no_llm_call_in_this_module",
        },
        "future_final_pws_eligibility_requirements": policy["eligibility_for_future_final_pws"],
        "parent_policy_notes": {
            "pws_policy_v1_read_as_reference": (root / "config/pws_policy_v1.json").is_file(),
            "llm_policy_v1_read_as_reference": (root / "config/llm_policy_v1.json").is_file(),
            "module_specific_policy_is_authoritative_for_pws_weights_v1": True,
        },
        "records_count": len(records),
        "date_range": date_range,
        "records": records,
        "deterministic_weights_computed": any(record["deterministic_effective_weights"] is not None for record in records),
        "final_pws_computed": False,
        "llm_used": False,
        "llm_adjustment_applied": False,
        "guardrails_artifact": "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json",
        "ready_for_next_module": ready_for_next,
        "private_data_notice": "PWS weight records contain private derived health and training information and must not be committed to version control.",
    }
    write_json(artifact_dir / "pws_weights.json", output_payload)
    write_csv(artifact_dir / "pws_weights.csv", records)
    write_json(artifact_dir / "pws_weights_schema.json", build_schema(policy))
    write_json(artifact_dir / "pws_weight_guardrails.json", guardrails)
    write_json(artifact_dir / "pws_weights_lineage.json", build_lineage(policy))
    quality = build_quality(records, policy, status, parquet_written, parquet_warning)
    write_json(artifact_dir / "pws_weights_quality_report.json", quality)
    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    finished_at = now_iso()
    generated = [
        "data/pipeline/11_compute_pws_weights/pws_weights.json",
        "data/pipeline/11_compute_pws_weights/pws_weights.csv",
        "data/pipeline/11_compute_pws_weights/pws_weights_schema.json",
        "data/pipeline/11_compute_pws_weights/pws_weights_quality_report.json",
        "data/pipeline/11_compute_pws_weights/pws_weights_lineage.json",
        "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json",
        "data/pipeline/11_compute_pws_weights/run_manifest.json",
        "data/pipeline/11_compute_pws_weights/run_log.txt",
        "data/pipeline/11_compute_pws_weights/errors.json",
    ]
    write_json(artifact_dir / "run_manifest.json", {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "success",
        "domain_status": status,
        "inputs": [
            "config/pws_weights_policy_v1.json",
            "config/pws_policy_v1.json",
            "config/llm_policy_v1.json",
            "config/pws_components_policy_v1.json",
            "data/pipeline/10_compute_pws_components/pws_components.json",
            "data/pipeline/10_compute_pws_components/pws_components_schema.json",
            "data/pipeline/10_compute_pws_components/pws_components_quality_report.json",
            "data/pipeline/10_compute_pws_components/pws_components_lineage.json",
        ],
        "generated_artifacts": generated,
        "optional_generated_artifacts": [{"path": "data/pipeline/11_compute_pws_weights/pws_weights.parquet", "written": parquet_written, "reason_if_not_written": parquet_warning}],
        "final_pws_computed": False,
        "llm_called": False,
        "llm_adjustment_applied": False,
        "log_file": "data/pipeline/11_compute_pws_weights/run_log.txt",
        "errors_file": "data/pipeline/11_compute_pws_weights/errors.json",
    })
    component_counts = {component: sum(1 for record in records if record["component_availability"][component]) for component in COMPONENTS}
    log_lines = [
        f"module_id={MODULE_ID}",
        f"started_at={started_at}",
        f"finished_at={finished_at}",
        f"policy_version={POLICY_VERSION}",
        "input_artifact=data/pipeline/10_compute_pws_components/pws_components.json",
        f"records_count={len(records)}",
        f"date_range={date_range}",
        "base_weights: LQ=0.20 REC=0.35 CAP=0.15 VS=0.30",
        "PWS is wellness-oriented and is not a reward for activity volume.",
        f"component_available_counts={component_counts}",
        f"weights_ready_for_final_pws_count={quality['weight_readiness']['weights_ready_for_final_pws_count']}",
        f"weights_not_ready_for_final_pws_count={quality['weight_readiness']['weights_not_ready_for_final_pws_count']}",
        f"partial_coverage_days={sum(1 for record in records if 0 < record['available_components_count'] < 4)}",
        f"days_with_reliability_factor_below_one={len(quality['deterministic_adjustment_usage']['days_with_reliability_factor_below_one'])}",
        f"days_with_urgency_factor_above_one={len(quality['deterministic_adjustment_usage']['days_with_urgency_factor_above_one'])}",
        f"days_with_movement_limits_applied={len(quality['deterministic_adjustment_usage']['days_with_movement_limits_applied'])}",
        f"days_with_overlap_controls_applied={len(quality['deterministic_adjustment_usage']['days_with_overlap_controls_applied'])}",
        f"partial_component_overlap_disclosed_count={quality['overlap_controls']['partial_component_overlap_disclosed_count']}",
        "future LLM guardrails written; no LLM call was made and no LLM adjustment was applied.",
        f"json_csv_written=true parquet_written={parquet_written} parquet_warning={parquet_warning}",
        "Missing component scores remain null. Technical effective_weight=0 for unavailable components means exclusion, not score zero.",
        "Final PWS was not computed.",
        "No medical diagnosis, injury prediction or training prescription was generated.",
        f"domain_status={status}",
    ]
    (artifact_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    try:
        return run()
    except Exception as exc:
        root = project_root()
        artifact_dir = root / "data/pipeline/11_compute_pws_weights"
        write_failure_outputs(root, artifact_dir, now_iso(), "pws_weight_computation_failed", [{"severity": "error", "code": "PWS_WEIGHT_COMPUTATION_FAILED", "message": str(exc)}])
        return 1


if __name__ == "__main__":
    sys.exit(main())
