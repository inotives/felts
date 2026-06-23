# Environment-specific Settings Files

Felts uses repo-level environment files under `settings/` instead of one root `.env`: `settings/.env.local`, `settings/.env.dev`, and `settings/.env.prod`.

`config.yaml` remains the home for safe non-secret project defaults, while `settings/.env.*` files hold environment-specific runtime values and secrets. Missing `FELTS_ENV` defaults to `local`, which loads `settings/.env.local`; dev/staging and production require explicit `FELTS_ENV` selection.

This keeps local Docker operation simple while leaving room for dev and production deployment settings without changing code. Felts does not adopt Prefect Blocks or an external secrets manager in Phase 06 because the current operating target is local Docker plus GitHub Actions fast CI, not a persistent cloud deployment.
