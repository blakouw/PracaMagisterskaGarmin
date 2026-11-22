from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_client import ConfiguredLLMClient, LLMClientError, LLMClientResult


MODULE_ID = "13_validate_llm_weight_influence"
MODULE_VERSION = "1.0.0"
POLICY_VERSION = "llm_assisted_pws_policy_v1"
PROMPT_VERSION = "llm_weight_adjustment_prompt_v1"
COMPONENTS = ["LQ", "REC", "CAP", "VS"]
READY_STATUSES = {
    "completed_assisted_score_computed",
    "completed_assisted_score_computed_with_warnings",
    "completed_batch_with_normalized_assisted_scores",
    "completed_no_adjustment_proposed",
    "completed_proposal_rejected",
    "skipped_llm_disabled",
    "skipped_missing_credentials",
    "skipped_no_eligible_date",
    "skipped_requested_date_not_found",
    "skipped_requested_date_not_eligible",
    "llm_response_invalid",
    "llm_request_failed",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


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
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optional bounded LLM-assisted PWS module.")
    parser.add_argument("--date", dest="date", help="Analyze exactly one date in YYYY-MM-DD format. Without it, analyze every eligible date.")
    parser.add_argument("--enable-llm", action="store_true", help="Allow one LLM request per eligible date if credentials exist.")
    parser.add_argument("--dry-run", action="store_true", help="Prepare audits and validate inputs without sending an LLM request.")
    return parser.parse_args(argv)


def validate_date(value: str | None) -> bool:
    if value is None:
        return True
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def load_required(root: Path, errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    paths = {
        "policy": root / "config" / "llm_assisted_pws_policy_v1.json",
        "prompt": root / "config" / "llm_weight_adjustment_prompt_v1.json",
        "llm_policy": root / "config" / "llm_policy_v1.json",
        "pws_score_policy": root / "config" / "pws_score_policy_v1.json",
        "components": root / "data" / "pipeline" / "10_compute_pws_components" / "pws_components.json",
        "components_schema": root / "data" / "pipeline" / "10_compute_pws_components" / "pws_components_schema.json",
        "weights": root / "data" / "pipeline" / "11_compute_pws_weights" / "pws_weights.json",
        "weights_schema": root / "data" / "pipeline" / "11_compute_pws_weights" / "pws_weights_schema.json",
        "guardrails": root / "data" / "pipeline" / "11_compute_pws_weights" / "pws_weight_guardrails.json",
        "pws_score": root / "data" / "pipeline" / "12_compute_pws_score" / "pws_score.json",
        "pws_score_schema": root / "data" / "pipeline" / "12_compute_pws_score" / "pws_score_schema.json",
        "pws_score_quality": root / "data" / "pipeline" / "12_compute_pws_score" / "pws_score_quality_report.json",
        "pws_score_lineage": root / "data" / "pipeline" / "12_compute_pws_score" / "pws_score_lineage.json",
    }
    missing_codes = {
        "policy": "LLM_ASSISTED_POLICY_NOT_FOUND",
        "prompt": "LLM_PROMPT_TEMPLATE_NOT_FOUND",
        "components": "PWS_COMPONENTS_NOT_FOUND",
        "weights": "PWS_WEIGHTS_NOT_FOUND",
        "guardrails": "PWS_WEIGHT_GUARDRAILS_NOT_FOUND",
        "pws_score": "DETERMINISTIC_PWS_NOT_FOUND",
    }
    for key, path in paths.items():
        if not path.is_file():
            errors.append({"severity": "error", "code": missing_codes.get(key, "REQUIRED_INPUT_NOT_FOUND"), "message": f"Missing required input: {rel(root, path)}"})
            if key in {"policy", "prompt", "components", "weights", "guardrails", "pws_score"}:
                return None
    try:
        return {key: read_json(path) for key, path in paths.items() if path.is_file()} | {"paths": paths}
    except json.JSONDecodeError as exc:
        errors.append({"severity": "error", "code": "REQUIRED_INPUT_INVALID_JSON", "message": str(exc)})
        return None


def validate_policy(data: dict[str, Any], errors: list[dict[str, Any]]) -> bool:
    policy = data.get("policy", {})
    prompt = data.get("prompt", {})
    guardrails = data.get("guardrails", {}).get("future_llm_adjustment", {})
    ok = True
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append({"severity": "error", "code": "LLM_ASSISTED_POLICY_INVALID", "message": "Invalid LLM-assisted policy version."})
        ok = False
    if prompt.get("prompt_version") != PROMPT_VERSION:
        errors.append({"severity": "error", "code": "LLM_PROMPT_TEMPLATE_INVALID", "message": "Invalid prompt template version."})
        ok = False
    validation = policy.get("validation_policy", {})
    for key in ["maximum_absolute_delta_per_component", "maximum_total_positive_weight_shift", "maximum_total_absolute_delta"]:
        if validation.get(key) != guardrails.get(key):
            errors.append({"severity": "warning", "code": "LLM_POLICY_CONFLICT_WITH_GUARDRAILS", "message": f"Policy {key} differs from module 11 guardrails; module 11 guardrails remain authoritative."})
    execution = policy.get("execution_policy", {})
    if execution.get("maximum_llm_calls_per_eligible_date") != 1:
        errors.append({"severity": "error", "code": "LLM_ASSISTED_POLICY_INVALID", "message": "maximum_llm_calls_per_eligible_date must be 1."})
        ok = False
    if execution.get("default_target_selection") != "all_eligible_dates_in_ascending_order":
        errors.append({"severity": "error", "code": "LLM_ASSISTED_POLICY_INVALID", "message": "default_target_selection must cover all eligible dates."})
        ok = False
    return ok


def validate_ready(data: dict[str, Any], errors: list[dict[str, Any]]) -> bool:
    ok = True
    for key, code in [("pws_score", "DETERMINISTIC_PWS_NOT_READY"), ("weights", "PWS_WEIGHTS_NOT_READY"), ("components", "PWS_COMPONENTS_NOT_READY")]:
        payload = data.get(key, {})
        if payload.get("ready_for_next_module") is not True:
            errors.append({"severity": "error", "code": code, "message": f"{key} artifact is not ready_for_next_module."})
            ok = False
    return ok


def records_by_date(records: list[dict[str, Any]], errors: list[dict[str, Any]], source: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        date = record.get("date")
        if not isinstance(date, str) or not validate_date(date):
            errors.append({"severity": "error", "code": "DATE_VALUE_INVALID", "source": source, "date": date})
            continue
        if date in indexed:
            errors.append({"severity": "error", "code": "DUPLICATE_DATE_FOUND", "source": source, "date": date})
            continue
        indexed[date] = record
    return indexed


def eligible(record: dict[str, Any]) -> bool:
    return (
        record.get("pws_deterministic_computed") is True
        and record.get("llm_adjustment_eligible") is True
        and is_number(record.get("pws_deterministic"))
        and isinstance(record.get("pws_deterministic_weights"), dict)
        and record.get("pws_available_components_count", 0) >= 3
    )


def select_record(records: list[dict[str, Any]], requested_date: str | None) -> tuple[str, dict[str, Any] | None, str | None, bool]:
    by_date = {record.get("date"): record for record in records if isinstance(record.get("date"), str)}
    if requested_date:
        selected = by_date.get(requested_date)
        if selected is None:
            return "explicit_date", None, "skipped_requested_date_not_found", False
        if not eligible(selected):
            return "explicit_date", selected, "skipped_requested_date_not_eligible", False
        return "explicit_date", selected, None, True
    eligible_records = [record for record in records if eligible(record)]
    if not eligible_records:
        return "latest_eligible_date", None, "skipped_no_eligible_date", False
    eligible_records.sort(key=lambda item: item["date"])
    return "latest_eligible_date", eligible_records[-1], None, True


def guardrail_limits(guardrails: dict[str, Any]) -> dict[str, Any]:
    future = guardrails.get("future_llm_adjustment", {})
    return {
        "maximum_absolute_delta_per_component": future.get("maximum_absolute_delta_per_component", 0.20),
        "maximum_total_positive_weight_shift": future.get("maximum_total_positive_weight_shift", 0.20),
        "maximum_total_absolute_delta": future.get("maximum_total_absolute_delta", 0.40),
        "weights_must_sum_to": future.get("weights_must_sum_to", 1.0),
        "unavailable_component_weight_must_remain_zero": future.get("unavailable_component_weight_must_remain_zero", True),
    }


def load_goal_context(root: Path, policy: dict[str, Any], warnings: list[dict[str, Any]]) -> dict[str, Any] | None:
    path = root / "data" / "local_context" / "llm_user_goal_context.json"
    if not path.is_file():
        return None
    try:
        payload = read_json(path)
    except json.JSONDecodeError:
        warnings.append({"severity": "warning", "code": "USER_GOAL_CONTEXT_INVALID", "message": "Optional goal context is not valid JSON and was omitted."})
        return None
    cfg = policy.get("approved_user_goal_context_policy", {})
    allowed_fields = set(cfg.get("allowed_fields", []))
    if set(payload) - allowed_fields:
        warnings.append({"severity": "warning", "code": "USER_GOAL_CONTEXT_INVALID", "message": "Optional goal context contains unsupported fields and was omitted."})
        return None
    if payload.get("goal_type") not in set(cfg.get("allowed_goal_types", [])):
        warnings.append({"severity": "warning", "code": "USER_GOAL_CONTEXT_INVALID", "message": "Optional goal context goal_type is unsupported and was omitted."})
        return None
    summary = payload.get("goal_summary", "")
    if not isinstance(summary, str) or len(summary) > cfg.get("maximum_goal_summary_characters", 300):
        warnings.append({"severity": "warning", "code": "USER_GOAL_CONTEXT_INVALID", "message": "Optional goal context summary is invalid and was omitted."})
        return None
    return payload


def build_context(root: Path, policy: dict[str, Any], guardrails: dict[str, Any], score_record: dict[str, Any], weight_record: dict[str, Any] | None, warnings: list[dict[str, Any]]) -> dict[str, Any]:
    overlap = []
    if isinstance(weight_record, dict):
        overlap = weight_record.get("overlap_disclosures") or weight_record.get("overlap_control_summary", {}).get("known_overlap_disclosures", []) or []
    if not overlap:
        overlap = [
            "LQ and REC may both contain ACWR exposure through readiness load balance.",
            "REC and VS may both rely on HRV and RHR under different interpretations.",
        ]
    return {
        "date": score_record.get("date"),
        "available_components": score_record.get("pws_available_components", []),
        "missing_components": score_record.get("pws_missing_components", []),
        "component_scores": score_record.get("pws_component_scores", {}),
        "component_statuses": score_record.get("pws_component_statuses", {}),
        "component_coverage_information": {
            "pws_coverage_tier": score_record.get("pws_coverage_tier"),
            "pws_coverage_ratio": score_record.get("pws_coverage_ratio"),
        },
        "pws_deterministic": score_record.get("pws_deterministic"),
        "deterministic_effective_weights": score_record.get("pws_deterministic_weights"),
        "overlap_disclosures": overlap,
        "guardrail_limits": guardrail_limits(guardrails),
        "approved_user_goal_context": load_goal_context(root, policy, warnings),
    }


def allowed_decisions_from_prompt(prompt: dict[str, Any] | None) -> set[str]:
    decision_schema = (((prompt or {}).get("required_response_schema") or {}).get("properties") or {}).get("decision") or {}
    enum_values = decision_schema.get("enum")
    if isinstance(enum_values, list) and enum_values and all(isinstance(value, str) for value in enum_values):
        return set(enum_values)
    return {"no_adjustment", "propose_adjustment"}


def response_schema_valid(response: Any, allowed_decisions: set[str] | None = None) -> tuple[bool, list[str]]:
    violations: list[str] = []
    if not isinstance(response, dict):
        return False, ["Response must be a JSON object."]
    expected = {"decision", "reason_summary", "proposed_weight_deltas"}
    if set(response) != expected:
        violations.append("Response must contain exactly decision, reason_summary and proposed_weight_deltas.")
    allowed = allowed_decisions or {"no_adjustment", "propose_adjustment"}
    if response.get("decision") not in allowed:
        violations.append(f"Invalid decision. Allowed decisions: {', '.join(sorted(allowed))}.")
    if not isinstance(response.get("reason_summary"), str) or len(response.get("reason_summary", "")) > 500:
        violations.append("reason_summary must be a string up to 500 characters.")
    deltas = response.get("proposed_weight_deltas")
    if not isinstance(deltas, dict) or set(deltas) != set(COMPONENTS):
        violations.append("proposed_weight_deltas must contain exactly LQ, REC, CAP and VS.")
    elif any(not is_number(deltas[c]) for c in COMPONENTS):
        violations.append("Every proposed delta must be numeric.")
    return not violations, violations


def label_for(score: float) -> tuple[str, str]:
    if score < 40:
        return "low", "niski"
    if score < 60:
        return "reduced", "obnizony"
    if score < 80:
        return "balanced", "stabilny"
    return "strong", "wysoki"


def validate_proposal(response: dict[str, Any] | None, record: dict[str, Any] | None, guardrails: dict[str, Any], allowed_decisions: set[str] | None = None) -> dict[str, Any]:
    weights = (record or {}).get("pws_deterministic_weights") or {}
    scores = (record or {}).get("pws_component_scores") or {}
    available = set((record or {}).get("pws_available_components") or [])
    missing = set((record or {}).get("pws_missing_components") or [])
    limits = guardrail_limits(guardrails)
    checks = {
        "schema_valid": False,
        "only_allowed_components_present": False,
        "delta_per_component_within_limit": False,
        "positive_shift_within_limit": False,
        "total_absolute_delta_within_limit": False,
        "delta_sum_zero_within_tolerance": False,
        "resulting_weights_sum_to_one": False,
        "no_negative_weights": False,
        "unavailable_components_remain_zero": False,
        "overlap_controls_respected": False,
        "deterministic_weights_preserved": True,
    }
    if response is None:
        return {
            "proposal_received": False,
            "proposal_decision": None,
            "validation_status": "not_applicable",
            "deterministic_effective_weights": weights or None,
            "proposed_weight_deltas": None,
            "validated_llm_adjusted_weights": None,
            "checks": checks,
            "violations": [],
            "assisted_score_permitted": False,
        }
    schema_ok, violations = response_schema_valid(response, allowed_decisions)
    checks["schema_valid"] = schema_ok
    if not schema_ok:
        return {
            "proposal_received": True,
            "proposal_decision": response.get("decision") if isinstance(response, dict) else None,
            "validation_status": "rejected_schema_invalid",
            "deterministic_effective_weights": weights or None,
            "proposed_weight_deltas": response.get("proposed_weight_deltas") if isinstance(response, dict) else None,
            "validated_llm_adjusted_weights": None,
            "checks": checks,
            "violations": violations,
            "assisted_score_permitted": False,
        }
    deltas = {component: float(response["proposed_weight_deltas"][component]) for component in COMPONENTS}
    checks["only_allowed_components_present"] = True
    if response["decision"] == "no_adjustment":
        all_zero = all(abs(deltas[c]) <= 0.000001 for c in COMPONENTS)
        checks.update({
            "delta_per_component_within_limit": all_zero,
            "positive_shift_within_limit": all_zero,
            "total_absolute_delta_within_limit": all_zero,
            "delta_sum_zero_within_tolerance": all_zero,
            "resulting_weights_sum_to_one": True,
            "no_negative_weights": True,
            "unavailable_components_remain_zero": True,
            "overlap_controls_respected": True,
        })
        if not all_zero:
            violations.append("No-adjustment response must contain zero deltas.")
            status = "rejected_guardrail_violation"
        else:
            status = "valid_no_adjustment"
        return {
            "proposal_received": True,
            "proposal_decision": "no_adjustment",
            "validation_status": status,
            "deterministic_effective_weights": weights,
            "proposed_weight_deltas": deltas,
            "validated_llm_adjusted_weights": weights if all_zero else None,
            "checks": checks,
            "violations": violations,
            "assisted_score_permitted": all_zero,
        }
    max_delta = float(limits["maximum_absolute_delta_per_component"])
    max_positive = float(limits["maximum_total_positive_weight_shift"])
    max_abs = float(limits["maximum_total_absolute_delta"])
    tol = 0.000001
    checks["delta_per_component_within_limit"] = all(abs(deltas[c]) <= max_delta + tol for c in COMPONENTS)
    checks["positive_shift_within_limit"] = sum(max(0.0, deltas[c]) for c in COMPONENTS) <= max_positive + tol
    checks["total_absolute_delta_within_limit"] = sum(abs(deltas[c]) for c in COMPONENTS) <= max_abs + tol
    checks["delta_sum_zero_within_tolerance"] = abs(sum(deltas.values())) <= tol
    adjusted = {c: round(float(weights.get(c, 0.0)) + deltas[c], 12) for c in COMPONENTS}
    checks["no_negative_weights"] = all(adjusted[c] >= -tol for c in COMPONENTS)
    checks["resulting_weights_sum_to_one"] = abs(sum(adjusted.values()) - 1.0) <= tol
    checks["unavailable_components_remain_zero"] = all(abs(deltas[c]) <= tol and abs(adjusted[c]) <= tol for c in missing)
    if len(available) == 4:
        checks["overlap_controls_respected"] = adjusted["LQ"] + adjusted["REC"] <= 0.55 + tol and adjusted["REC"] + adjusted["VS"] <= 0.65 + tol
    else:
        checks["overlap_controls_respected"] = True
    messages = {
        "delta_per_component_within_limit": "Maximum absolute delta per component exceeded.",
        "positive_shift_within_limit": "Maximum total positive weight shift exceeded.",
        "total_absolute_delta_within_limit": "Maximum total absolute delta exceeded.",
        "delta_sum_zero_within_tolerance": "Proposed deltas must sum to zero.",
        "resulting_weights_sum_to_one": "Resulting weights must sum to one.",
        "no_negative_weights": "Resulting weights must not be negative.",
        "unavailable_components_remain_zero": "Unavailable components must keep zero delta and zero resulting weight.",
        "overlap_controls_respected": "Overlap controls were violated.",
    }
    for key, message in messages.items():
        if not checks[key]:
            violations.append(message)
    accepted = not violations
    return {
        "proposal_received": True,
        "proposal_decision": "propose_adjustment",
        "validation_status": "accepted" if accepted else "rejected_guardrail_violation",
        "deterministic_effective_weights": weights,
        "proposed_weight_deltas": deltas,
        "validated_llm_adjusted_weights": adjusted if accepted else None,
        "checks": checks,
        "violations": violations,
        "assisted_score_permitted": accepted,
    }


def normalize_guardrail_violating_proposal(validation: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    if validation.get("validation_status") != "rejected_guardrail_violation":
        return validation
    deltas = validation.get("proposed_weight_deltas")
    weights = record.get("pws_deterministic_weights") or {}
    available = set(record.get("pws_available_components") or [])
    if not isinstance(deltas, dict) or not available:
        return validation

    raw_target_weights = {
        component: float(weights.get(component, 0.0)) + float(deltas.get(component, 0.0))
        for component in COMPONENTS
    }
    clipped_target_weights = {
        component: max(0.0, raw_target_weights[component]) if component in available else 0.0
        for component in COMPONENTS
    }
    available_total = sum(clipped_target_weights[component] for component in available)
    fallback_to_deterministic = available_total <= 0.000001
    if fallback_to_deterministic:
        clipped_target_weights = {
            component: float(weights.get(component, 0.0)) if component in available else 0.0
            for component in COMPONENTS
        }
        available_total = sum(clipped_target_weights.values())
    if available_total <= 0.000001:
        return validation

    normalized = {
        component: round(clipped_target_weights[component] / available_total, 12)
        for component in COMPONENTS
    }
    residual = round(1.0 - sum(normalized.values()), 12)
    anchor = max(available, key=lambda component: normalized[component])
    normalized[anchor] = round(normalized[anchor] + residual, 12)
    effective_deltas = {
        component: round(normalized[component] - float(weights.get(component, 0.0)), 12)
        for component in COMPONENTS
    }
    return {
        **validation,
        "raw_validation_status": validation.get("validation_status"),
        "validation_status": "accepted_with_normalization_warnings",
        "validated_llm_adjusted_weights": normalized,
        "effective_weight_deltas_after_normalization": effective_deltas,
        "assisted_score_permitted": True,
        "proposal_interpretation_mode": "permissive_simplex_normalization",
        "normalization_details": {
            "raw_target_weights": raw_target_weights,
            "clipped_target_weights": clipped_target_weights,
            "normalized_available_weights": normalized,
            "unavailable_components_zeroed": sorted(set(COMPONENTS) - available),
            "negative_target_weights_clipped": sorted(
                component for component in available if raw_target_weights[component] < 0.0
            ),
            "fallback_to_deterministic_weights": fallback_to_deterministic,
            "raw_guardrail_violations_preserved_as_warnings": True,
        },
    }


def compute_assisted(record: dict[str, Any], adjusted: dict[str, float]) -> dict[str, Any]:
    scores = record.get("pws_component_scores") or {}
    contributions = {}
    raw = 0.0
    for component in COMPONENTS:
        score = scores.get(component)
        weight = adjusted.get(component, 0.0)
        contribution = float(score) * weight if is_number(score) and weight > 0 else 0.0
        contributions[component] = round(contribution, 4)
        raw += contribution
    score = round(raw, 2)
    label_id, label = label_for(score)
    return {
        "pws_llm_assisted_weighted_contributions": contributions,
        "pws_llm_assisted": score,
        "pws_llm_assisted_computed": True,
        "pws_llm_assisted_delta_from_deterministic": round(score - float(record["pws_deterministic"]), 2),
        "pws_llm_assisted_label_id": label_id,
        "pws_llm_assisted_label": label,
    }


def provider_config(llm_policy: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    runtime = policy.get("llm_runtime", {})
    provider = llm_policy.get("provider") or llm_policy.get("default_provider") or "openai"
    model = llm_policy.get("model") or llm_policy.get("default_model") or "gpt-4.1-mini"
    endpoint = llm_policy.get("endpoint") or "https://api.openai.com/v1/chat/completions"
    env_name = llm_policy.get("api_key_environment_variable") or runtime.get("default_api_key_environment_variable", "OPENAI_API_KEY")
    return {
        "provider": provider,
        "model": model,
        "endpoint": endpoint,
        "api_key_environment_variable": env_name,
        "temperature": runtime.get("temperature", 0),
        "timeout_seconds": runtime.get("timeout_seconds", 60),
    }


def build_record(selection_mode: str, selected: dict[str, Any] | None, args: argparse.Namespace, response: dict[str, Any] | None, validation: dict[str, Any], domain_status: str) -> dict[str, Any]:
    base = {
        "date": selected.get("date") if selected else None,
        "selection_mode": selection_mode,
        "pws_deterministic": selected.get("pws_deterministic") if selected else None,
        "pws_deterministic_label_id": selected.get("pws_label_id") if selected else None,
        "pws_deterministic_label": selected.get("pws_label") if selected else None,
        "component_scores": selected.get("pws_component_scores") if selected else None,
        "available_components": selected.get("pws_available_components") if selected else [],
        "missing_components": selected.get("pws_missing_components") if selected else [],
        "deterministic_effective_weights": selected.get("pws_deterministic_weights") if selected else None,
        "llm_execution_enabled": bool(args.enable_llm) and not bool(args.dry_run),
        "llm_called": False,
        "llm_response_decision": None,
        "llm_reason_summary": None,
        "llm_proposed_weight_deltas": None,
        "llm_proposal_validation_status": validation.get("validation_status"),
        "llm_raw_proposal_validation_status": validation.get("raw_validation_status", validation.get("validation_status")),
        "llm_guardrail_violations": validation.get("violations", []),
        "validated_llm_adjusted_weights": validation.get("validated_llm_adjusted_weights"),
        "llm_effective_weight_deltas": validation.get("effective_weight_deltas_after_normalization"),
        "proposal_interpretation_mode": validation.get("proposal_interpretation_mode", "strict_validation"),
        "llm_normalization_details": validation.get("normalization_details"),
        "pws_llm_assisted": None,
        "pws_llm_assisted_computed": False,
        "pws_llm_assisted_delta_from_deterministic": None,
        "llm_adjustment_applied": False,
        "deterministic_pws_preserved_unchanged": True,
        "llm_assisted_status": domain_status,
        "llm_tool_execution": {
            "tool_name": "persist_llm_assisted_pws_record",
            "attempted": False,
            "succeeded": False,
            "error": None,
        },
        "warnings": [],
    }
    if response:
        base["llm_response_decision"] = response.get("decision")
        base["llm_reason_summary"] = response.get("reason_summary")
        base["llm_proposed_weight_deltas"] = response.get("proposed_weight_deltas")
    return base


def write_artifacts(root: Path, started_at: str, finished_at: str, domain_status: str, args: argparse.Namespace, selection_mode: str, selected: dict[str, Any] | None, context: dict[str, Any] | None, provider: dict[str, Any], request_sent: bool, response_payload: dict[str, Any] | None, response_parse_status: str, validation: dict[str, Any], record: dict[str, Any], errors: list[dict[str, Any]], llm_calls_attempted: int, llm_calls_completed: int, credentials_available: bool) -> None:
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    ready = domain_status in READY_STATUSES
    generated = [
        f"data/pipeline/{MODULE_ID}/llm_assisted_pws.json",
        f"data/pipeline/{MODULE_ID}/llm_assisted_pws_schema.json",
        f"data/pipeline/{MODULE_ID}/llm_assisted_pws_quality_report.json",
        f"data/pipeline/{MODULE_ID}/llm_assisted_pws_lineage.json",
        f"data/pipeline/{MODULE_ID}/llm_request_audit.json",
        f"data/pipeline/{MODULE_ID}/llm_response_audit.json",
        f"data/pipeline/{MODULE_ID}/llm_validation_report.json",
        f"data/pipeline/{MODULE_ID}/llm_conversations/",
        f"data/pipeline/{MODULE_ID}/llm_conversation_index.json",
        f"data/pipeline/{MODULE_ID}/run_manifest.json",
        f"data/pipeline/{MODULE_ID}/run_log.txt",
        f"data/pipeline/{MODULE_ID}/errors.json",
    ]
    main = {
        "module_id": MODULE_ID,
        "contract_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "prompt_version": PROMPT_VERSION,
        "status": domain_status,
        "optional_module": True,
        "source_artifacts": {
            "pws_components": "data/pipeline/10_compute_pws_components/pws_components.json",
            "pws_weights": "data/pipeline/11_compute_pws_weights/pws_weights.json",
            "pws_weight_guardrails": "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json",
            "pws_deterministic": "data/pipeline/12_compute_pws_score/pws_score.json",
        },
        "execution_scope": {
            "maximum_llm_calls_per_run": 1,
            "selection_mode": selection_mode,
            "requested_date": args.date,
            "selected_date": selected.get("date") if selected else None,
            "historical_batch_processing_performed": False,
        },
        "deterministic_path": {"preserved_unchanged": True, "score_field": "pws_deterministic"},
        "llm_path": {
            "llm_enabled": bool(args.enable_llm) and not bool(args.dry_run),
            "llm_called": llm_calls_completed > 0,
            "llm_calls_attempted": llm_calls_attempted,
            "llm_calls_completed": llm_calls_completed,
            "adjustment_accepted": validation.get("validation_status") in {"accepted", "accepted_with_normalization_warnings"},
            "no_adjustment_recorded_as_assisted_variant": validation.get("validation_status") == "valid_no_adjustment" and record.get("pws_llm_assisted_computed") is True,
            "assisted_score_computed": record.get("pws_llm_assisted_computed") is True,
            "persist_tool": record.get("llm_tool_execution"),
        },
        "record": record,
        "ready_for_next_module": ready,
        "private_data_notice": "LLM-assisted PWS artifacts contain private derived wellness information and model interaction audit data and must not be committed to version control.",
    }
    write_json(artifact_dir / "llm_assisted_pws.json", main)
    request_audit = {
        "module_id": MODULE_ID,
        "prompt_version": PROMPT_VERSION,
        "llm_request_prepared": context is not None,
        "llm_request_sent": request_sent,
        "request_not_sent_reason": None if request_sent else domain_status,
        "selected_date": selected.get("date") if selected else None,
        "provider": provider.get("provider"),
        "model": provider.get("model"),
        "temperature": provider.get("temperature", 0),
        "structured_context": context,
        "forbidden_context_confirmation": {
            "raw_health_records_sent": False,
            "raw_activity_records_sent": False,
            "raw_files_sent": False,
            "tokens_or_credentials_sent": False,
        },
    }
    write_json(artifact_dir / "llm_request_audit.json", request_audit)
    response_audit = {
        "module_id": MODULE_ID,
        "llm_called": llm_calls_completed > 0,
        "response_received": response_payload is not None,
        "response_parse_status": response_parse_status,
        "raw_response_stored": False,
        "parsed_response": response_payload,
        "notes": [
            "Only the parsed bounded proposal is stored by default.",
            "No medical diagnosis or training recommendation is expected or accepted.",
        ],
    }
    write_json(artifact_dir / "llm_response_audit.json", response_audit)
    validation_report = {"module_id": MODULE_ID, "selected_date": selected.get("date") if selected else None, **validation}
    write_json(artifact_dir / "llm_validation_report.json", validation_report)
    if selected and selected.get("date"):
        prompt_payload = read_json(root / "config" / "llm_weight_adjustment_prompt_v1.json")
        conversation_log = {
            "module_id": MODULE_ID,
            "date": selected["date"],
            "prompt_version": PROMPT_VERSION,
            "system_instruction": prompt_payload.get("system_instruction"),
            "structured_context": context,
            "provider": provider.get("provider"),
            "model": provider.get("model"),
            "temperature": provider.get("temperature", 0),
            "request_sent": request_sent,
            "response_parse_status": response_parse_status,
            "parsed_model_response": response_payload,
            "reason_summary": (response_payload or {}).get("reason_summary"),
            "raw_proposal_validation_status": validation.get("raw_validation_status", validation.get("validation_status")),
            "final_interpretation_status": validation.get("validation_status"),
            "guardrail_findings": validation.get("violations", []),
            "proposal_interpretation_mode": validation.get("proposal_interpretation_mode", "strict_validation"),
            "normalization_details": validation.get("normalization_details"),
            "effective_weight_deltas": validation.get("effective_weight_deltas_after_normalization"),
            "effective_assisted_weights": validation.get("validated_llm_adjusted_weights"),
            "pws_deterministic": record.get("pws_deterministic"),
            "pws_llm_assisted": record.get("pws_llm_assisted"),
            "hidden_reasoning_stored": False,
            "hidden_reasoning_note": "Only the model's explicit JSON response and concise reason_summary are stored; hidden chain-of-thought is neither requested nor available.",
            "privacy_boundary": {
                "raw_health_records_stored": False,
                "raw_activity_records_stored": False,
                "tokens_or_credentials_stored": False,
            },
        }
        write_json(artifact_dir / "llm_conversations" / f"{selected['date']}.json", conversation_log)
    schema = {
        "module_id": MODULE_ID,
        "schema_version": "llm_assisted_pws_schema_v1",
        "policy_version": POLICY_VERSION,
        "processed_records_per_run_maximum": 1,
        "deterministic_score_field": "pws_deterministic",
        "assisted_score_field": "pws_llm_assisted",
        "deterministic_score_must_remain_unchanged": True,
        "fields": [
            {"name": "date", "type": "string", "nullable": True, "description": "The single selected eligible date for optional LLM analysis."},
            {"name": "deterministic_effective_weights", "type": "object", "nullable": True, "description": "Original deterministic weights copied without modification."},
            {"name": "llm_proposed_weight_deltas", "type": "object", "nullable": True, "description": "Bounded weight deltas proposed by the LLM."},
            {"name": "validated_llm_adjusted_weights", "type": "object", "nullable": True, "description": "Locally validated adjusted weights."},
            {"name": "llm_effective_weight_deltas", "type": "object", "nullable": True, "description": "Effective deltas after optional permissive normalization."},
            {"name": "llm_guardrail_violations", "type": "array", "nullable": False, "description": "Raw proposal findings retained for interpretation even when normalization permits an assisted score."},
            {"name": "pws_llm_assisted", "type": "number", "nullable": True, "description": "Optional assisted PWS computed locally only after accepted proposal."},
        ],
        "privacy_policy": "minimum_structured_context_only_no_raw_health_records_or_secrets",
        "prohibited_outputs": ["medical_diagnosis", "injury_prediction", "training_recommendation", "coach_message", "raw_private_history"],
    }
    write_json(artifact_dir / "llm_assisted_pws_schema.json", schema)
    quality = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": domain_status,
        "optional_module": True,
        "selection": {"selection_mode": selection_mode, "requested_date": args.date, "selected_date": selected.get("date") if selected else None, "eligible": selected is not None and eligible(selected)},
        "execution": {
            "llm_enabled": bool(args.enable_llm) and not bool(args.dry_run),
            "dry_run": bool(args.dry_run),
            "credentials_available": credentials_available,
            "llm_calls_attempted": llm_calls_attempted,
            "llm_calls_completed": llm_calls_completed,
            "maximum_llm_calls_per_run": 1,
            "historical_batch_processing_performed": False,
        },
        "proposal": {"decision": record.get("llm_response_decision"), "proposal_received": response_payload is not None, "raw_validation_status": validation.get("raw_validation_status", validation.get("validation_status")), "validation_status": validation.get("validation_status"), "interpretation_mode": validation.get("proposal_interpretation_mode", "strict_validation"), "guardrail_violations": validation.get("violations", [])},
        "score_result": {
            "pws_deterministic": record.get("pws_deterministic"),
            "pws_llm_assisted": record.get("pws_llm_assisted"),
            "pws_llm_assisted_computed": record.get("pws_llm_assisted_computed"),
            "delta_from_deterministic": record.get("pws_llm_assisted_delta_from_deterministic"),
            "deterministic_pws_preserved_unchanged": True,
            "persist_tool": record.get("llm_tool_execution"),
        },
        "privacy_validation": {"minimum_structured_context_only": True, "raw_health_records_sent": False, "raw_activity_records_sent": False, "raw_files_sent": False, "tokens_or_credentials_sent": False},
        "safety_validation": {"medical_diagnosis_generated": False, "injury_prediction_generated": False, "training_recommendation_generated": False, "coaching_message_generated": False},
        "warnings": [
            "LLM-assisted PWS is optional and must never replace deterministic PWS.",
            "The LLM proposed weight deltas only; validation and assisted score calculation were performed locally when applicable.",
        ],
        "ready_for_next_module": ready,
    }
    write_json(artifact_dir / "llm_assisted_pws_quality_report.json", quality)
    lineage = {
        "module_id": MODULE_ID,
        "lineage_version": "llm_assisted_pws_lineage_v1",
        "source_artifacts": [
            {"module_id": "10_compute_pws_components", "artifact_path": "data/pipeline/10_compute_pws_components/pws_components.json", "role": "component_score_source"},
            {"module_id": "11_compute_pws_weights", "artifact_path": "data/pipeline/11_compute_pws_weights/pws_weights.json", "role": "deterministic_weight_source"},
            {"module_id": "11_compute_pws_weights", "artifact_path": "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json", "role": "hard_validation_constraint_source"},
            {"module_id": "12_compute_pws_score", "artifact_path": "data/pipeline/12_compute_pws_score/pws_score.json", "role": "deterministic_score_source"},
        ],
        "llm_boundary": {"prompt_template": "config/llm_weight_adjustment_prompt_v1.json", "structured_context_only": True, "maximum_calls_per_run": 1, "llm_allowed_output": "bounded_weight_delta_proposal_only", "llm_not_allowed_to_compute_authoritative_score": True},
        "assisted_score_transformation": {"formula": "sum(component_score * validated_or_normalized_llm_adjusted_weight for available components)", "computed_locally_after_validation_or_audited_normalization": True, "raw_proposal_preserved": True, "deterministic_score_modified": False},
        "forbidden_action_confirmation": {"deterministic_pws_modified": False, "deterministic_weights_modified": False, "component_scores_modified": False, "raw_health_history_sent_to_llm": False, "medical_diagnosis_generated": False, "injury_prediction_generated": False, "training_prescription_generated": False},
    }
    write_json(artifact_dir / "llm_assisted_pws_lineage.json", lineage)
    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    manifest = {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "policy_version": POLICY_VERSION,
        "prompt_version": PROMPT_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "success" if ready else "failed",
        "domain_status": domain_status,
        "optional_module": True,
        "inputs": [
            "config/llm_assisted_pws_policy_v1.json",
            "config/llm_weight_adjustment_prompt_v1.json",
            "config/llm_policy_v1.json",
            "config/pws_score_policy_v1.json",
            "data/pipeline/10_compute_pws_components/pws_components.json",
            "data/pipeline/11_compute_pws_weights/pws_weights.json",
            "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json",
            "data/pipeline/12_compute_pws_score/pws_score.json",
            "optional: data/local_context/llm_user_goal_context.json",
        ],
        "selection": {"selection_mode": selection_mode, "requested_date": args.date, "selected_date": selected.get("date") if selected else None},
        "llm_execution": {"llm_enabled": bool(args.enable_llm) and not bool(args.dry_run), "dry_run": bool(args.dry_run), "credentials_available": credentials_available, "calls_attempted": llm_calls_attempted, "calls_completed": llm_calls_completed, "maximum_calls_per_run": 1},
        "generated_artifacts": generated,
        "deterministic_pws_modified": False,
        "deterministic_weights_modified": False,
        "llm_adjustment_applied": record.get("llm_adjustment_applied") is True,
        "pws_llm_assisted_computed": record.get("pws_llm_assisted_computed") is True,
        "historical_batch_processing_performed": False,
        "log_file": f"data/pipeline/{MODULE_ID}/run_log.txt",
        "errors_file": f"data/pipeline/{MODULE_ID}/errors.json",
    }
    write_json(artifact_dir / "run_manifest.json", manifest)
    log_lines = [
        f"module_id={MODULE_ID}",
        "optional_module=true",
        f"started_at={started_at}",
        f"policy_version={POLICY_VERSION}",
        f"prompt_version={PROMPT_VERSION}",
        "inputs=data/pipeline/10_compute_pws_components/pws_components.json; data/pipeline/11_compute_pws_weights/pws_weights.json; data/pipeline/12_compute_pws_score/pws_score.json",
        f"selection_mode={selection_mode}",
        f"requested_date={args.date}",
        f"selected_date={selected.get('date') if selected else None}",
        f"eligible={selected is not None and eligible(selected)}",
        f"llm_enabled={bool(args.enable_llm) and not bool(args.dry_run)}",
        f"credentials_available={credentials_available}",
        f"provider={provider.get('provider')}",
        f"model={provider.get('model')}",
        f"llm_calls_attempted={llm_calls_attempted}",
        f"llm_calls_completed={llm_calls_completed}",
        "maximum_one_day_per_run=true",
        "historical_batch_processing_performed=false",
        "minimum_structured_context_only=true",
        "raw_health_records_or_secrets_sent=false",
        f"llm_decision={record.get('llm_response_decision') or 'no_call'}",
        f"validation_status={validation.get('validation_status')}",
        f"guardrail_violations={validation.get('violations', [])}",
        f"pws_llm_assisted_computed={record.get('pws_llm_assisted_computed')}",
        f"delta_from_deterministic={record.get('pws_llm_assisted_delta_from_deterministic')}",
        "pws_deterministic_preserved_unchanged=true",
        "deterministic_weights_preserved_unchanged=true",
        "medical_diagnosis_generated=false",
        "injury_prediction_generated=false",
        "coaching_or_training_recommendation_generated=false",
        f"finished_at={finished_at}",
        f"domain_status={domain_status}",
    ]
    write_text = (artifact_dir / "run_log.txt").write_text
    write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def batch_arguments(args: argparse.Namespace, date: str) -> list[str]:
    argv = ["--date", date]
    if args.enable_llm:
        argv.append("--enable-llm")
    if args.dry_run:
        argv.append("--dry-run")
    return argv


def aggregate_batch_artifacts(
    root: Path,
    started_at: str,
    args: argparse.Namespace,
    selected_dates: list[str],
    runs: list[dict[str, Any]],
) -> int:
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    latest = runs[-1]
    records = [item["main"]["record"] for item in runs]
    request_audits = [item["request"] for item in runs]
    response_audits = [item["response"] for item in runs]
    validation_records = [item["validation"] for item in runs]
    errors = [error for item in runs for error in item["errors"].get("errors", [])]
    calls_attempted = sum(int(item["main"].get("llm_path", {}).get("llm_calls_attempted", 0)) for item in runs)
    calls_completed = sum(int(item["main"].get("llm_path", {}).get("llm_calls_completed", 0)) for item in runs)
    assisted_count = sum(record.get("pws_llm_assisted_computed") is True for record in records)
    accepted_count = sum(record.get("llm_adjustment_applied") is True for record in records)
    normalized_count = sum(record.get("proposal_interpretation_mode") == "permissive_simplex_normalization" for record in records)
    ready = all(item["main"].get("ready_for_next_module") is True for item in runs)
    finished_at = now_iso()
    source_statuses = [item["main"].get("status") for item in runs]
    batch_status = source_statuses[-1]
    if assisted_count == len(records) and normalized_count > 0:
        batch_status = "completed_batch_with_normalized_assisted_scores"
    elif len(set(source_statuses)) > 1 and assisted_count > 0:
        batch_status = "completed_batch_with_partial_assisted_scores"

    main = latest["main"]
    main["status"] = batch_status
    main["execution_scope"] = {
        "call_scope": "one_call_per_eligible_date",
        "maximum_llm_calls_per_eligible_date": 1,
        "maximum_llm_calls_per_run": len(selected_dates),
        "selection_mode": "all_eligible_dates",
        "requested_date": None,
        "selected_dates": selected_dates,
        "selected_date": selected_dates[-1],
        "processed_records_count": len(records),
        "historical_batch_processing_performed": True,
    }
    main["llm_path"].update({
        "llm_called": calls_completed > 0,
        "llm_calls_attempted": calls_attempted,
        "llm_calls_completed": calls_completed,
        "adjustments_accepted_count": accepted_count,
        "assisted_scores_computed_count": assisted_count,
    })
    main["records"] = records
    main["record"] = records[-1]
    main["ready_for_next_module"] = ready
    write_json(artifact_dir / "llm_assisted_pws.json", main)

    request_audit = dict(request_audits[-1])
    request_audit.update({
        "selection_mode": "all_eligible_dates",
        "selected_dates": selected_dates,
        "requests_prepared_count": sum(item.get("llm_request_prepared") is True for item in request_audits),
        "requests_sent_count": sum(item.get("llm_request_sent") is True for item in request_audits),
        "requests": request_audits,
    })
    write_json(artifact_dir / "llm_request_audit.json", request_audit)

    response_audit = dict(response_audits[-1])
    response_audit.update({
        "selection_mode": "all_eligible_dates",
        "selected_dates": selected_dates,
        "responses_received_count": sum(item.get("response_received") is True for item in response_audits),
        "responses": response_audits,
    })
    write_json(artifact_dir / "llm_response_audit.json", response_audit)

    validation_report = dict(validation_records[-1])
    validation_report.update({
        "selection_mode": "all_eligible_dates",
        "selected_dates": selected_dates,
        "records": validation_records,
        "accepted_count": sum(item.get("validation_status") in {"accepted", "accepted_with_normalization_warnings"} for item in validation_records),
        "normalized_with_warnings_count": sum(item.get("validation_status") == "accepted_with_normalization_warnings" for item in validation_records),
        "rejected_count": sum(str(item.get("validation_status", "")).startswith("rejected") for item in validation_records),
    })
    write_json(artifact_dir / "llm_validation_report.json", validation_report)
    conversation_index = {
        "module_id": MODULE_ID,
        "prompt_version": PROMPT_VERSION,
        "selection_mode": "all_eligible_dates",
        "records_count": len(records),
        "entries": [
            {
                "date": record.get("date"),
                "path": f"data/pipeline/{MODULE_ID}/llm_conversations/{record.get('date')}.json",
                "interpretation_mode": record.get("proposal_interpretation_mode"),
                "validation_status": record.get("llm_proposal_validation_status"),
                "guardrail_findings_count": len(record.get("llm_guardrail_violations") or []),
                "pws_llm_assisted_computed": record.get("pws_llm_assisted_computed") is True,
            }
            for record in records
        ],
        "hidden_reasoning_stored": False,
        "private_local_artifact": True,
    }
    write_json(artifact_dir / "llm_conversation_index.json", conversation_index)

    quality = latest["quality"]
    quality["status"] = batch_status
    quality["selection"] = {
        "selection_mode": "all_eligible_dates",
        "requested_date": None,
        "selected_dates": selected_dates,
        "selected_date": selected_dates[-1],
        "eligible_records_count": len(selected_dates),
    }
    quality["execution"].update({
        "llm_calls_attempted": calls_attempted,
        "llm_calls_completed": calls_completed,
        "maximum_llm_calls_per_eligible_date": 1,
        "maximum_llm_calls_per_run": len(selected_dates),
        "historical_batch_processing_performed": True,
    })
    quality["record_results"] = [
        {
            "date": record.get("date"),
            "status": record.get("llm_assisted_status"),
            "validation_status": record.get("llm_proposal_validation_status"),
            "assisted_score_computed": record.get("pws_llm_assisted_computed") is True,
        }
        for record in records
    ]
    quality["assisted_scores_computed_count"] = assisted_count
    quality["normalized_with_warnings_count"] = normalized_count
    quality["ready_for_next_module"] = ready
    write_json(artifact_dir / "llm_assisted_pws_quality_report.json", quality)

    schema = read_json(artifact_dir / "llm_assisted_pws_schema.json")
    schema.update({
        "schema_version": "llm_assisted_pws_schema_v2",
        "processed_records_per_run_maximum": "all_eligible_dates",
        "record_collection_field": "records",
        "latest_record_compatibility_alias": "record",
    })
    write_json(artifact_dir / "llm_assisted_pws_schema.json", schema)

    lineage = latest["lineage"]
    lineage["llm_boundary"].update({
        "call_scope": "one_call_per_eligible_date",
        "maximum_calls_per_eligible_date": 1,
        "maximum_calls_per_run": len(selected_dates),
        "selected_dates": selected_dates,
    })
    lineage["historical_batch_processing_performed"] = True
    write_json(artifact_dir / "llm_assisted_pws_lineage.json", lineage)

    write_json(artifact_dir / "errors.json", {"module_id": MODULE_ID, "errors": errors})
    manifest = latest["manifest"]
    manifest.update({
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": "success" if ready else "failed",
        "domain_status": batch_status,
        "selection": {
            "selection_mode": "all_eligible_dates",
            "requested_date": None,
            "selected_dates": selected_dates,
            "selected_date": selected_dates[-1],
        },
        "llm_execution": {
            **manifest.get("llm_execution", {}),
            "calls_attempted": calls_attempted,
            "calls_completed": calls_completed,
            "maximum_calls_per_eligible_date": 1,
            "maximum_calls_per_run": len(selected_dates),
        },
        "llm_adjustment_applied": accepted_count > 0,
        "pws_llm_assisted_computed": assisted_count > 0,
        "pws_llm_assisted_computed_count": assisted_count,
        "normalized_with_warnings_count": normalized_count,
        "historical_batch_processing_performed": True,
    })
    write_json(artifact_dir / "run_manifest.json", manifest)

    log_lines = [
        f"module_id={MODULE_ID}",
        f"started_at={started_at}",
        f"finished_at={finished_at}",
        f"policy_version={POLICY_VERSION}",
        f"prompt_version={PROMPT_VERSION}",
        "selection_mode=all_eligible_dates",
        f"selected_dates={selected_dates}",
        f"processed_records_count={len(records)}",
        f"llm_calls_attempted={calls_attempted}",
        f"llm_calls_completed={calls_completed}",
        f"assisted_scores_computed_count={assisted_count}",
        f"adjustments_accepted_count={accepted_count}",
        f"normalized_with_warnings_count={normalized_count}",
        "maximum_one_call_per_eligible_date=true",
        "historical_batch_processing_performed=true",
        "minimum_structured_context_only=true",
        "raw_health_records_or_secrets_sent=false",
        "pws_deterministic_preserved_unchanged=true",
        "deterministic_weights_preserved_unchanged=true",
        f"domain_status={batch_status}",
    ]
    (artifact_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return 0 if ready else 1


def run_all_eligible_dates(
    args: argparse.Namespace,
    *,
    injected_llm_client: Any | None,
    root: Path,
) -> int:
    errors: list[dict[str, Any]] = []
    data = load_required(root, errors)
    if data is None:
        return run([], injected_llm_client=injected_llm_client, root=root, _single_date_mode=True)
    eligible_records = sorted(
        (record for record in data.get("pws_score", {}).get("records", []) if eligible(record)),
        key=lambda record: record["date"],
    )
    if not eligible_records:
        passthrough: list[str] = []
        if args.enable_llm:
            passthrough.append("--enable-llm")
        if args.dry_run:
            passthrough.append("--dry-run")
        return run(passthrough, injected_llm_client=injected_llm_client, root=root, _single_date_mode=True)

    started_at = now_iso()
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    runs: list[dict[str, Any]] = []
    for selected in eligible_records:
        run(
            batch_arguments(args, selected["date"]),
            injected_llm_client=injected_llm_client,
            root=root,
            _single_date_mode=True,
        )
        runs.append({
            "main": read_json(artifact_dir / "llm_assisted_pws.json"),
            "request": read_json(artifact_dir / "llm_request_audit.json"),
            "response": read_json(artifact_dir / "llm_response_audit.json"),
            "validation": read_json(artifact_dir / "llm_validation_report.json"),
            "quality": read_json(artifact_dir / "llm_assisted_pws_quality_report.json"),
            "lineage": read_json(artifact_dir / "llm_assisted_pws_lineage.json"),
            "manifest": read_json(artifact_dir / "run_manifest.json"),
            "errors": read_json(artifact_dir / "errors.json"),
        })
    return aggregate_batch_artifacts(root, started_at, args, [record["date"] for record in eligible_records], runs)


def run(
    argv: list[str] | None = None,
    *,
    injected_llm_client: Any | None = None,
    root: Path | None = None,
    _single_date_mode: bool = False,
) -> int:
    args = parse_args(argv)
    started_at = now_iso()
    root = root or root_dir()
    if args.date is None and not _single_date_mode:
        return run_all_eligible_dates(args, injected_llm_client=injected_llm_client, root=root)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None
    response_parse_status = "not_called"
    llm_calls_attempted = 0
    llm_calls_completed = 0
    request_sent = False
    credentials_available = False
    selection_mode = "latest_eligible_date"
    provider = {"provider": None, "model": None, "temperature": 0}
    validation = validate_proposal(None, None, {})
    domain_status = "llm_assisted_module_failed"
    record: dict[str, Any] = {}
    if not validate_date(args.date):
        errors.append({"severity": "error", "code": "DATE_VALUE_INVALID", "message": "--date must use YYYY-MM-DD."})
    data = load_required(root, errors)
    if data is None:
        if any(item.get("code") == "DETERMINISTIC_PWS_NOT_FOUND" for item in errors):
            domain_status = "blocked_missing_deterministic_pws"
        elif any(item.get("code") == "PWS_WEIGHTS_NOT_FOUND" for item in errors):
            domain_status = "blocked_missing_pws_weights"
        elif any(item.get("code") == "PWS_WEIGHT_GUARDRAILS_NOT_FOUND" for item in errors):
            domain_status = "blocked_missing_guardrails"
        else:
            domain_status = "invalid_llm_assisted_policy"
        provider = {}
        record = build_record(selection_mode, None, args, None, validation, domain_status)
        write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, None, None, provider, False, None, response_parse_status, validation, record, errors, 0, 0, False)
        return 1
    provider = provider_config(data.get("llm_policy", {}), data.get("policy", {}))
    if not validate_policy(data, errors):
        domain_status = "invalid_llm_assisted_policy"
    elif not validate_ready(data, errors):
        domain_status = "blocked_inputs_not_ready"
    records = data.get("pws_score", {}).get("records", [])
    pws_records_by_date = records_by_date(records, errors, "pws_score")
    weights_by_date = records_by_date(data.get("weights", {}).get("records", []), errors, "pws_weights")
    _components_by_date = records_by_date(data.get("components", {}).get("records", []), errors, "pws_components")
    if any(item.get("code") == "DUPLICATE_DATE_FOUND" for item in errors):
        domain_status = "blocked_inputs_not_ready"
    if domain_status.startswith("blocked") or domain_status.startswith("invalid"):
        validation = validate_proposal(None, None, data.get("guardrails", {}))
        record = build_record(selection_mode, None, args, None, validation, domain_status)
        write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, None, None, provider, False, None, response_parse_status, validation, record, errors, 0, 0, False)
        return 1
    selection_mode, selected, skip_status, eligible_found = select_record(list(pws_records_by_date.values()), args.date)
    if not eligible_found:
        domain_status = skip_status or "skipped_no_eligible_date"
        if domain_status == "skipped_requested_date_not_found":
            errors.append({"severity": "warning", "code": "REQUESTED_DATE_NOT_FOUND", "date": args.date})
        elif domain_status == "skipped_requested_date_not_eligible":
            errors.append({"severity": "warning", "code": "REQUESTED_DATE_NOT_ELIGIBLE", "date": args.date})
        else:
            errors.append({"severity": "warning", "code": "NO_ELIGIBLE_DATE_FOUND"})
        validation = validate_proposal(None, selected, data.get("guardrails", {}))
        record = build_record(selection_mode, selected, args, None, validation, domain_status)
        write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, selected, None, provider, False, None, response_parse_status, validation, record, errors, 0, 0, False)
        return 0
    context = build_context(root, data["policy"], data["guardrails"], selected, weights_by_date.get(selected["date"]), warnings)
    errors.extend(warnings)
    if args.dry_run or not args.enable_llm:
        domain_status = "skipped_llm_disabled"
        errors.append({"severity": "warning", "code": "LLM_EXECUTION_DISABLED", "message": "LLM request was not sent because --enable-llm was not provided or dry-run was requested."})
        validation = validate_proposal(None, selected, data.get("guardrails", {}))
        record = build_record(selection_mode, selected, args, None, validation, domain_status)
        write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, selected, context, provider, False, None, response_parse_status, validation, record, errors, 0, 0, False)
        return 0
    api_key = os.environ.get(provider.get("api_key_environment_variable", "OPENAI_API_KEY"))
    credentials_available = bool(api_key)
    if not credentials_available:
        domain_status = "skipped_missing_credentials"
        errors.append({"severity": "warning", "code": "LLM_CREDENTIALS_MISSING", "message": "Configured API key environment variable is missing."})
        validation = validate_proposal(None, selected, data.get("guardrails", {}))
        record = build_record(selection_mode, selected, args, None, validation, domain_status)
        write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, selected, context, provider, False, None, response_parse_status, validation, record, errors, 0, 0, False)
        return 0
    try:
        llm_calls_attempted = 1
        client = injected_llm_client or ConfiguredLLMClient(provider["provider"], provider["model"], provider["endpoint"], api_key, int(provider.get("timeout_seconds", 60)))
        result: LLMClientResult = client.complete_json(data["prompt"]["system_instruction"], context, provider.get("temperature", 0))
        request_sent = True
        llm_calls_completed = 1
        response_payload = result.parsed_json
        response_parse_status = "parsed_valid_json" if response_payload is not None else "invalid_json"
        if response_payload is None:
            domain_status = "llm_response_invalid"
            errors.append({"severity": "error", "code": "LLM_RESPONSE_NOT_JSON", "message": result.parse_error or "Response was not JSON."})
            validation = validate_proposal(None, selected, data.get("guardrails", {}))
            record = build_record(selection_mode, selected, args, None, validation, domain_status)
            record["llm_assisted_status"] = "error_llm_no_assisted_score_delivered"
            record["llm_tool_execution"] = {
                "tool_name": "persist_llm_assisted_pws_record",
                "attempted": True,
                "succeeded": False,
                "error": "LLM_RESPONSE_NOT_JSON",
            }
            write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, selected, context, provider, request_sent, None, response_parse_status, validation, record, errors, llm_calls_attempted, llm_calls_completed, credentials_available)
            return 0
    except LLMClientError as exc:
        domain_status = "llm_request_failed"
        errors.append({"severity": "error", "code": "LLM_REQUEST_FAILED", "message": str(exc)})
        validation = validate_proposal(None, selected, data.get("guardrails", {}))
        record = build_record(selection_mode, selected, args, None, validation, domain_status)
        record["llm_assisted_status"] = "error_llm_no_assisted_score_delivered"
        record["llm_tool_execution"] = {
            "tool_name": "persist_llm_assisted_pws_record",
            "attempted": True,
            "succeeded": False,
            "error": "LLM_REQUEST_FAILED",
        }
        write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, selected, context, provider, request_sent, None, response_parse_status, validation, record, errors, llm_calls_attempted, llm_calls_completed, credentials_available)
        return 0
    validation = validate_proposal(response_payload, selected, data.get("guardrails", {}), allowed_decisions_from_prompt(data.get("prompt")))
    normalization_enabled = data.get("policy", {}).get("validation_policy", {}).get("normalization_policy", {}).get("enabled") is True
    if normalization_enabled and validation.get("validation_status") == "rejected_guardrail_violation":
        validation = normalize_guardrail_violating_proposal(validation, selected)
    if validation["validation_status"] == "accepted":
        domain_status = "completed_assisted_score_computed"
    elif validation["validation_status"] == "accepted_with_normalization_warnings":
        domain_status = "completed_assisted_score_computed_with_warnings"
        errors.append({"severity": "warning", "code": "LLM_PROPOSAL_NORMALIZED_WITH_WARNINGS", "date": selected["date"], "violations": validation["violations"]})
    elif validation["validation_status"] == "valid_no_adjustment":
        domain_status = "completed_no_adjustment_proposed"
    elif validation["validation_status"].startswith("rejected_schema"):
        domain_status = "llm_response_invalid"
        errors.append({"severity": "error", "code": "LLM_RESPONSE_SCHEMA_INVALID", "violations": validation["violations"]})
    else:
        domain_status = "completed_proposal_rejected"
        errors.append({"severity": "warning", "code": "LLM_PROPOSAL_REJECTED", "violations": validation["violations"]})
    record = build_record(selection_mode, selected, args, response_payload, validation, domain_status)
    record["llm_called"] = True
    if validation["validation_status"] in {"accepted", "accepted_with_normalization_warnings"}:
        assisted = compute_assisted(selected, validation["validated_llm_adjusted_weights"])
        record.update(assisted)
        record["llm_adjustment_applied"] = True
        normalized_with_warnings = validation["validation_status"] == "accepted_with_normalization_warnings"
        record["llm_assisted_status"] = "accepted_adjustment_applied_with_normalization_warnings" if normalized_with_warnings else "accepted_adjustment_applied"
        record["warnings"] = list(validation.get("violations", [])) if normalized_with_warnings else []
        record["llm_tool_execution"] = {
            "tool_name": "persist_llm_assisted_pws_record",
            "attempted": True,
            "succeeded": True,
            "error": None,
        }
        errors.append({"severity": "info", "code": "ASSISTED_SCORE_COMPUTED", "date": selected["date"], "normalized_with_warnings": normalized_with_warnings})
    elif validation["validation_status"] == "valid_no_adjustment":
        deterministic_weights = selected.get("pws_deterministic_weights") or {}
        validation["validated_llm_adjusted_weights"] = deterministic_weights
        validation["assisted_score_permitted"] = True
        record["validated_llm_adjusted_weights"] = deterministic_weights
        record.update(compute_assisted(selected, deterministic_weights))
        record["pws_llm_assisted_delta_from_deterministic"] = 0.0
        record["llm_adjustment_applied"] = False
        record["llm_assisted_status"] = "no_adjustment_assisted_score_recorded"
        record["llm_tool_execution"] = {
            "tool_name": "persist_llm_assisted_pws_record",
            "attempted": True,
            "succeeded": True,
            "error": None,
        }
        errors.append({"severity": "info", "code": "ASSISTED_SCORE_COMPUTED_NO_ADJUSTMENT", "date": selected["date"]})
    elif domain_status == "llm_response_invalid":
        record["llm_assisted_status"] = "error_llm_no_assisted_score_delivered"
        record["llm_tool_execution"] = {
            "tool_name": "persist_llm_assisted_pws_record",
            "attempted": True,
            "succeeded": False,
            "error": "LLM_RESPONSE_SCHEMA_INVALID",
        }
    elif domain_status == "completed_proposal_rejected":
        record["llm_assisted_status"] = "proposal_rejected"
    write_artifacts(root, started_at, now_iso(), domain_status, args, selection_mode, selected, context, provider, request_sent, response_payload, response_parse_status, validation, record, errors, llm_calls_attempted, llm_calls_completed, credentials_available)
    return 0 if domain_status in READY_STATUSES else 1


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())

