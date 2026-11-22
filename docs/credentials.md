# Local Secrets

This directory is reserved for local, unversioned secrets and machine-specific sensitive configuration.

Examples include Garmin token stores, API tokens, future LLM API keys, local `.env` files, OAuth material and other confidential settings required only on this workstation.

Do not commit real secrets to the repository. Future modules may copy secrets here one time from an older project, but the new pipeline must never depend on the old project at runtime.
