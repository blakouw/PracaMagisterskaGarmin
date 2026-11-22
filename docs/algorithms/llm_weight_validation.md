# 13_validate_llm_weight_influence

This optional module requests one bounded LLM weight-adjustment proposal for every eligible date in the available sample. Dates are processed independently in ascending order, and each proposal is validated separately.

The deterministic PWS path remains primary, unchanged and fully auditable. An LLM-assisted score is computed separately only after a proposed weight adjustment passes deterministic guardrail validation.

The LLM may propose small weight deltas only. It may not alter component scores, invent missing data, assign weight to unavailable components, bypass guardrails or calculate an authoritative final score.

Only the minimum structured component and weight context for the current date may be provided to the LLM. The full private history is never sent in one request. Raw health records, raw activity files, tokens and credentials must never be sent.

This module does not generate medical diagnoses, injury predictions, coaching messages or training prescriptions.

## Purpose

The module reads deterministic PWS outputs from module 12, deterministic weights and guardrails from module 11, and component scores from module 10. It optionally asks an LLM for one structured proposal to redistribute existing component weights for each eligible date. Every proposal remains advisory and deterministic PWS remains unchanged.

## Inputs

- `config/llm_assisted_pws_policy_v1.json`
- `config/llm_weight_adjustment_prompt_v1.json`
- `config/llm_policy_v1.json`
- `config/pws_score_policy_v1.json`
- `data/pipeline/10_compute_pws_components/pws_components.json`
- `data/pipeline/11_compute_pws_weights/pws_weights.json`
- `data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json`
- `data/pipeline/12_compute_pws_score/pws_score.json`
- optional local user goal context at `data/local_context/llm_user_goal_context.json`

## Date Selection

Use `--date YYYY-MM-DD` to analyze one explicit date. Without `--date`, the module processes all records with `pws_deterministic_computed = true` and `llm_adjustment_eligible = true` in ascending date order.

LLM execution is disabled unless `--enable-llm` is provided. `--dry-run` validates inputs and prepares the request audit without sending a request.

## Validation And Normalization

Every response is validated against the standard guardrails:

- maximum absolute delta per component: `0.20`
- maximum total positive shift: `0.20`
- maximum total absolute delta: `0.40`
- delta sum must equal `0`
- no negative resulting weights
- no weight change for unavailable components
- overlap controls are reapplied for full component coverage

Schema-invalid, nonnumeric or incomplete responses remain errors because no meaningful weight vector can be derived from them. A schema-valid numeric proposal outside the standard limits is not discarded: its raw deltas and all findings are preserved, then the proposed target weights are deterministically projected to a nonnegative unit-sum vector over available components. The assisted score is calculated from those effective weights and is marked as normalized with warnings. Deterministic weights and deterministic PWS are never changed.

`no_adjustment` remains a valid explicit model decision and records a comparison equal to deterministic PWS. The default full-sample run creates one output record for every eligible date. Dates without an eligible deterministic base remain explicit unavailable dates rather than invented scores.

## Per-Date LLM Audit

Each attempted date has a separate JSON log under `data/pipeline/13_validate_llm_weight_influence/llm_conversations/<date>.json`. The index is `llm_conversation_index.json`. A log contains the startup prompt, structured context sent to the local model, parsed response, explicit `reason_summary`, raw and final validation status, findings, normalization details, effective weights and both scores. Hidden model reasoning is neither requested nor stored.

## Outputs

The module writes `llm_assisted_pws.json`, schema, quality report, lineage, request/response audits, validation report, per-date conversation logs and index, manifest, log and errors under `data/pipeline/13_validate_llm_weight_influence/`.

## Commands

Dry run:

```bat
pipeline\13_validate_llm_weight_influence\run.bat --dry-run
```

Real LLM for all eligible dates:

```bat
pipeline\13_validate_llm_weight_influence\run.bat --enable-llm
```

Real LLM for an explicit date:

```bat
pipeline\13_validate_llm_weight_influence\run.bat --enable-llm --date 2026-05-22
```

Tests:

```bat
py -m pytest tests\00_project_contract tests\01_find_input_workbook tests\02_read_xlsx_workbook tests\03_trim_workbook tests\04_garmin_activity_ingest tests\05_normalize_daily_records tests\06_normalize_activities tests\07_build_daily_features tests\08_compute_load_metrics tests\09_compute_readiness tests\10_compute_pws_components tests\11_compute_pws_weights tests\12_compute_pws_score tests\13_validate_llm_weight_influence
```

Visualization:

```bat
visualization\13_validate_llm_weight_influence\run_visualization.bat
```

Artifacts contain private derived wellness and LLM interaction data and are ignored by Git.

## Optional OpenAI Comparison

The OpenAI path is a second optional comparison provider inside this module. It receives the same bounded per-date structured context as the local model and its proposal passes through the same local schema validation, guardrails and deterministic score calculation. It cannot replace deterministic PWS or the local LLM result.

The external request is opt-in and uses the Responses API with strict structured output. Set `OPENAI_API_KEY` only in the process environment; it is never written to artifacts. The model defaults to the value in `config/openai_pws_policy_v1.json` and can be overridden with `OPENAI_PWS_MODEL`.

Validate without a network request:

```bat
pipeline\13_validate_llm_weight_influence\run_openai.bat --dry-run
```

Run OpenAI for all eligible dates:

```bat
pipeline\13_validate_llm_weight_influence\run_openai.bat --enable-openai
```

Run one date without discarding cached history:

```bat
pipeline\13_validate_llm_weight_influence\run_openai.bat --enable-openai --date 2026-05-22
```

The external artifacts are `openai_assisted_pws.json`, `openai_assisted_pws_quality_report.json`, `openai_conversation_index.json` and per-date files under `openai_conversations/`. Audit files contain the bounded prompt context, parsed answer and validation result, but not hidden reasoning, credentials or raw source records.
