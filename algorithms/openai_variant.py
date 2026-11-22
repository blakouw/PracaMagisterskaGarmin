from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import main as bounded_pws
from llm_client import LLMClientError, LLMClientResult
from openai_client import OpenAIResponsesClient


MODULE_ID = bounded_pws.MODULE_ID
VARIANT_ID = "openai_external"
POLICY_VERSION = "openai_pws_policy_v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optional external OpenAI PWS comparison.")
    parser.add_argument("--enable-openai", action="store_true", help="Permit requests to the configured OpenAI endpoint.")
    parser.add_argument("--date", help="Analyze one eligible date instead of all eligible dates.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and write audit metadata without a network call.")
    parser.add_argument("--force", action="store_true", help="Ignore cached records for unchanged contexts.")
    return parser.parse_args(argv)


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def provider_config(root: Path) -> dict[str, Any]:
    policy = read_json(root / "config" / "openai_pws_policy_v1.json")
    if policy.get("policy_version") != POLICY_VERSION:
        raise ValueError("Invalid OpenAI PWS policy version")
    model = os.getenv(str(policy.get("model_environment_variable", "OPENAI_PWS_MODEL"))) or policy.get("model")
    endpoint = policy.get("endpoint")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("OpenAI model is not configured")
    if endpoint != "https://api.openai.com/v1/responses":
        raise ValueError("OpenAI PWS endpoint must be the approved HTTPS Responses API endpoint")
    return {**policy, "model": model}


def compatible_result(result: Any) -> LLMClientResult:
    if isinstance(result, LLMClientResult):
        return result
    if isinstance(result, dict):
        raw = json.dumps(result, ensure_ascii=False)
        return LLMClientResult(raw_text=raw, parsed_json=result)
    raise LLMClientError("Injected OpenAI client returned an unsupported result")


def call_client(
    client: Any,
    system_instruction: str,
    context: dict[str, Any],
    response_schema: dict[str, Any],
) -> LLMClientResult:
    try:
        result = client.complete_json(system_instruction, context, response_schema)
    except TypeError:
        result = client.complete_json(system_instruction, context)
    return compatible_result(result)


def cached_records(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    try:
        payload = read_json(path)
    except (json.JSONDecodeError, OSError):
        return {}
    records = payload.get("records", []) if isinstance(payload, dict) else []
    return {
        record["date"]: record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("date"), str)
    }


def base_record(date: str, score_record: dict[str, Any], config: dict[str, Any], context_hash: str) -> dict[str, Any]:
    return {
        "date": date,
        "variant_id": VARIANT_ID,
        "provider": "openai",
        "model": config["model"],
        "prompt_version": bounded_pws.PROMPT_VERSION,
        "input_context_hash": context_hash,
        "pws_deterministic": score_record.get("pws_deterministic"),
        "pws_deterministic_weights": score_record.get("pws_deterministic_weights"),
        "pws_llm_assisted": None,
        "pws_llm_assisted_computed": False,
        "pws_llm_assisted_delta_from_deterministic": None,
        "pws_openai_assisted": None,
        "pws_openai_assisted_computed": False,
        "llm_called": False,
        "llm_response_decision": None,
        "llm_reason_summary": None,
        "llm_proposed_weight_deltas": None,
        "llm_effective_weight_deltas": None,
        "validated_llm_adjusted_weights": None,
        "llm_guardrail_violations": [],
        "proposal_interpretation_mode": None,
        "llm_assisted_status": "pending",
    }


def apply_validation(record: dict[str, Any], response: dict[str, Any], validation: dict[str, Any], score_record: dict[str, Any]) -> None:
    record["llm_response_decision"] = response.get("decision")
    record["llm_reason_summary"] = response.get("reason_summary")
    record["llm_proposed_weight_deltas"] = validation.get("proposed_weight_deltas")
    record["llm_guardrail_violations"] = validation.get("violations") or []
    record["validated_llm_adjusted_weights"] = validation.get("validated_llm_adjusted_weights")
    record["llm_effective_weight_deltas"] = validation.get("effective_weight_deltas_after_normalization")
    record["proposal_interpretation_mode"] = validation.get("proposal_interpretation_mode")

    adjusted = validation.get("validated_llm_adjusted_weights")
    if validation.get("assisted_score_permitted") is not True or not isinstance(adjusted, dict):
        record["llm_assisted_status"] = "proposal_rejected"
        return

    assisted = bounded_pws.compute_assisted(score_record, adjusted)
    record.update(assisted)
    record["pws_openai_assisted"] = assisted["pws_llm_assisted"]
    record["pws_openai_assisted_computed"] = True
    record["llm_adjustment_applied"] = True
    record["llm_tool_execution"] = {
        "tool_name": "persist_openai_assisted_pws_record",
        "attempted": True,
        "succeeded": True,
        "error": None,
    }
    record["llm_assisted_status"] = (
        "accepted_adjustment_applied_with_normalization_warnings"
        if validation.get("proposal_interpretation_mode") == "permissive_simplex_normalization"
        else "accepted_adjustment_applied"
    )


