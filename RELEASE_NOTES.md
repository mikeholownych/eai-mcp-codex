# Release Notes

## Hardening and CI Enablement
- Added CI pipeline enforcing typecheck (mypy), lint (ruff + eslint), tests, container build, and security scans (pip-audit, npm audit, Trivy).
- Introduced `ci_local.sh` to mirror CI locally.
- Added `mypy.ini` and `.ruff.toml` to standardize static analysis.
- Tests: added `psycopg2-binary` to unblock DB connectivity test.
- Security: policy documented in `SECURITY.md`. Secrets must not be committed.
- Health: Standardized `/healthz` and `/readyz` endpoints across services.
- Helm: chart now exposes configurable probes; lint wired in CI.

## Migration Notes
- If you previously relied on `.env.secrets` in repo, move to untracked secrets and rotate keys.
- Use `/healthz` (liveness) and `/readyz` (readiness) endpoints going forward.
