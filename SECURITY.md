## Security Policy

- No plaintext secrets in the repository. Do not commit `.env`, `.env.*`, or any secrets. Use a secret manager or local untracked files.
- Rotate any credentials suspected to be exposed immediately.
- CI runs:
  - gitleaks (or equivalent) for secret scanning
  - Trivy on built images (critical/high fail the build)
  - pip-audit for Python deps
  - npm audit (fail on high/critical, allow temporary exceptions with justification)

### Secrets Management
- Local development: copy `.env.example` to `.env` and fill values.
- Production: use Vault or platform secrets; inject via environment.
- Never log secrets. Structured logs must redact sensitive fields.

### Dependency and Supply Chain
- Pin base images to slim variants; prefer digest pinning where possible.
- Update dependencies regularly; address critical/high promptly.

### Reporting
- Use private channels to report vulnerabilities; provide steps to reproduce and impacted versions.
