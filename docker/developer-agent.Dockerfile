# ---------- Base Image ----------
FROM mcp-base as base

ENV SERVICE_NAME=developer-agent \
    SERVICE_PORT=8015

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0" > requirements.txt; \
    fi && \
    python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base as developer-agent

WORKDIR /app

USER root

# Copy dependencies from deps
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp scripts/ ./scripts/

# Create logs directory and secure permissions
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

USER mcp

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8015/health || exit 1

# Expose port
EXPOSE 8015

# Run the agent
CMD ["python", "scripts/start_developer_agent.py"]
