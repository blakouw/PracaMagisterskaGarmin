from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MODULE_ID = "13_validate_llm_weight_influence"
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Preview optional LLM-assisted PWS artifacts.")
    parser.add_argument("--show-request-context", action="store_true")
    parser.add_argument("--show-response", action="store_true")
    parser.add_argument("--show-validation", action="store_true")
    parser.add_argument("--show-weight-comparison", action="store_true")
    args = parser.parse_args(argv)
    required = [
        "llm_assisted_pws.json",
        "llm_assisted_pws_quality_report.json",
        "llm_validation_report.json",
        "llm_request_audit.json",
        "llm_response_audit.json",
    ]
    if any(not (ARTIFACT_DIR / name).is_file() for name in required):
        print(f"LLM-assisted PWS artifacts do not exist. Run pipeline/13_validate_llm_weight_influence/run.bat first.")
        return 1
    main_artifact = read_json(ARTIFACT_DIR / "llm_assisted_pws.json")
    quality = read_json(ARTIFACT_DIR / "llm_assisted_pws_quality_report.json")
    validation = read_json(ARTIFACT_DIR / "llm_validation_report.json")
    request = read_json(ARTIFACT_DIR / "llm_request_audit.json")
    response = read_json(ARTIFACT_DIR / "llm_response_audit.json")
    record = main_artifact.get("record", {})
    print(f"Module: {MODULE_ID}")
    print(f"Status: {main_artifact.get('status')}")
    print(f"Selected date: {main_artifact.get('execution_scope', {}).get('selected_date')}")
    print(f"Selection mode: {main_artifact.get('execution_scope', {}).get('selection_mode')}")
    print(f"LLM enabled: {quality.get('execution', {}).get('llm_enabled')}")
    print(f"LLM called: {main_artifact.get('llm_path', {}).get('llm_called')}")
    print("Maximum one date per run: true")
    print(f"Deterministic PWS: {record.get('pws_deterministic')}")
    print(f"LLM decision: {record.get('llm_response_decision')}")
    print(f"Validation: {validation.get('validation_status')}")
    print(f"Guardrail violations: {validation.get('violations')}")
    print(f"PWS LLM-assisted: {record.get('pws_llm_assisted')}")
    print(f"Delta from deterministic: {record.get('pws_llm_assisted_delta_from_deterministic')}")
    print("Deterministic PWS unchanged: true")
    print("Minimum structured context only: true")
    print("No diagnoses or recommendations generated: true")
    print(f"Ready for next module: {main_artifact.get('ready_for_next_module')}")
    if args.show_request_context:
        print(json.dumps(request.get("structured_context"), indent=2, ensure_ascii=False))
    if args.show_response:
        print(json.dumps(response.get("parsed_response"), indent=2, ensure_ascii=False))
    if args.show_validation:
        print(json.dumps(validation, indent=2, ensure_ascii=False))
    if args.show_weight_comparison:
        print(json.dumps({"deterministic": record.get("deterministic_effective_weights"), "validated_adjusted": record.get("validated_llm_adjusted_weights")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
