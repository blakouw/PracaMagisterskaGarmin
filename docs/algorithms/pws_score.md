# 12_compute_pws_score

This module computes the final deterministic Personal Wellness Score from existing PWS component scores and validated deterministic effective weights only.

The deterministic score is the primary auditable PWS path. This module does not call an LLM and does not calculate an LLM-assisted PWS variant.

Missing component scores remain null and are never replaced with zero. A score computed from partial eligible coverage must explicitly disclose that limitation.

PWS is a heuristic decision-support indicator and is not a medical diagnosis, injury prediction or professional training prescription.

## Inputs

- `data/pipeline/10_compute_pws_components/pws_components.json`
- `data/pipeline/11_compute_pws_weights/pws_weights.json`
- `data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json`
- `config/pws_score_policy_v1.json`

## Formula

`pws_deterministic = sum(component_score * deterministic_effective_weight)`

Weights come only from `deterministic_effective_weights` produced by module 11. The module validates these weights, but never recomputes or modifies them.

## Coverage

- `full`: all four components are available.
- `partial_eligible`: module 11 marked the date ready, but at least one component is missing.
- `insufficient`: module 11 did not mark the date ready; no final score is computed.

## Labels

- `low` / `niski`: `< 40`
- `reduced` / `obnizony`: `40–<60`
- `balanced` / `stabilny`: `60–<80`
- `strong` / `wysoki`: `80–100`
- `insufficient_data` when no deterministic score exists.

## Outputs

- `pws_score.json`
- `pws_score.csv`
- optional `pws_score.parquet`
- `pws_score_schema.json`
- `pws_score_quality_report.json`
- `pws_score_lineage.json`
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

Generated artifacts contain private derived health and training data and must not be committed to version control.

## Run

```bat
pipeline\12_compute_pws_score\run.bat
```

## Tests

```bat
py -m pytest tests\12_compute_pws_score
```

## Visualization

```bat
visualization\12_compute_pws_score\run_visualization.bat
```
