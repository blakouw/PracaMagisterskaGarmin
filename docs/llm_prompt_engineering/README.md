# LLM Prompt Engineering

This directory documents the startup prompts and audit-log shape for the local
LLM-assisted parts of the project.

It is intentionally separate from runtime pipeline configuration. The currently
executed PWS-assisted prompt remains `config/llm_weight_adjustment_prompt_v1.json`.
Files here are prompt-engineering reference artifacts and templates for future
review, thesis documentation and controlled implementation work.

## Prompt Split

There are two different prompt families:

- `prompts/pws_assisted_startup_prompt_v1.md` describes the constrained prompt
  for optional LLM-assisted PWS weight influence. It must not replace the
  deterministic PWS path.
- `prompts/user_conversation_startup_prompt_v1.md` describes a future dashboard
  conversation prompt. It may explain already computed dashboard data through
  local read-only API tools, but it must not calculate metrics, run the pipeline,
  sync Garmin data or generate coaching.

## Tool Boundary

The PWS-assisted prompt has no direct filesystem, Garmin, pipeline, API or UI
tool access. It receives a prepared structured context from module
`13_validate_llm_weight_influence` and returns a strict JSON proposal.

The future user-conversation prompt may use read-only dashboard API tools only,
such as `GET /api/v1/dashboard/current-state` and
`GET /api/v1/dashboard/time-series`.

## Logging Boundary

The logs in `logs/` are audit logs and templates. They record prompt versions,
allowed tools, selected data boundaries, concise rationale summaries and local
validation results.

They do not store hidden chain-of-thought. The project should log only
observable reasoning summaries, tool choices, validation checks and final
decisions. This keeps the system auditable without exposing private internal
model reasoning.

## Privacy

Do not copy raw Garmin data, tokens, credentials, raw LLM responses or private
health records into this directory. Runtime LLM artifacts under
`data/pipeline/13_validate_llm_weight_influence/` are private runtime artifacts
and are ignored by Git.

