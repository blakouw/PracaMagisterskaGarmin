# Garmin Tokenstore

This directory is reserved for local Garmin tokenstore files owned by this new project.

Expected local files when optional API ingest is enabled:

- `oauth1_token.json` with `oauth_token` and `oauth_token_secret`
- `oauth2_token.json` with `access_token` and `refresh_token`

Do not commit real token files. The optional module reads these files only from this local secrets directory and never writes token values to pipeline artifacts or logs.

A tokenstore from an older project may be copied here once as a local manual/bootstrap step, but the new project must not depend on that older project at runtime.
