# Project Context

- **REPO_NAME:** rag-agent
- **RUNTIMES:** Python 3.11, Node.js 18
- **PACKAGE_MANAGERS:** poetry, npm
- **BUILD_CMD:** `docker-compose build`
- **TEST_CMD:** `pytest && npm test --prefix cli`
- **TYPECHECK_CMD:** `mypy . && npm run build --prefix cli`
- **LINT_CMD:** `ruff check . && npm run lint --prefix cli`
- **ENTRYPOINTS:** `chain.py`, `embed_corpus.py`, `retrieve_context.py`, `cli/bin/rag-agent-cli`, various services in `docker/`
- **ENV_FILES:** None found in the provided file listing.
- **INFRA:** docker-compose, Docker, Kubernetes, Helm
- **PROD_TARGET:** container
- **SLO:** N/A