def write_outputs(
    root: Path,
    config: dict[str, Any],
    records: list[dict[str, Any]],
    conversations: dict[str, dict[str, Any]],
    started_at: str,
    errors: list[dict[str, Any]],
    execution_mode: str,
) -> None:
    artifact_dir = root / "data" / "pipeline" / MODULE_ID
    finished_at = now_iso()
    computed_count = sum(record.get("pws_openai_assisted_computed") is True for record in records)
    called_count = sum(record.get("llm_called") is True for record in records)
    cached_count = sum(record.get("cache_hit") is True for record in records)
    status = (
        "completed_openai_assisted_scores"
        if computed_count == len(records) and records
        else "completed_openai_assisted_scores_partial"
        if computed_count
        else "skipped_openai_not_enabled"
        if execution_mode in {"disabled", "dry_run"}
        else "openai_assisted_scores_unavailable"
    )
    payload = {
        "module_id": MODULE_ID,
        "variant_id": VARIANT_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "provider": "openai",
        "model": config.get("model"),
        "records": records,
        "record": records[-1] if records else None,
        "records_count": len(records),
        "computed_count": computed_count,
        "ready_for_next_module": True,
        "must_not_replace_primary_score": True,
        "must_not_replace_local_llm_variant": True,
    }
    write_json(artifact_dir / "openai_assisted_pws.json", payload)
    for date, conversation in conversations.items():
        write_json(artifact_dir / "openai_conversations" / f"{date}.json", conversation)
    write_json(
        artifact_dir / "openai_conversation_index.json",
        {
            "module_id": MODULE_ID,
            "variant_id": VARIANT_ID,
            "provider": "openai",
            "model": config.get("model"),
            "records": [
                {
                    "date": record.get("date"),
                    "path": f"data/pipeline/{MODULE_ID}/openai_conversations/{record.get('date')}.json",
                    "computed": record.get("pws_openai_assisted_computed") is True,
                    "cache_hit": record.get("cache_hit") is True,
                }
                for record in records
            ],
        },
    )
    quality = {
        "module_id": MODULE_ID,
        "variant_id": VARIANT_ID,
        "policy_version": POLICY_VERSION,
        "status": status,
        "provider": "openai",
        "model": config.get("model"),
        "records_count": len(records),
        "assisted_scores_computed_count": computed_count,
        "llm_calls_completed": called_count,
        "cache_hits": cached_count,
        "same_context_as_local_llm": True,
        "same_guardrails_as_local_llm": True,
        "scores_calculated_locally": True,
        "raw_private_data_sent": False,
        "credentials_logged": False,
        "ready_for_next_module": True,
    }
    write_json(artifact_dir / "openai_assisted_pws_quality_report.json", quality)
    write_json(artifact_dir / "openai_errors.json", {"module_id": MODULE_ID, "variant_id": VARIANT_ID, "errors": errors})
    write_json(
        artifact_dir / "openai_run_manifest.json",
        {
            "module_id": MODULE_ID,
            "variant_id": VARIANT_ID,
            "policy_version": POLICY_VERSION,
            "started_at": started_at,
            "finished_at": finished_at,
            "execution_mode": execution_mode,
            "execution_status": "success",
            "domain_status": status,
            "provider": "openai",
            "model": config.get("model"),
            "generated_artifacts": [
                f"data/pipeline/{MODULE_ID}/openai_assisted_pws.json",
                f"data/pipeline/{MODULE_ID}/openai_assisted_pws_quality_report.json",
                f"data/pipeline/{MODULE_ID}/openai_conversation_index.json",
                f"data/pipeline/{MODULE_ID}/openai_run_manifest.json",
                f"data/pipeline/{MODULE_ID}/openai_errors.json",
            ],
            "deterministic_pws_modified": False,
            "local_llm_variant_modified": False,
        },
    )


