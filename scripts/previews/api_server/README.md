# Local API Server Visualization

This helper previews the startup validation and API contract artifacts produced by `17_local_api_server`.

It does not start the API server, run the pipeline, call an LLM, implement a UI, or print private dashboard payload records.

Run after validating the module:

```bat
pipeline\17_local_api_server\run.bat --validate-only
visualization\17_local_api_server\run_visualization.bat
```

Optional flags:

- `--show-endpoints`
- `--show-runtime`
- `--show-validation`
- `--show-lineage`

