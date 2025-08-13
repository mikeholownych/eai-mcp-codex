# ---------- Base Image ----------
FROM mcp-base as base

ENV SERVICE_NAME=collaboration-orchestrator \
    SERVICE_PORT=8012

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0\nredis>=4.0.0" > requirements.txt; \
    fi && \
    python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# ---------- Runtime Stage ----------
FROM base as collaboration-orchestrator

WORKDIR /app

USER root

# Copy installed packages
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp scripts/ ./scripts/

# Create logs directory and secure permissions
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

# Switch to secure user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8012/health || exit 1

EXPOSE 8012

CMD ["python", "-m", "uvicorn", "src.collaboration_orchestrator.app:app", "--host", "0.0.0.0", "--port", "8012"]
