# =====================================
# WORKFLOW ORCHESTRATOR SERVICE
# =====================================
FROM mcp-base AS base

ENV SERVICE_NAME=workflow-orchestrator \
    SERVICE_PORT=8004

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0\ncelery>=5.2.0\nredis>=4.0.0\nrequests>=2.28.0" > requirements.txt; \
    fi && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base as workflow-orchestrator

WORKDIR /app

USER root

# Copy dependencies
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy only required source components
COPY --chown=mcp:mcp src/common/ ./src/common/
COPY --chown=mcp:mcp src/workflow_orchestrator/ ./src/workflow_orchestrator/
COPY --chown=mcp:mcp scripts/start_workflow_orchestrator.py ./start.py
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py

# Ensure correct permissions
RUN mkdir -p /app/logs && chown -R mcp:mcp /app

# Run as non-root user
USER mcp

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=workflow-orchestrator --port=8004

EXPOSE 8004

CMD ["python", "start.py"]
