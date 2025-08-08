# ---------- Base Stage ----------
FROM mcp-base as base

ENV SERVICE_NAME=agent-pool \
    SERVICE_PORT=8011

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0" > requirements.txt; \
    fi && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Build/Runtime Stage ----------
FROM base as agent-pool

WORKDIR /app

USER root

# Copy installed dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp scripts/ ./scripts/

# Create logs directory and secure it
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

USER mcp

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8011/health || exit 1

EXPOSE 8011

CMD ["python", "-m", "uvicorn", "src.agent_pool.app:app", "--host", "0.0.0.0", "--port", "8011"]
