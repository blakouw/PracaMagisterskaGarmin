# 11_compute_pws_weights

This module computes deterministic PWS component weights only. It does not calculate final PWS and does not call an LLM.

The module consumes `data/pipeline/10_compute_pws_components/pws_components.json` and the accompanying schema, quality report and lineage from module 10. Its public policy is `config/pws_weights_policy_v1.json`.

The base weights are LQ 0.20, REC 0.35, CAP 0.15 and VS 0.30 because PWS is designed as a wellness-oriented indicator rather than a reward for activity volume.

`CAP` has the lowest base weight because it is a duration-based performed-capacity proxy. It must not reward excessive activity volume or dominate recovery and vital stability.

## Scope

The module writes auditable weights for the four components:

- `LQ` - Load Quality
- `REC` - Recovery
- `CAP` - Capacity
- `VS` - Vital Stability

It does not recompute components, readiness, ACWR, final PWS, LLM-assisted PWS, coach output, dashboard payload, API or UI.

## Missing Components

Missing component scores remain null. A zero effective weight for an unavailable component means exclusion from the weighted calculation, not zero component quality.

The module records component availability, missing components and the reason a date is or is not eligible for a future final PWS calculation.

## Eligibility

`weights_ready_for_final_pws` is true only when:

- at least 3 components are available,
- available base weight sum is at least `0.65`,
- at least one of `REC` or `VS` is available.

## Weighting

Base weights are first renormalized over available components only. For eligible days the module then applies:

- reliability factors for fallback or partial metadata,
- urgency factors for low component scores below target `80`,
- movement limits of `0.07` per component and `0.20` total absolute movement,
- overlap controls for `LQ/REC` and `REC/VS` when all four components are available.

Deterministic weights may be moderately adjusted by reliability, urgency and overlap controls, but all changes are bounded and auditable.

## LLM Guardrails

A future optional LLM stage may only propose small validated weight shifts within published guardrails. The deterministic path must remain available and unchanged.

Module 11 writes `pws_weight_guardrails.json` but does not call an LLM and does not apply any LLM adjustment.

## Outputs

- `pws_weights.json`
- `pws_weights.csv`
- optional `pws_weights.parquet`
- `pws_weights_schema.json`
- `pws_weights_quality_report.json`
- `pws_weights_lineage.json`
- `pws_weight_guardrails.json`
- `run_manifest.json`
- `run_log.txt`
- `errors.json`

Generated artifacts contain private derived health and training information and must not be committed to version control.

The module does not generate medical diagnoses, injury predictions or training prescriptions, and it has no runtime dependency on any previous project.

## Run

```bat
pipeline\11_compute_pws_weights\run.bat
```

## Tests

```bat
pytest tests/11_compute_pws_weights
```

## Visualization

```bat
visualization\11_compute_pws_weights\run_visualization.bat
```