def run(
    argv: list[str] | None = None,
    *,
    root: Path | None = None,
    injected_client: Any | None = None,
) -> int:
    args = parse_args(argv)
    root = root or bounded_pws.root_dir()
    started_at = now_iso()
    errors: list[dict[str, Any]] = []
    try:
        config = provider_config(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        config = {"model": None}
        errors.append({"severity": "error", "code": "OPENAI_PWS_POLICY_INVALID", "message": str(exc)})
        write_outputs(root, config, [], {}, started_at, errors, "invalid_policy")
        return 1

    data = bounded_pws.load_required(root, errors)
    if data is None or not bounded_pws.validate_policy(data, errors) or not bounded_pws.validate_ready(data, errors):
        write_outputs(root, config, [], {}, started_at, errors, "blocked_inputs")
        return 1

    scores = [record for record in data["pws_score"].get("records", []) if bounded_pws.eligible(record)]
    scores.sort(key=lambda item: item["date"])
    if args.date:
        scores = [record for record in scores if record.get("date") == args.date]
    weights_by_date = bounded_pws.records_by_date(data["weights"].get("records", []), errors, "pws_weights")
    artifact_path = root / "data" / "pipeline" / MODULE_ID / "openai_assisted_pws.json"
    cached = cached_records(artifact_path)
    records: list[dict[str, Any]] = []
    conversations: dict[str, dict[str, Any]] = {}

    enabled = args.enable_openai and not args.dry_run
    key_name = str(config.get("api_key_environment_variable", "OPENAI_API_KEY"))
    api_key = os.getenv(key_name, "")
    execution_mode = "enabled" if enabled else "dry_run" if args.dry_run else "disabled"
    if enabled and not api_key and injected_client is None:
        execution_mode = "missing_credentials"
        errors.append({"severity": "warning", "code": "OPENAI_API_KEY_MISSING", "message": f"{key_name} is not configured."})

    client = injected_client if enabled else None
    if enabled and client is None and api_key:
        client = OpenAIResponsesClient(
            model=config["model"],
            endpoint=config["endpoint"],
            api_key=api_key,
            timeout_seconds=int(config.get("timeout_seconds", 90)),
        )

    prompt = data["prompt"]
    system_instruction = prompt["system_instruction"]
    response_schema = prompt["required_response_schema"]
    allowed_decisions = bounded_pws.allowed_decisions_from_prompt(prompt)
    for score_record in scores:
        date = score_record["date"]
        warnings: list[dict[str, Any]] = []
        context = bounded_pws.build_context(
            root,
            data["policy"],
            data["guardrails"],
            score_record,
            weights_by_date.get(date),
            warnings,
        )
        context_hash = canonical_hash(
            {
                "context": context,
                "prompt_version": bounded_pws.PROMPT_VERSION,
                "model": config["model"],
                "provider": "openai",
            }
        )
        old = cached.get(date)
        if (
            not args.force
            and isinstance(old, dict)
            and old.get("input_context_hash") == context_hash
            and old.get("model") == config["model"]
            and old.get("pws_openai_assisted_computed") is True
        ):
            cached_record = dict(old)
            cached_record["cache_hit"] = True
            records.append(cached_record)
            continue

        record = base_record(date, score_record, config, context_hash)
        record["cache_hit"] = False
        conversation = {
            "module_id": MODULE_ID,
            "variant_id": VARIANT_ID,
            "date": date,
            "provider": "openai",
            "model": config["model"],
            "prompt_version": bounded_pws.PROMPT_VERSION,
            "system_instruction": system_instruction,
            "structured_context": context,
            "context_fields": sorted(context),
            "raw_private_data_sent": False,
            "hidden_reasoning_requested_or_stored": False,
            "request_sent": False,
            "parsed_response": None,
            "validation": None,
            "warnings": warnings,
        }
        if client is None:
            record["llm_assisted_status"] = "skipped_openai_not_available"
            conversations[date] = conversation
            records.append(record)
            continue

        try:
            result = call_client(client, system_instruction, context, response_schema)
            record["llm_called"] = True
            conversation["request_sent"] = True
            conversation["response_parse_error"] = result.parse_error
            conversation["parsed_response"] = result.parsed_json
            if result.parsed_json is None:
                record["llm_assisted_status"] = "llm_response_invalid"
                errors.append({"severity": "warning", "code": "OPENAI_RESPONSE_INVALID_JSON", "date": date})
            else:
                validation = bounded_pws.validate_proposal(
                    result.parsed_json,
                    score_record,
                    data["guardrails"],
                    allowed_decisions,
                )
                if validation.get("validation_status") == "rejected_guardrail_violation":
                    validation = bounded_pws.normalize_guardrail_violating_proposal(validation, score_record)
                apply_validation(record, result.parsed_json, validation, score_record)
                conversation["validation"] = validation
        except LLMClientError as exc:
            record["llm_called"] = True
            record["llm_assisted_status"] = "llm_request_failed"
            errors.append({"severity": "warning", "code": "OPENAI_REQUEST_FAILED", "date": date, "message": str(exc)})
            conversation["request_sent"] = True
            conversation["request_error"] = str(exc)
        conversations[date] = conversation
        records.append(record)

    if args.date:
        selected_dates = {record.get("date") for record in records}
        records.extend(
            dict(record)
            for date, record in cached.items()
            if date not in selected_dates
        )
        records.sort(key=lambda item: str(item.get("date", "")))

    write_outputs(root, config, records, conversations, started_at, errors, execution_mode)
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
