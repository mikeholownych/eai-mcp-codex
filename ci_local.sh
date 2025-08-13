#!/usr/bin/env bash
set -euo pipefail
export TESTING_MODE=true
export OTEL_SDK_DISABLED=true
export JAEGER_ENABLED=false
export OTLP_ENABLED=false

python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null
pip install ruff mypy pip-audit >/dev/null
(cd cli && npm ci)

echo "Typecheck..."
mypy .
npm run build --prefix cli

echo "Lint..."
ruff check .
npm run lint --prefix cli

echo "Tests..."
make test

echo "Build containers..."
docker build -t mcp-base -f docker/base.Dockerfile .
docker build -t mcp-model-router -f docker/model-router.Dockerfile .

echo "Security scans..."
pip-audit -r requirements.txt --strict
npm audit --omit=dev --audit-level=high --prefix cli || true

echo "Helm lint..."
helm lint ./helm/mcp-services

echo "All checks passed."
